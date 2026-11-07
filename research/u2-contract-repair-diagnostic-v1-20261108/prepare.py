from pathlib import Path
import json,hashlib,shutil,subprocess,os,sys,importlib.util,csv
O=Path(__file__).resolve().parent;R=O.parent.parent;B=R.parent/'temporal-contract-bench-git';X=R/'research/contract-extraction-evolution-u2-v2-20261107';mapping=R/'research/contract-standard-mapping-v1-20261107';HIST=B/'results/core-24-completion-20261005/recovered-06-node18';CASE=B/'case-clusters/download-polling-restoration/arms/download-polling-restoration-low-cue-react18'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):p=O/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def hashes(p):return {str(x.relative_to(p)):sha(x) for x in sorted(p.rglob('*')) if x.is_file()}
def git(p,*args):return subprocess.check_output(['git','-C',str(p),*args],text=True)
# Native historical tree hashing definition, read from current file; no model calls.
sys.path.insert(0,str(B));import agentbench
initial={n:{'head':git(p,'rev-parse','HEAD').strip(),'status':git(p,'status','--porcelain=v1'),'diff':git(p,'diff'),'staged_diff':git(p,'diff','--cached')} for n,p in [('analyzer',R),('bench',B)]};initial['global_config_sha256']=sha(Path.home()/'.codex/config.toml');initial['AGENTS']='No AGENTS.md at repo root/ancestors or selected source directories.';save('initial-state.json',initial)
plan=json.loads((HIST/'plan.json').read_text());source=json.loads((mapping/'SOURCES.json').read_text());pair=source['repair_pair'];save('historical-pair.mapping.json',pair)
for rel,h in plan['input_sha256'].items():
 if rel.startswith(str(CASE.relative_to(B))) and ('/base/' in rel or '/oracle/' in rel or rel.endswith('/case.json')):assert sha(B/rel)==h,rel
shutil.copytree(CASE/'base',O/'materials/candidate');shutil.copyfile(X/'materials/task.md',O/'materials/task.md')
assert hashes(O/'materials/candidate')==json.loads((X/'scope-and-sources.json').read_text())['candidate_files']
rows=[]
for j in ['j0001','j0002']:
 d=HIST/'jobs'/j/'agent';run=json.loads((d/'run.json').read_text());score=json.loads((d/'score.json').read_text())
 assert agentbench.tree_sha256(CASE/'base')==run['workspace_input_tree_sha256']==run['base_tree_sha256']
 assert agentbench.tree_sha256(d/'candidate')==run['candidate_tree_sha256'];assert sha(d/'prompt.md')==run['prompt_sha256'];assert sha(CASE/'case.json')==run['case_manifest_sha256']
 target=O/'history'/j;target.mkdir(parents=True)
 for name in ['run.json','prompt.md','score.json','final-message.md']:shutil.copyfile(d/name,target/name)
 diff=subprocess.run(['diff','-ruN',str(CASE/'base'),str(d/'candidate')],capture_output=True,text=True);(target/'derived-patch.diff').write_text(diff.stdout)
 rows.append({'job':j,'actual_prompt':str(d/'prompt.md'),'run':run,'score_verdict':score['verdict'],'effects':score['observed_effects'],'candidate_files':hashes(d/'candidate'),'patch_provenance':'offline diff from hash-verified archived candidate; not historical standalone patch','events_sha256':sha(d/'events.jsonl')})
N=(HIST/'jobs/j0001/agent/prompt.md').read_text();HH=(HIST/'jobs/j0002/agent/prompt.md').read_text();contract=pair['contract_verbatim'];assert contract in HH
assert '\n'.join(x for x in HH.replace(contract,'').splitlines() if x.strip())=='\n'.join(x for x in N.splitlines() if x.strip())
common_compare={k:[row['run'].get(k) for row in rows] for k in ['base_tree_sha256','workspace_input_tree_sha256','case_manifest_sha256','model','reasoning_effort','timeout_seconds','variant','codex_cli_version','isolation','checkpoint_capture']};assert all(v[0]==v[1] for v in common_compare.values())
save('historical-pair-verification.json',{'jobs':rows,'same_fields':common_compare,'only_nonblank_prompt_delta':'exact historical Contract suffix','overlays':[job['workspace_overlay'] for job in plan['jobs']],'limitations':['One run per arm, ordered N then H, no randomization.','N patch accepts string pending/ready; worker uses false/true; H patch accepts true/ready/object forms.','Historical service_tier, low-level request cap and final-output hard limit not present in plan/run; not retrospectively invented.','No independent per-run oracle digest receipt. Plan input_sha256 lists oracle; all current oracle files match that pre-run plan.']})
(O/'contracts').mkdir();(O/'contracts/H.txt').write_text(contract)
ks=[]
for slot in json.loads((X/'schedule.json').read_text())['order']:
 if slot['phase']=='K1':
  rec=json.loads((X/'runs'/slot['call_id']/'receipt.json').read_text());valid=json.loads((X/'runs'/slot['call_id']/'validity.json').read_text())
  if rec['status']=='completed' and valid['status']=='PASS':ks.append(rec)
selected=min(ks,key=lambda x:x['started_at']);assert selected['call_id']=='k1-1';d=X/'runs'/selected['call_id'];raw=(d/'raw-answer.txt').read_bytes();assert hashlib.sha256(raw).hexdigest()==selected['raw_sha256'];report=(d/'contract.md').read_text();assert json.loads(raw)['report']==report
start='1. 可确认的 Contract\n';end='2. 每条的条件、效果、来源及依据\n';assert report.count(start)==report.count(end)==1;M=report.split(start,1)[1].split(end,1)[0];assert M.strip();(O/'contracts/M.txt').write_text(M)
save('M-selection.json',{'rule':'earliest actual valid K1; exact section 1 body after heading newline until exact section 2 heading; preserve all whitespace; no other section, fill or correction','slot':selected['call_id'],'started_at_unix':selected['started_at'],'source':str(d/'contract.md'),'report_sha256':sha(d/'contract.md'),'raw_sha256':selected['raw_sha256'],'M_sha256':sha(O/'contracts/M.txt'),'validity':str(d/'validity.json'),'extraction_skill':str(X/'contract_extraction_K1.md'),'skill_sha256':sha(X/'contract_extraction_K1.md'),'skill_provided_to_repair':False})
# Preserve exact historical task/runtime text, adding the same maintenance/output clause to all arms.
marker='Work only from the provided candidate workspace;';i=N.index(marker);before=N[:i].rstrip();after=N[i:]
common='\n\n完成原维护任务，实际修改候选代码并做相关验证。仅在 /workspace 内工作。依赖可从 NODE_PATH 指向的只读运行时使用。最终返回 JSON，唯一字段 report，最多6000个Unicode字符，说明实际修改和验证；补丁由工作区差异归档。\n'
for g,extra in [('N',''),('H',contract),('M',M)]:
 text=before+('\n\n'+extra if extra else '')+'\n\n'+after+common;p=O/'prompts'/(g+'.md');p.parent.mkdir(exist_ok=True);p.write_text(text)
save('prompt-differences.json',{'history_N_sha256':hashlib.sha256(N.encode()).hexdigest(),'history_H_sha256':hashlib.sha256(HH.encode()).hexdigest(),'common_before':before,'common_after':after+common,'only_group_difference':'extra Contract body; no group-specific reminders, role or checklist','historical_difference':'common /workspace, dependency-path and JSON report instruction appended equally; actual historical runtime path retained'})
with (mapping/'MAPPING.csv').open(encoding='utf-8-sig',newline='') as f:maprows=list(csv.DictReader(f))
save('H-source-applicability.json',{'H_exact_historical_text':contract,'H_sha256':sha(O/'contracts/H.txt'),'clauses':[ {k:row[k] for k in ['obligation_id','contract_original_quote','human_extra_requirement','project_evidence_sufficiency','evaluation_coverage','unknowns']} for row in maprows],'interpretation':'O1/O3 directly recoverable task obligations; O2 exact loading field, O4-O6 foreground timer/all-response/generation and O7 workspace ownership/authorization are historical explicit extra specifications to varying degrees; concrete policy disputes preserved. No expectation extraction must guess unavailable policy.','scoring_scope':'Reuse exact historical ungranted benchmark including extra authored specs, not a newly approved product standard; N/M assessed against same existing rubric with input-policy asymmetry disclosed.','not_independent_human_review':True})
node=Path(plan['config']['node_binary']);assert sha(node)==plan['runtimes'][CASE.name]['node']['sha256'];save('runtime.json',{'node':str(node),'sha256':sha(node),'version':subprocess.check_output([str(node),'--version'],text=True).strip(),'react_dependencies':str(B/'runtimes/react18/node_modules')})
shutil.copyfile(Path.home()/'.codex/models_cache.json',O/'models-cache.snapshot.json');model=json.loads((O/'models-cache.snapshot.json').read_text());assert any(m.get('slug')=='gpt-5.6-terra' for m in model['models'])
(O/'research-config.toml').write_text('model = "gpt-5.6-terra"\nmodel_reasoning_effort = "medium"\nservice_tier = "priority"\n')
save('configuration-differences.json',{'matched':['gpt-5.6-terra','medium','600 seconds','exact original candidate/task','Node v18.17.0 binary/hash','historical H text','ungranted oracle bytes match original plan'],'different':{'CLI':{'history':'0.159.2 old binary missing','now':subprocess.check_output(['/home/sribd/.vscode/extensions/openai.chatgpt-26.51021.22027-linux-x64/bin/linux-x86_64/codex','--version'],text=True).strip()},'service_tier':{'history':'not archived, unknown','now':'priority explicitly configured; route unattested'},'limits':{'history':'600 sec; no explicit low-level request/final-report cap found','now':'600 sec, 12 native requests/slot, 49 globally, report 6000 chars, carried from verified research configuration'},'isolation':{'history':'temporary auth-only CODEX_HOME + workspace-write; no filesystem namespace receipt','now':'bwrap candidate writable, research/scorer/history/other runs unmounted; isolated auth/config; native autonomous danger-full-access within namespace'},'tools':'code_mode_host and shell_tool explicitly available; apps/plugins/multi-agent/web disabled; no extraction skill added','public_instruction':'same extra output/dependency instruction for all arms; exact historical self-check node path retained','runtime_dependencies':'read-only React runtime via NODE_PATH; candidate files unchanged'},'strict_historical_reproduction':False,'within_round_contract_only':True})
roots=[mapping,X,R/'research/candidate-contract-repair-exec-v1-20261108',HIST,CASE]
protected={str(p):sha(p) for root in roots for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and '.runtime' not in p.parts};save('protected-files.json',protected)
print('prepared',len(protected),'protected files; M=',repr(M))
