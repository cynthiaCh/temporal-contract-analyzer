"""Prepare exact inputs, prompts and preservation manifest. No model calls."""
from pathlib import Path
import json,hashlib,subprocess,time,sys
A=Path(__file__).resolve().parent;R=A.parents[1];V=A.parent/'two-class-experience-pilot-20261108_200017'
sys.path.insert(0,str(A))
from toolflow import public_material,extraction_prompt,canonical,digest

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def hashes(p):return {str(f.relative_to(p)):sha(f) for f in p.rglob('*') if f.is_file()}
def compact(ast):return {'status':ast['status'],'summary':ast['summary'],'limitations':ast['limitations'],'files':[{'path':f['path'],'status':f['status'],'events':[{k:v for k,v in e.items() if k in ['kind','line','callee','target','text','tags']} for e in f['events'] if e.get('tags')][:45]} for f in ast['files']],'findings':ast['findings'][:12]}

def main():
 start=time.monotonic();cohort=json.loads((A/'cohort.json').read_text());protected={}
 for name in subprocess.check_output(['git','ls-files','-z'],cwd=R).decode().split('\0'):
  if name and (R/name).is_file():protected[str(R/name)]=sha(R/name)
 # Protect every old archive file, even if untracked, plus original case sources.
 for base in [V]+[Path(c['source_case']) for c in cohort]:
  for f in base.rglob('*'):
   if f.is_file():protected[str(f)]=sha(f)
 runtime={}
 for name,cmd in [('node',[cohort[0]['node'],'--version']),('python',['/usr/bin/python3','--version']),('bwrap',['bwrap','--version'])]:
  r=subprocess.run(cmd,capture_output=True,text=True,timeout=10);assert r.returncode==0;runtime[name]={'command':cmd,'stdout':r.stdout,'stderr':r.stderr}
 for c in cohort:
  d=A/'materials'/c['alias'];src=Path(c['source_case'])
  assert hashes(d/'candidate')==c['candidate_files']==hashes(src/'base')
  assert sha(d/'task.md')==c['task_sha256']
  assert hashes(d/'evaluation')==c['oracle_files']==hashes(src/'oracle')
  for f in (A/'calibration'/c['alias']).glob('*/receipt.json'):
   receipt=json.loads(f.read_text());assert receipt['score_valid'];assert hashes(f.parent/'candidate')==receipt['candidate_before']
  if c['alias'] in ['D1','T1']:
   sources={str(f.relative_to(d/'candidate')):f.read_text() for f in (d/'candidate').rglob('*') if f.is_file() and f.suffix in ['.md','.js','.py']};sources['TASK']=(d/'task.md').read_text()
   mat=public_material((d/'task.md').read_text(),sources,compact(json.loads((d/'ast.json').read_text())),json.loads((A/'spec/taxonomy.json').read_text())['classes'])
   prompt=extraction_prompt(mat)
   assert all(x['case'] not in prompt for x in cohort)
   (d/'preanalysis-prompt.md').write_text(prompt)
 for alias in ['D2','T2']:
  for name in ['analysis.json','automatic-contract.md']:
   assert (A/'derived'/alias/name).read_bytes()==(V/'derived'/alias/name).read_bytes()
 save(A/'protected-files.json',protected)
 save(A/'prepare-receipt.json',{'seconds':time.monotonic()-start,'model_calls':0,'calibration_runs_reused':44,'all_input_versions_match':True,'affected_reextraction':['D1','T1'],'unchanged_auto_contracts':['D2','T2'],'v1_exposure_preserved':True})
 save(A/'runtime-check.json',runtime)
 actual=[]
 for p in (V/'runs').glob('*/archive/command.json'):
  cmd=json.loads(p.read_text());phase=json.loads((p.parent/'receipt.json').read_text())['phase'];model=cmd[cmd.index('-m')+1];effort=[s for s in cmd if s.startswith('model_reasoning_effort=')]
  assert model==('gpt-6-sol' if phase=='extract' else 'gpt-5.6-terra');assert effort==['model_reasoning_effort="'+('medium' if phase=='reflect' else 'low')+'"']
  actual.append({'source':str(p),'phase':phase,'model':model,'effort_flag':effort})
 save(A/'configuration-audit.json',{'v1_actual_commands':actual,'v2_same_roles_and_caps':True,'seconds_per_session':600,'caps':{'extract':12,'repair':24,'reflect':12},'difference':'v2 scores only complete valid candidates and stops on first infrastructure anomaly; v1 permitted partial resource-limit scoring and stopped on two general infra errors.'})
 print('PREPARED',len(protected),'protected files, 44 pinned calibrations; zero models')
if __name__=='__main__':main()
