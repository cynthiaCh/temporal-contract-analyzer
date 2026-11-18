"""Explicit AI-delegated research review, separate from human expert approval.

All model dispatch is through the supplied backend (normally MeteredBackend).
This module never invokes the human approval or human expert-summary APIs.
"""
from copy import deepcopy
import json
import os
import tempfile
from pathlib import Path

from . import archive, experience_memory as memory, taxonomy
from .candidate_files import capture
from .core import EvidenceError, canonical, sha

SNAPSHOT_VERSION='experience-ai-reviewed-snapshot-v1'
REVIEW_VERSION='experience-ai-delegated-review-v1'
STR=dict(type='string',minLength=1)


def obj(properties):
    return dict(type='object',properties=properties,required=list(properties),additionalProperties=False)


CITATIONS=dict(type='array',items=obj(dict(file=STR,quote=STR)))
REVIEW_SCHEMA=obj(dict(decision=dict(type='string',enum=['accept','reject']),reason=STR,
    rules=dict(type='array',items=obj(dict(rule_id=STR,supported=dict(type='boolean'),reason=STR,evidence=CITATIONS)))))


def failure_schema():
    from .tempoevo_v4 import EXPERIENCE_SCHEMA
    return obj(dict(decision=dict(type='string',enum=['candidate','no_update']),reason=STR,
        confirmed_conclusions=dict(type='array',items=STR),unverified_hypotheses=dict(type='array',items=STR),
        unresolved_behaviors=dict(type='array',items=STR),
        experience=dict(anyOf=[dict(type='null'),EXPERIENCE_SCHEMA]),
        rule_evidence=dict(type='array',items=obj(dict(rule_index=dict(type='integer',minimum=1),evidence=CITATIONS)))))


def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))


def immutable(path,value):
    path=Path(path);raw=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if path.read_bytes()!=raw:raise EvidenceError('Immutable AI review conflict: '+str(path))
    else:
        fd,temp=tempfile.mkstemp(prefix='.review-',dir=path.parent)
        try:
            with os.fdopen(fd,'wb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
            os.replace(temp,path)
        finally:
            if os.path.exists(temp):os.unlink(temp)
    return value


def public_context(trajectory_root):
    """Exclude training acceptance, raw Gold, evaluator paths, and expert identity."""
    root=Path(trajectory_root);p=read(root/'protocol.json');state=read(root/'state.json')
    if p['mode']!='learning':raise EvidenceError('AI review is restricted to D learning cases')
    files,_=capture(root/'original');sources={k:v.decode('utf-8') for k,v in files.items()}
    attempts=[]
    for row in state.get('attempts',[]):
        feedback=row.get('feedback') or {}
        attempts.append(dict(number=row['number'],visible_passed=row['visible_passed'],
            public_feedback={k:deepcopy(feedback[k]) for k in ('observations','regressions','unknowns') if k in feedback},
            candidate_sources=deepcopy(row['candidate_sources'])))
    return dict(task_id=p.get('task_id'),task=p['task'],sources=sources,attempts=attempts,
                source_sha256=p.get('source_sha256'))


def _evidence(rows,context,required=False):
    from .tempoevo_v4 import evidence_valid
    if required and not rows:raise EvidenceError('Accepted AI rules require exact public citations')
    evidence_valid(rows,context['task'],context['sources'])


def _context(store,context):
    code=sha(canonical(context).encode());immutable(Path(store)/'workflow/ai-review-contexts'/(code+'.json'),context)
    return code


def _seal(value):return dict(value,sha256=sha(canonical(value).encode()))


def _receipt(store,context,decision,reason,model,candidate=None,rules=(),method='deterministic_no_update',at=None,output=None):
    value=dict(schema_version=REVIEW_VERSION,reviewer_kind='ai_delegated',human_reviewed=False,
        delegation='User explicitly delegated this experiment content review and failure analysis to AI; see the bound run authorization.',
        scope='exploratory',effectiveness_verified=False,decision=decision,reason=reason,
        candidate_sha256=candidate,rules=list(rules),model=deepcopy(model),evaluation_method=method,
        context_sha256=_context(store,context),at=at or archive.now(),
        model_output_sha256=sha(canonical(output).encode()) if output is not None else None)
    if output is not None:immutable(Path(store)/'workflow/ai-review-outputs'/(value['model_output_sha256']+'.json'),output)
    receipt=_seal(value);immutable(Path(store)/'workflow/ai-reviews'/(receipt['sha256']+'.json'),receipt)
    return receipt


def _run(backend,payload,model,limits,directory):
    """Idempotent completed-stage reuse; never silently replay a started call."""
    directory=Path(directory);input_hash=sha(canonical(payload).encode())
    if (directory/'started.json').exists():
        started=read(directory/'started.json')
        if started['input_sha256']!=input_hash:raise EvidenceError('AI review input changed')
        if not (directory/'result.json').exists():raise EvidenceError('Started AI review cannot silently replay')
        result=read(directory/'result.json')
    else:
        immutable(directory/'input.json',payload)
        started=dict(input_sha256=input_hash,at=archive.now(),reviewer_kind='ai_delegated',human_reviewed=False)
        immutable(directory/'started.json',started);(directory/'execution').mkdir()
        result=backend.execute('extract',payload,model,limits,directory/'execution')
        immutable(directory/'result.json',result)
    if result.get('valid') is not True or result.get('model')!=model:
        raise EvidenceError('AI review execution invalid: '+str(result.get('error')))
    from ._session_runtime.schema_validator import validate
    validate(result.get('output'),payload['schema'])
    return result['output'],started['at']


def _result(receipt,outcome):
    return dict(decision=receipt['decision'],outcome=outcome,candidate_sha256=receipt['candidate_sha256'],
        receipt_sha256=receipt['sha256'],reviewer_kind='ai_delegated',human_reviewed=False)


def record_no_update(store,trajectory_root,reason,directory=None,model=None):
    if not memory.text(reason):raise EvidenceError('AI no-update needs an explicit reason')
    context=public_context(trajectory_root);local=Path(directory)/'decision.json' if directory else None
    if local and local.exists():
        receipt=read(local)
        if receipt['reason']!=reason or receipt['context_sha256']!=sha(canonical(context).encode()):
            raise EvidenceError('AI no-update decision changed')
    else:
        receipt=_receipt(store,context,'no_update',reason,model or dict(model='deterministic_controller'),
                         method='deterministic_no_update')
        if local:immutable(local,receipt)
    return _result(receipt,'ai_no_update')


def review_candidate(backend,trajectory_root,store,candidate_sha256,directory,model,limits,*,evidence_only=False):
    context=public_context(trajectory_root);bundles={b['sha256']:b for b in memory.records(store)}
    if candidate_sha256 not in bundles:raise EvidenceError('Unknown AI-review candidate')
    bundle=bundles[candidate_sha256]
    candidate={k:deepcopy(bundle[k]) for k in ('sha256','id','labels','requires','excludes','rules')}
    prior=read(Path(trajectory_root)/'memory-snapshot.json')
    approved=[{k:deepcopy(entry['bundle'][k]) for k in ('sha256','id','labels','requires','excludes','rules')}
              for entry in prior['entries']]
    payload=dict(task=context['task'],sources=context['sources'],public_context=context,candidate=candidate,
        prior_approved_guidance=approved,candidate_lineage_notes=deepcopy(bundle['audit']['notes']),
        schema=REVIEW_SCHEMA,instruction='You are the explicitly delegated AI reviewer, not a human expert. '
        'Review each candidate rule in exact order against original public task/source and public observations. '
        'Accept only when every rule is source-supported, applicability and exclusions are justified, and no '
        'unproved causal or cross-task effectiveness claim is made. Give exact original public quotes for each '
        'supported rule. Evidence file must be exactly TASK or a key in sources. Quote that exact original source text. '
        'Public observations/feedback are not source files: never attribute their wording to README or VISIBLE_CHECKS.md. '
        'If a rule lacks original source support, mark it unsupported and reject instead of inventing a citation. '
        'Reject unsupported claims; do not infer hidden Gold assertions or new requirements. '
        'Compare the prior approved guidance for duplication, conflict, scope and incremental value; '
        'a different language or wording alone is not a new mechanism. For revisions or merges, check preserved obligations and supported changes. '
        'An evidence-only review may confirm an unchanged target without claiming a new rule. '
        'Training success alone does not prove transfer effectiveness. Return accept or reject; do not rewrite rules.')
    if evidence_only:
        payload['instruction']+=' This is an evidence-only proposal for unchanged approved guidance. Judge the additional evidence; this decision must neither activate nor revoke the existing rule.'
    output,at=_run(backend,payload,model,limits,directory)
    if [r['rule_id'] for r in output['rules']]!=[r['id'] for r in bundle['rules']]:
        raise EvidenceError('AI review must cover every rule in exact order')
    for row in output['rules']:
        _evidence(row['evidence'],context,required=row['supported'])
    if output['decision']=='accept' and not all(r['supported'] for r in output['rules']):
        raise EvidenceError('Unsupported AI rules cannot be accepted')
    if output['decision']=='accept' and bundle['review']['status']=='rejected':
        raise EvidenceError('A rejected candidate cannot be AI accepted')
    receipt=_receipt(store,context,output['decision'],output['reason'],model,candidate_sha256,
        output['rules'],'model_evidence_review' if evidence_only else 'model_source_review',at,output)
    immutable(Path(directory)/'decision.json',receipt)
    return _result(receipt,'ai_review_completed')


def reflect_failure(backend,trajectory_root,store,directory,model,limits):
    """Generate an AI failure lesson candidate, never a human expert summary."""
    root=Path(trajectory_root);state=read(root/'state.json');attempts=state.get('attempts',[])
    if len(attempts)!=3 or any(a.get('acceptance_passed') is not False or
            (a.get('training_result') or {}).get('valid') is not True for a in attempts):
        raise EvidenceError('AI failure reflection requires three completed valid failed D attempts')
    context=public_context(root)
    payload=dict(task=context['task'],sources=context['sources'],public_context=context,
        schema=failure_schema(),instruction='You are an explicitly delegated AI failure analyst, not a human expert. '
        'These three completed D attempts did not satisfy training acceptance. Only original public task/source '
        'and public observations supplied here may justify lessons; no hidden Gold cause is available. '
        'Separate confirmed source-supported conclusions, hypotheses and unresolved behavior. Produce a reusable '
        'candidate only when each rule has exact original public quotes and justified scope/exclusions. '
        'Do not claim a correct fix, causal proof, human review or transfer effectiveness. Prefer no_update when '
        'public evidence is insufficient. A failure lesson must still receive separate AI source review.')
    output,at=_run(backend,payload,model,limits,directory)
    if output['decision']=='no_update':
        if output['experience'] is not None or output['rule_evidence']:
            raise EvidenceError('AI no-update must not carry guidance')
        receipt=_receipt(store,context,'no_update',output['reason'],model,method='model_failure_reflection',at=at,output=output)
        immutable(Path(directory)/'decision.json',receipt);return _result(receipt,'ai_no_update')
    experience=output['experience']
    from .tempoevo_v4 import EXPERIENCE_SCHEMA
    from ._session_runtime.schema_validator import validate
    validate(experience,EXPERIENCE_SCHEMA)
    if [r['rule_index'] for r in output['rule_evidence']]!=list(range(1,len(experience['rules'])+1)):
        raise EvidenceError('AI failure rules need ordered complete evidence')
    for row in output['rule_evidence']:_evidence(row['evidence'],context,required=True)
    source=Path(directory)/'ai-failure-source.json'
    immutable(source,dict(schema_version='experience-ai-failure-reflection-v1',origin='ai_failure_reflection',
        reviewer_kind='ai_delegated',human_reviewed=False,effectiveness_verified=False,context=context,model_output=output))
    code=sha(source.read_bytes());rules=[dict(id='R%02d'%i,**r) for i,r in enumerate(experience['rules'],1)]
    payload=dict(schema_version=memory.BUNDLE_VERSION_V2,id='ai-failure-'+sha(str(root.resolve()).encode())[:24],
        version='v1',parent_sha256=None,taxonomy_version=taxonomy.VERSION,labels=experience['labels'],
        requires=experience['requires'],excludes=experience['excludes'],rules=rules,
        review=dict(status='candidate',kind='ai_assisted',source_sha256=code,limitations=experience['limitations']+
            ['AI-generated failure lesson; no human review or correct repair established; transfer effectiveness unknown.']),
        audit=dict(sources=[dict(path=str(source),sha256=code)],
            rule_links=[dict(rule_id=r['id'],source_sha256=code,pointer='/model_output/experience/rules/'+str(i)) for i,r in enumerate(rules)],
            notes=['Origin: ai_failure_reflection','Not a human expert summary; separate AI review required.'],outcome_refs=[]))
    expected=memory.seal(payload);existing=next((b for b in memory.records(store) if b['id']==payload['id']),None)
    if existing and existing!=expected:raise EvidenceError('AI failure candidate identity conflict')
    bundle=existing or memory.add(store,payload,[source])
    receipt=_receipt(store,context,'candidate',output['reason'],model,bundle['sha256'],
        method='model_failure_reflection',at=at,output=output)
    immutable(Path(directory)/'decision.json',receipt)
    return _result(receipt,'ai_failure_candidate')


def decisions(store):
    result=[]
    for path in sorted((Path(store)/'workflow/ai-reviews').glob('*.json')):
        row=read(path);value={k:v for k,v in row.items() if k!='sha256'}
        memory.object_fields(row,{'schema_version','reviewer_kind','human_reviewed','delegation','scope',
            'effectiveness_verified','decision','reason','candidate_sha256','rules','model','evaluation_method',
            'context_sha256','at','model_output_sha256','sha256'},'AI review receipt')
        if row.get('schema_version')!=REVIEW_VERSION or row.get('sha256')!=sha(canonical(value).encode()) or path.stem!=row['sha256']:
            raise EvidenceError('AI decision digest mismatch')
        if row.get('reviewer_kind')!='ai_delegated' or row.get('human_reviewed') is not False or row.get('effectiveness_verified') is not False:
            raise EvidenceError('AI decision must not claim human review or established effectiveness')
        if row['scope']!='exploratory' or not memory.text(row['delegation']) or not memory.text(row['at']) or not isinstance(row['model'],dict) or not memory.text(row['model'].get('model')):
            raise EvidenceError('AI review requires declared delegation, model and exploratory scope')
        context=read(Path(store)/'workflow/ai-review-contexts'/(row['context_sha256']+'.json'))
        if sha(canonical(context).encode())!=row['context_sha256']:raise EvidenceError('AI review context drift')
        if row.get('model_output_sha256'):
            output=read(Path(store)/'workflow/ai-review-outputs'/(row['model_output_sha256']+'.json'))
            if sha(canonical(output).encode())!=row['model_output_sha256']:raise EvidenceError('AI model output drift')
        else:output=None
        if row['decision'] not in ('accept','reject','candidate','no_update') or not memory.text(row.get('reason')):
            raise EvidenceError('Invalid AI review decision')
        from ._session_runtime.schema_validator import validate
        if row['evaluation_method'] in ('model_source_review','model_evidence_review'):
            validate(output,REVIEW_SCHEMA)
            if output['decision']!=row['decision'] or output['reason']!=row['reason'] or output['rules']!=row['rules']:
                raise EvidenceError('AI receipt differs from actual model review')
        elif row['evaluation_method']=='model_failure_reflection':
            validate(output,failure_schema())
            if output['decision']!=row['decision'] or output['reason']!=row['reason'] or row['rules']:
                raise EvidenceError('AI receipt differs from actual failure reflection')
        elif row['evaluation_method']=='deterministic_no_update':
            if row['decision']!='no_update' or output is not None or row['rules']:
                raise EvidenceError('Deterministic closure cannot approve guidance')
        else:raise EvidenceError('Unknown AI review evaluation method')
        if row['decision']=='no_update' and row['candidate_sha256'] is not None:
            raise EvidenceError('AI no-update cannot install a candidate')
        if row['decision']!='no_update' and (not isinstance(row['candidate_sha256'],str) or len(row['candidate_sha256'])!=64):
            raise EvidenceError('AI candidate decision requires an exact content digest')
        result.append(row)
    return sorted(result,key=lambda r:(r['at'],r['sha256']))


def freeze(store):
    bundles={b['sha256']:b for b in memory.records(store)};latest={}
    for row in decisions(store):
        if row['candidate_sha256'] and row['decision'] in ('accept','reject') and row['evaluation_method']!='model_evidence_review':latest[row['candidate_sha256']]=row
    accepted={c:r for c,r in latest.items() if r['decision']=='accept'}
    # One accepted version per identity, selected by retained review order.
    chosen={}
    for code,row in sorted(accepted.items(),key=lambda v:(v[1]['at'],v[1]['sha256'])):
        if code not in bundles:raise EvidenceError('AI review references missing candidate')
        chosen[bundles[code]['id']]=code
    selected=set(chosen.values());superseded=set()
    for code in selected:
        bundle=bundles[code];parent=bundle['parent_sha256']
        while parent:
            superseded.add(parent)
            if parent not in bundles:raise EvidenceError('AI accepted parent is missing')
            parent=bundles[parent]['parent_sha256']
        notes=bundle['audit']['notes']
        if 'Reflection operation: merge' in notes:
            targets=next((n.partition(': ')[2].split(',') for n in reversed(notes) if n.startswith('Reflection targets: ')),[])
            if len(set(targets))>=2:superseded.update(targets)
    # Repeated independent cases may generate exactly the same guidance. Retain all
    # receipts but expose identical normalized guidance only once in the snapshot.
    entries=[];content_seen=set()
    for code in sorted(selected-superseded,key=lambda c:(accepted[c]['at'],accepted[c]['sha256'])):
        bundle=bundles[code]
        normalized=dict(labels=sorted(bundle['labels']),requires=sorted(bundle['requires']),excludes=sorted(bundle['excludes']),
            rules=[dict(category=r['category'],body=' '.join(r['body'].split())) for r in bundle['rules']])
        fingerprint=sha(canonical(normalized).encode())
        if fingerprint in content_seen:continue
        content_seen.add(fingerprint);entries.append(dict(bundle=bundle,ai_review=accepted[code]))
    entries.sort(key=lambda e:(e['bundle']['id'],e['bundle']['sha256']))
    value=dict(schema_version=SNAPSHOT_VERSION,scope='research_only',reviewer_kind='ai_delegated',human_reviewed=False,entries=entries)
    return _seal(value)


def validate_snapshot(store,snapshot):
    fields={'schema_version','scope','reviewer_kind','human_reviewed','entries','sha256'}
    if not isinstance(snapshot,dict) or set(snapshot)!=fields or snapshot['schema_version']!=SNAPSHOT_VERSION or snapshot['scope']!='research_only' or snapshot['reviewer_kind']!='ai_delegated' or snapshot['human_reviewed'] is not False or snapshot['sha256']!=sha(canonical({k:v for k,v in snapshot.items() if k!='sha256'}).encode()):
        raise EvidenceError('Invalid AI-reviewed frozen snapshot')
    if not isinstance(snapshot['entries'],list):raise EvidenceError('AI snapshot entries must be a list')
    retained={r['sha256']:r for r in decisions(store)};seen=set()
    for entry in snapshot['entries']:
        memory.object_fields(entry,{'bundle','ai_review'},'AI snapshot entry');bundle=entry['bundle'];review=entry['ai_review']
        memory.validate(bundle,lambda c:memory.source_bytes(store,c))
        if bundle['review']['status']=='rejected':raise EvidenceError('Rejected guidance cannot enter an AI snapshot')
        if retained.get(review.get('sha256'))!=review or review['decision']!='accept' or review['candidate_sha256']!=bundle['sha256'] or bundle['sha256'] in seen:
            raise EvidenceError('AI snapshot needs a unique retained AI acceptance')
        context=read(Path(store)/'workflow/ai-review-contexts'/(review['context_sha256']+'.json'))
        if [r['rule_id'] for r in review['rules']]!=[r['id'] for r in bundle['rules']] or not all(r['supported'] for r in review['rules']):
            raise EvidenceError('AI acceptance must support every rule')
        for row in review['rules']:_evidence(row['evidence'],context,required=True)
        seen.add(bundle['sha256'])
    return snapshot
