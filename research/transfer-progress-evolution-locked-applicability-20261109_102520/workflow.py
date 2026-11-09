"""New authorized batch: only rules may evolve; metadata is inherited explicitly."""
import difflib,json,shutil,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
from evolve import (A,P,read,write,save,sha,cp,runner,object_digest,maintenance_prompt,
 verify_ledger,rebuild_feedback,assemble_payload,reference_view,PREDICATES,
 preflight,execute,render,validate_candidate,numbered_rules,stop,freeze,develop)
from locked_scope import metadata,revision_schema,assemble
Q=A.parent/'transfer-progress-evolution-20261109_100402'

def prepare():
 assert read(A/'actual-schedule.json',[])==[] and not (A/'runs').exists()
 # No model call has taken place. Preserve the preparatory inherited driver
 # inputs before applying this batch's explicit output scope.
 before=A/'prelaunch-scope-snapshot';before.mkdir(exist_ok=False)
 for name in ['initial-freeze.json','reflection.schema.json','protocol.json']:
  if (A/name).exists():shutil.copy2(A/name,before/name)
 save(before/'receipt.json',{'sessions_started':0,'requests_started':0,'reason':'Preparatory common-driver artifacts replaced by the new locked-scope protocol before any call; no model retry.'})
 runner.verify(read(A/'initial-state.json')['parent_files'])
 c=read(A/'case.json');parent=read(P/'development/experience-object.json')
 assert read(P/'development/content-review.json')['development_eligible']
 assert runner.backend.hashes(A/'materials/D/candidate')==c['candidate_files']
 assert sha(A/'materials/D/task.md')==c['task_sha256']
 for name,value in c['oracle_files'].items():assert sha(Path(c['source_case'])/'oracle'/name)==value
 public=(A/'development/AUTO-prompt.md').read_text()
 assert public==maintenance_prompt((A/'materials/D/task.md').read_text(),(A/'derived/D/automatic-contract.md').read_text())
 rows=[]
 for slot in ['session-02','session-03','session-05','session-06']:
  arc=P/'runs'/slot/'archive';r=read(arc/'receipt.json');cfg=read(arc/'input/config.json')
  assert cfg['model']=='gpt-5.6-terra' and cfg['effort']=='low' and cfg['requests_per_session']==24 and cfg['seconds_per_session']==600
  assert r['infrastructure_valid'] and r['scoring_admissible'] and r['scoring_status']=='COLLECTED' and r['scored_candidate_unchanged']
  assert runner.backend.hashes(arc/'input/original')==c['candidate_files'] and sha(arc/'input/task.md')==c['task_sha256']
  actual=(arc/'input/actual-prompt.md').read_text()
  assert actual==public if slot in ['session-02','session-03'] else actual.startswith(public+'\n\n')
  assert read(arc/'score/receipt.json')['oracle_files']==c['oracle_files']
  rows.append({'slot':slot,'archive':str(arc),'receipt_sha256':sha(arc/'receipt.json'),'score_sha256':sha(arc/'score/stdout.json'),'same_inputs_model_tools_budgets_scorer':True})
 save(A/'baseline-selection.json',{'selection':'Both fixed valid parent AUTO slots, no selection by outcome or additional AUTO','rows':rows})
 locked=metadata(parent);save(A/'locked-metadata.json',locked)
 save(A/'locked-metadata-provenance.json',{'source':str(P/'development/experience-object.json'),'source_sha256':sha(P/'development/experience-object.json'),
  'content_review':str(P/'development/semantic-review.json'),'review_status':'AI-assisted; not independent human approval',
  'fields':list(locked),'operation':'Exact field copy from content-supported parent, never model regenerated','object_sha256':object_digest(locked),
  'previous_rejected_candidate_unchanged':str(Q/'development/experience-object.json')})
 ledger=read(A/'training/evidence-ledger.json')
 for name in ['experience-object.json','experience.md','semantic-review.json','applicability-conflict.json']:
  rel='inputs/previous-rejection/'+name;dest=cp(Q/'development'/name,'training/'+rel)
  ledger['files'][rel]={'role':'training_rejection_review','sha256':sha(dest)}
 save(A/'training/evidence-ledger.json',ledger);verify_ledger(A/'training',ledger)
 fb=rebuild_feedback(A/'training',ledger);save(A/'training/feedback.json',fb)
 payload=assemble_payload(A/'training',ledger,fb)
 for m in payload['materials']:
  if m['artifact'].endswith('.json'):m['content']=json.loads(m['content'])
 payload['mechanism_predicates']=PREDICATES;payload['locked_parent_metadata']=locked
 payload['output_protocol']={'editable_fields':['rules','unresolved'],'inherited_fields':list(locked),
  'mandatory_counterevidence':ledger['mandatory_counterevidence'],'preservation_constraints':[r['id'] for r in ledger['constraints']]}
 save(A/'training/reflection-input.json',payload);view=reference_view(payload);save(A/'training/reflection-model-view.json',view)
 save(A/'reflection.schema.json',revision_schema(ledger,PREDICATES))
 instructions='''Produce ONE rule revision object with ONLY rules and unresolved at the top level. No tools, alternatives, retries, reference patch, test feedback, external experience or extra judge.
This new authorized batch fixes output-scope drift. Python will COPY version/requires/excludes/applicability from the separately frozen CONTENT-SUPPORTED parent. Those fields are NOT editable and must NOT appear in the output. The previous rejected candidate remains rejected; its actual body and rejection are revision history, not a newly admitted candidate.
Use the existing single-source rule schema: 5-7 concise rules covering applicability/event_relation/verification/preservation/exclusion, each body ONCE (at most 480 characters), no model rule IDs or duplicate full text. Chinese preferred. Python only joins exact bodies and carries inherited metadata; it cannot repair semantic mistakes.
Retain the supported parent scope and preservation boundaries. Refine timing and verification using both actual development patches, complete outcomes/event traces and executed self-check commands; avoid merely restating the broad obligation.
Address in DELIVERED BODIES: retirement stops fresh admission even while the cleanup/remover/handle is not yet returned; already admitted events retain exactly-once audit at later decode completion, never erased by current-visit completion gating; verify follow-up emissions after synchronous navigation but BEFORE the outer startup returns, including same-source reopen, hide and switch, checking retired admission and valid current audit/progress separately. Post-return cleanup tests alone do not cover this window.
No unique API/implementation, blanket observerless cancellation, altered retry/cancel/navigation/resource ownership, interface or record policy. No case IDs, grading/check names, paths, specialized fields/functions, evidence IDs or copyable patches in delivered bodies. Maintenance sees only those bodies.
The dictionary boundary_persistence specifically means documented settlement BEFORE a leave/submit boundary returns. Retained delayed audit AFTER retirement does not establish that deadline. It remains unknown here and is absent from locked requires; do not smuggle this deadline into bodies or unresolved requirements. If inherited scope is actually inconsistent with evidence, report an unresolved policy/applicability issue instead of assuming it met.
support/conditions/counterevidence contain only existing evidence IDs; preserve only constraint IDs; explanations belong in explanation fields. Every normative rule needs genuinely relevant documented requirement/source fact/preservation inference support, not observed results alone. Cover all preservation constraints and mandatory counterexamples. Structure is not entailment.
Repair final deliveries are unverified claims. Source placement and observed ordering support temporal reasoning, but no controlled intervention has isolated causal contributions. No full repair or benefit has been established. Preserve accepted late audit, current ownership, subsequent source reuse, retries, cancellation, independent workspaces and retained command format. Do not promote unknown causes to certainty.
One complete revision only. Subsequent review is execution-agent AI-assisted review, not independent human approval.
Complete frozen training payload uses lossless repeated-subtree references: recursively replace each object containing only $same with its identical shared_values entry. These serialization keys are not evidence IDs. No source, check, trace, success, regression or unknown is omitted:
'''
 text=instructions+json.dumps(view,ensure_ascii=False,separators=(',',':'))
 write(A/'training/reflection-prompt.md',text);write(A/'training/reflection-task.md','One rules-only evolution with locked inherited applicability; no tools.\n')
 save(A/'training/model-workspace/payload.json',payload)
 save(A/'serialization-audit.json',{'operation':'Same verified lossless repeated-subtree reference view','expanded_input_sha256':object_digest(payload),'view_sha256':object_digest(view),'prompt_bytes':len(text.encode()),'model_calls':0})
 protocol=read(Q/'protocol.json');protocol.update({'version':'locked-applicability-1','previous_rejected_batch':str(Q),
  'authorization':'User do: fix output scope, one reflection and at most two development repairs',
  'editable_reflection_fields':['rules','unresolved'],'locked_reflection_fields':list(locked),'entrypoint':'workflow.py'})
 save(A/'protocol.json',protocol);save(A/'actual-schedule.json',[])
 write(A/'PLAN.md','一个规则修订候选，最多两次独立开发维护。程序继承父候选已核验元数据，模型仅输出规则和未决说明。候选须通过结构及语义核查；无据候选停止。维护公共条件及原20项评分不变。无重试、额外提取/评委、测试集或下一轮。\n')
 write(A/'FIX.md','输出 schema 仅有 rules/unresolved，字段内部沿用原约束。Python严格拒绝锁定字段，并原样继承通过内容核查的父元数据。分别保存原始修订对象、派生完整候选和合成证明，不是删除旧候选错误字段或改写业务规则。正文依旧接受逐条语义核查。\n')
 preflight()

def reflect():
 assert len(read(A/'actual-schedule.json'))==0
 rec=execute('reflection','reflect',(A/'training/reflection-prompt.md').read_text(),A/'training/model-workspace',A/'training/reflection-task.md')
 raw=(A/'runs'/rec['slot']/'archive/raw-answer.txt').read_bytes();(A/'development/reflection-raw.txt').write_bytes(raw)
 try:
  revision=json.loads(raw);save(A/'development/raw-rule-revision.json',revision)
  candidate,composition=assemble(revision,read(A/'locked-metadata.json'),read(A/'training/evidence-ledger.json'),PREDICATES)
  save(A/'development/experience-object.json',candidate);save(A/'development/composition.json',composition)
  result=validate_candidate(candidate,read(A/'training/evidence-ledger.json'),PREDICATES);text=render(candidate)
  banned=[read(A/'case.json')['case'],'src/','```']+[s['effect'] for s in read(A/'materials/D/standards.json')]
  if any(x in text for x in banned):raise ValueError('Prohibited case/path/scoring/patch in delivered prose')
  write(A/'development/experience.md',text);save(A/'development/structural-review.json',result)
  save(A/'development/rule-evidence.json',{'rules':numbered_rules(candidate),'applicability':candidate['applicability'],'unresolved':candidate['unresolved']})
  save(A/'development/metadata-invariance.json',{'parent':str(P/'development/experience-object.json'),'fields':list(read(A/'locked-metadata.json')),'unchanged':metadata(candidate)==read(A/'locked-metadata.json'),'source':'Program-inherited; not model regenerated'})
  write(A/'development/parent-body.diff',''.join(difflib.unified_diff((P/'development/experience.md').read_text().splitlines(True),text.splitlines(True),fromfile='parent-experience',tofile='new-derived-experience')))
  save(A/'development/derivation.json',{'operation':'Derived full candidate = exact raw model rules/unresolved plus locked parent metadata; deterministic exact-body numbering/rendering','raw_revision_sha256':sha(A/'development/raw-rule-revision.json'),'candidate_sha256':object_digest(candidate),'text_sha256':sha(A/'development/experience.md')})
 except Exception as exc:
  save(A/'development/rejection.json',{'reason':repr(exc),'raw_retained':True});stop('candidate',repr(exc))

if __name__=='__main__':
 try:
  stage=sys.argv[1]
  if stage=='develop':develop(int(sys.argv[2]))
  else:{'prepare':prepare,'reflect':reflect,'freeze':freeze}[stage]()
 except Exception as exc:
  if not (A/'stop.json').exists():save(A/'stop.json',{'time':time.time(),'kind':'stage_exception','reason':repr(exc),'no_retry':True,'no_more_model_calls':True})
  print('STOP',repr(exc),flush=True);sys.exit(1)
