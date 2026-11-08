"""New batch controller; never executes or resumes any prior dispatcher."""
import pathlib as P,json,importlib.util,sys,time,random,shutil
sys.dont_write_bytecode=True
A=P.Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('batch_runner',A/'runner.py');r=importlib.util.module_from_spec(sp);sp.loader.exec_module(r)
save=r.save
TRAIN,VALID=[c['case'] for c in r.cases()]
def rows():return r.read(A/'actual-schedule.json') if (A/'actual-schedule.json').exists() else []
def check():
 r.verify()
 for p,h in r.read(A/'protected-files.json').items():assert r.sha(p)==h,('protected drift',p)
 for p in (A/'contracts').glob('*/freeze.json') if (A/'contracts').exists() else []:
  for f,h in r.read(p)['files'].items():assert r.sha(f)==h,('contract drift',f)
 if (A/'experience-freeze.json').exists():
  for f,h in r.read(A/'experience-freeze.json')['files'].items():assert r.sha(f)==h,('experience drift',f)
def run(slot,prompt):
 check();assert slot['slot'] not in {x['slot'] for x in rows()},'no rerun'
 assert len(rows())<15 and sum(x.get('native',{}).get('started',0) for x in rows())<324
 z=r.session(slot,prompt);save(A/'actual-schedule.json',rows()+[z]);check()
 assert sum(x.get('native',{}).get('started',0) for x in rows())<=324
 print(json.dumps({k:z.get(k) for k in ['slot','status','raw_verdict','failure_class','seconds','stop_reason']},ensure_ascii=False),flush=True)
 # Isolation/version/accounting/model/tool failures stop immediately; other service issues are never retried.
 if z.get('stop_reason') or z['status']!='VALID':stop(z.get('stop_reason') or z.get('failure_class') or 'invalid evidence')
 return z
def stop(reason):
 save(A/'stop.json',{'reason':reason,'time':time.time(),'unstarted':[s for s in r.read(A/'schedule.json')['slots'] if s['slot'] not in {x['slot'] for x in rows()}],'no_replacement':True});raise SystemExit(0)
def extract(cid,slot):
 p=A/'prompts'/cid;z=run({'slot':slot,'case':cid,'phase':'extract','condition':'AUTO','repeat':None},(p/'extraction.md').read_text());cp=A/'contracts'/cid;cp.mkdir(parents=True)
 for source,dest in [('contract.md','automatic.md'),('contract-full.md','full-report.md')]:shutil.copyfile(A/'runs'/slot/source,cp/dest)
 (p/'AUTO.md').write_text((p/'AUTO.template.md').read_text().replace('{{FROZEN_AUTOMATIC_CONTRACT}}',(cp/'automatic.md').read_text()))
 save(cp/'freeze.json',{'unedited':True,'mechanical_rule':'exact section 1 content before section 2; whitespace preserved','files':{str(f):r.sha(f) for f in [cp/'automatic.md',cp/'full-report.md',p/'AUTO.md']},'source_slot':slot,'frozen_before_maintenance':True})
def repair(cid,slot,condition,repeat):
 p=(A/'prompts'/cid/'AUTO.md').read_text()
 if condition=='AUTO_EXP':p+='\n\n'+(A/'NEW_EXPERIENCE.md').read_text()
 return run({'slot':slot,'case':cid,'phase':'repair','condition':condition,'repeat':repeat},p)
def screen():
 assert not rows(),'fresh batch only'
 extract(VALID,'py-extract')
 rr=[repair(VALID,f'py-screen-{i}','AUTO',i) for i in [1,2]]
 if not all(z.get('infrastructure_valid') and z.get('scoring_valid') for z in rr):stop('Python screening evidence insufficient; no rerun')
 if all(z['raw_verdict']=='PASS' for z in rr):stop('本次未观察到提升空间：Python筛查2/2整体通过')
 extract(TRAIN,'js-extract')
 rr=[repair(TRAIN,f'js-base-{i}','AUTO',i) for i in [1,2]]
 if not all(z.get('infrastructure_valid') and z.get('scoring_valid') for z in rr):stop('JS baseline evidence insufficient; no rerun')
 if all(z['raw_verdict']=='PASS' for z in rr):stop('当前训练条件下缺少失败反馈：JS基线2/2整体通过')
 save(A/'stage-state.json',{'stage':'M2_COMPLETE_READY_TRAINING_FEEDBACK','formal_validation_started':False})
def reflect():
 assert len(rows())==6 and not (A/'stop.json').exists()
 assert (A/'training-feedback-freeze.json').exists()
 for f,h in r.read(A/'training-feedback-freeze.json')['files'].items():assert r.sha(f)==h
 z=run({'slot':'reflection','case':TRAIN,'phase':'reflect','condition':'REFLECTION','repeat':None},(A/'reflection-input.md').read_text())
 shutil.copyfile(A/'runs/reflection/experience.md',A/'NEW_EXPERIENCE.md')
 save(A/'experience-freeze.json',{'files':{str(A/'NEW_EXPERIENCE.md'):r.sha(A/'NEW_EXPERIENCE.md')},'unchanged_raw_report':True,'single_reflection':True,'before_train_revalidation':True})
def revalidate():
 assert len(rows())==7 and r.read(A/'experience-review.json')['admitted_for_training']
 for i in [1,2]:repair(TRAIN,f'js-exp-{i}','AUTO_EXP',i)
 save(A/'stage-state.json',{'stage':'M3_REVALIDATION_COMPLETE_REQUIRES_ACCEPTANCE','formal_validation_started':False})
def validate():
 assert len(rows())==9 and r.read(A/'acceptance.json')['accepted'] and not (A/'stop.json').exists()
 save(A/'stage-state.json',{'stage':'M4_RUNNING','no_feedback_until_all_runs':True})
 for slot in r.read(A/'schedule.json')['slots']:
  if slot['slot'].startswith('py-final-'):repair(VALID,slot['slot'],slot['condition'],slot['repeat'])
 save(A/'stage-state.json',{'stage':'M4_COMPLETE','no_more_evolution':True})
if __name__=='__main__':globals()[sys.argv[1]]()
