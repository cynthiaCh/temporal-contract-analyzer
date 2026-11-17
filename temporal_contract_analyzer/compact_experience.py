"""Categorized experience files and inline acceptance, without audit sidecars."""
from html import escape
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import tempfile

from . import experience_memory as memory, taxonomy
from .core import EvidenceError, canonical, sha
from . import archive

VERSION = 'experience-library-single-file-v1'
SECTIONS = [('applicability', '适用条件'), ('event_relation', '建议'),
            ('preservation', '需要保留'), ('exclusion', '不适用情况'),
            ('verification', '检查方法')]
STATES = {'pending': '待审核', 'accept': '已接受', 'revise': '需修改', 'reject': '已拒绝'}


def is_library(path):
    path = Path(path)
    return path.is_file() or (path.is_dir() and not (path/'memory.json').exists()
                             and any(path.glob('*.json')))


def documents(path):
    path = Path(path)
    paths = [path] if path.is_file() else sorted(path.glob('*.json'))
    if not paths:
        raise EvidenceError('分类经验库中没有 JSON 文件')
    values = [(p, load(p)) for p in paths]
    ids = [item['id'] for _, value in values for item in value['experiences']]
    if len(ids) != len(set(ids)):
        raise EvidenceError('不同分类文件中存在重复的经验 ID')
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
        raise EvidenceError('分类名称不能为空')
    if 'review' in value:
        validate_review(value['review'])
    if not isinstance(value['experiences'], list) or not value['experiences']:
        raise EvidenceError('Experience list must not be empty')
    ids = set()
    for item in value['experiences']:
        fields = {'id', 'title', 'labels', 'requires', 'excludes'} | {key for key, _ in SECTIONS}
        if isinstance(item, dict) and 'review' in item:
            fields.add('review')
        if isinstance(item, dict) and 'proposal' in item:
            fields.add('proposal')
        if isinstance(item,dict) and 'evidence_ref' in item:fields.add('evidence_ref')
        memory.object_fields(item, fields, 'experience')
        if not memory.text(item['id']) or item['id'] in ids or not memory.text(item['title']) \
                or any(not memory.text(item[key]) for key, _ in SECTIONS):
            raise EvidenceError('Invalid or duplicate experience')
        ids.add(item['id'])
        validate_review(review_for(value, item))
        if 'proposal' in item:
            validate_proposal(item['proposal'])
        if 'evidence_ref' in item:evidence_attachment(path,item)
    return value


def _bundle(file, item):
    raw=canonical({k:v for k,v in item.items() if k!='review'}).encode('utf-8')
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
    explicit=set()
    for key,item in entries.items():
        proposal=item.get('proposal',{})
        if proposal.get('operation')!='merge' or not proposal.get('target_sha256s') or 'evidence_ref' not in item:continue
        targets=proposal['target_ids']
        if key in ancestry[key] or any(target not in entries or bundles[target]['sha256']!=code
                for target,code in zip(targets,proposal['target_sha256s'])):continue
        if any(target in ancestry[target] for target in targets):continue
        explicit.update(targets)
    superseded.update(explicit)
    return dict(policy='compact-current-guidance-v2',active_ids=sorted(set(entries)-superseded),
        superseded_ids=sorted(superseded),explicit_consolidation_source_ids=sorted(explicit),unresolved_ids=sorted(blocked),issues=issues,
        accepted_count=len(entries),active_count=len(entries)-len(superseded))


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
    """Stage compact content for review; never accept or replace existing guidance."""
    from . import experience_reflection as reflection
    experience=record['experience'];update=record['reflection_update']
    targets={b['sha256']:b for b in record['related_experiences']}
    if any(code not in targets for code in update['target_sha256s']):
        raise EvidenceError('Candidate refers to an unknown experience')
    target_ids=list(dict.fromkeys(targets[code]['id'] for code in update['target_sha256s']))
    with _locked(path):
        values=documents(path)
        if update['operation']=='evidence':
            current={b['sha256']:b for b in materialize(path)[0]}
            if len(update['target_sha256s'])!=1:
                raise EvidenceError('Evidence supplement requires one unchanged guidance target')
            target=update['target_sha256s'][0]
            if reflection.content(experience)!=reflection.content(targets[target]):
                raise EvidenceError('Evidence supplement requires unchanged current guidance')
            code=sha(canonical(dict(experience=experience,update=update)).encode())
            # Evidence for training-only guidance is archival, never memory admission.
            return dict(published_proposal_sha256=code,publication_kind='evidence_proposal' if target in current else 'provisional_evidence_proposal')
        proposal=dict(operation=update['operation'],target_ids=target_ids)
        if target_ids:proposal['target_sha256s']=list(update['target_sha256s'])
        validate_proposal(proposal)
        rules=experience['rules']
        if not isinstance(rules,list) or not rules:
            raise EvidenceError('Candidate rules must not be empty')
        for rule in rules:
            memory.object_fields(rule, {'category','body'}, 'candidate rule')
            if rule['category'] not in memory.CATEGORIES or not memory.text(rule['body']):
                raise EvidenceError('Invalid candidate rule')
        limitations=experience.get('limitations',[])
        memory.strings(limitations, 'candidate limitations')
        title=rules[0]['body'].strip().splitlines()[0][:120]
        item=dict(title='Candidate: '+title,labels=experience['labels'],
                  requires=experience['requires'],excludes=experience['excludes'])
        for key,_ in SECTIONS:
            item[key]='\n\n'.join(r['body'] for r in rules if r['category']==key) or 'Not specified in this candidate.'
        if limitations:item['exclusion']+='\n\nCandidate limitations:\n'+'\n'.join('- '+v for v in limitations)
        item['proposal']=proposal
        item=dict(id='candidate-'+sha(canonical(item).encode())[:32],**item,
                  review=dict(reviewer=None,decision='pending',at=None))
        existing=next(((file,entry) for file,value in values for entry in value['experiences'] if entry['id']==item['id']),None)
        if existing:
            file,entry=existing
            if {k:v for k,v in entry.items() if k!='review'}!={k:v for k,v in item.items() if k!='review'}:
                raise EvidenceError('Published candidate content changed; refusing to overwrite it')
        else:
            path=Path(path);file=path if path.is_file() else path/'candidates.json'
            value=next((value for owner,value in values if owner==file),None)
            if value is None:value=dict(schema_version=VERSION,category='Candidate experiences',experiences=[])
            _bundle(file,item)  # Validate before any write can affect retrieval/review.
            value['experiences'].append(item)
            _write(file,value)
        return dict(published_sha256=_bundle(file,item)[0]['sha256'],publication_kind='experience_version')


def save_review(path, request):
    """Serialize review and publication writes without separate decision files."""
    with _locked(path):
        return _save_review(path, request)


def _save_review(path, request):
    memory.object_fields(request, {'id', 'expected_record', 'expected_review', 'reviewer', 'decision'}, 'review request')
    if not memory.text(request['reviewer']) or request['decision'] not in ('accept', 'revise', 'reject'):
        raise EvidenceError('请填写审核人并选择审核结论')
    values = documents(path)
    bundles = materialize(path)[0]
    match = next(((file,value,item) for file,value in values for item in value['experiences']
                  if item['id']==request['id']), None)
    bundle = next((b for b in bundles if b['id']==request['id']), None)
    if match is None:
        raise EvidenceError('Experience not found')
    file, value, item = match
    if bundle['sha256']!=request['expected_record'] or review_for(value, item)!=request['expected_review']:
        raise EvidenceError('经验或审核状态已变化，请刷新后重新审核')
    proposal=item.get('proposal',{})
    if request['decision']=='accept' and review_for(value,item)['decision']!='accept' and proposal.get('target_sha256s'):
        current={b['id']:b['sha256'] for b in bundles}
        active=set(active_view(path)['active_ids'])
        for ident,code in zip(proposal['target_ids'],proposal['target_sha256s']):
            if current.get(ident)!=code or ident not in active:
                raise EvidenceError('Update target changed or was superseded; rebase against current guidance')
    # Move existing whole-file acceptance onto its existing items before saving.
    if 'review' in value:
        for entry in value['experiences']:
            entry.setdefault('review', dict(value['review']))
        del value['review']
    item['review'] = dict(reviewer=request['reviewer'].strip(), decision=request['decision'], at=archive.now())
    # Preserve JSON field order so a review update does not reformat every entry.
    _write(file,value)
    return dict(review=item['review'], record_sha256=bundle['sha256'], file=file.name)


def page(path):
    values = documents(path)
    bundles = {b['id']:b for b in materialize(path)[0]}
    cards = []
    lifecycle=active_view(path)
    categories = list(dict.fromkeys(value.get('category', '未分类') for _,value in values))
    entries = [(file,value,item) for file,value in values for item in value['experiences']]
    for file, value, item in entries:
        category = value.get('category', '未分类')
        review = review_for(value, item)
        state = review['decision']
        status = STATES[state]
        saved = status if state=='pending' else f'{status} · {review["reviewer"]} · {review["at"]}'
        if item['id'] in lifecycle['superseded_ids']:saved+=' · 已被替代，不参与新检索'
        elif item['id'] in lifecycle['unresolved_ids']:saved+=' · 替代关系待核对，暂保留检索'
        sections = ''.join(f'<dt>{label}</dt><dd>{escape(item[key])}</dd>'
                           for key, label in SECTIONS)
        proposal=item.get('proposal')
        appendix=('<p class="meta">证据附件：'+escape(item['evidence_ref']['path'])+'</p>') if 'evidence_ref' in item else ''
        context=('<p class="meta">Proposal: '+escape(proposal['operation'])+' · Targets: '+escape(', '.join(proposal['target_ids']) or 'none')+'</p>') if proposal else ''
        cards.append(f'<article class="panel" data-state="{state}" data-category="{escape(category, quote=True)}"><h2>{escape(item["title"])}</h2>'
                     f'<p class="meta">{escape(category)} · {escape(file.name)}</p>'
                     f'<p class="compact-status">{escape(saved)}</p>{context}{appendix}<dl>{sections}</dl>'
                     f'<form data-id="{escape(item["id"], quote=True)}" '
                     f'data-record="{bundles[item["id"]]["sha256"]}" '
                     f'data-review="{escape(canonical(review), quote=True)}">'
                     '<label>审核人<input name="reviewer" required '
                     f'value="{escape(review["reviewer"] or "", quote=True)}"></label>'
                     '<label>审核结论<select name="decision" required><option value="">请选择</option>'
                     '<option value="accept">接受</option><option value="revise">需修改</option>'
                     '<option value="reject">拒绝</option></select></label>'
                     '<button type="submit">保存审核</button></form></article>')
    html = ('<!doctype html><html lang="zh-CN"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>TempoEvo · 经验审核</title><link rel="stylesheet" href="/memory-review.css">'
            '<script src="/compact-review.js" defer></script><body class="compact-review"><main><section>'
            f'<h1>TempoEvo · 经验库 · {len(cards)} 条</h1><p id="compact-counts"></p>'
            f'<p>经验位置：<code>{escape(str(path))}</code></p>'
            '<p>阅读经验及适用边界后填写审核结论。结果写回对应分类文件，不生成独立审核文件。</p>'
            '<label>分类<select id="compact-category"><option value="">全部分类</option>'
            + ''.join(f'<option>{escape(category)}</option>' for category in categories) + '</select></label>'
            '<label>显示<select id="compact-filter"><option value="all">全部经验</option>'
            '<option value="pending">待审核</option><option value="accept">已接受</option>'
            '<option value="revise">需修改</option><option value="reject">已拒绝</option></select></label>'
            '<p id="compact-empty" hidden>此分类下没有经验。</p>'
            + ''.join(cards) + '</section></main><p id="message" role="status" aria-live="polite"></p></body></html>')
    return html.encode('utf-8')
