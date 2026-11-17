"""Bound wire prompts without deleting product files or weakening source validation."""
from copy import deepcopy
import hashlib,re
from .core import canonical,EvidenceError
MAX_CHARS=900000
SOURCE_MAPS={'sources','candidate_sources','previous_candidate','original_sources','numbered_sources'}

def compact(payload):
    original_chars=len(canonical(payload))
    if original_chars<=MAX_CHARS:return payload,dict(compacted=False,original_chars=original_chars,wire_chars=original_chars)
    task=str(payload.get('task',''));tokens=set(re.findall(r'[A-Za-z][A-Za-z0-9_]{3,}',task.lower()))
    def priority(name):
        lower=name.lower();base=lower.rsplit('/',1)[-1]
        return (0 if base in ('readme.md','projection.md','visible_checks.md') else 1 if lower.startswith('src/') or '/asyncsubject.' in lower else 2,-sum(t in lower for t in tokens),name)
    for budget in (60000,20000,0):
        indexes=[]
        def walk(value,path='payload'):
            if isinstance(value,list):return [walk(v,path+'/'+str(i)) for i,v in enumerate(value)]
            if not isinstance(value,dict):return value
            out={}
            for key,v in value.items():
                if key in SOURCE_MAPS and isinstance(v,dict) and all(isinstance(x,str) for x in v.values()):
                    chosen={};size=0;manifest=[]
                    for name in sorted(v,key=priority):
                        body=v[name];entry=dict(path=name,characters=len(body),sha256=hashlib.sha256(body.encode()).hexdigest(),inline=False)
                        cost=len(canonical({name:body}))
                        if size+cost<=budget:chosen[name]=body;size+=cost;entry['inline']=True
                        manifest.append(entry)
                    out[key]=chosen;indexes.append(dict(payload_path=path+'/'+key,files=manifest))
                else:out[key]=walk(v,path+'/'+key)
            return out
        result=walk(deepcopy(payload));result['public_context_transport']=dict(policy='bounded-inline-full-workspace-v1',indexes=indexes,
            instruction='Inline source maps are explicitly incomplete previews. The full current public candidate is in /workspace: inspect omitted source paths with allowed tools before conclusions. Original source quotes still require exact original evidence; do not invent omitted text. Historical candidate versions may be represented by hashes rather than full bodies; use supplied diffs/feedback and retain unknowns where original version context is unavailable. No requirements or experience approval are inferred from omission.')
        length=len(canonical(result))
        if length<=MAX_CHARS:return result,dict(compacted=True,original_chars=original_chars,wire_chars=length,inline_char_budget_per_map=budget,indexes=indexes)
    raise EvidenceError('Non-source prompt metadata exceeds bounded transport size; no model call made')
