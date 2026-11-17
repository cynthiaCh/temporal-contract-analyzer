"""Authorized incremental construction -> Silas automatic acceptance -> new20 testing.
All model work uses the public CLI. Four workers, phase barriers, durable receipts.
"""
import argparse,csv,datetime,fcntl,hashlib,json,os,shutil,subprocess,sys,time
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
import threading
REPO=Path(__file__).resolve().parents[2];sys.path.insert(0,str(REPO))
from temporal_contract_analyzer import archive,experience_approval as approval,compact_experience as compact
from temporal_contract_analyzer.tempoevo_v4 import Trajectory,current_protocol
from temporal_contract_analyzer.tempoevo_backend import NativeV4Backend
from temporal_contract_analyzer.swe_tempoc_inputs import case_input
from temporal_contract_analyzer.candidate_files import capture

def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def read(p):return json.loads(Path(p).read_text())
def save(p,x):archive.atomic_json(Path(p),x)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rows(p):return list(csv.DictReader(Path(p).open(encoding='utf-8-sig')))
def run(cmd,log):
 with Path(log).open('a') as out:return subprocess.run(cmd,cwd=REPO,stdout=out,stderr=subprocess.STDOUT).returncode

def arguments(root,selection,destination,mode,start=1,count=1,bank=None):
 p=read(root/'plan.json');a=[sys.executable,'-B',str(REPO/'tools/tempoevo-docker/prepare_selected.py'),'--root',str(destination),'--selection-file',str(selection),'--evaluation-split',str(root/'split.json'),'--swe-tempoc-root',p['benchmark'],'--solver-image',p['solver_image'],'--grader-image',p['grader_image'],'--model-config',str(root/'model-profiles.json'),'--model-profile','sol61-medium','--store',str(root/'experience-library'),'--memory-snapshot',str(bank or root/'initial-memory-snapshot.json'),'--mode',mode,'--condition','structured','--start-rank',str(start),'--limit',str(count)]
 if mode=='learning':a+=['--training-recipe','v8-compatible-v1','--learning-policy','online','--online-memory',str(root/'provisional'),'--public-checks-docs',str(root/'public-checks-docs.json'),'--visible-evaluators',str(root/'visible-evaluators.json')]
 else:a+=['--retrieval-profile','business-source-v1']
 return a

def prepare(root):
 p=read(root/'plan.json');assert not (root/'preflight.json').exists(),'Use a fresh preparation root'
 # Bind all selected benchmark files to the immutable grader image.
 roster={r['case_id']:r for r in read(Path(p['benchmark'])/'benchmark/swe-tempoc.json')['cases']};files={}
 for item in rows(root/'selected_100_cases.csv'):
  for f in (Path(p['benchmark'])/roster[item['case_id']]['manifest']).parent.rglob('*'):
   if f.is_file() and '__pycache__' not in f.parts:files[f.relative_to(p['benchmark']).as_posix()]=sha(f)
 code="import sys,json,hashlib;from pathlib import Path;d=json.load(sys.stdin);print(json.dumps(dict(files_checked=len(d),mismatches=[k for k,v in d.items() if not (Path('/opt/swe-tempoc')/k).is_file() or hashlib.sha256((Path('/opt/swe-tempoc')/k).read_bytes()).hexdigest()!=v])))"
 result=subprocess.run(['docker','run','--rm','-i','--network','none','--read-only','--entrypoint','python3',p['grader_image'],'-B','-c',code],input=json.dumps(files),capture_output=True,text=True,check=True)
 identity=json.loads(result.stdout);save(root/'selected-case-image-verification.json',identity);assert not identity['mismatches']
 train=rows(root/'training_to_run.csv');test=rows(root/'testing_new20_cases.csv')
 def prepare_one(item,mode):
  cid=item['case_id'];base=root/('prepared-train' if mode=='learning' else 'preflight-test')/cid;base.mkdir(parents=True,exist_ok=True)
  for previous in sorted(base.glob('batch*'),reverse=True):
   try:
    retained=read(previous/'progress.json')[0]
    assert retained['status']=='prepared'
    Trajectory(Path(retained['root'])/'trajectory').verify()
    if mode=='testing':
     controls=[read(base/('checks-'+previous.name)/name/'result.json') for name in ('original','reference','negative')]
     assert all(v.get('valid') is True and v.get('passed')==(i==1) for i,v in enumerate(controls))
    return retained
   except (OSError,ValueError,KeyError,AssertionError):pass
  dest=base/('batch' if not (base/'batch').exists() else 'batch-reprepare-'+str(time.time_ns()));cmd=arguments(root,root/('training_to_run.csv' if mode=='learning' else 'testing_new20_cases.csv'),dest,mode,int(item['rank']))
  save(base/'command.json',cmd);rc=run(cmd,base/'preparation.log');assert rc==0,(cid,'preparation failed',str(base/'preparation.log'))
  result=read(dest/'progress.json')[0];Trajectory(Path(result['root'])/'trajectory').verify()
  if mode=='testing':
   c=case_input(cid,p['benchmark']);manifest=Path(p['benchmark'])/c['case_record']['manifest'];m=read(manifest);ev=dict(image=p['grader_image'],inputs={str(Path(result['root'])/'case.json'):'/checks/case.json',str(REPO/'tools/tempoevo-docker/gold.py'):'/checks/gold.py'},command=['/usr/bin/python3','/checks/gold.py'],seconds=180)
   if read(Path(result['root'])/'case.json').get('projection',{}).get('kind')=='frozen_base_public_projection_v1':ev.update(inputs={str(Path(result['root'])/'case.json'):'/checks/case.json',str(REPO/'tools/tempoevo-docker/projected_gold.py'):'/checks/gold.py'},seconds=300)
   if m.get('schema_version')=='python-pilot-0.1':ev['inputs'][str(REPO/'tools/tempoevo-docker/python_gold.py')]=ev['inputs'].pop(str(REPO/'tools/tempoevo-docker/gold.py'))
   for name,overlay in [('original',None),('reference',(m.get('reference') or m['references']['bounded'])),('negative',m['mutants'][0])]:
    subject=base/('calibration-'+dest.name)/name;shutil.copytree(c['candidate'],subject)
    if overlay:shutil.copytree(manifest.parent/overlay,subject,dirs_exist_ok=True)
    output=base/('checks-'+dest.name)/name;output.mkdir(parents=True);raw=NativeV4Backend({}).evaluate('gold',dict(candidate=str(subject),evaluator=ev),output);save(output/'result.json',raw);assert raw.get('valid') is True and raw.get('passed')==(name=='reference'),(cid,name,raw.get('error'))
  return result
 results=[];errors=[]
 with ThreadPoolExecutor(max_workers=4) as pool:
  jobs={pool.submit(prepare_one,item,mode):(item,mode) for mode,items in [('learning',train),('testing',test)] for item in items}
  for future in as_completed(jobs):
   item,mode=jobs[future]
   try:r=future.result();results.append(dict(mode=mode,**r));print(json.dumps(dict(prepared=item['case_id'],mode=mode)),flush=True)
   except Exception as e:errors.append(dict(case_id=item['case_id'],mode=mode,error=repr(e)));print(json.dumps(errors[-1]),flush=True)
   save(root/'preparation-progress.json',dict(prepared=len(results),expected=len(train)+len(test),errors=errors))
 if errors:raise RuntimeError('Preflight errors: '+json.dumps(errors))
 batch=root/'train-batch';batch.mkdir();save(batch/'progress.json',sorted([r for r in results if r['mode']=='learning'],key=lambda r:r['rank']))
 save(root/'preflight.json',dict(valid=True,model_calls=0,train_prepared=len(train),test_prepared=20,source_image_identity=identity,public_checks='syntax/build smoke for newly executed cases; training Oracle independent',zero_model_controls='3Gold+3public per training case;3Gold per new test',prepared_trajectories=results,finished_at=now()))

def check_authorization(root):
 a=read(root/'authorization.json');assert a['execute_training'] and a['execute_new20_test'] and a['automatic_accept_new_experiences'] and a['reviewer']=='Silas'
 assert a['kind']=='explicit_user_authorization' and a['review_is_automatic'] is True
 assert sha(root/'split.json')==a['split_sha256']
 return a

def execute(root):
 auth=check_authorization(root);pre=read(root/'preflight.json');assert pre['valid'] and read(root/'agent-follows-doc.json')['valid']
 if (root/'completion.json').exists():raise ValueError('Completed chain is read-only')
 jobs=read(root/'train-batch/progress.json');plan=read(root/'plan.json');eventlock=threading.Lock()
 def event(value):
  with eventlock:
   with (root/'queue-events.jsonl').open('a') as f:f.write(json.dumps(dict(at=now(),**value))+'\n')
 def execute_one(item):
  t=Path(item['root'])/'trajectory';Trajectory(t).verify();s=read(t/'state.json')
  if any(z['status']=='started' for z in s['stages']):raise ValueError('Incomplete started stage requires investigation: '+item['case_id'])
  if not s.get('finalized') and s['status'] not in ['execution_invalid','cancelled']:
   cmd=[sys.executable,'-B','-m','temporal_contract_analyzer','tempoevo','run','--root',str(t),'--execute']
   with (t.parent/'training.log').open('a') as log:
    process=subprocess.Popen(cmd,cwd=REPO,stdout=log,stderr=subprocess.STDOUT);event(dict(event='train_started',case_id=item['case_id'],pid=process.pid));rc=process.wait()
  else:rc=None
  s=read(t/'state.json');event(dict(event='train_finished',case_id=item['case_id'],status=s['status']))
  extraction_only_failure=s['status']=='execution_invalid' and s.get('training_accepted') is True and any(z['kind']=='extract' and z['status']=='invalid' for z in s['stages'])
  return dict(case_id=item['case_id'],rank=item['rank'],root=str(t),status='repair_accepted_extraction_unavailable' if extraction_only_failure else s['status'],raw_status=s['status'],accepted=s.get('training_accepted'),attempts=len(s['attempts']),exit_code=rc,error=s.get('error'),extraction_only_failure=extraction_only_failure)
 event(dict(event='phase_started',phase='train',workers=4,cases=len(jobs),reused=plan['reuse']))
 results=[]
 with ThreadPoolExecutor(max_workers=4) as pool:
  futures={pool.submit(execute_one,item):item for item in jobs}
  for future in as_completed(futures):
   item=futures[future]
   try:value=future.result()
   except Exception as e:value=dict(case_id=item['case_id'],root=str(Path(item['root'])/'trajectory'),status='queue_error',error=repr(e),accepted=False)
   results.append(value);save(root/'training-progress.json',dict(reused=plan['reuse'],executed=len(results),expected=len(jobs),cases=results))
 # Preserve every candidate, including unfinished/failed reflections, before approval.
 archive_dir=REPO/'experience-memory/training-runs'/root.name;archive_dir.mkdir(parents=True,exist_ok=True)
 for value in results:
  t=Path(value['root']);dest=archive_dir/'cases'/value['case_id'];dest.mkdir(parents=True,exist_ok=True)
  for name in ['protocol.json','state.json','summary.json']:
   if (t/name).exists():shutil.copyfile(t/name,dest/name)
  if (t/'candidate-pool').exists():shutil.copytree(t/'candidate-pool',dest/'candidate-pool',dirs_exist_ok=True)
 if (root/'provisional').exists():shutil.copytree(root/'provisional',archive_dir/'provisional',dirs_exist_ok=True)
 bad=[r for r in results if r['status'] in ['queue_error','execution_invalid','cancelled']]
 if bad:
  save(root/'needs-investigation.json',dict(phase='train',cases=bad,policy='preserve roots; fix confirmed tooling error before preparing replacement attempts; never silently replay a started stage'))
  subprocess.run(['git','add',str(archive_dir)],cwd=REPO,check=True);subprocess.run(['git','commit','--only',str(archive_dir),'-m','Archive incremental training results requiring investigation'],cwd=REPO,check=True)
  raise RuntimeError('Training infrastructure/invalid jobs need investigation; test phase not started')
 publications=[]
 for value in results:
  t=Path(value['root']);candidate=t/'candidate-pool/success.json'
  if not candidate.exists():continue
  code=run([sys.executable,'-B','-m','temporal_contract_analyzer','tempoevo','publish-candidate','success','--root',str(t)],t.parent/'publication.log');assert code==0
  record=read(candidate);publications.append(dict(case_id=value['case_id'],candidate_id=record.get('published_sha256'),record=record))
 # Accept only content newly published by THIS authorized run; preserve previous reviews.
 initial_ids={r['id'] for p,v in compact.documents(root/'initial-library') for r in v['experiences']}
 accepted=[]
 for file,value in compact.documents(root/'experience-library'):
  changed=False
  for item in value['experiences']:
   if item['id'] not in initial_ids and item.get('review',{}).get('decision')=='pending':
    item['review']=dict(reviewer='Silas',decision='accept',at=now());changed=True;accepted.append(item['id'])
  if changed:compact._write(file,value)
 # Publish accepted additions to the shared library without replacing unrelated edits.
 with compact._locked(REPO/'experience-memory/library'):
  current=compact.documents(REPO/'experience-memory/library');known={i['id'] for f,v in current for i in v['experiences']};f=REPO/'experience-memory/library/candidates.json';v=read(f) if f.exists() else dict(schema_version=compact.VERSION,category='candidates',experiences=[])
  for file,value in compact.documents(root/'experience-library'):
   for item in value['experiences']:
    if item['id'] in accepted and item['id'] not in known:v['experiences'].append(item);known.add(item['id'])
  compact._write(f,v)
 save(root/'automatic-review.json',dict(reviewer='Silas',kind='user_authorized_automatic_acceptance',independent_human_review=False,authority=auth,accepted_ids=accepted,at=now()))
 bank=approval.freeze(root/'experience-library');save(root/'final-memory-snapshot.json',bank)
 for name in ['training-progress.json','automatic-review.json','final-memory-snapshot.json','reuse.json','authorization.json','plan.json']:shutil.copy2(root/name,archive_dir/name)
 shutil.copytree(root/'experience-library',archive_dir/'final-library',dirs_exist_ok=True)
 for value in publications:
  t=next(Path(r['root']) for r in results if r['case_id']==value['case_id']);shutil.copytree(t/'candidate-pool',archive_dir/'cases'/value['case_id']/'candidate-pool',dirs_exist_ok=True)
 subprocess.run(['git','add',str(archive_dir),str(REPO/'experience-memory/library/candidates.json')],cwd=REPO,check=True)
 subprocess.run(['git','commit','--only',str(archive_dir),str(REPO/'experience-memory/library/candidates.json'),'-m','Archive incremental training and user-authorized Silas automatic approvals'],cwd=REPO,check=True)
 event(dict(event='phase_started',phase='test20',approved_entries=len(bank['entries'])))
 testroot=root/(root.name+'-new20');testroot.mkdir(exist_ok=True)
 cmd=arguments(root,root/'testing_new20_cases.csv',testroot/'batch','testing',1,20,root/'final-memory-snapshot.json')
 assert run(cmd,root/'prepare-final-test.log')==0
 save(testroot/'plan.json',dict(test_cases=20,approved_entries=len(bank['entries']),memory_snapshot_sha256=bank['sha256']))
 rc=run([sys.executable,'-B',str(REPO/'tools/tempoevo-docker/run_testing.py'),'--root',str(testroot),'--workers','4','--execute'],root/'testing.log')
 completion=read(testroot/'completion.json');prior=read(Path(plan['retained_root'])/'completion.json')
 summary=dict(finished_at=now(),train_total=70,reused=plan['reuse'],new_training_cases=results,new20=completion,retained10=dict(root=plan['retained_root'],passed=8,failed=2,bank='historical39',results_reused=True),combined=dict(passed=completion['passed']+8,total=30,failed=completion['failed']+2,execution_invalid=completion['execution_invalid'],interpretation='mixed-cohort mixed-time/mixed-bank diagnostic result; new20 primary, old10 development regression'),testing_exit_code=rc,automatic_review=root.name+'/automatic-review.json');save(root/'completion.json',summary)
 target=REPO/'experiments/incremental-runs'/root.name;target.mkdir(parents=True,exist_ok=True)
 for name in ['completion.json','automatic-review.json','training-progress.json','queue-events.jsonl','plan.json','reuse.json','authorization.json','final-memory-snapshot.json']:shutil.copy2(root/name,target/name)
 subprocess.run(['git','add',str(target),str(REPO/'experiments/testing-runs'/testroot.name)],cwd=REPO,check=True)
 subprocess.run(['git','commit','--only',str(target),str(REPO/'experiments/testing-runs'/testroot.name),'-m','Record incremental training and new20 plus retained10 test results'],cwd=REPO,check=True)
 event(dict(event='chain_completed',passed=summary['combined']['passed'],total=30))

def main():
 a=argparse.ArgumentParser();a.add_argument('--root',type=Path,required=True);g=a.add_mutually_exclusive_group(required=True);g.add_argument('--prepare-only',action='store_true');g.add_argument('--execute',action='store_true');args=a.parse_args();root=args.root.resolve()
 with (root/('prepare.lock' if args.prepare_only else 'queue.lock')).open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  if args.prepare_only:prepare(root)
  else:execute(root)
if __name__=='__main__':main()
