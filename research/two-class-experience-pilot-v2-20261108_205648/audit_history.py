"""Evidence-backed historical audit, independent of v1 report conclusions."""
import json,hashlib
from pathlib import Path
A=Path(__file__).resolve().parent;V=A.parent/'two-class-experience-pilot-20261108_200017'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def refs(paths):return [{'path':str(V/p),'sha256':sha(V/p)} for p in paths]

def main():
 from feedback_v2 import feedback,checks
 findings=[]
 for alias in ['D1','T1']:
  contract=(V/'derived'/alias/'automatic-contract.md').read_text(); task=(V/'materials'/alias/'task.md').read_text()
  findings.append({'issue':'Contract direction','alias':alias,'requirement_verbatim':task,'model_verbatim':contract,
    'judgment':'confirmed with narrower quotation: original task says Repair ... and describes the unwanted phenomenon; it does not literally contain must not.',
    'contradiction':'The model turns the reported defect into allowed/required continuation with a live cancellation signal.',
    'impact':'D1 common material supplied to two AUTO baselines and development; T1 supplied to started failed A session. Exact causal contribution to model decisions unknown; no counterfactual isolation.',
    'evidence':refs([f'materials/{alias}/task.md',f'derived/{alias}/automatic-contract.md',f'runs/{alias}-preanalysis/archive/raw-answer.txt'])})
 py=(V/'materials/T1/candidate/src/workflow.py').read_text().splitlines()
 findings.append({'issue':'T1 consumption ownership','source_fact':[{'line':n,'text':t} for n,t in enumerate(py,1) if 'q.consumed' in t],
   'model_quote':'并将消费归属记录到该次执行','judgment':'unsupported preservation change: current lazy getter updates owning query, physical attempt identity is a separate concern.',
   'boundary':'This is existing-source preservation evidence, not a claim of full upstream equivalence or an independently approved new business policy.'})
 standards=json.loads((V/'materials/D1/standards.json').read_text());orig=json.loads((V/'calibration/D1/original/stdout.json').read_text())
 scores=[json.loads((V/f'runs/D1-AUTO-{n}/archive/score/stdout.json').read_text()) for n in [1,2]]
 rebuilt=feedback(orig,scores,standards)
 save(A/'audit/v1-feedback-corrected.json',rebuilt)
 actual=scores[0]['schedules']['offline-detach-false']
 raw=json.loads((V/'development/D1/reflection-raw.txt').read_text())
 findings.append({'issue':'reflection attribution','model_quote':'将消费记录完全改归当前执行，修复了离线创建、离开后又恢复执行的问题',
   'patch_fact':'AUTO-1 moves lazy consumption and unsubscribe check from shared query to attempt; leaves fresh orphan resume path unretired.',
   'actual_schedule':actual,'public_delivery':(V/'runs/D1-AUTO-1/archive/raw-answer.txt').read_text(),
   'judgment':'confirmed false outcome attribution; no-live-at-entry actual false, expected true, and calls show abortedAtInvocation false.',
   'cause_status':'The incorrect outcome is established. Why the reflection model made it is unknown. Multiple patch hunks and changed auxiliary material do not isolate a unique causal variable.',
   'impact':'False attribution is copied verbatim into the frozen v1 T4 text. Replace learned candidate if still needed after corrected D1 baselines; do not seed new reflection with old experience.',
   'evidence':refs(['development/D1/reflection-input/training-feedback.json','development/D1/reflection-prompt.md','development/D1/reflection-raw.txt','runs/D1-AUTO-1/archive/patch.diff','runs/D1-AUTO-1/archive/score/stdout.json','frozen-library.json'])})
 findings.append({'issue':'feedback schema omission','code_quote':"for a in schedule.get('assertions', [])",
   'actual_schema':'Query schedules have checks, while document schedules have assertions.',
   'old_failed_check_records':0,'corrected_failed_check_records':[len(r['failed_checks']) for r in rebuilt['runs']],
   'old_original_successes_including_lost':21,'corrected_retained_successes':[len(r['retained_original_successes']) for r in rebuilt['runs']],
   'judgment':'confirmed missing actual/expected observations and ambiguous prior-success label. Effect vectors themselves were accurate; do not claim the old feedback explicitly said the first repair succeeded.',
   'cause_status':'This is an information-loss defect. It may facilitate misreading, but its causal role in the reflection error is unknown.'})
 for alias in ['D2','T2']:
  findings.append({'issue':'unaffected Contract review','alias':alias,'model_verbatim':(V/'derived'/alias/'automatic-contract.md').read_text(),
   'source_basis':'Current task, candidate README and host API specify quiet batching, synchronous boundary persistence, entry-bound receipt and visit-bound notice; inspected conditions/polarities are compatible.',
   'judgment':'reuse unchanged; auxiliary Contract is not exhaustive, and no completeness or policy approval is inferred merely from reference PASS.',
   'evidence':refs([f'materials/{alias}/task.md',f'materials/{alias}/candidate/README.md',f'derived/{alias}/automatic-contract.md'])})
 save(A/'audit/semantic-evidence.json',findings)
 text=['# Semantic audit of v1','', 'The executing agent checked original artifacts rather than adopting REPORT.md conclusions. All judgments below distinguish observations from causal hypotheses.','']
 for f in findings:text+=['## '+f['issue'],'','```json',json.dumps(f,ensure_ascii=False,indent=2),'```','']
 text+=['## v2 handling','','D1/T1: re-extract once each with a general defect-versus-obligation/polarity/ownership self-check, only current visible task/source/docs/AST. No gold scorer or expected class is supplied. The executing agent can veto unresolved contradictions but cannot rewrite model output.','', 'D2/T2: reuse unmodified Contracts/analyses on exact same inputs. D1 AUTO gets two fresh runs because common Contract changes. Rebuild generic feedback with both checks/assertions, all actual successes, retained successes, losses, improvements, unknowns, source facts and hypothesis separation. Do not seed the new reflection with the inaccurate frozen text.','', 'A new semantic veto record binds exact task, sources and Contract, and routes only approved compatible material. Quoted evidence is necessary but is not treated as proof of semantic correctness. Unresolved core contradictions stop before further paid calls.']
 (A/'SEMANTIC_AUDIT.md').write_text('\n'.join(text)+'\n')
 print('audited evidence chains',len(findings))
if __name__=='__main__':main()
