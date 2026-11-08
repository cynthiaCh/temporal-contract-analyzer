"""Isolated frozen experiment; no search, retries, replacements or subagents.

Commands: offline, prepare-prompts, freeze, run. `run` requires explicit E1 approval.
"""
import importlib.util, json, os, re, shlex, shutil, signal, subprocess, sys, time
from pathlib import Path

O=Path(__file__).resolve().parent; R=O.parent.parent
sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('frozen_native_backend',O/'native_backend.py')
backend=importlib.util.module_from_spec(spec);spec.loader.exec_module(backend);backend.OUT=O
read=backend.read;save=backend.save;hashes=backend.hashes
def sha(p):return backend.sha(Path(p).read_bytes())
def cases():return read(O/'cohort.json')['cases']
def getcase(cid):return next(c for c in cases() if c['case']==cid)

def command(call,folder,c,phase):
 meter=folder/'meter'
 if not (meter/'config.json').exists():save(meter/'config.json',{'global_cap':12,'calls':{call:{'cap':12,'mode':'maintenance' if phase=='repair' else 'extraction'}}})
 cmd=backend.command(call,folder,'extraction',True,meter)
 if phase=='repair':
  i=cmd.index(str(folder/'workspace'));assert cmd[i-1]=='--ro-bind';cmd[i-1]='--bind'
  cmd[cmd.index('--sandbox')+1]='danger-full-access'
  cmd[cmd.index('-m')+1]='gpt-5.6-terra'
  cmd=[x.replace('model_reasoning_effort="low"','model_reasoning_effort="medium"') for x in cmd]
 node=Path(c['node']);runtime=R.parent/'temporal-contract-bench-git/runtimes'
 mounts=['--ro-bind',str(node),'/runtime/node']
 # Existing runtime dependencies only; no download/install. Same mounts in every arm of a case.
 framework=c['mechanisms'].get('carrier')
 source=Path(c['source_case']);manifest=read(source/'case.json');name=manifest['framework']['runtime']
 dep=runtime/name/'node_modules'
 if dep.exists():mounts+=['--ro-bind',str(dep),'/runtime/node_modules','--setenv','NODE_PATH','/runtime/node_modules']
 i=cmd.index('--chdir');cmd[i:i]=mounts
 return cmd

def make_prompts():
 common='\n\n完成原维护任务，实际修改候选代码并做相关验证。仅在 /workspace 内工作，不查看研究材料、历史、评分器或网络。Node自检使用 /runtime/node，并记录 --version。依赖仅使用已有只读运行时。最终返回JSON，唯一字段report，最多6000个Unicode字符，报告实际交付、验证与未覆盖范围。补丁从工作区归档。\n'
 warning='以下为辅助材料。依据原任务和项目证据核查其适用性；存在冲突或证据不足时不要盲目执行。\n'
 experience=(O/'EXPERIENCE.md').read_text()
 skill=(O/'contract_extraction_K1.md').read_text()
 for c in cases():
  cid=c['case'];d=O/'materials'/cid;p=O/'prompts'/cid;p.mkdir(parents=True,exist_ok=True)
  task=(d/'task.md').read_text()
  extraction=task+'\n\n只从 /workspace 的任务相关源码和文档提取Contract，不修改或运行代码。不访问历史、研究评价、人工Contract或网络。\n\n'+skill+'\n\n最终返回JSON，唯一字段report，最多6000个Unicode字符；严格使用四个栏目标题：\n1. 可确认的 Contract\n2. 每条的条件、效果、来源及依据\n3. 不能确认的候选要求\n4. 建议验证范围\n'
  (p/'extraction.md').write_text(extraction)
  (p/'N.md').write_text(task+common)
  (p/'H.md').write_text(task+'\n\n'+warning+(d/'H.md').read_text()+common)
  # These two templates cannot be dispatched until an extraction output is frozen.
  (p/'M.template.md').write_text(task+'\n\n'+warning+'{{FROZEN_AUTOMATIC_CONTRACT}}'+common)
  (p/'E.template.md').write_text(task+'\n\n'+warning+'{{FROZEN_AUTOMATIC_CONTRACT}}'+common+'\n<experience>\n'+experience+'\n</experience>\n')
 save(O/'prompt-equivalence.json',{'common':common,'warning':warning,'experience_stage':'repair','M_E_contract':'same byte-identical frozen section 1','only_E_difference':'append the single frozen E1-v1','all_contracts_referenced_from_visible_sources':True,'M_E_templates_not_dispatchable':True})

def offline():
 results=[]
 # Validate every distinct runtime mount and both read-only extraction/writable repair paths.
 distinct={(c['node'],read(Path(c['source_case'])/'case.json')['framework']['runtime']):c for c in cases()}
 for c in distinct.values():
  for phase in ['extraction','repair']:
   call='offline-v3-'+str(len(results));folder=O/'offline'/call
   shutil.copytree(O/'materials'/c['case']/'candidate',folder/'workspace')
   cmd=command(call,folder,c,phase);prefix=cmd[:cmd.index('--')+1]
   body="from pathlib import Path\nimport subprocess\np=Path('/workspace')\nassert not Path('/home/sribd').exists()\nassert not Path('/proc/1/root/home/sribd').exists()\nassert not Path('/workspace/oracle').exists()\nassert not Path('/workspace/H.md').exists()\nassert not Path('/workspace/task.md').exists()\nprint(subprocess.check_output(['/runtime/node','--version'],text=True))\nprint(next(x for x in sorted(p.rglob('*')) if x.is_file() and x.suffix in ['.js','.jsx','.vue']).read_text())\n"
   if phase=='repair':body+="q=p/'write-probe';q.write_text('ok');q.unlink()\n"
   else:body+="try:\n (p/'write-probe').write_text('bad')\n raise AssertionError('read-only failed')\nexcept OSError:pass\n"
   runtime=read(Path(c['source_case'])/'case.json')['framework']['runtime']
   if runtime in ['react18','vue2','vue3']:
    package='react' if runtime=='react18' else 'vue'
    body+="print(subprocess.check_output(['/runtime/node','-p',\"require('"+package+"/package.json').version\"],text=True))\n"
   test=subprocess.run(prefix+['/usr/bin/python3','-c',body],capture_output=True,text=True,timeout=20)
   (folder/'namespace-probe.txt').write_text(test.stdout+test.stderr);assert test.returncode==0,test.stderr
   flags=[]
   for i,x in enumerate(cmd):
    if x in ['-c','--enable','--disable']:flags+=cmd[i:i+2]
   features=subprocess.run(prefix+['/opt/codex','features','list']+flags,capture_output=True,text=True,timeout=20)
   (folder/'features.txt').write_text(features.stdout+features.stderr);assert features.returncode==0
   f={x.split()[0]:x.split()[-1]=='true' for x in features.stdout.splitlines() if x.strip()}
   assert f['code_mode_host'] and f['shell_tool'] and not any(f.get(k) for k in ['apps','plugins','multi_agent'])
   host=subprocess.run(prefix+['/opt/codex-code-mode-host','--help'],capture_output=True,text=True,timeout=20);assert host.returncode==0
   # Synthetic native hook events only. No model is invoked.
   save(folder/'meter/config.json',{'global_cap':1,'calls':{call:{'cap':1,'mode':'maintenance'}}})
   fake="import subprocess,json;ev=lambda k:json.dumps({'hook_event_name':k,'status':'completed'});subprocess.run(['/usr/bin/python3','/request_guard.py'],input=ev('PreModelRequest'),text=True);subprocess.run(['/usr/bin/python3','/request_guard.py'],input=ev('PostModelRequest'),text=True);subprocess.run(['/usr/bin/python3','/request_guard.py'],input=ev('PreModelRequest'),text=True);open('/output/over-cap','w').write('bad')"
   killed=subprocess.run(prefix+['/bin/bash','-c','exec -a /opt/codex /usr/bin/python3 -c '+shlex.quote(fake)],capture_output=True,text=True,timeout=20)
   assert killed.returncode!=0 and not (folder/'cli-output/over-cap').exists()
   results.append({'case':c['case'],'node':c['node'],'phase':phase,'namespace':'PASS','features':f,'backend_help':'PASS','cap_kill_exit':killed.returncode,'model_calls':0,'argv':cmd})
   shutil.rmtree(O/'.runtime'/call)
 save(O/'offline-validation.json',{'status':'PASS','model_calls':0,'checks':results,'meter_scope':'one independent meter per slot, aggregate bounded by 90 unique slots × 12; never share another session ledger','limitations':'Cooperative model; system binaries/network transport remain available to CLI. No network source tools enabled; not a hostile security boundary.'})

def freeze():
 assert read(O/'admission.json')['eligible_cases']==[c['case'] for c in cases()]
 assert read(O/'offline-validation.json')['status']=='PASS'
 catalog=read(O/'models-cache.snapshot.json')['models']
 for name,effort in [('gpt-5.6-terra','medium'),('gpt-6-sol','low')]:
  m=next(m for m in catalog if m.get('slug')==name);assert effort in [x['effort'] for x in m['supported_reasoning_levels']]
 config={'repair_model':'gpt-5.6-terra','repair_effort':'medium','extraction_model':'gpt-6-sol','extraction_effort':'low','service_tier':'priority','server_route_attested':False,'backend':['native Codex exec','code_mode_host','shell_tool'],'ReAct':False,'subagents':False,'global_config_before':backend.global_snapshot(),'binary':str(backend.BINARY),'binary_sha256':sha(backend.BINARY),'cli_version':subprocess.check_output([str(backend.BINARY),'--version'],text=True).strip(),'budget':read(O/'budget.json'),'experience_sha256':sha(O/'EXPERIENCE.md'),'experience_confirmation':'pending; checked again at execution','extraction_skill_sha256':sha(O/'contract_extraction_K1.md'),'automatic_contract_packaging':'exact section 1 body between fixed headings, as historical M; no manual fill. Full output retained separately.','new_extractions':10,'reuse':0,'output_limit_scope':'6000 Unicode characters in final report only; native reasoning/tool output not falsely called capped','stop':'first repair source-body gate failure; missing accounting; two consecutive infrastructure failures; scoring anomaly; no retry/replacement/model switch'}
 save(O/'frozen-config.json',config)
 shutil.copyfile(O/'schedule.proposed.json',O/'schedule.json')
 files=[p for sub in ['materials','prompts'] for p in (O/sub).rglob('*') if p.is_file()]
 files += [O/n for n in ['PLAN.md','DIAGNOSIS.md','EXPERIENCE.md','admission.json','cohort.json','budget.json','metric-spec.json','source-scope.json','exposure-index.json','runner.py','prepare.py','scope.py','audit.py','summarize.py','native_backend.py','request_guard.py','research-config.toml','models-cache.snapshot.json','contract_extraction_K1.md','extraction.schema.json','schedule.json','frozen-config.json','offline-validation.json']]
 for c in cases():
  case=Path(c['source_case']);files += [case/'case.json']+list((case/'oracle').glob('*'))+[Path(c['node'])]
 files += list((R.parent/'temporal-contract-bench-git/harnesses').glob('*.cjs'))
 save(O/'protocol.json',{'frozen_before_model_calls':True,'stage':'prepared; expert confirmation required before dispatch','files':{str(p):sha(p) for p in files if p.is_file()}})
 (O/'protocol.sha256').write_text(sha(O/'protocol.json')+'\n')

def verify():
 assert sha(O/'protocol.json')==(O/'protocol.sha256').read_text().strip()
 for p,h in read(O/'protocol.json')['files'].items():assert sha(p)==h,p

def read_proof(events,c):
 lines={line.strip() for p in (O/'materials'/c['case']/'candidate').rglob('*') if p.is_file() and p.suffix in ['.js','.jsx','.vue'] for line in p.read_text().splitlines() if len(line.strip())>=20}
 proofs=[]
 for n,e in enumerate(events,1):
  i=e.get('item',{})
  if e.get('type')=='item.completed' and i.get('type')=='command_execution' and i.get('exit_code')==0:
   output=i.get('aggregated_output','');normalized={re.sub(r'^\s*\d+\s+','',l).strip() for l in output.splitlines()};matched=sorted(lines&normalized)
   if len(matched)>=3:proofs.append({'event_line':n,'matched_source_lines':matched,'output_sha256':backend.sha(output)})
 return proofs

def session(slot,prompt,phase):
 verify();c=getcase(slot['case']);call=slot['slot'];folder=O/'runs'/call
 folder.mkdir(parents=True,exist_ok=False);shutil.copytree(O/'materials'/c['case']/'candidate',folder/'workspace')
 save(folder/'frozen-start.json',hashes(folder/'workspace'));assert hashes(folder/'workspace')==c['candidate_files']
 (folder/'actual-prompt.md').write_text(prompt);cmd=command(call,folder,c,phase)
 rec=dict(slot,phase=phase,status='LAUNCHED',started_at=time.time(),argv=cmd,prompt_sha256=backend.sha(prompt))
 save(folder/'receipt.json',rec)
 try:
  with (folder/'actual-prompt.md').open('rb') as inp,(folder/'events.jsonl').open('wb') as out,(folder/'stderr.log').open('wb') as err:
   proc=subprocess.Popen(cmd,stdin=inp,stdout=out,stderr=err,start_new_session=True,cwd=folder/'workspace')
   try:proc.wait(timeout=600)
   except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait();rec['timed_out']=True
  events=[];malformed=[]
  for n,l in enumerate((folder/'events.jsonl').read_text().splitlines(),1):
   try:events.append(json.loads(l))
   except ValueError:malformed.append(n)
  meter=read(folder/'meter/ledger.json') if (folder/'meter/ledger.json').exists() else {};native=meter.get('sessions',{}).get(call,{})
  posts=[e['event'] for e in meter.get('events',[]) if e['event'].get('hook_event_name')=='PostModelRequest']
  tokenkeys=['input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens']
  usage={k:sum(e.get('token_usage',{}).get(k,0) or 0 for e in posts) for k in tokenkeys}
  expected_model='gpt-5.6-terra' if phase=='repair' else 'gpt-6-sol'
  model_match=all(e.get('model')==expected_model for e in posts)
  rawpath=folder/'cli-output/answer.json';raw=rawpath.read_text() if rawpath.exists() else '';(folder/'raw-answer.txt').write_text(raw)
  try:answer=json.loads(raw);format_ok=set(answer)=={'report'} and isinstance(answer['report'],str) and len(answer['report'])<=6000
  except (ValueError,TypeError):answer={};format_ok=False
  complete=proc.returncode==0 and sum(e.get('type')=='turn.completed' for e in events)==1
  metered=bool(native.get('started')) and native.get('started')==native.get('completed') and not native.get('blocked_requests')
  rec.update(exit_code=proc.returncode,seconds=time.time()-rec['started_at'],native=native,usage=usage,usage_incomplete=not metered or any(not e.get('token_usage') for e in posts),model_match=model_match,format_ok=format_ok,malformed_events=malformed,tools=sum(e.get('type')=='item.completed' and e.get('item',{}).get('type')=='command_execution' for e in events),source_body_proofs=read_proof(events,c),delivered_files=hashes(folder/'workspace'))
  rec['status']='VALID' if complete and metered and format_ok and model_match and not malformed else 'INVALID'
  if rec['status']=='VALID':rec['failure_class']=None
  elif not native.get('started') or not model_match:rec['failure_class']='accounting_or_model_configuration'
  elif native.get('blocked_requests') and native.get('started')==12:rec['failure_class']='execution_request_limit'
  elif not complete or malformed:rec['failure_class']='infrastructure'
  elif not metered:rec['failure_class']='accounting_or_model_configuration'
  else:rec['failure_class']='model_delivery'
  if phase=='extract':
   assert hashes(folder/'workspace')==c['candidate_files']
   full=answer.get('report','');(folder/'contract-full.md').write_text(full)
   h1='1. 可确认的 Contract\n';h2='2. 每条的条件、效果、来源及依据\n'
   if rec['status']=='VALID' and rec['source_body_proofs'] and full.count(h1)==full.count(h2)==1:
    contract=full.split(h1,1)[1].split(h2,1)[0];assert contract.strip()
    (folder/'contract.md').write_text(contract);rec['contract_sha256']=backend.sha(contract)
   else:rec['status']='INVALID';rec['failure_class']=rec['failure_class'] or 'model_extraction_format_or_source_read'
  else:
   diff=subprocess.run(['diff','-ruN',str(O/'materials'/c['case']/'candidate'),str(folder/'workspace')],capture_output=True,text=True);(folder/'patch.diff').write_text(diff.stdout)
   # Scores are archived even for invalid partial delivery, but never used as valid model outcomes.
   score=subprocess.run([c['node'],str(Path(c['source_case'])/'oracle/probe.cjs'),str(folder/'workspace'),'ungranted'],capture_output=True,text=True,timeout=90)
   (folder/'score.stdout.json').write_text(score.stdout);(folder/'score.stderr.txt').write_text(score.stderr)
   try:rec['verdict']=json.loads(score.stdout)['verdict'];rec['scoring_anomaly']=score.returncode not in [0,1]
   except (ValueError,KeyError):rec['scoring_anomaly']=True
  save(folder/'receipt.json',rec);return rec
 except Exception as exc:
  # Preserve partial files and any already-accounted usage, never replace this slot.
  rec.update(status='INVALID',failure_class='infrastructure',exception_type=type(exc).__name__,exception=str(exc),seconds=time.time()-rec['started_at'])
  if (folder/'meter/ledger.json').exists():
   meter=read(folder/'meter/ledger.json');rec['native']=meter.get('sessions',{}).get(call,{})
   posts=[e['event'] for e in meter.get('events',[]) if e['event'].get('hook_event_name')=='PostModelRequest']
   rec['usage']={k:sum(e.get('token_usage',{}).get(k,0) or 0 for e in posts) for k in ['input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens']}
  rec['usage_incomplete']=True
  save(folder/'receipt.json',rec);return rec
 finally:
  profile=O/'.runtime'/call
  if (profile/'config.toml').exists():save(folder/'configuration-after.json',{'profile_sha256':sha(profile/'config.toml'),'global_config':backend.global_snapshot()})
  shutil.rmtree(profile,ignore_errors=True)

def run():
 verify()
 approval=read(O/'experience-approval.json')
 assert approval.get('status')=='confirmed' and approval.get('experience_sha256')==sha(O/'EXPERIENCE.md') and approval.get('user_statement'), 'Explicit expert confirmation of this exact E1 text is required.'
 assert not (O/'actual-schedule.json').exists(), 'No automatic restart/resume/retry.'
 records=[];save(O/'actual-schedule.json',records)
 infra_streak=0
 for index,c in enumerate(cases(),1):
  slot={'slot':'x%02d'%index,'case':c['case'],'condition':'extraction','repeat':None}
  rec=session(slot,(O/'prompts'/c['case']/'extraction.md').read_text(),'extract');records.append(rec);save(O/'actual-schedule.json',records)
  print(slot['slot'],rec['status'],flush=True)
  infra_streak=infra_streak+1 if rec['failure_class'] in ['infrastructure','accounting_or_model_configuration'] else 0
  if infra_streak>=2 or rec['failure_class']=='accounting_or_model_configuration':return
 if any(r['status']!='VALID' for r in records):return
 # Freeze all automatic Contracts and repair prompts before the first maintenance score.
 contract_files={}
 for index,c in enumerate(cases(),1):
  cid=c['case'];m=(O/'runs'/('x%02d'%index)/'contract.md').read_text();p=O/'prompts'/cid
  (O/'materials'/cid/'M.frozen.md').write_text(m)
  for g in ['M','E']:
   (p/(g+'.md')).write_text((p/(g+'.template.md')).read_text().replace('{{FROZEN_AUTOMATIC_CONTRACT}}',m))
  for f in [O/'materials'/cid/'M.frozen.md',p/'M.md',p/'E.md']:contract_files[str(f)]=sha(f)
 save(O/'automatic-contract-freeze.json',{'before_any_maintenance':True,'files':contract_files,'reuse':0,'generations':10,'manual_edits':False})
 for index,slot in enumerate(read(O/'schedule.json')['order']):
  for p,h in contract_files.items():assert sha(p)==h,p
  rec=session(slot,(O/'prompts'/slot['case']/(slot['condition']+'.md')).read_text(),'repair');records.append(rec);save(O/'actual-schedule.json',records)
  print(slot['slot'],slot['condition'],rec['status'],rec.get('verdict'),flush=True)
  if index==0:
   passed=rec['status']=='VALID' and bool(rec['source_body_proofs'])
   save(O/'first-formal-gate.json',{'status':'PASS' if passed else 'FAIL','slot':slot['slot'],'source_body_proofs':rec['source_body_proofs'],'scored_slot_in_budget':True})
   if not passed:return
  infra_streak=infra_streak+1 if rec['failure_class'] in ['infrastructure','accounting_or_model_configuration'] else 0
  if infra_streak>=2 or rec['failure_class']=='accounting_or_model_configuration' or rec.get('scoring_anomaly'):return

if __name__=='__main__':
 {'prepare-prompts':make_prompts,'offline':offline,'freeze':freeze,'run':run}[sys.argv[1]]()
