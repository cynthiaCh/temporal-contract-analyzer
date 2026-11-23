"""Source-bound reflection proposals. Never approve guidance or dispatch models."""
from copy import deepcopy
import json
from pathlib import Path
from . import experience_memory as memory
from .core import EvidenceError, canonical, sha

OPERATIONS=('new','evidence','revise','merge')
UPDATE_DISCOVERY_CANDIDATES=2

def content(value):
    return dict(labels=sorted(value['labels']),requires=sorted(value['requires']),excludes=sorted(value['excludes']),
        rules=[dict(category=r['category'],body=' '.join(r['body'].split())) for r in value['rules']])


def related(protocol, delivery):
    if protocol['condition'] not in ('structured','fixed_contract','bm25'):return []
    bundles=[e['bundle'] for e in protocol['memory_snapshot']['entries']]
    # Keep delivered rules for attribution and reserve separate update discovery.
    query=protocol['task']+'\n'+'\n'.join(o['text'] for o in delivery.get('business_obligations',[]))
    from .business_retrieval import recall
    bank=protocol['memory_snapshot']['entries']
    ranked=recall(query,{},bundles,summaries={e['bundle']['sha256']:e['retrieval_summary'] for e in bank if 'retrieval_summary' in e})['candidates']
    delivered=list(dict.fromkeys(delivery.get('selected_sha256s',[])))
    discovered=[r['sha256'] for r in ranked if r['sha256'] not in delivered][:UPDATE_DISCOVERY_CANDIDATES]
    codes=list(dict.fromkeys(delivered+discovered))
    return [deepcopy(next(b for b in bundles if b['sha256']==code)) for code in codes]


def plan(experience, update, candidates, attempts):
    allowed={b['sha256']:b for b in candidates}
    if update is None:
        update=dict(operation='new',target_sha256s=[],reason='No human update specified.',change_summary=[],failure_attribution='unknown',supporting_attempts=[])
    fields={'operation','target_sha256s','reason','change_summary','failure_attribution','supporting_attempts'}
    if not isinstance(update,dict) or set(update)!=fields:raise EvidenceError('Invalid reflection update fields')
    result=deepcopy(update);op=result['operation'];targets=result['target_sha256s']
    if op not in OPERATIONS or not isinstance(targets,list) or len(targets)>5 or any(not isinstance(c,str) or c not in allowed for c in targets) or len(set(targets))!=len(targets):raise EvidenceError('Reflection targets must belong to the frozen related experience shortlist')
    if not memory.text(result['reason']) or not isinstance(result['change_summary'],list) or any(not memory.text(x) for x in result['change_summary']):raise EvidenceError('Reflection needs a reason and structured change summary')
    if result['failure_attribution'] not in ('experience_gap','implementation_gap','unknown','not_applicable'):raise EvidenceError('Invalid reflection attribution')
    if not isinstance(result['supporting_attempts'],list) or any(type(n) is not int or n not in range(1,attempts+1) for n in result['supporting_attempts']):raise EvidenceError('Unknown reflection attempt evidence')
    # Exact duplication is deterministically reduced to an evidence proposal.
    matches=[b for b in candidates if content(b)==content(experience)]
    if matches and op!='merge':
        result.update(operation='evidence',target_sha256s=[sorted(matches,key=lambda b:b['sha256'])[0]['sha256']],change_summary=[])
        result['deduplication']='exact_normalized_content'
        return result
    if op=='new' and candidates and (not result['change_summary'] or not result['supporting_attempts']):
        raise EvidenceError('New guidance requires an independent increment and actual attempt evidence after comparing existing guidance')
    if op=='new' and targets or op in ('evidence','revise') and len(targets)!=1 or op=='merge' and len(targets)<2:raise EvidenceError('Invalid reflection target cardinality')
    if op=='evidence':raise EvidenceError('Evidence-only proposal must retain the target guidance unchanged')
    if op in ('revise','merge') and (not result['change_summary'] or not result['supporting_attempts']):raise EvidenceError('Guidance changes require a delta and actual attempt evidence')
    if op in ('revise','merge') and result['failure_attribution']=='implementation_gap':raise EvidenceError('Implementation failure alone does not justify changing experience')
    return result

def immutable(path,value):
    raw=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode();path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if path.read_bytes()!=raw:raise EvidenceError('Immutable reflection proposal conflict')
    else:
        with path.open('xb') as f:f.write(raw)
    return value
