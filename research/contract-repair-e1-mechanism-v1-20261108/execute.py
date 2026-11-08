import importlib.util,json,pathlib as P,shutil,subprocess,time,sys
sys.dont_write_bytecode=True
O=P.Path(__file__).resolve().parent;A=P.Path('/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/contract-repair-e1-mechanism-v1-20261108')
spec=importlib.util.spec_from_file_location('mechanism_runner',O/'runner.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r);save=r.save;sha=r.sha

def archive():
 for p in O.rglob('*'):
  if not p.is_file() or '.runtime' in p.relative_to(O).parts or '__pycache__' in p.relative_to(O).parts:continue
  assert p.name!='auth.json'
  q=A/p.relative_to(O);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)

def prepare():
 assert not (O/'actual-schedule.json').exists()
 # Zero-model check reuses the verified command backend; auth remains outside Git.
 d=O/'offline/current-source';shutil.copytree(O/'materials'/r.cases()[0]['case']/'candidate',d/'workspace');cmd=r.command('offline-source',d,'extract');prefix=cmd[:cmd.index('--')+1]
 body='''import subprocess,json,sys
from pathlib import Path
sys.path.insert(0,'/')
from read_policy import allowed
command='for f in /workspace/src/* /workspace/package.json; do echo "$f"; nl -ba "$f"; done'
assert allowed(command)
p=subprocess.run(['/bin/bash','-lc',command],capture_output=True,text=True);assert p.returncode==0
normalized=[__import__('re').sub(r'^\\s*\\d+\\s+','',x).strip() for x in p.stdout.splitlines()]
for f in Path('/workspace').rglob('*'):
 if f.is_file():assert all(s.strip() in normalized for s in f.read_text().splitlines() if len(s.strip())>=20)
try:Path('/workspace/write-probe').write_text('x');raise AssertionError('writable extraction')
except OSError:pass
assert not Path('/home/sribd').exists() and not Path('/workspace/oracle').exists()
assert subprocess.check_output(['/runtime/node','--version'],text=True).strip()=='v18.20.8'
print(p.stdout)
'''
 # Query installed Node version first, as metadata only (no candidate execution).
 node_version=subprocess.check_output([r.cases()[0]['node'],'--version'],text=True).strip();body=body.replace('v18.20.8',node_version)
 check=subprocess.run(prefix+['/usr/bin/python3','-c',body],capture_output=True,text=True,timeout=20)
 (d/'stdout.txt').write_text(check.stdout);(d/'stderr.txt').write_text(check.stderr);assert check.returncode==0,check.stderr
 shutil.rmtree(O/'.runtime/offline-source')
 save(O/'offline-validation.json',{'status':'PASS','model_requests':0,'current_candidate_body_all_lines_verified':True,'current_source_hashes':r.hashes(d/'workspace'),'extraction_read_only':True,'research_hidden':True,'node_version':node_version,'prior_verified_policy':sha(O/'read_policy.py'),'prior_validated_guard':sha(O/'request_guard.py'),'inherited_accounting_timeout_tests':'prior-offline-validation.json','preparation_error':'initial source task lookup assumed task.md; corrected from manifest core_prompt before any formal call; no inputs changed'})
 save(O/'frozen-config.json',{'repair_model':'gpt-5.6-terra','repair_effort':'medium','extraction_model':'gpt-6-sol','extraction_effort':'low','service_tier':'priority','server_route_attested':False,'CLI_binary':str(r.backend.BINARY),'CLI_sha256':sha(r.backend.BINARY),'CLI_version':subprocess.check_output([str(r.backend.BINARY),'--version'],text=True).strip(),'global_config_before':r.backend.global_snapshot(),'global_requests_cap':156,'maintenance_per_session_cap':24,'extraction_cap':12,'seconds_per_session':600,'report_characters':6000,'stdout_bytes':16777216,'concurrency':1,'runtime_and_auth_outside_git':str(O)})
 files=[p for p in O.rglob('*') if p.is_file() and '.runtime' not in p.parts]
 c=r.cases()[0];files += [P.Path(c['source_case'])/'case.json',P.Path(c['node'])]+list((P.Path(c['source_case'])/'oracle').rglob('*'))
 files += list((P.Path(c['source_case']).parents[3]/'harnesses').glob('*.cjs'))
 save(O/'protocol.json',{'frozen_before_formal_calls':True,'files':{str(p):sha(p) for p in files if p.is_file()}})
 archive()

def run():
 assert not (O/'actual-schedule.json').exists(),'No resume/retry'
 slots=r.read(O/'schedule.json')['slots'];assert len(slots)==7
 actual=[];save(O/'actual-schedule.json',actual)
 for slot in slots:
  cid=slot['case'];prom=O/'prompts'/cid
  if slot['phase']=='repair':
   for p,h in r.read(O/'contracts'/cid/'freeze.json')['files'].items():assert sha(p)==h
  prompt=prom/('extraction.md' if slot['phase']=='extract' else slot['condition']+'.md')
  rec=r.session(slot,prompt.read_text());actual.append(rec);save(O/'actual-schedule.json',actual)
  assert sum(x.get('native',{}).get('started',0) for x in actual)<=156
  print(json.dumps({k:rec.get(k) for k in ['slot','status','failure_class','raw_verdict','seconds','stop_reason']},ensure_ascii=False),flush=True)
  if rec.get('stop_reason'):
   save(O/'stop.json',{'reason':rec['stop_reason'],'slot':slot['slot'],'unstarted':[s for s in slots if s['slot'] not in {x['slot'] for x in actual}],'no_retry':True});archive();return
  if slot['phase']=='extract':
   cp=O/'contracts'/cid;cp.mkdir(parents=True);shutil.copyfile(O/'runs'/slot['slot']/'contract.md',cp/'automatic.md');shutil.copyfile(O/'runs'/slot['slot']/'contract-full.md',cp/'full-report.md')
   text=(cp/'automatic.md').read_text();files=[cp/'automatic.md',cp/'full-report.md']
   for group in ['A','B']:
    out=prom/(group+'.md');out.write_text((prom/(group+'.template.md')).read_text().replace('{{FROZEN_AUTOMATIC_CONTRACT}}',text));files.append(out)
   assert (prom/'B.md').read_text()==(prom/'A.md').read_text()+'\n\n'+(O/'EXPERIENCE.md').read_text()
   save(cp/'freeze.json',{'frozen_at':time.time(),'before_any_maintenance_score':True,'unedited':True,'mechanical_rule':'section 1 before section 2, original whitespace retained','source_run':'x01','source_prompt_sha256':sha(prom/'extraction.md'),'K1_sha256':sha(O/'contract_extraction_K1.md'),'candidate':r.cases()[0]['candidate_files'],'task_sha256':r.cases()[0]['task_sha256'],'configuration':'frozen-config.json','contract_sha256':sha(cp/'automatic.md'),'E1_sha256':sha(O/'EXPERIENCE.md'),'A_B_same_contract':True,'only_difference':'B appends exact E1-v1','files':{str(p):sha(p) for p in files}})
  archive()
 save(O/'completion.json',{'formal_sessions':len(actual),'maintenance_sessions':6,'extraction_sessions':1,'stopped_after_frozen_plan':True});archive()
if __name__=='__main__':
 if sys.argv[1]=='prepare':prepare()
 else:run()
