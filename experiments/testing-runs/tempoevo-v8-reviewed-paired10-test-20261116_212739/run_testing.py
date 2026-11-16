"""Run both approved, frozen test arms once; never learn from final scores."""
import datetime,json,subprocess,sys,time,shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
ROOT=Path(__file__).resolve().parent
REPO=Path('/home/sribd/Downloads/wangshu/temporal-contract-analyzer')
ARMS=['A-seed16','B-seed16-plus2']
started=time.time()
def summarize(arm,exit_code,elapsed):
 rows=[]
 for item in json.loads((ROOT/arm/'progress.json').read_text()):
  trajectory=Path(item['root'])/'trajectory';state=json.loads((trajectory/'state.json').read_text());path=trajectory/'summary.json';report=json.loads(path.read_text()) if path.exists() else {}
  gold=state.get('gold_result') or {}
  rows.append(dict(case_id=item['case_id'],rank=item['rank'],status=state['status'],actions=len(state['attempts']),gold_passed=gold.get('passed') if state['status']=='scored' else None,gold_verdict=gold.get('verdict'),requests=report.get('requests'),known_tokens=report.get('known_tokens'),usage_incomplete=report.get('usage_incomplete'),error=state.get('error'),transport_retries=report.get('transport_retries',0),tool_policy_recoveries=report.get('tool_policy_recoveries',0)))
 result=dict(arm=arm,expected_cases=10,passed=sum(x['gold_passed'] is True for x in rows),failed=sum(x['gold_passed'] is False for x in rows),execution_invalid=sum(x['status']=='execution_invalid' for x in rows),unscored=sum(x['gold_passed'] is None for x in rows),requests=sum(x['requests'] or 0 for x in rows),known_tokens=sum(x['known_tokens'] or 0 for x in rows),elapsed_seconds=elapsed,queue_exit_code=exit_code,cases=rows)
 (ROOT/(arm+'-results.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');return result

def execute(arm):
 start=time.time()
 with (ROOT/(arm+'.log')).open('w') as log:process=subprocess.run([sys.executable,'-B','tools/tempoevo-docker/run_selected.py','--root',str(ROOT/arm),'--execute'],cwd=REPO,stdout=log,stderr=subprocess.STDOUT)
 result=summarize(arm,process.returncode,time.time()-start)
 print(json.dumps({k:v for k,v in result.items() if k!='cases'}),flush=True);return result
with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(execute,ARMS))
a,b=results;paired=[dict(case_id=x['case_id'],A=x['gold_passed'],B=y['gold_passed']) for x,y in zip(a['cases'],b['cases'])]
assert all(x['case_id']==y['case_id'] for x,y in zip(a['cases'],b['cases']))
summary=dict(finished_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),elapsed_seconds=time.time()-started,expected_cases_per_arm=10,A_passed=a['passed'],B_passed=b['passed'],improved=sum(x['A'] is False and x['B'] is True for x in paired),regressed=sum(x['A'] is True and x['B'] is False for x in paired),unscored_pairs=sum(x['A'] is None or x['B'] is None for x in paired),model_requests=sum(r['requests'] for r in results),known_tokens=sum(r['known_tokens'] for r in results),experience_updates=False,arms=results,paired=paired)
(ROOT/'completion.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
archive=REPO/'experiments/testing-runs'/ROOT.name;archive.mkdir(parents=True,exist_ok=True)
for name in ['completion.json','A-seed16-results.json','B-seed16-plus2-results.json']:shutil.copyfile(ROOT/name,archive/name)
print(json.dumps({k:v for k,v in summary.items() if k not in ['arms','paired']}),flush=True)
sys.exit(int(any(r['queue_exit_code']!=0 or r['unscored'] for r in results)))
