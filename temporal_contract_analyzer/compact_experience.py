"""Categorized experience files and inline acceptance, without audit sidecars."""
from html import escape
from contextlib import contextmanager
import fcntl
import json
import os
import re
from pathlib import Path
import tempfile

from . import experience_memory as memory, taxonomy
from .core import EvidenceError, canonical, sha
from . import archive

VERSION = 'experience-library-single-file-v1'
SECTIONS = [('applicability', 'Applicability conditions'), ('event_relation', 'Recommendation'),
            ('preservation', 'Preservation requirements'), ('exclusion', 'Exclusions'),
            ('verification', 'Verification')]
STATES = {'pending': 'Pending review', 'accept': 'Accepted', 'revise': 'Revision required', 'reject': 'Rejected'}


def is_library(path):
    path = Path(path)
    return path.is_file() or (path.is_dir() and not (path/'memory.json').exists()
                             and any(path.glob('*.json')))


def documents(path):
    path = Path(path)
    paths = [path] if path.is_file() else sorted(path.glob('*.json'))
    if not paths:
        raise EvidenceError('No JSON files in the categorized experience library')
    values = [(p, load(p)) for p in paths]
    ids = [item['id'] for _, value in values for item in value['experiences']]
    if len(ids) != len(set(ids)):
        raise EvidenceError('Duplicate experience IDs across category files')
    return values


def review_for(value, item):
    return item.get('review', value.get('review')) or dict(reviewer=None, decision='pending', at=None)


def validate_review(review):
    memory.object_fields(review, {'reviewer', 'decision', 'at'}, 'inline review')
    if review['decision'] not in STATES:
        raise EvidenceError('Invalid inline review')
    if review['decision']=='pending':
        if review['reviewer'] is not None or review['at'] is not None:
            raise EvidenceError('Pending experience must not claim a reviewer or review time')
    elif not memory.text(review['reviewer']) or not memory.text(review['at']):
        raise EvidenceError('A completed review requires reviewer and time')


def validate_proposal(proposal):
    fields={'operation','target_ids'}
    if isinstance(proposal,dict) and 'target_sha256s' in proposal:fields.add('target_sha256s')
    memory.object_fields(proposal, fields, 'candidate proposal')
    operation=proposal['operation'];targets=proposal['target_ids']
    memory.strings(targets, 'candidate targets')
    if operation not in ('new','revise','merge') or (operation=='new' and targets) \
            or (operation=='revise' and len(targets)!=1) or (operation=='merge' and len(targets)<2):
        raise EvidenceError('Invalid candidate operation or targets')
    if 'target_sha256s' in proposal:
        hashes=proposal['target_sha256s']
        if not isinstance(hashes,list) or len(hashes)!=len(targets) or any(not isinstance(c,str) or len(c)!=64 or any(x not in '0123456789abcdef' for x in c) for c in hashes):
            raise EvidenceError('Invalid exact target hashes')



def evidence_attachment(file,item):
    """Load a content-bound local evidence appendix, never solver guidance."""
    ref=item['evidence_ref']
    memory.object_fields(ref,{'path','sha256'},'evidence attachment')
    if not isinstance(ref['path'],str) or not ref['path'].startswith('evidence/') or '\\' in ref['path'] or '..' in Path(ref['path']).parts:
        raise EvidenceError('Evidence attachment must stay in library evidence/')
    base=Path(file).parent.resolve();target=base/ref['path']
    if base not in target.resolve().parents or not target.is_file():
        raise EvidenceError('Missing or external evidence attachment')
    raw=target.read_bytes()
    if ref['sha256']!=sha(raw):raise EvidenceError('Evidence attachment digest mismatch')
    value=json.loads(raw)
    if not isinstance(value,dict) or value.get('schema_version')!='experience-consolidation-evidence-v1' or value.get('consolidated_id')!=item['id']:
        raise EvidenceError('Evidence attachment identity mismatch')
    expected={k:item[k] for k in ('id','title','labels','requires','excludes')+tuple(k for k,_ in SECTIONS)}
    if value.get('merged_guidance')!=expected:raise EvidenceError('Evidence appendix does not bind current guidance')
    sources=value.get('sources',[]);proposal=item.get('proposal',{})
    if not isinstance(sources,list) or not all(isinstance(s,dict) for s in sources):raise EvidenceError('Invalid evidence sources')
    if [(s.get('id'),s.get('bundle_sha256')) for s in sources]!=list(zip(proposal.get('target_ids',[]),proposal.get('target_sha256s',[]))):
        raise EvidenceError('Evidence appendix does not bind exact merge targets')
    try:
        for source in sources:
            original=source['record']
            if original['id']!=source['id'] or _bundle(Path(source['file']),original)[0]['sha256']!=source['bundle_sha256']:
                raise EvidenceError('Archived evidence source content mismatch')
    except (KeyError,TypeError) as error:
        raise EvidenceError('Incomplete archived evidence source') from error
    return value


def load(path):
    value = json.loads(Path(path).read_text(encoding='utf-8'))
    required = {'schema_version', 'experiences'}
    if isinstance(value, dict) and 'review' in value:
        required.add('review')
    if isinstance(value, dict) and 'category' in value:
        required.add('category')
    memory.object_fields(value, required, 'experience file')
    if value['schema_version'] != VERSION:
        raise EvidenceError('Unknown single-file experience format')
    if 'category' in value and not memory.text(value['category']):
        raise EvidenceError('Category name must not be empty')
    if 'review' in value:
        validate_review(value['review'])
    if not isinstance(value['experiences'], list):
        raise EvidenceError('Experience list must be an array')
    ids = set()
    for item in value['experiences']:
        fields = {'id', 'title', 'labels', 'requires', 'excludes'} | {key for key, _ in SECTIONS}
        if isinstance(item, dict) and 'review' in item:
            fields.add('review')
        if isinstance(item, dict) and 'proposal' in item:
            fields.add('proposal')
        if isinstance(item,dict) and 'evidence_ref' in item:fields.add('evidence_ref')
        if isinstance(item,dict) and 'summary' in item:fields.add('summary')
        if isinstance(item,dict) and 'learning' in item:fields.add('learning')
        if isinstance(item,dict) and 'superseded_by' in item:fields.add('superseded_by')
        if isinstance(item,dict) and 'superseded' in item:fields.add('superseded')
        memory.object_fields(item, fields, 'experience')
        if not memory.text(item['id']) or item['id'] in ids or not memory.text(item['title']) \
                or any(not memory.text(item[key]) for key, _ in SECTIONS):
            raise EvidenceError('Invalid or duplicate experience')
        if 'superseded_by' in item and (not memory.text(item['superseded_by']) or item['superseded_by']==item['id']):raise EvidenceError('Invalid explicit replacement')
        if 'superseded' in item and type(item['superseded']) is not bool:raise EvidenceError('Invalid replacement state')
        ids.add(item['id'])
        validate_review(review_for(value, item))
        if 'summary' in item:validate_summary(item['summary'])
        if 'learning' in item:
            from .experience_learning import validate
            validate(item['learning'])
        if 'proposal' in item:
            validate_proposal(item['proposal'])
        if 'evidence_ref' in item:evidence_attachment(path,item)
    return value


def validate_summary(value):
    memory.object_fields(value, {'text','expert_questions','review','source_record'}, 'experience summary')
    if not memory.text(value['text']) or not memory.text(value['expert_questions']):
        raise EvidenceError('Summary and expert questions must not be empty')
    if not isinstance(value['source_record'],str) or not re.fullmatch(r'[0-9a-f]{64}',value['source_record']):
        raise EvidenceError('Summary must bind its experience version')
    validate_review(value['review'])


def reviewed_summaries(path):
    return {item['id']:item['summary'] for file,value in documents(path) for item in value['experiences']
            if 'summary' in item and item['summary']['review']['decision']=='accept'
            and item['summary']['source_record']==_bundle(file,item)[0]['sha256']}


def save_summary(path, request):
    memory.object_fields(request, {'id','expected_record','expected_summary','text','expert_questions','reviewer','decision'}, 'summary review request')
    if not memory.text(request['reviewer']) or request['decision'] not in STATES:
        raise EvidenceError('Enter a reviewer and select a summary decision')
    with _locked(path):
        values=documents(path)
        match=next(((file,value,item) for file,value in values for item in value['experiences'] if item['id']==request['id']),None)
        if match is None:raise EvidenceError('Experience not found')
        file,value,item=match
        if _bundle(file,item)[0]['sha256']!=request['expected_record'] or item.get('summary')!=request['expected_summary']:
            raise EvidenceError('Experience or summary changed; refresh before reviewing again')
        review=(dict(reviewer=None,decision='pending',at=None) if request['decision']=='pending' else
                dict(reviewer=request['reviewer'].strip(),decision=request['decision'],at=archive.now()))
        summary=dict(text=request['text'].strip(),expert_questions=request['expert_questions'].strip(),
                     source_record=request['expected_record'],review=review)
        validate_summary(summary)
        item['summary']=summary
        _write(file,value)
        return dict(summary=summary,file=file.name)


def _bundle(file, item):
    raw=canonical({k:v for k,v in item.items() if k not in ('review','summary','learning','superseded_by','superseded')}).encode('utf-8')
    code=sha(raw)
    bundle=memory.seal(dict(schema_version=memory.BUNDLE_VERSION_V2,
        id=item['id'], version='single-file-v1', parent_sha256=None,
        taxonomy_version=taxonomy.VERSION, labels=item['labels'],
        requires=item['requires'], excludes=item['excludes'],
        rules=[dict(id=f'R{i:02d}', category=key, body=item[key])
               for i, (key, _) in enumerate(SECTIONS, 1)],
        review=dict(status='candidate', kind='ai_assisted', source_sha256=code,
                    limitations=['Content acceptance does not establish cross-task effectiveness.']),
        audit=dict(sources=[dict(path=file.name, sha256=code)],
                   rule_links=[], notes=[], outcome_refs=[])))
    memory.validate(bundle, lambda digest:raw if digest==code else b'')
    return bundle, code, raw


def materialize(path):
    """Adapt categorized content to existing retrieval objects in memory only."""
    bundles, decisions, blobs = [], [], {}
    entries = [(file, value, item) for file,value in documents(path) for item in value['experiences']]
    sequence=0
    for file, value, item in entries:
        bundle, code, raw = _bundle(file, item)
        blobs[code] = raw
        bundles.append(bundle)
        review = review_for(value, item)
        if review['decision']=='pending':
            continue
        sequence+=1
        row = dict(review, reason='', scope='research', actor='named_operator',
                   schema_version='experience-expert-decision-v1',
                   candidate_sha256=bundle['sha256'], report_sha256=None, sequence=sequence,
                   rules=[dict(rule_id=r['id'], supported=review['decision']=='accept', reason='')
                          for r in bundle['rules']])
        row['sha256'] = memory.digest(canonical(row))
        decisions.append(row)
    return bundles, decisions, blobs


def active_view(path):
    """Resolve unambiguous accepted replacements without altering archive/reviews.

    Ambiguous components remain visible with issues; never pick a branch by time,
    file order or score. Pending/rejected updates cannot supersede accepted text.
    """
    entries={item['id']:item for _,value in documents(path) for item in value['experiences']
             if review_for(value,item)['decision']=='accept'}
    bundles={b['id']:b for b in materialize(path)[0]}
    edges={key:set() for key in entries};neighbors={key:set() for key in entries}
    issues=[];bad=set();owners={}
    for key,item in entries.items():
        proposal=item.get('proposal',{})
        if proposal.get('operation') not in ('revise','merge'):continue
        targets=proposal['target_ids']
        for i,target in enumerate(targets):
            if target not in entries:
                issues.append(dict(id=key,code='unresolved_target',target_id=target));bad.add(key);continue
            edges[key].add(target);neighbors[key].add(target);neighbors[target].add(key)
            owners.setdefault(target,[]).append(key)
            expected=proposal.get('target_sha256s')
            if expected is not None and expected[i]!=bundles[target]['sha256']:
                issues.append(dict(id=key,code='stale_target',target_id=target));bad.add(key)
    def ancestors(key):
        found=set();pending=list(edges[key])
        while pending:
            target=pending.pop()
            if target not in found:found.add(target);pending.extend(edges[target])
        return found
    ancestry={key:ancestors(key) for key in entries}
    for target,children in owners.items():
        # An explicitly accepted descendant that merges every competing branch
        # resolves that fork; it must be possible to consolidate old conflicts.
        resolved=any(set(children)<=parents for parents in ancestry.values())
        if len(children)>1 and not resolved:
            issues.append(dict(id=target,code='conflicting_replacements',replacement_ids=sorted(children)))
            bad.add(target)
    # DFS also detects cycles through merges. Propagate ambiguity across the
    # connected lineage so descendants cannot hide an unresolved branch.
    visiting=set();done=set()
    def visit(key):
        if key in visiting:
            issues.append(dict(id=key,code='replacement_cycle'));bad.add(key);return
        if key in done:return
        visiting.add(key)
        for target in sorted(edges[key]):visit(target)
        visiting.remove(key);done.add(key)
    for key in sorted(entries):visit(key)
    blocked=set(bad);pending=list(bad)
    while pending:
        for other in neighbors[pending.pop()]-blocked:blocked.add(other);pending.append(other)
    superseded={target for key,targets in edges.items() if key not in blocked for target in targets}
    # A reviewed exact-target consolidation may replace those sources even if
    # their older ancestry is incomplete. It does not choose between unrelated
    # branches or retire any target not explicitly covered by the reviewed merge.
    explicit=set();resolved_merges=set()
    for key,item in entries.items():
        proposal=item.get('proposal',{})
        # Exact target hashes and acceptance authorize replacement; an optional
        # archival appendix must not decide whether a reviewed merge takes effect.
        if proposal.get('operation')!='merge' or not proposal.get('target_sha256s'):continue
        targets=proposal['target_ids']
        if key in ancestry[key] or any(target not in entries or bundles[target]['sha256']!=code
                for target,code in zip(targets,proposal['target_sha256s'])):continue
        if any(target in ancestry[target] for target in targets):continue
        explicit.update(targets)
        if all(set(owners.get(target,[]))=={key} for target in targets):
            resolved_merges.add(key)
    superseded.update(explicit)
    superseded.update(item['id'] for _,value in documents(path) for item in value['experiences'] if item.get('superseded') is True)
    superseded.update(key for key,item in entries.items() if item.get('superseded_by') in entries and item['superseded_by'] not in blocked)
    blocked.difference_update(resolved_merges)
    return dict(policy='compact-current-guidance-v2',active_ids=sorted(set(entries)-superseded),
        superseded_ids=sorted(superseded),explicit_consolidation_source_ids=sorted(explicit),unresolved_ids=sorted(blocked),issues=issues,
        accepted_count=len(entries),active_count=len(set(entries)-superseded))


@contextmanager
def _locked(path):
    # Lock the stable directory inode; atomic JSON replacement needs no lock sidecar.
    path=Path(path)
    descriptor=os.open(path.parent if path.is_file() else path, os.O_RDONLY)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
    finally:
        os.close(descriptor)


def _write(file, value):
    descriptor, temporary = tempfile.mkstemp(prefix='.write-', dir=file.parent)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, file)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def publish_candidate(path, record):
    """Update one stable entry in place; only explicit merges retire other IDs."""
    from . import experience_reflection as reflection
    from .experience_learning import empty,validate
    experience=record['experience'];update=record['reflection_update']
    from .tempoevo_v4 import EXPERIENCE_SCHEMA
    from ._session_runtime.schema_validator import validate as validate_schema
    try:validate_schema(experience,EXPERIENCE_SCHEMA)
    except ValueError as error:raise EvidenceError('Invalid experience: '+str(error)) from error
    targets={b['sha256']:b for b in record['related_experiences']}
    if any(code not in targets for code in update['target_sha256s']):raise EvidenceError('Unknown experience target')
    with _locked(path):
        values=documents(path)
        if update['operation']=='evidence':
            target=update['target_sha256s'][0]
            if reflection.content(experience)!=reflection.content(targets[target]):raise EvidenceError('Evidence supplement must preserve guidance')
            return dict(published_proposal_sha256=target,publication_kind='evidence_proposal')
        target_ids=[targets[code]['id'] for code in update['target_sha256s']]
        primary=target_ids[0] if target_ids else None
        if update['operation']=='merge':
            for code,ident in zip(update['target_sha256s'][1:],target_ids[1:]):
                target=next(((f,i) for f,v in values for i in v['experiences'] if i['id']==ident),None)
                if target is None or _bundle(target[0],target[1])[0]['sha256']!=code:raise EvidenceError('Merge target changed')
        found=next(((file,value,item) for file,value in values for item in value['experiences'] if item['id']==primary),None)
        if primary and found is None:raise EvidenceError('Stable update target not found')
        item=dict(title=found[2]['title'] if found else 'Candidate: '+experience['rules'][0]['body'].splitlines()[0][:120],
                  labels=experience['labels'],requires=experience['requires'],excludes=experience['excludes'])
        for key,_ in SECTIONS:item[key]='\n\n'.join(r['body'] for r in experience['rules'] if r['category']==key) or 'Not specified in this candidate.'
        if experience.get('limitations'):item['exclusion']+='\n\nCandidate limitations:\n'+'\n'.join('- '+v for v in experience['limitations'])
        item=dict(id=primary or 'candidate-'+sha(canonical(item).encode())[:32],**item)
        if update['operation']=='merge':
            item['proposal']=dict(operation='revise' if len(target_ids)==2 else 'merge',target_ids=target_ids[1:],target_sha256s=update['target_sha256s'][1:])
        existing=found or next(((file,value,old) for file,value in values for old in value['experiences'] if old['id']==item['id']),None)
        if existing:
            file,value,old=existing
            same=all(old.get(k)==v for k,v in item.items())
            if not same and not primary:raise EvidenceError('Published candidate was edited; refusing to overwrite it')
            if not same and primary:
                if _bundle(file,old)[0]['sha256']!=update['target_sha256s'][0] or (primary not in active_view(path)['active_ids'] and review_for(value,old)['decision']!='revise'):
                    raise EvidenceError('Update target changed; rebase against current guidance')
            if same:
                if update['operation']=='merge':
                    for owner,document in values:
                        changed=False
                        for target in document['experiences']:
                            if target['id'] in target_ids[1:] and target.get('superseded_by')!=primary:
                                target['superseded_by']=primary;changed=True
                        if changed:_write(owner,document)
                return dict(published_sha256=_bundle(file,old)[0]['sha256'],publication_kind='experience_update')
            value['experiences'][value['experiences'].index(old)]=item
        else:
            path=Path(path);file=path if path.is_file() else (values[0][0] if len(values)==1 and not values[0][1]['experiences'] else path/'candidates.json')
            value=next((v for f,v in values if f==file),None)
            if value is None:value=dict(schema_version=VERSION,category='Candidate experiences',experiences=[])
            value['experiences'].append(item)
        item['review']=dict(reviewer=None,decision='pending',at=None)
        item['learning']=record.get('learning',empty());validate(item['learning'])
        bundle=_bundle(file,item)[0]
        from .business_retrieval import summary as preview
        item['summary']=dict(text=record.get('abstract') or preview(bundle),expert_questions='None.',source_record=bundle['sha256'],
            review=dict(reviewer=None,decision='pending',at=None))
        validate_summary(item['summary'])
        _write(file,value)
        if update['operation']=='merge':
            for owner,document in values:
                dirty=False
                for old in document['experiences']:
                    if old['id'] in target_ids[1:]:
                        code=update['target_sha256s'][target_ids.index(old['id'])]
                        if _bundle(owner,old)[0]['sha256']!=code:raise EvidenceError('Merge target changed')
                        old['superseded_by']=item['id'];dirty=True
                if dirty:_write(owner,document)
        return dict(published_sha256=bundle['sha256'],publication_kind='experience_update' if primary else 'experience_entry')


def save_review(path, request):
    """Serialize review and publication writes without separate decision files."""
    with _locked(path):
        return _save_review(path, request)


def _save_review(path, request):
    memory.object_fields(request, {'id', 'expected_record', 'expected_review', 'reviewer', 'decision'}, 'review request')
    if not memory.text(request['reviewer']) or request['decision'] not in ('accept', 'revise', 'reject'):
        raise EvidenceError('Enter a reviewer and select a review decision')
    values = documents(path)
    bundles = materialize(path)[0]
    match = next(((file,value,item) for file,value in values for item in value['experiences']
                  if item['id']==request['id']), None)
    bundle = next((b for b in bundles if b['id']==request['id']), None)
    if match is None:
        raise EvidenceError('Experience not found')
    file, value, item = match
    if bundle['sha256']!=request['expected_record'] or review_for(value, item)!=request['expected_review']:
        raise EvidenceError('Experience or review state changed; refresh before reviewing again')
    proposal=item.get('proposal',{})
    if request['decision']=='accept' and review_for(value,item)['decision']!='accept' and proposal.get('target_sha256s'):
        current={b['id']:b['sha256'] for b in bundles}
        active=set(active_view(path)['active_ids'])
        for ident,code in zip(proposal['target_ids'],proposal['target_sha256s']):
            owned=next((i for _,v in values for i in v['experiences'] if i['id']==ident and i.get('superseded_by')==item['id'] and i.get('superseded') is True),None)
            if current.get(ident)!=code or (ident not in active and owned is None):
                raise EvidenceError('Update target changed or was superseded; rebase against current guidance')
    # Move existing whole-file acceptance onto its existing items before saving.
    if 'review' in value:
        for entry in value['experiences']:
            entry.setdefault('review', dict(value['review']))
        del value['review']
    item['review'] = dict(reviewer=request['reviewer'].strip(), decision=request['decision'], at=archive.now())
    # Preserve JSON field order so a review update does not reformat every entry.
    _write(file,value)
    if request['decision']=='accept':
        for owner,document in values:
            changed=False
            for target in document['experiences']:
                if target.get('superseded_by')==item['id'] and not target.get('superseded'):
                    target['superseded']=True;changed=True
            if changed:_write(owner,document)
    return dict(review=item['review'], record_sha256=bundle['sha256'], file=file.name, lifecycle=active_view(path))


def page(path):
    values = documents(path)
    bundles = {b['id']:b for b in materialize(path)[0]}
    cards = []
    queue = []
    lifecycle=active_view(path)
    superseded = set(lifecycle['superseded_ids'])
    entries = [(file,value,item) for file,value in values for item in value['experiences']
               if item['id'] not in superseded]
    categories = list(dict.fromkeys(value.get('category', 'Uncategorized') for _,value,_ in entries))
    for file, value, item in entries:
        category = value.get('category', 'Uncategorized')
        review = review_for(value, item)
        state = review['decision']
        view_state = 'active' if state=='accept' else state
        status = {'active':'Active', 'pending':'Pending review'}.get(view_state, STATES[state])
        saved = status if state=='pending' else f'{status} · {review["reviewer"]} · {review["at"]}'
        if item['id'] in lifecycle['unresolved_ids']:saved+=' · Supersession requires review; retained for retrieval for now'
        sections = ''.join(f'<dt>{label}</dt><dd>{escape(item[key])}</dd>'
                           for key, label in SECTIONS)
        proposal=item.get('proposal')
        appendix=('<p class="meta">Evidence attachment: '+escape(item['evidence_ref']['path'])+'</p>') if 'evidence_ref' in item else ''
        context=('<p class="meta">Proposal: '+escape(proposal['operation'])+' · Targets: '+escape(', '.join(proposal['target_ids']) or 'none')+'</p>') if proposal else ''
        from .experience_learning import score,empty
        metadata=item.get('learning',empty());origin=metadata['origin']
        learning_info=('Unknown' if origin is None else origin['reflection_model']+' / '+str(origin['reflection_effort'])+'; first success: '+str(origin['first_success_attempt']))
        learning_display=f'<p class="meta">Weight: {score(metadata)} · Reflection model: {escape(learning_info)}</p>'
        summary=item.get('summary')
        summary_state=summary['review']['decision'] if summary else 'pending'
        if summary and summary['source_record']!=bundles[item['id']]['sha256']:summary_state='stale'
        summary_labels=dict(STATES,stale='Outdated · review again')
        summary_status=summary_labels[summary_state]
        summary_review=(summary or {}).get('review',{})
        reviewed_by=' · '.join(str(summary_review[k]) for k in ('reviewer','at') if summary_review.get(k))
        questions=summary['expert_questions'] if summary else 'Not reviewed.'
        queue.append(f'<button type="button" class="queue-item" data-target="{escape(item["id"],quote=True)}">'
                     f'<strong>{escape(item["title"])}</strong><small>{escape(category)} · {escape(status)}</small>'
                     f'<small>Summary · {escape(summary_status)}</small></button>')
        summary_panel=(f'<section class="summary-panel"><div class="section-heading"><h3>Retrieval summary</h3>'
            f'<span class="summary-status">{escape(summary_status)}</span></div>'
            '<p class="meta">Review against the full experience below. Only accepted summaries inform retrieval.</p>'
            f'<p class="meta summary-review-meta">{escape(reviewed_by)}</p>'
            f'<form class="summary-form" data-summary-id="{escape(item["id"],quote=True)}" '
            f'data-record="{bundles[item["id"]]["sha256"]}" data-summary="{escape(canonical(summary),quote=True)}">'
            f'<label>Summary<textarea name="text" required rows="7">{escape(summary["text"] if summary else "")}</textarea></label>'
            f'<label>Questions for the expert<textarea name="expert_questions" required rows="3">{escape(questions)}</textarea></label>'
            '<div class="review-fields"><label>Reviewer<input name="reviewer" required value="'
            +escape((summary or {}).get('review',{}).get('reviewer') or '',quote=True)+'"></label>'
            '<label>Summary decision<select name="decision" required><option value="">Select a decision</option>'
            '<option value="pending">Save draft · Pending review</option><option value="accept">Accept summary</option>'
            '<option value="revise">Revision required</option><option value="reject">Reject summary</option></select></label></div>'
            '<button type="submit" class="primary">Save summary review</button></form></section>')
        cards.append(f'<article class="panel" data-id="{escape(item["id"],quote=True)}" data-summary-state="{summary_state}" data-state="{state}" data-lifecycle="{view_state}" data-category="{escape(category, quote=True)}"><h2>{escape(item["title"])}</h2>'
                     f'<p class="meta">{escape(category)} · {escape(file.name)}</p>'
                     f'<p class="compact-status">{escape(saved)}</p>{learning_display}{context}{appendix}{summary_panel}<details class="full-experience"><summary>Full experience · applicability and verification</summary><dl>{sections}</dl></details><h3>Experience review</h3>'
                     f'<form data-id="{escape(item["id"], quote=True)}" '
                     f'data-record="{bundles[item["id"]]["sha256"]}" '
                     f'data-review="{escape(canonical(review), quote=True)}">'
                     '<label>Reviewer<input name="reviewer" required '
                     f'value="{escape(review["reviewer"] or "", quote=True)}"></label>'
                     '<label>Review decision<select name="decision" required><option value="">Select a decision</option>'
                     '<option value="accept">Accept</option><option value="revise">Revision required</option>'
                     '<option value="reject">Reject</option></select></label>'
                     '<button type="submit">Save review</button></form></article>')
    html = ('<!doctype html><html lang="en"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>TempoEvo · Expert review</title><link rel="stylesheet" href="/memory-review.css">'
            '<script src="/compact-review.js" defer></script><body class="compact-review">'
            '<header class="review-topbar"><span class="review-brand">T</span><strong>TempoEvo</strong>'
            '<span class="brand-caption">RESEARCH WORKSPACE</span><span class="local">Expert review · Local only</span></header>'
            '<div class="review-heading"><p class="eyebrow">TEMPORAL CONTRACTS / EXPERIENCE LEARNING</p>'
            '<h1>Experience &amp; summary review</h1><p>Inspect the full guidance. Refine its summary. Record your decisions.</p></div>'
            '<main><aside class="review-queue"><h2>Review queue</h2>'
            '<p id="compact-counts"></p>'
            '<label>Search<input id="compact-search" type="search" placeholder="Title, ID or content"></label>'
            '<label>Category<select id="compact-category"><option value="">All categories</option>'
            + ''.join(f'<option>{escape(category)}</option>' for category in categories) + '</select></label>'
            '<label>Experience state<select id="compact-filter"><option value="all">All experiences</option>'
            '<option value="active">Active</option><option value="pending">Pending review</option>'
            '<option value="revise">Revision required</option><option value="reject">Rejected</option></select></label>'
            '<label>Summary state<select id="summary-filter"><option value="all">All summaries</option>'
            '<option value="pending">Pending review / Missing</option><option value="accept">Accepted</option>'
            '<option value="revise">Revision required</option><option value="reject">Rejected</option><option value="stale">Outdated</option></select></label>'
            '<nav id="compact-queue" aria-label="Experiences">'+''.join(queue)+'</nav></aside>'
            '<section class="review-detail"><p id="compact-empty" hidden>No experiences match these filters.</p>'
            + ''.join(cards) + f'<details class="library-location"><summary>Library location</summary><code>{escape(str(path))}</code></details>'
            '</section></main><p id="message" role="status" aria-live="polite"></p></body></html>')
    return html.encode('utf-8')
