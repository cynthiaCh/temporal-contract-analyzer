from pathlib import Path
import hashlib
O=Path(__file__).resolve().parent;B=O.parent.parent.parent/'temporal-contract-bench-git';CASE=B/'case-clusters/download-polling-restoration/arms/download-polling-restoration-low-cue-react18';HIST=B/'results/core-24-completion-20261005/recovered-06-node18'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):(O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def hashes(p):return {str(x.relative_to(p)):sha(x) for x in p.rglob('*') if x.is_file()}
import json,subprocess,shutil
node=json.loads((O/'runtime.json').read_text())['node'];rows=[]
for label,src in [('unchanged',O/'materials/candidate'),('historical-N',HIST/'jobs/j0001/agent/candidate'),('historical-H',HIST/'jobs/j0002/agent/candidate')]:
 d=O/'calibration'/label;d.mkdir(parents=True);p=subprocess.run([node,str(CASE/'oracle/probe.cjs'),str(src),'ungranted'],capture_output=True,text=True,timeout=110);(d/'stdout.json').write_text(p.stdout);(d/'stderr.txt').write_text(p.stderr)
 raw=json.loads(p.stdout);row={'label':label,'exit_code':p.returncode,'verdict':raw['verdict'],'effects':raw['observed_effects'],'raw':str(d/'stdout.json')}
 if label.startswith('historical'):
  j='j0001' if label.endswith('N') else 'j0002';old=json.loads((HIST/'jobs'/j/'agent/score.json').read_text());row['exact_historical_effects_match']=old['observed_effects']==raw['observed_effects'];assert row['exact_historical_effects_match']
 rows.append(row)
assert rows[0]['verdict']!='PASS' and rows[1]['verdict']=='UNDERREACH' and rows[2]['verdict']=='PASS'
save('admission.json',{'status':'PASS','calibration':rows,'model_calls':0,'case_manifest':str(CASE/'case.json'),'manifest_sha256':sha(CASE/'case.json'),'oracle_files':hashes(CASE/'oracle'),'oracle_hash_provenance':'matches historical plan input_sha256; no independent per-run byte attestation','variant':'ungranted','scoring_explicit_scope':['historical foreground pending waiting loading and retryScheduled','pending polling until ready and completed token exactly once','close clears loading and in-flight responses inert','reopen different token old ready inert','background continues after panel close'],'not_covered':['close after retry already queued','same-token reopen','multiple concurrent in-flight responses','authorization ownership migration','full real file delivery beyond completed array','unknown status protocol outside historical boolean fixture'],'policy_limit':'Existing authored benchmark specs retained for historical diagnostic, not new product-policy approval; H explicitly supplied extra rules unavailable to M/N; no expected guessing of missing input.','scorer_isolation':'host-only after session exit, no oracle/reference/history mounts'})
print(json.dumps(rows,ensure_ascii=False,indent=2))
