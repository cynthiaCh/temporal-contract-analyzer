"""Conditional new-batch controller; no historical scheduler or rerun path."""
import sys,json,time,random,shutil,subprocess
from pathlib import Path
sys.dont_write_bytecode=True
A=Path(__file__).resolve().parent;sys.path.insert(0,str(A))
import runner as r
from archive import save,sha,inventory,digest
C=json.loads((A/'cohort.json').read_text());CID=C['case']
def read(p):return json.loads(Path(p).read_text())
def rows():return read(A/'actual-schedule.json') if (A/'actual-schedule.json').exists() else []
def check():
 assert sha(A/'protocol.json')==(A/'protocol.sha256').read_text().strip()
 r.verify(read(A/'protocol.json')['files']);r.verify(read(A/'protected-files.json'))
 for name in ['contract-freeze.json','feedback-freeze.json','experience-freeze.json']:
  if (A/name).exists():r.verify(read(A/name)['files'])
def stop(reason):
 done={x['slot'] for x in rows()};save(A/'stop.json',{'reason':reason,'time':time.time(),'unstarted':[s for s in read(A/'schedule.json')['slots'] if s['slot'] not in done],'no_retry':True,'no_case_effort_or_experience_change':True});raise SystemExit(0)
def score(final,out):
 cmd=[C['node'],str(Path(C['source_case'])/'oracle/probe.cjs'),str(final),'ungranted']
 with (out/'stdout.json').open('wb') as stdout,(out/'stderr.txt').open('wb') as stderr:
  z=subprocess.run(cmd,stdout=stdout,stderr=stderr,timeout=90)
 s=read(out/'stdout.json');assert z.returncode in [0,1] and s['case_id']==CID
 assert set(s['observed_effects'])==set(C['calibration'][0]['effects'])
 rules=read(A/'materials/evaluation/effects.json')['variants']['ungranted'];missing=[k for k in rules['required'] if not s['observed_effects'].get(k)];forbidden=[k for k in rules['forbidden'] if s['observed_effects'].get(k)]
 assert missing==s['missing_required_effects'] and forbidden==s['observed_forbidden_effects']
 expected=('UNDERREACH_AND_OVERREACH' if forbidden else 'UNDERREACH') if missing else ('OVERREACH' if forbidden else 'PASS');assert expected==s['verdict']
 save(out/'receipt.json',{'command':cmd,'exit_code':z.returncode,'case':CID,'source_oracle_sha256':C['oracle_files'],'candidate_digest':digest(inventory(final))})
 return {'verdict':s['verdict'],'effects':s['observed_effects'],'missing':missing,'forbidden':forbidden,'runtime_errors':{k:v['runtimeError'] for k,v in s['schedules'].items() if v.get('runtimeError')},'score_valid':True}
def run(slot,prompt):
 check();rr=rows();assert slot['slot'] not in {x['slot'] for x in rr} and len(rr)<12
 assert sum(x.get('native',{}).get('started',0) for x in rr)<264
 rec=r.session(slot,prompt,case=C,candidate=A/'materials/candidate',task=A/'materials/task.md',config={'seconds_per_session':600,'stdout_bytes':16777216,'frozen_files':read(A/'protocol.json')['files']},run_dir=A/'runs'/slot['slot'],score_fn=score if slot['phase']=='repair' else None,allow_model_execution=True)
 save(A/'actual-schedule.json',rr+[rec]);check()
 assert sum(x.get('native',{}).get('started',0) for x in rows())<=264
 print(json.dumps({'slot':slot['slot'],'status':rec['status'],'failure_class':rec.get('failure_class'),'archive':rec['archive_status']['status'],'seconds':rec['seconds'],**({'verdict':rec.get('score_result',{}).get('verdict')} if not slot['slot'].startswith('final-') else {})},ensure_ascii=False),flush=True)
 if rec['archive_failure_requires_stop']:stop('归档异常；不请求模型修复归档')
 if not rec['infrastructure_valid']:stop('隔离/服务/计量或执行证据异常；不足，不补跑')
 if slot['phase']=='repair' and (rec.get('scoring_status')!='COLLECTED' or not rec.get('scored_candidate_unchanged')):stop('评分交接或候选摘要异常')
 if slot['phase']=='extract' and rec['status']!='VALID':stop('缺少有效固定Contract，不重抽')
 return rec
def slot(name):return next(s for s in read(A/'schedule.json')['slots'] if s['slot']==name)
def repair(name):
 s=slot(name);prompt=(A/'prompts/AUTO.md').read_text()
 if s['condition']=='AUTO_EXP':prompt+='\n\n'+(A/'NEW_EXPERIENCE.md').read_text()
 return run(s,prompt)
def baseline():
 assert not rows() and not (A/'stop.json').exists()
 rec=run(slot('extract'),(A/'prompts/extraction.md').read_text());source=A/'runs/extract/archive';shutil.copyfile(source/'contract.md',A/'automatic-contract.md');shutil.copyfile(source/'contract-full.md',A/'automatic-contract-full.md')
 p=A/'prompts/AUTO.md';p.write_text((A/'prompts/AUTO.template.md').read_text().replace('{{FROZEN_AUTOMATIC_CONTRACT}}',(A/'automatic-contract.md').read_text()))
 save(A/'contract-freeze.json',{'mechanical_rule':'section 1 before section 2, unedited whitespace','files':{str(x):sha(x) for x in [p,A/'automatic-contract.md',A/'automatic-contract-full.md']},'before_any_maintenance':True})
 rr=[repair(f'base-{i}') for i in [1,2]]
 if all(x['score_result']['verdict']=='PASS' for x in rr):stop('本次未观察到同题经验提升空间：AUTO开发基线2/2整体通过')
 save(A/'stage-state.json',{'stage':'M2_COMPLETE_REQUIRES_SOURCE_BOUND_FEEDBACK','formal_started':False})
def reflection():
 assert len(rows())==3 and not (A/'stop.json').exists() and (A/'feedback-freeze.json').exists()
 rec=run(slot('reflection'),(A/'reflection-input.md').read_text());raw=A/'runs/reflection/archive/experience.md';shutil.copyfile(raw,A/'NEW_EXPERIENCE.md')
 save(A/'experience-freeze.json',{'files':{str(A/'NEW_EXPERIENCE.md'):sha(A/'NEW_EXPERIENCE.md')},'unmodified_raw_report':True,'one_reflection_only':True})
def revalidate():
 assert len(rows())==4 and read(A/'experience-review.json')['admitted_for_revalidation'] and not (A/'stop.json').exists()
 for i in [1,2]:repair(f'reval-{i}')
 save(A/'stage-state.json',{'stage':'M3_REVALIDATED_REQUIRES_ACCEPTANCE','formal_started':False})
def validate():
 assert len(rows())==6 and read(A/'acceptance.json')['accepted'] and not (A/'stop.json').exists()
 save(A/'stage-state.json',{'stage':'M4_RUNNING','frozen_experience_and_contract':True,'no_result_feedback_or_revision':True})
 for s in read(A/'schedule.json')['slots']:
  if s['slot'].startswith('final-'):repair(s['slot'])
 save(A/'stage-state.json',{'stage':'M4_COMPLETE','no_further_evolution':True})
if __name__=='__main__':globals()[sys.argv[1]]()
