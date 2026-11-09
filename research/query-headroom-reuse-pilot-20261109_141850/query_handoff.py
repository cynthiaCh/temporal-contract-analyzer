"""Reuse the repaired, source-pinned query evidence ledger, not old experience."""
import json
from pathlib import Path
from archive import save,sha
from evidence import verify_ledger,rebuild_feedback,assemble_payload
from handoff import VERSION
from toolflow import PREDICATES
A=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text())

INSTRUCTIONS='''Generate ONE fresh language-independent experience rule revision from the supplied TRAINING sources and two actual AUTO failures. No tools, retry, alternatives, old E2/experience seed, reference patch, test feedback or extra judge.
Output ONLY rules and unresolved under the supplied schema, 5-7 concise rules, each body once, all five categories applicability/event_relation/verification/preservation/exclusion. Chinese preferred. Python copies version/requires/excludes/applicability from the separately source-reviewed training analysis; do NOT output or alter those fields. If they are contradicted by evidence, record an unresolved policy/applicability issue instead of assuming it met.
Bodies are delivered alone to repair agents; express applicability, event relations, verification, preserved behavior and exclusions. No case IDs, paths, grading assertion names, evidence IDs, specialized field/function names or copyable patches in bodies. Max480 characters per body. No duplicate full text or model rule IDs. Explanations belong in explanation fields.
support/conditions/counterevidence use only existing evidence IDs; preserve only constraint IDs. Every normative support needs a genuinely relevant documented requirement/source fact/preservation inference, not observations alone. Cover every preservation constraint and mandatory counterexample; ID existence does not prove entailment.
Use the complete actual patches, source, outcomes, expected/actual checks and traces. Distinguish original successes, improvements, regressions, unknowns, source facts, observations, causal hypotheses and verified causes. No controlled intervention has independently isolated causes. Public repair deliveries are unverified claims and cannot override actual source or scoring. Never infer business policy or root cause from assertion names alone.
Derive current ownership/policy from current task/source, not generic cancellation intuitions. In particular distinguish fresh uncached never-entered offline work, lawful paused work with an existing successful cache, started work whose cancellation capability is unconsumed, and later actual lazy consumption. Shared consumption-record ownership is not attempt-controller ownership. Do not relocate or reset a record merely because a controller is attempt-local; do not erase currently supported delayed reads. Do not turn all observerless work into cancellation, or treat every paused/unstarted label as the same state.
The target forbids invocation with a LIVE signal in its documented fresh-offline-departure situation. Evaluation permits zero invocation OR invocation with an ALREADY ABORTED signal; do not narrow this to mandatory zero entry. Whichever implementation is used must also preserve legitimate cached background work, later consumption, state restoration, observer reuse and existing completion/timing/network/focus/retry policies. Permitted outcomes are not proof of a complete repair.
The predeclared question is whether a grounded new candidate can improve on two real 27/29 AUTO outcomes without hiding other losses. No improvement or unsupported policy stops this batch before test; two full passes are not required for eligibility. Do not claim an already proven fix or stable/generalized benefit. Review is execution-agent AI-assisted review, not independent human approval.
Complete frozen training payload below uses lossless repeated-subtree references: substitute each object containing only $same by the identical shared_values entry recursively. These serialization keys are not evidence IDs. No source/check/trace/success/regression or unknown is removed:
'''

def reference_view(value):
 dictionary={};seen={}
 def encode(x):
  key=json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
  if len(key)<320:return x
  if key in seen:return {'$same':seen[key]}
  v={k:encode(z) for k,z in x.items()} if isinstance(x,dict) else [encode(z) for z in x] if isinstance(x,list) else x
  token='D%04d'%(len(dictionary)+1);dictionary[token]=v;seen[key]=token;return {'$same':token}
 root=encode(value)
 def expand(x):
  if isinstance(x,dict) and set(x)=={'$same'}:return expand(dictionary[x['$same']])
  if isinstance(x,dict):return {k:expand(v) for k,v in x.items()}
  if isinstance(x,list):return [expand(v) for v in x]
  return x
 assert expand(root)==value
 return {'serialization':'lossless-repeated-subtree-references-1','shared_values':dictionary,'payload':root}

def build():
 root=A/'training';ledger=read(root/'evidence-ledger.json');verify_ledger(root,ledger)
 analysis=read(A/'derived/D/analysis.json');app=[]
 for fact in analysis['facts']:
  if fact['predicate'] not in list(PREDICATES)[:10] or fact['state']!='known':continue
  ids=[]
  for ref in fact['evidence']:
   file='inputs/task.md' if ref['file']=='TASK' else 'inputs/README.md' if ref['file']=='README.md' else 'inputs/original.js'
   eid='M-'+fact['predicate'];text=(root/file).read_text().splitlines();line=ref['line']
   assert ref['quote'] in text[line-1]
   ledger['entries'].append({'id':eid,'kind':'source_fact','statement':'Frozen source-reviewed training analysis marks this mechanism known: '+PREDICATES[fact['predicate']],
    'author':'execution_agent_rechecked_frozen_analysis','related':[], 'anchors':[{'type':'lines','file':file,'start':line,'end':line,'quote':text[line-1]}]});ids.append(eid)
  app.append({'predicate':fact['predicate'],'status':'known','evidence':ids,'explanation':'Exact supported mechanism from the frozen training analysis; no new applicability generation.'})
 locked={'version':VERSION,'requires':[r['predicate'] for r in app],'excludes':[],'applicability':app};assert locked['requires']
 save(A/'locked-metadata.json',locked)
 policy='The current task forbids a live signal at invocation for the fresh offline-departure situation. The original training check accepts zero calls or calls with an already-aborted signal; this does not establish a mandatory zero-entry implementation. All existing cached/active work and state/observer policies remain independently required.\n'
 (root/'inputs/allowed-entry-policy.md').write_text(policy)
 ledger['files']['inputs/allowed-entry-policy.md']={'role':'training_standard','sha256':sha(root/'inputs/allowed-entry-policy.md')}
 ledger['entries'].append({'id':'I-entry-boundary','kind':'preservation_inference','statement':'Do not strengthen no-live-signal-at-entry into mandatory zero execution; allowed alternatives remain subject to all preservation obligations.',
  'author':'execution_agent_training_standard_adapter_AI_assisted','related':['R-task','R-entry','R-background'],
  'anchors':[{'type':'lines','file':'inputs/allowed-entry-policy.md','start':1,'end':1,'quote':policy.strip()}]})
 save(root/'evidence-ledger.json',ledger);verify_ledger(root,ledger)
 fb=rebuild_feedback(root,ledger);save(root/'feedback.json',fb);payload=assemble_payload(root,ledger,fb)
 for m in payload['materials']:
  if m['artifact'].endswith('.json'):m['content']=json.loads(m['content'])
 payload['mechanism_predicates']=PREDICATES;payload['locked_metadata']=locked
 payload['output_protocol']={'mandatory_counterevidence':ledger['mandatory_counterevidence'],'preservation_constraints':[r['id'] for r in ledger['constraints']]}
 save(root/'reflection-input.json',payload);view=reference_view(payload);save(root/'model-view.json',view)
 return ledger,INSTRUCTIONS+json.dumps(view,ensure_ascii=False,separators=(',',':'))
