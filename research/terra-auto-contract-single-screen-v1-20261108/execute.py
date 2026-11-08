import importlib.util,json,pathlib as P,shutil,subprocess,time,sys
sys.dont_write_bytecode=True
O=P.Path(__file__).resolve().parent;A=P.Path('/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/terra-auto-contract-single-screen-v1-20261108')
sp=importlib.util.spec_from_file_location('screen_runner',O/'runner.py');r=importlib.util.module_from_spec(sp);sp.loader.exec_module(r);save=r.save

def archive():
 for p in O.rglob('*'):
  if not p.is_file() or '.runtime' in p.relative_to(O).parts or '__pycache__' in p.relative_to(O).parts:continue
  assert p.name!='auth.json';q=A/p.relative_to(O);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)

def prepare():
 assert not (O/'actual-schedule.json').exists()
 c=r.cases()[0];d=O/'offline/source-read';shutil.copytree(O/'materials'/c['case']/'candidate',d/'workspace');cmd=r.command('offline-source',d,'extract');prefix=cmd[:cmd.index('--')+1]
 body='''import subprocess,sys,re
from pathlib import Path
sys.path.insert(0,'/')
from read_policy import allowed
command='for f in /workspace/README.md /workspace/dependencies.lock.json /workspace/src/workflow.py; do echo "$f"; nl -ba "$f"; done'
assert allowed(command)
p=subprocess.run(['/bin/bash','-lc',command],capture_output=True,text=True);assert p.returncode==0,p.stderr
normalized=[re.sub(r'^\\s*\\d+\\s+','',x).strip() for x in p.stdout.splitlines()]
for f in Path('/workspace').rglob('*'):
 if f.is_file():assert all(s.strip() in normalized for s in f.read_text().splitlines() if len(s.strip())>=20)
try:Path('/workspace/write-probe').write_text('x');raise AssertionError('writable extraction')
except OSError:pass
assert not Path('/home/sribd').exists() and not Path('/workspace/oracle').exists()
print(p.stdout)
print(subprocess.check_output(['/usr/bin/python3','--version'],text=True))
print(subprocess.check_output(['/runtime/node','--version'],text=True))
'''
 z=subprocess.run(prefix+['/usr/bin/python3','-c',body],capture_output=True,text=True,timeout=20);(d/'stdout.txt').write_text(z.stdout);(d/'stderr.txt').write_text(z.stderr);assert z.returncode==0,z.stderr;shutil.rmtree(O/'.runtime/offline-source')
 catalog=r.read(O/'models-cache.snapshot.json')['models']
 for n,eff in [('gpt-5.6-terra','medium'),('gpt-6-sol','low')]:assert any(x['slug']==n and eff in [e['effort'] for e in x['supported_reasoning_levels']] for x in catalog)
 save(O/'offline-validation.json',{'status':'PASS','model_calls':0,'current_candidate_all_body_lines_verified':True,'extraction_read_only':True,'research_hidden':True,'source_hashes':r.hashes(d/'workspace'),'prior_backend_accounting_validation':'prior-offline-validation.json','source_proof_adaptation':'same native session code; .py rather than .js suffix for evidence collection only; frozen before calls','preparation_issue':'source provenance extension .json instead of assumed .md; corrected before any formal model call; eight calibrations were not repeated'})
 save(O/'frozen-config.json',{'repair_model':'gpt-5.6-terra','repair_effort':'medium','extraction_model':'gpt-6-sol','extraction_effort':'low','service_tier':'priority','server_route_attested':False,'CLI_binary':str(r.backend.BINARY),'CLI_sha256':r.sha(r.backend.BINARY),'CLI_version':subprocess.check_output([str(r.backend.BINARY),'--version'],text=True).strip(),'global_config_before':r.backend.global_snapshot(),'max_top_level':3,'max_maintenance':2,'global_requests_cap':60,'maintenance_per_session_cap':24,'extraction_cap':12,'seconds_per_session':600,'report_characters':6000,'stdout_bytes':16777216,'concurrency':1,'runtime_and_auth_outside_git':str(O),'experience_in_execution_prompt':False})
 files=[p for p in O.rglob('*') if p.is_file() and '.runtime' not in p.parts and '__pycache__' not in p.parts]+[P.Path(c['source_case'])/'case.json',P.Path(c['node'])]+list((P.Path(c['source_case'])/'oracle').rglob('*'))
 save(O/'protocol.json',{'frozen_before_any_model_call':True,'files':{str(p):r.sha(p) for p in files if p.is_file()}});archive()

def run():
 r.verify();assert not (O/'actual-schedule.json').exists(),'No resume/retry'
 slots=r.read(O/'schedule.json')['slots'];assert len(slots)==3 and sum(s['phase']=='repair' for s in slots)==2
 actual=[];save(O/'actual-schedule.json',actual)
 for slot in slots:
  cid=slot['case'];p=O/'prompts'/cid
  if slot['phase']=='repair':
   for f,h in r.read(O/'contracts'/cid/'freeze.json')['files'].items():assert r.sha(P.Path(f))==h
  prompt=p/('extraction.md' if slot['phase']=='extract' else 'baseline.md')
  rec=r.session(slot,prompt.read_text());actual.append(rec);save(O/'actual-schedule.json',actual);assert sum(d.get('native',{}).get('started',0) for d in actual)<=60
  print(json.dumps({k:rec.get(k) for k in ['slot','status','failure_class','raw_verdict','seconds','stop_reason']},ensure_ascii=False),flush=True)
  if rec.get('stop_reason'):
   save(O/'stop.json',{'slot':slot['slot'],'reason':rec['stop_reason'],'no_retry':True,'unstarted':[s for s in slots if s['slot'] not in {d['slot'] for d in actual}]});archive();return
  if slot['phase']=='extract':
   cp=O/'contracts'/cid;cp.mkdir(parents=True);shutil.copyfile(O/'runs'/slot['slot']/'contract.md',cp/'automatic.md');shutil.copyfile(O/'runs'/slot['slot']/'contract-full.md',cp/'full-report.md');text=(cp/'automatic.md').read_text();out=p/'baseline.md';out.write_text((p/'baseline.template.md').read_text().replace('{{FROZEN_AUTOMATIC_CONTRACT}}',text))
   save(cp/'freeze.json',{'frozen_at':time.time(),'before_any_maintenance_score':True,'automatic_text_unedited':True,'source_run':slot['slot'],'source_prompt_sha256':r.sha(p/'extraction.md'),'skill_K1_sha256':r.sha(O/'contract_extraction_K1.md'),'candidate_files':r.cases()[0]['candidate_files'],'task_sha256':r.cases()[0]['task_sha256'],'configuration':'frozen-config.json','delivered_range':'only exact section 1 before section 2, whitespace retained; other sections NOT supplied','same_prompt_for_two_repairs':True,'experience_or_human_contract_added':False,'files':{str(f):r.sha(f) for f in [cp/'automatic.md',cp/'full-report.md',out]}})
  archive()
 save(O/'completion.json',{'formal_sessions':3,'maintenance_sessions':2,'extraction_sessions':1,'stopped_after_fixed_plan':True,'no_E1_or_additional_case':True});archive()
if __name__=='__main__':{'prepare':prepare,'run':run}[sys.argv[1]]()
