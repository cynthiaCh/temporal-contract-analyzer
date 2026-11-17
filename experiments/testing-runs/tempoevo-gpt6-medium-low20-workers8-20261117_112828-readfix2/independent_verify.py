import json,hashlib,sys
from pathlib import Path
repo=Path('/home/sribd/Downloads/wangshu/temporal-contract-analyzer');sys.path.insert(0,str(repo))
from temporal_contract_analyzer.tempoevo_v4 import Trajectory
from temporal_contract_analyzer._session_runtime.read_policy import allowed
from temporal_contract_analyzer import experience_approval as approval
from temporal_contract_analyzer.candidate_files import capture,inventory
r=Path(__file__).resolve().parent;parent=Path(str(r)[:-9]);cid='workspace-draft-projection-latent-vanilla-port-vue3';o=parent/'batch'/cid/'trajectory';n=r/'batch'/cid/'trajectory'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text());p=read(o/'protocol.json');q=Trajectory(n).verify();s=read(o/'state.json');z=read(n/'state.json');b=read(o/'binding.json');nb=read(n/'binding.json')
diff={k for k in p.keys()|q.keys() if p.get(k)!=q.get(k)};assert diff=={'candidate','store'},diff
assert nb['evaluators']==b['evaluators'] and all(sha(k)==v for k,v in nb['evaluators'].items()) and p['backend']==q['backend']
assert inventory(capture(o/'original')[0])==inventory(capture(n/'original')[0])==q['original_inventory'] and q['source_sha256']==p['source_sha256']
assert q['mode']=='testing' and q['learning_policy']=='frozen' and q['split_status']=='final_only_gold_testing'
assert q['model']=={'model':'gpt-6-sol','reasoning_effort':'medium'} and q['max_attempts']==1 and q['total_request_cap']==48 and q['evaluation_budget']=={'gold':1,'oracle':0,'visible':0}
assert not s['attempts'] and not z['attempts'] and s.get('gold_result') is None and z.get('gold_result') is None and all(x['kind'] not in ['action','gold'] for x in s['stages']+z['stages'])
assert z['stages'][0]==s['stages'][0] and z['stages'][0]['requests']==1
for fname in ['result.json','input.json','prompt-context.json']:
 if (o/'stages/selection-1'/fname).exists():assert sha(o/'stages/selection-1'/fname)==sha(n/'stages/selection-1'/fname)
for key in ['delivery.json','online-snapshot.json','routing-analysis.json']:
 if (o/key).exists():assert sha(o/key)==sha(n/key)
c=dict(s['stages'][1]);c['key']='historical-contract-error';assert z['stages'][1]==c and c['requests']==2 and Trajectory(n)._remaining_limit(q,'contract','contract')['requests']==10 and q['limits']['action']['requests']==24
bank=approval.validate_snapshot(r/'experience-library',read(r/'memory-snapshot.json'));assert len(bank['entries'])==73 and q['memory_snapshot']==p['memory_snapshot'] and sha(r/'memory-snapshot.json')==sha(parent/'memory-snapshot.json')
positive=["if [ -f 'docs/host-api.md' ]; then cat 'docs/host-api.md'; fi",'if [ -e README.md ]; then head -n 5 README.md; fi','if [ -d src ]; then ls src; fi']
negative=['if [ -f README.md ]; then '+x+'; fi' for x in ['touch README.md','cat README.md > out','echo bad >> README.md','sed -i s/x/y/ README.md','cat /etc/passwd','cat ../README.md','cat README.md; else cat README.md','cat README.md; elif true; then cat README.md','cat "$(pwd)/README.md"','cat `pwd`/README.md','python -c pass','bash -c true','rm README.md','git checkout README.md','rg --pre sh README.md','cat <(pwd)','echo x | tee out','printf -v value hi','cat README.md &']]
negative+=['if [ -f '+x+' ]; then cat README.md; fi' for x in ['/etc/passwd','../README.md','"$(pwd)/README.md"','"$FILE"','README.md -o -e /etc/passwd']]
negative+=['if [ -f README.md ]; then cat README.md & fi','if [ -f README.md ]; then cat README.md &> out; fi']
tests=[dict(command=c,expected=True,actual=allowed(c)) for c in positive]+[dict(command=c,expected=False,actual=allowed(c)) for c in negative];assert all(x['expected']==x['actual'] for x in tests),[x for x in tests if x['expected']!=x['actual']]
before=read(r/'original-case-before-hashes.json');assert all(sha(parent/k)==v for k,v in before.items())
initial=read(Path(str(parent)+'-readfix1')/'parent-before-hashes.json');assert all(initial[k]==v for k,v in before.items())
cal=read(parent/'calibration.json');assert cal['valid'] and cal['controls']==60
assert all(c['valid'] and c['passed']==(c['control']=='reference') for row in cal['results'] for c in row['controls'])
assert sha(parent/'calibration.json')==initial['calibration.json'] and sha(parent/'agent-follows-doc.json')==initial['agent-follows-doc.json']
spec=read(r/'env-spec.json');assert sha(r/'prepare_recovery.py')==spec['prepare_script_sha256'] and all(sha(repo/k)==v for k,v in spec['files'].items())
report=dict(valid=True,ready=True,prepare_exit_code=0,documented_command='/usr/bin/python3 -B '+str(r/'prepare_recovery.py'),cwd=str(repo),model_calls=0,new_gold_calls=0,production_edits=False,bindings=1,original_root_unchanged=True,original_case_files_verified=len(before),previous_full_parent_files_verified=len(initial),previous_full_parent_snapshot=str(Path(str(parent)+'-readfix1')/'parent-before-hashes.json'),protocol_only_path_differences=sorted(diff),source_inventory_files=len(q['original_inventory']),original_source_evaluator_image_identity_preserved=True,controls_reused=60,parent_controls_report=str(parent/'agent-follows-doc.json'),selection_result_reused=True,selection_requests_retained=1,contract_requests_spent=2,remaining_contract_requests=10,original_actions=0,new_actions_allowed=1,action_request_cap=24,original_gold_calls=0,new_final_gold_allowed=1,no_gold_feedback=True,approved_entries=73,model=q['model'],grammar_tests=tests,divergences=[],notes=['Original failed case and 19 other scores retained.','Original source/evaluator/image identities unchanged; original/reference/negative controls reused without execution.','Historical usage, including unknown usage request, retained unchanged.','First unused readfix1 root and failed report retained.'])
(r/'agent-follows-doc.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='grammar_tests'},indent=2))
