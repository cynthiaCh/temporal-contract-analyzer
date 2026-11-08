"""New case protocol preparation; offline only, no historical dispatcher."""
from pathlib import Path
import json,hashlib,shutil,subprocess,time,random
A=Path(__file__).resolve().parent;R=A.parents[1];OLD=R/'research/cached-detail-same-case-low-20261108_133600';B=R.parent/'temporal-contract-bench-git';CID='query-paused-initial-fetch-10266-vanilla'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d):(A/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def hashes(root):return {str(p.relative_to(root)):sha(p) for p in root.rglob('*') if p.is_file()}
assert not (A/'cohort.json').exists()
save('initial-state.json',{'HEAD':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'status':subprocess.check_output(['git','status','--short'],text=True),'diff':subprocess.check_output(['git','diff','--binary'],text=True),'instructions':'No applicable ancestor/project/research AGENTS.md. Initial inspection before new directory was clean; HEAD changed externally since previous batch, preserved.'})
tracked=[R/p for p in subprocess.check_output(['git','ls-files','-z']).decode().split('\0') if p]
protect={str(p):sha(p) for p in tracked if p.is_file()};protect[str(Path.home()/'.codex/config.toml')]=sha(Path.home()/'.codex/config.toml')
copy=['runner.py','archive.py','native_backend.py','guard_server.py','guard_client.py','request_guard.py','read_policy.py','prompts.py','research-config.toml','models-cache.snapshot.json','extraction.schema.json','reflection.schema.json','test_offline.py']
for n in copy:shutil.copyfile(OLD/n,A/n)
save('reuse-provenance.json',{'source':str(OLD),'files':{n:sha(OLD/n) for n in copy},'adaptation':'No role or archive changes: repair Terra low, reflection Terra medium, extraction Sol low. Only current-case controller/scoring checks format and node path adapted. No historical dispatcher imported.'})
cluster=B/'case-clusters/query-paused-initial-fetch-10266';reg=json.loads((cluster/'cluster.json').read_text());arm=next(x for x in reg['arms'] if x['id']==CID);src=cluster/arm['path'];m=json.loads((src/'case.json').read_text());assert m['id']==CID
shutil.copyfile(cluster/'cluster.json',A/'cluster-registry.json');d=A/'materials';shutil.copytree(src/'base',d/'candidate');shutil.copyfile(src/m['diagnostic_tasks']['maintenance']['core_prompt'],d/'task.md');shutil.copyfile(src/'case.json',d/'manifest.json');shutil.copytree(src/'oracle',d/'evaluation');assert not list((d/'candidate').rglob('AGENTS.md')) and not any(p.is_symlink() for p in (d/'candidate').rglob('*'))
# Exact native runtime resolved from the oracle's documented launch/re-exec path.
node=B/'results/student-case-expansion-runtime/compat-node16/node_modules/node-linux-x64/bin/node';assert node.is_file();assert subprocess.check_output([str(node),'--version'],text=True).strip()=='v16.20.2'
c={'case':CID,'source_case':str(src),'node':str(node),'candidate_files':hashes(d/'candidate'),'task_sha256':sha(d/'task.md'),'manifest_sha256':sha(src/'case.json'),'oracle_files':hashes(src/'oracle'),'calibration':[]}
for label,overlay in [('unchanged',None),('reference-bounded',src/m['references']['bounded']),('reference-expanded',src/m['references']['expanded'])]+[(x.replace('/','-'),src/x) for x in m['mutants']]:
 dest=A/'calibration'/label;shutil.copytree(src/'base',dest/'candidate')
 if overlay:shutil.copytree(overlay,dest/'candidate',dirs_exist_ok=True)
 cmd=[str(node),str(src/'oracle/probe.cjs'),str(dest/'candidate'),'ungranted'];t=time.monotonic();z=subprocess.run(cmd,capture_output=True,text=True,timeout=90);(dest/'stdout.json').write_text(z.stdout);(dest/'stderr.txt').write_text(z.stderr);s=json.loads(z.stdout)
 assert z.returncode in [0,1] and s['case_id']==CID and not any(x.get('runtimeError') for x in s['schedules'].values()),(label,z.stderr)
 rec={'label':label,'command':cmd,'seconds':time.monotonic()-t,'exit_code':z.returncode,'verdict':s['verdict'],'effects':s['observed_effects'],'raw':str(dest/'stdout.json')};(dest/'receipt.json').write_text(json.dumps(rec,indent=2)+'\n');c['calibration'].append(rec)
 print(label,s['verdict'],s['missing_required_effects'],flush=True)
# Bounded must pass; all listed mutants must discriminate. Expanded is recorded as
# actual control result, not assumed to be overreach when this case has no grant.
assert next(x for x in c['calibration'] if x['label']=='reference-bounded')['verdict']=='PASS'
assert all(x['verdict']!='PASS' for x in c['calibration'] if x['label']=='unchanged' or x['label'].startswith('mutants-'))
save('cohort.json',c);protect.update({str(p):sha(p) for p in src.rglob('*') if p.is_file()});save('protected-files.json',protect)
# Historical input correspondence, NOT a matched new AUTO baseline.
h=B/'results/terra-low-lgc-20261018-r1';plan=json.loads((h/'block-20/plan.json').read_text());prefix=str(src.relative_to(B))+'/';entries={k:v for k,v in plan['input_sha256'].items() if k.startswith(prefix+'base/') or k.startswith(prefix+'oracle/') or k in [prefix+'case.json',prefix+'prompts/maintenance-core.md']};assert all(sha(B/k)==v for k,v in entries.items())
save('historical-context.json',{'batch':str(h),'case':CID,'model':'gpt-5.6-terra','effort':'low','current_frozen_inputs_match_history':entries,'checks_count':len(entries),'L':{'run':str(h/'block-20/jobs/j0004/agent/run.json'),'pass_effects':25,'effects':29},'G':{'run':str(h/'block-20/jobs/j0005/agent/run.json'),'pass_effects':26,'effects':29},'C':{'run':str(h/'block-20/jobs/j0006/agent/run.json'),'pass_effects':28,'effects':29,'missing':['offline-nonconsuming-detach']},'different_prompt_conditions_not_three_repetitions':True,'not_given_to_actors':True,'not_reused_as_this_batch_baseline':True})
shutil.copyfile(R/'research/contract-extraction-evolution-u2-v2-20261107/contract_extraction_K1.md',A/'contract_extraction_K1.md')
old=(OLD/'prompts/extraction.md').read_text();task=(d/'task.md').read_text();p=A/'prompts';p.mkdir();(p/'extraction.md').write_text(task+'\n\n'+old[old.index('只读取 /workspace'):])
from prompts import POLICY
common=task+'\n\n以下为辅助材料。依据原任务和项目证据核查其适用性；存在冲突或证据不足时不要盲目执行。\n{{FROZEN_AUTOMATIC_CONTRACT}}\n\n完成原维护任务，实际修改候选代码并做相关验证。仅在 /workspace 内工作，不查看研究材料、历史、评分器、其他槽位或网络。Node自检使用 /runtime/node，并记录 --version；不安装依赖。最终返回JSON，唯一字段report，最多6000个Unicode字符，报告实际交付、验证与未覆盖范围。\n\n'+POLICY+'\n';(p/'AUTO.template.md').write_text(common)
slots=[{'slot':'extract','phase':'extract','condition':'CONTRACT','repeat':None}]+[{'slot':f'base-{i}','phase':'repair','condition':'AUTO','repeat':i} for i in [1,2]]+[{'slot':'reflection','phase':'reflect','condition':'REFLECTION','repeat':None}]+[{'slot':f'reval-{i}','phase':'repair','condition':'AUTO_EXP','repeat':i} for i in [1,2]];rng=random.Random(20261108)
for i in [1,2,3]:
 arms=['AUTO','AUTO_EXP'];rng.shuffle(arms)
 for g in arms:slots.append({'slot':f'final-{i}-{g}','phase':'repair','condition':g,'repeat':i})
for s in slots:s['case']=CID
save('schedule.json',{'slots':slots,'seed':20261108,'seed_scope':'schedule only; no model sampling seed','concurrency':1,'conditional':True})
print('Zero-model preparation complete',flush=True)
