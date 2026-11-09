"""New fixed pair: snapshots, AST and necessary native offline calibration."""
import json,sys,time,shutil,subprocess
from pathlib import Path
sys.dont_write_bytecode=True
A=Path(__file__).resolve().parent;REPO=A.parent.parent;BENCH=REPO.parent/'temporal-contract-bench-git'
sys.path.insert(0,str(A));sys.path.insert(0,str(REPO))
from archive import save,sha,inventory,digest
from toolflow import public_material,extraction_prompt
from temporal_contract_analyzer.core import scan

def read(p):return json.loads(Path(p).read_text())
def hashes(p):return {str(f.relative_to(p)):sha(f) for f in p.rglob('*') if f.is_file()}

def main():
 assert not (A/'prepared.json').exists()
 started=time.time();cases=[];checks=[]
 roots=BENCH/'case-clusters/transfer-retry-handoff/arms'
 node18=BENCH/'results/student-case-expansion-runtime/node18/bin/node'
 node16=BENCH/'results/student-case-expansion-runtime/compat-node16/node_modules/node-linux-x64/bin/node'
 for alias,cid,node in [('D','transfer-progress-maintenance-v2-vanilla',node16),('T','transfer-progress-maintenance-v2-python3',node18)]:
  src=roots/cid;m=read(src/'case.json');dest=A/'materials'/alias;dest.mkdir(parents=True)
  shutil.copytree(src/'base',dest/'candidate');shutil.copytree(src/'oracle',dest/'evaluation')
  shutil.copyfile(src/'case.json',dest/'manifest.json');shutil.copyfile(src/'provenance/source-record.json',dest/'source-record.json')
  shutil.copyfile(src/m['diagnostic_tasks']['maintenance']['core_prompt'],dest/'task.md')
  assert not list((dest/'candidate').rglob('AGENTS.md'))
  rules=read(dest/'evaluation/effects.json');variant=rules['variants']['ungranted'];descriptions={e['id']:e['description'] for e in rules['effects']}
  standards=[{'effect':k,'expected':k in variant['required'],'description':descriptions[k],
              'policy_support':'Current task, candidate README/source; executing-agent review, not assertion-name root cause.',
              'evaluator_interpretation_only':True} for k in variant['required']+variant['forbidden']]
  save(dest/'standards.json',standards)
  ast=scan(dest/'candidate',node=str(node));save(dest/'ast.json',ast)
  assert ast['summary']['parsed_files']==ast['summary']['files']>0
  sources={str(f.relative_to(dest/'candidate')):f.read_text() for f in (dest/'candidate').rglob('*') if f.is_file() and f.suffix in ['.md','.js','.py']}
  compact={'status':ast['status'],'summary':ast['summary'],'limitations':ast['limitations'],
           'files':[{'path':f['path'],'status':f['status'],'events':[{k:v for k,v in e.items() if k in ['kind','line','callee','target','text','tags']} for e in f['events'] if e.get('tags')][:45]} for f in ast['files']],
           'findings':ast['findings'][:12]}
  mat=public_material((dest/'task.md').read_text(),sources,compact,read(A/'taxonomy.json')['classes'])
  prompt=extraction_prompt(mat)
  assert cid not in prompt
  (dest/'preanalysis-prompt.md').write_text(prompt)
  c={'alias':alias,'case':cid,'role':'train' if alias=='D' else 'test','source_case':str(src),'node':str(node),
     'candidate_files':hashes(dest/'candidate'),'task_sha256':sha(dest/'task.md'),'oracle_files':hashes(src/'oracle'),
     'framework':m['framework'],'independent_unit_id':m['independent_unit_id'],'AST_summary':ast['summary'],
     'exposure':'Source-unit related prior runs and author outcome-informed design; both current cases inspected; no unseen claim.'}
  cases.append(c)
  # Reference bodies remain external to training/reflection/actors. Only scores
  # and receipts calibrate this exact version. Do not import reference patches.
  variants=[('original',src/'base'),('reference-bounded',src/'reference/bounded'),
            ('reference-expanded',src/'reference/expanded'),('reference-alternative',src/'reference/alternative'),
            ('reference-noop',src/'reference/noop')]+[('mutant-'+v.name,v) for v in sorted((src/'mutants').iterdir())]
  for label,candidate in variants:
   if label=='reference-noop' and not list(candidate.rglob('src/*')):candidate=src/'base' # explicit no-op semantics, not empty tree
   out=A/'calibration'/alias/label;out.mkdir(parents=True)
   command=[str(node),str(src/'oracle/probe.cjs'),str(candidate),'ungranted']
   before=hashes(candidate);t=time.time()
   with (out/'stdout.json').open('wb') as o,(out/'stderr.txt').open('wb') as e:z=subprocess.run(command,stdout=o,stderr=e,timeout=120)
   score=read(out/'stdout.json');errs=[k for k,v in score['schedules'].items() if v.get('runtimeError')]
   ok=z.returncode in (0,1) and score['case_id']==cid and not errs and hashes(candidate)==before
   assert ok,(alias,label,errs)
   if label in ['reference-bounded','reference-alternative']:assert score['verdict']=='PASS',(alias,label,score['verdict'])
   if label in ['original','reference-noop'] or label.startswith('mutant-'):assert score['verdict']!='PASS',(alias,label)
   receipt={'command':command,'candidate_before':before,'exit_code':z.returncode,'verdict':score['verdict'],
            'score_valid':ok,'runtime_errors':errs,'seconds':time.time()-t,'oracle_files':c['oracle_files'],'model_calls':0}
   save(out/'receipt.json',receipt);checks.append({'alias':alias,'variant':label,'verdict':score['verdict'],'score_valid':ok})
 save(A/'cases.json',cases);save(A/'calibration-summary.json',checks)
 save(A/'runtime.json', {name:subprocess.check_output(cmd,text=True).strip() for name,cmd in [('node16',[str(node16),'--version']),('node18',[str(node18),'--version']),('python',['/usr/bin/python3','--version']),('bwrap',['bwrap','--version'])]})
 save(A/'protocol.json',{'scope':'One new fixed training/test pair, same source unit; independent new batch, no inherited experience.',
  'models':{'extract':['gpt-6-sol','low',12,600],'repair':['gpt-5.6-terra','low',24,600],'reflect':['gpt-5.6-terra','medium',12,600]},
  'maximum_sessions':11,'maximum_requests':228,'concurrency':1,'no_retry':True,'no_extra_judge_or_connection_probe':True,
  'development':'one extraction, two AUTO, one new reflection if needed, two independent revalidations',
  'test':'only after library freeze: one extraction, B1/A1/A2/B2, all from original; never use test scores to learn',
  'admission':'at least one evidenced target/overall improvement; no confirmed unsupported policy; record all regressions, neither require nor imply two full passes',
  'early_stop':'two AUTO both pass -> no new experience and stop; invalid/unsupported experience or no qualifying improvement -> stop before test; first infrastructure/meter/isolation/archive anomaly -> stop',
  'normal_behavior_failures':'valid UNDER/OVER continues within the fixed stage',
  'no_case_replacement':True,'production_update':False})
 save(A/'prepared.json',{'time':time.time(),'seconds':time.time()-started,'model_calls':0,'native_calibrations':len(checks)})
 print('PREPARED',len(checks),'offline calibrated variants, no models',flush=True)

if __name__=='__main__':main()
