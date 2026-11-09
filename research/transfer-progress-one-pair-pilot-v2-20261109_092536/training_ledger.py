"""Training-only evidence assembly; source interpretations are explicitly AI-authored."""
import json,shutil
from pathlib import Path
from archive import save,sha
from feedback import feedback

A=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text())

REFLECTION_INSTRUCTIONS='''Generate ONE new experience candidate from this batch's training evidence only.
No tools, alternative candidate, retry, old experience or reference patch.
Use the existing single-source typed JSON rule schema: version single-source-rules-1;
requires/excludes contain mechanism predicate keys, applicability covers exactly those
selected keys with status, existing evidence IDs and explanation. A required predicate
must be known, an excluded predicate contradicted; unknown is not applicable. Use
the provided full predicate dictionary, not labels inferred from case identity.

Write 5-7 concise rules, body at most 480 characters each, with all categories:
applicability, event_relation, verification, preservation, exclusion. Chinese preferred.
Each body is written ONCE. Do not output full text, quotations or model rule IDs;
Python only numbers and joins exact bodies under category headings. Body must not
contain case IDs, grading assertion names, paths, specialized fields/functions or
copyable patches. Bodies should be useful event/verification guidance, not a score report.

support/conditions/counterevidence contain only existing evidence IDs; preserve only
existing constraint IDs. Explain meanings and counterexamples in explanation. Every
rule support itself needs at least one genuinely relevant documented requirement,
source fact or preservation-inference ID; observations alone cannot create policy,
even if a source appears in conditions. Cover all preservation constraints and the
mandatory counterevidence list across rules. No invented evidence or business rules.

Distinguish documented requirements, source facts, preservation inferences, observed
actual/expected values, unverified repair-agent delivery claims, hypotheses and unknown
causes. Preserve existing successes and expose all regressions. The current bad state
is not automatically a preservation requirement. An assertion label is not a cause.
Do not claim an isolated cause from a patch changing multiple things. State only
current-evidence-supported timing, ownership, admission, completion and cleanup rules;
do not transfer adjacent-object policy without support. Verification must assess the
actual obligation and allowed outcomes, not mandate one convenient implementation.
Unknown causality or absence of a proven full repair is a scope/validation limitation,
not by itself a new business-policy conflict. Narrow uncertain rules or record unresolved
issues with statement and impact (scope_limit/policy/applicability); do not fabricate
certainty or silently assume prerequisites. Subsequent review is AI-assisted, not
independent human approval. Development benefit has not been established.
Complete frozen training payload:
'''

def build():
 root=A/'training';root.mkdir(exist_ok=False);files={}
 def cp(src,name,role):
  dest=root/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
  files[name]={'role':role,'sha256':sha(dest)}
 cp(A/'materials/D/task.md','inputs/task.md','training_task')
 for p in (A/'materials/D/candidate').rglob('*'):
  if p.is_file() and p.suffix in ['.md','.js']:
   cp(p,'inputs/source/'+str(p.relative_to(A/'materials/D/candidate')),'training_document' if p.suffix=='.md' else 'training_source')
 cp(A/'materials/D/standards.json','inputs/standards.json','training_standard')
 cp(A/'materials/D/evaluation/recovery-rubric.json','inputs/rubric.json','training_standard')
 cp(A/'derived/D/automatic-contract.md','inputs/contract.md','training_contract')
 cp(A/'calibration/D/original/stdout.json','inputs/original-score.json','training_score')
 baseline=read(A/'development/baselines.json')
 for i,r in enumerate(baseline,1):
  arc=A/'runs'/r['slot']/'archive'
  for name,target,role in [('score/stdout.json','score.json','training_score'),('patch.diff','patch.diff','training_patch'),('raw-answer.txt','delivery.txt','training_public_delivery')]:
   cp(arc/name,f'inputs/auto{i}/'+target,role)
  for p in (arc/'final-candidate').rglob('*.js'):
   cp(p,f'inputs/auto{i}/final/'+str(p.relative_to(arc/'final-candidate')),'training_source')
 entries=[]
 def lines(eid,kind,statement,file,start,end,related=()):
  entries.append({'id':eid,'kind':kind,'statement':statement,'author':'execution_agent_source_review',
   'related':list(related),'anchors':[{'type':'lines','file':file,'start':start,'end':end,
     'quote':'\n'.join((root/file).read_text().splitlines()[start-1:end])}]})
 lines('R-task','documented_requirement','Restore the initial warm-source update, preserving ordinary streaming and existing transfer/retry/navigation/cleanup/audit behavior; record-format extension is outside scope.','inputs/task.md',1,4)
 lines('R-source-timing','documented_requirement','Starting the shared progress source can emit synchronously; decoding can settle synchronously or later and the same source can be reused across visits.','inputs/source/README.md',45,50)
 lines('R-history-view','documented_requirement','Each admitted event must retain exactly one audit at decode completion even after departure; retired visits admit no new events; visible updates stop on closing/replacement; callbacks may reenter.','inputs/source/README.md',52,62)
 lines('R-retry-entry','documented_requirement','An accepted retry is bound at entry, cancellation precedes enqueue, exactly one retained command survives reentrant navigation.','inputs/source/README.md',11,16)
 lines('R-reentry','documented_requirement','Native abort callbacks run synchronously and may navigate or reopen identical data; newer visit retains ownership. Retained retry and cleanup obligations remain.','inputs/source/README.md',18,34)
 lines('R-format','documented_requirement','Keep public sink and queue interfaces; adjacent record extension needs separate authorization.','inputs/source/README.md',36,41)
 lines('F-progress','source_fact','Current listener delivers to record and view after decode; current source calls source start before adding its listener. This ordering is a current fact, not intended preservation.','inputs/source/src/progress.js',1,12)
 lines('F-view-owner','source_fact','The audit callback captures entry file/attempt, while visible delivery checks current visit identity.','inputs/source/src/queue.js',8,19)
 lines('F-cancel','source_fact','Transfer owns a controller and a deferred cleanup callback; its abort invokes cleanup and synchronous cancellation observer. The returned resource remains attempt-local.','inputs/source/src/transfer.js',3,16)
 lines('F-navigation','source_fact','Selection publishes an identity before enqueue, then checks whether it is still current before assigning the resulting handle; hide invalidates before releasing.','inputs/source/src/panel.js',10,34)
 lines('F-retry','source_fact','Retry captures current visit, cancels prior handle and enqueues for the captured visit; active view identity gates publication.','inputs/source/src/retry.js',4,15)
 lines('I-preserve','preservation_inference','Preservation applies to documented accepted audit/retry histories and visit-owned display/resource semantics; it does not authorize retaining the reported missing-initial-update defect.','inputs/task.md',1,4,['R-history-view','R-retry-entry','R-reentry','F-view-owner'])
 original=read(root/'inputs/original-score.json');repairs=[read(root/f'inputs/auto{i}/score.json') for i in (1,2)]
 standards=read(root/'inputs/standards.json');fb=feedback(original,repairs,standards);mandatory=[]
 for i,score in enumerate(repairs,1):
  for ordinal,rel in enumerate(fb['runs'][i-1]['differences']):
   effect=rel['effect'];eid=f'O-auto{i}-{ordinal}'
   # Each relation's complete observed schedule (including traces) is pinned,
   # not converted to a root cause based on an assertion name.
   schedule=score['schedules'].get(effect)
   path='/schedules/'+effect if schedule is not None else '/observed_effects/'+effect
   value=schedule if schedule is not None else score['observed_effects'][effect]
   entries.append({'id':eid,'kind':'observed_result','statement':'Complete observed failing relation and raw checks; not an isolated cause.','author':'python_score_extraction','related':[],
     'anchors':[{'type':'json','file':f'inputs/auto{i}/score.json','pointer':path,'value':value}]})
   mandatory.append(eid)
 entries.append({'id':'U-cause','kind':'unknown','statement':'Independent causal contributions of multi-change patches are unverified.','author':'execution_agent','related':[],'anchors':[]})
 constraints=[
 {'id':'C-initial','statement':'Restore supported initial and subsequent event delivery without imposing an unevidenced implementation.','evidence':['R-task','R-source-timing','F-progress']},
 {'id':'C-history','statement':'Retain exactly-once accepted audit through later decode, but stop retired admission and visible effects according to documented policies.','evidence':['R-history-view','F-view-owner']},
 {'id':'C-reentry','statement':'Keep newer visit ownership, entry-bound retry/record and attempt cancellation semantics under synchronous reentry and late handles.','evidence':['R-retry-entry','R-reentry','F-navigation','F-cancel','F-retry']},
 {'id':'C-scope','statement':'Keep shared-source reuse, independent owners and existing interfaces; do not add record-format extensions.','evidence':['R-format','R-reentry','R-source-timing']}]
 ledger={'schema':'evidence-ledger-1','scope':'current batch D training only; no test feedback, old experience or reference patch',
  'files':files,'entries':entries,'constraints':constraints,'mandatory_counterevidence':mandatory,
  'causal_interventions':[],'verified_causes':[],
  'feedback_inputs':{'original':'inputs/original-score.json','repairs':['inputs/auto1/score.json','inputs/auto2/score.json'],'standards':'inputs/standards.json'}}
 # Match the reused generic rebuilding function's explicit uncertainty field.
 fb['causal_status']='No cause independently verified; see evidence ledger for separately authored source reasoning.'
 save(root/'evidence-ledger.json',ledger);save(root/'feedback.json',fb)
