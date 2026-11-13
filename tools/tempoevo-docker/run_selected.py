"""Sequential batch launcher. The public tempoevo CLI owns every model call."""
import argparse,json,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--execute',action='store_true');a=p.parse_args()
if not a.execute:p.error('--execute is required for explicitly authorized paid training')
repo=Path(__file__).resolve().parents[2];sys.path.insert(0,str(repo))
from temporal_contract_analyzer.tempoevo_v4 import VERSION
root=a.root.resolve();items=json.loads((root/'progress.json').read_text());results=[]
for item in items:
 if item['status']=='prepared' and json.loads((Path(item['root'])/'trajectory/protocol.json').read_text()).get('schema_version')!=VERSION:
  p.error('Historical batch is read-only; prepare a new root under '+VERSION)
for item in items:
 trajectory=Path(item['root'])/'trajectory';row=dict(case_id=item['case_id'],rank=item['rank'])
 if item['status']!='prepared':row.update(status='not_started',reason=item.get('error','Preparation incomplete'));results.append(row);continue
 state=json.loads((trajectory/'state.json').read_text())
 if state['status'] not in ['execution_invalid','cancelled'] and any(s['status']=='started' for s in state['stages']):
  row.update(status='not_replayed',reason='Previously started incomplete stage; explicit investigation required');results.append(row);continue
 if not state.get('finalized') and state['status'] not in ['execution_invalid','cancelled']:
  with (trajectory.parent/'training.log').open('w') as log:
   process=subprocess.run([sys.executable,'-B','-m','temporal_contract_analyzer','tempoevo','run','--root',str(trajectory),'--execute'],cwd=repo,stdout=log,stderr=subprocess.STDOUT)
 state=json.loads((trajectory/'state.json').read_text());row.update(status=state['status'],attempts=len(state['attempts']),visible_passed=any(x['visible_passed'] for x in state['attempts']),gold_verdict=(state.get('final_acceptance') or state.get('gold_result') or {}).get('verdict'),training_accepted=state.get('training_accepted'),stop_reason=state.get('stop_reason'),requests=sum(s['requests'] for s in state['stages'] if type(s.get('requests')) is int),unknown_request_stages=[s['key'] for s in state['stages'] if s['kind'] in ('routing','contract','action','diagnosis','extract') and type(s.get('requests')) is not int],transport_retries=sum(max(len(s.get('executions',[]))-1,0) for s in state['stages']),error=state.get('error'))
 if (trajectory/'candidate-pool/success.json').exists() and not json.loads((trajectory/'candidate-pool/success.json').read_text()).get('published_sha256'):
  with (trajectory.parent/'publication.log').open('w') as log:subprocess.run([sys.executable,'-B','-m','temporal_contract_analyzer','tempoevo','publish-candidate','success','--root',str(trajectory)],cwd=repo,stdout=log,stderr=subprocess.STDOUT,check=True)
 if (trajectory/'candidate-pool/success.json').exists():row['candidate_sha256']=json.loads((trajectory/'candidate-pool/success.json').read_text()).get('published_sha256')
 results.append(row);(root/'training-progress.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(row),flush=True)
(root/'training-progress.json').write_text(json.dumps(results,indent=2)+'\n')
