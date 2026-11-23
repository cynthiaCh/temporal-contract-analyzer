"""Small inline learning metadata; scores are observations, never causal proof."""
from copy import deepcopy
from .core import EvidenceError
from . import experience_memory as memory

COUNTERS=('delivered_cases','positive_cases','negative_cases')

def empty(origin=None, priority=0):
    return dict(origin=origin,initial_priority=priority,usage_by_model={})


def validate(value):
    memory.object_fields(value,{'origin','initial_priority','usage_by_model'},'learning metadata')
    if type(value['initial_priority']) is not int or value['initial_priority'] not in (0,1):
        raise EvidenceError('Initial priority must be zero or one')
    origin=value['origin']
    if origin is not None:
        memory.object_fields(origin,{'reflection_model','reflection_effort','repair_model','first_success_attempt'},'learning origin')
        if not memory.text(origin['reflection_model']) or not memory.text(origin['repair_model']) or (origin['reflection_effort'] is not None and not memory.text(origin['reflection_effort'])):
            raise EvidenceError('Learning origin needs actual model identities')
        if origin['first_success_attempt'] not in (None,2,3):raise EvidenceError('Learning requires a failed-to-successful trajectory')
    if not isinstance(value['usage_by_model'],dict):raise EvidenceError('Invalid model usage')
    for model,row in value['usage_by_model'].items():
        if not memory.text(model):raise EvidenceError('Missing repair model')
        memory.object_fields(row,set(COUNTERS)|{'cases'},'model usage')
        if not isinstance(row['cases'],dict) or any(not memory.text(k) or v not in ('delivered','adopted','misleading','rule_error') for k,v in row['cases'].items()):
            raise EvidenceError('Invalid usage deduplication')
        expected=(len(row['cases']),sum(v=='adopted' for v in row['cases'].values()),sum(v in ('misleading','rule_error') for v in row['cases'].values()))
        if any(type(row[k]) is not int or row[k]!=n for k,n in zip(COUNTERS,expected)):
            raise EvidenceError('Usage counters do not match unique cases')
    return value


def score(value,model=None):
    value=value or empty();rows=value['usage_by_model']
    if model in rows and rows[model]['positive_cases']+rows[model]['negative_cases']>0:
        delta=rows[model]['positive_cases']-rows[model]['negative_cases']
    else:
        cases={}
        for row in rows.values():
            for case,result in row['cases'].items():
                if result!='delivered':cases.setdefault(case,set()).add(result)
        delta=sum(1 if outcomes=={'adopted'} else -1 if 'adopted' not in outcomes else 0 for outcomes in cases.values())
    return max(-3,min(5,value['initial_priority']+delta))


def record_usage(store,case_id,model,expected,judgments):
    """Atomically count each task/model once per entry; no extra usage files."""
    from . import compact_experience as compact
    if not compact.is_library(store):return []
    changed=[]
    with compact._locked(store):
        for file,value in compact.documents(store):
            dirty=False
            for item in value['experiences']:
                if expected.get(item['id'])!=compact._bundle(file,item)[0]['sha256']:continue
                metadata=deepcopy(item.get('learning',empty()))
                row=metadata['usage_by_model'].setdefault(model,dict(delivered_cases=0,positive_cases=0,negative_cases=0,cases={}))
                result=judgments.get(item['id'],'delivered');previous=row['cases'].get(case_id)
                if previous==result or previous not in (None,'delivered'):continue
                row['cases'][case_id]=result
                row['delivered_cases']=len(row['cases'])
                row['positive_cases']=sum(v=='adopted' for v in row['cases'].values())
                row['negative_cases']=sum(v in ('misleading','rule_error') for v in row['cases'].values())
                validate(metadata);item['learning']=metadata
                # A model finding is a review concern, not an approval decision.
                dirty=True;changed.append(item['id'])
            if dirty:compact._write(file,value)
    return changed


def contributions(rows,related,attempts,task,sources):
    """Check rule and exact changed-code evidence. Semantic judgments stay fallible."""
    from .tempoevo_v4 import evidence_valid
    allowed={b['sha256']:b for b in related};results={};issues=[]
    if len(attempts)<2 or attempts[-1]['acceptance_passed'] is not True:return results,issues
    failed=[a['candidate_sources'] for a in attempts[:-1] if a['acceptance_passed'] is False]
    after=attempts[-1]['candidate_sources']
    delivered={code for a in attempts for code in a['delivered_sha256s']}
    grouped={}
    for row in rows:grouped.setdefault(row['experience_sha256'],[]).append(row)
    for code,items in grouped.items():
        try:
            if len(items)!=1 or code not in delivered or code not in allowed:raise EvidenceError('Contribution must uniquely name delivered guidance')
            row=items[0];bundle=allowed[code]
            rule=next((r for r in bundle['rules'] if r['id']==row['rule_id']),None)
            if rule is None or not memory.text(row['rule_quote']) or row['rule_quote'] not in rule['body']:raise EvidenceError('Unsupported experience rule quote')
            evidence_valid([row['after']],task,after)
            if row['before']['quote']==row['after']['quote']:
                raise EvidenceError('Contribution requires changed failed and successful code')
            if not any(_changed_pair(row['before'],row['after'],before,after) for before in failed):
                raise EvidenceError('Contribution quotes must identify the same actual edit from a failed attempt')
            if not row['supporting_evidence']:raise EvidenceError('Contribution needs original task/source evidence')
            evidence_valid(row['supporting_evidence'],task,sources)
            results[bundle['id']]=row['decision']
        except (EvidenceError,ValueError) as error:issues.append(dict(experience_sha256=code,error=str(error)))
    return results,issues


def _changed_pair(before_quote,after_quote,before,after):
    """Pair literal excerpts at one edit, including insertion/deletion boundaries."""
    from difflib import SequenceMatcher
    name=before_quote['file']
    if name!=after_quote['file'] or name not in before or name not in after:return False
    old=before[name];new=after[name]
    def locations(text,quote):
        start=text.find(quote)
        while start>=0:
            yield start,start+len(quote)
            start=text.find(quote,start+1)
    left=list(locations(old,before_quote['quote']));right=list(locations(new,after_quote['quote']))
    if not left or not right:return False
    def overlaps(text,quotes,start,end):
        for a,b in quotes:
            if start!=end:
                if a<end and b>start:return True
            elif a<=start<=b:return True
            else:
                gap=text[b:start] if b<start else text[start:a]
                if gap.isspace() and gap.count('\n')<=1:return True
        return False
    old_lines=old.splitlines(keepends=True);new_lines=new.splitlines(keepends=True)
    old_offsets=[0];new_offsets=[0]
    for line in old_lines:old_offsets.append(old_offsets[-1]+len(line))
    for line in new_lines:new_offsets.append(new_offsets[-1]+len(line))
    for tag,a,b,c,d in SequenceMatcher(None,old_lines,new_lines,autojunk=False).get_opcodes():
        if tag=='equal':continue
        old_start=old_offsets[a];new_start=new_offsets[c]
        for kind,i,j,k,l in SequenceMatcher(None,old[old_start:old_offsets[b]],new[new_start:new_offsets[d]],autojunk=False).get_opcodes():
            if kind!='equal' and overlaps(old,left,old_start+i,old_start+j) and overlaps(new,right,new_start+k,new_start+l):
                return True
    return False
