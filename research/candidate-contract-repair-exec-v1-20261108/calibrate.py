from pathlib import Path
import json,subprocess,hashlib,shutil
R=Path.cwd(); O=R/'research/candidate-contract-repair-exec-v1-20261108'; B=R.parent/'temporal-contract-bench-git'; old=json.loads((O/'source-score-bindings.previous.json').read_text()); node=R/'results/ad-model-effort-20261104/runtime/node-v16.20.2-linux-x64/bin/node'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
results={}
for c in ['C1','C3']:
 case=Path(old['cases'][c]['case_manifest']).parent
 assert sha(case/'case.json')==old['cases'][c]['case_manifest_sha256']
 for name,h in old['cases'][c]['oracle_files'].items():assert sha(case/'oracle'/name)==h
 if c=='C1':
  results[c]={'eligible':False,'reason':'现有 ungranted 评分把未决迟到解码显示政策设为必答；历史 PASS 校准不能修复政策适用冲突。未改评分器或删断言。','blocking_required_effects':['decode-after-switch','decode-after-close','same-channel-reopen'],'evidence':[str(case/'oracle/effects.json'),str(case/'oracle/probe.cjs')],'missing_acceptable_scoring_path':'未找到与当前冻结版本匹配、覆盖已明确要求且不把迟到解码政策作为必答的既有评分入口。','previous_calibration':old['cases'][c]['calibration']}
  continue
 rows=[]
 for label,src in [('unchanged',O/'materials/C3/candidate'),('reference-bounded',case/'reference/bounded'),('mutant-ui-correct-observation-wrong',case/'mutants/ui-correct-observation-wrong'),('mutant-observation-correct-ui-wrong',case/'mutants/observation-correct-ui-wrong')]:
  d=O/'calibration/C3'/label;d.mkdir(parents=True,exist_ok=True)
  if label!='unchanged':
   target=d/'candidate';shutil.copytree(O/'materials/C3/candidate',target);shutil.copytree(src,target,dirs_exist_ok=True);src=target
  p=subprocess.run([str(node),str(case/'oracle/probe.cjs'),str(src),'ungranted'],capture_output=True,text=True,timeout=60)
  (d/'stdout.json').write_text(p.stdout);(d/'stderr.txt').write_text(p.stderr)
  raw=json.loads(p.stdout);rows.append({'label':label,'exit_code':p.returncode,'verdict':raw['verdict'],'effects':raw['observed_effects'],'raw':str(d/'stdout.json')})
 save(O/'calibration/C3/summary.json',rows)
 results[c]={'eligible':rows[0]['verdict']!='PASS' and rows[1]['verdict']=='PASS' and all(r['verdict']!='PASS' for r in rows[2:]),'calibration':rows,'runtime':str(node),'runtime_sha256':sha(node),'variant':'ungranted','coverage':'worker checks entry snapshot, post-success single audit/revision, failure no audit, accepted close/reopen, latest UI, Promise pending/settlement and preview hide/reuse/40ms preservation.','unknown_policy_review':'No assertion on rejected submit value/error propagation, no-visit return, host exceptions or nested mutable identity. Rejection of first submitted Promise handled in either direction by worker.','limitation':'Latest-error retirement and all public method semantics are not exhaustively tested; existing authored scenarios are bounded. No new scoring assertions introduced.','historical_pair_required':False}
 save(O/'scoring/C3/oracle-file-hashes.json',old['cases'][c]['oracle_files'])
save(O/'admission.json',results);print(json.dumps(results,ensure_ascii=False,indent=2))
