"""Durable offline replay of the exact v1 failed response and null ledger."""
import json,sys,shutil
from pathlib import Path
A=Path(__file__).resolve().parent;V=A.parent/'two-class-experience-pilot-20261108_200017'
sys.path.insert(0,str(A))
import runner
from archive import save,inventory

def main():
 src=V/'runs/T1-block-1-A/archive';case=json.loads((A/'cohort.json').read_text())[2];calls=[]
 def build(a,runtime,guard):
  ledger=json.loads((src/'meter/ledger.json').read_text());ledger['sessions']={'replay-v1-failure':next(iter(ledger['sessions'].values()))};save(guard.meter/'ledger.json',ledger)
  # Reproduce already-observed partial workspace, no model or oracle invocation.
  shutil.copytree(src/'final-candidate',a.workspace,dirs_exist_ok=True)
  body='import sys\nsys.stdout.write('+repr((src/'events.jsonl').read_text())+');sys.stdout.flush()\nsys.stderr.write('+repr((src/'stderr.log').read_text())+');sys.exit(1)\n'
  return [sys.executable,'-B','-c',body]
 def score(final,out):calls.append(str(final));raise AssertionError('failed replay must never reach scoring')
 rec=runner.session({'slot':'replay-v1-failure','phase':'repair','condition':'OFFLINE_REAL_STREAM_REPLAY'},'offline fixture',case=case,candidate=A/'materials/T1/candidate',task=A/'materials/T1/task.md',config={'seconds_per_session':30},run_dir=A/'offline/replay-v1-failure',command_factory=build,score_fn=score)
 root=A/'offline/replay-v1-failure/archive';u=json.loads((root/'usage.json').read_text())
 assert rec['archive_status']['status']=='OK' and not rec['scoring_admissible'] and not calls
 assert u['usage_unknown_requests']==1 and u['total_usage'] is None and u['observed_usage_subtotal']['total_tokens']==34555
 assert inventory(root/'final-candidate')==inventory(src/'final-candidate')
 save(A/'offline/failure-replay-receipt.json',{'status':'PASS','experimental_model_calls':0,'scoring_calls':0,'synthetic_hooks_from_existing_ledger':True,'source':str(src),'usage_unknown_requests':1,'known_total_tokens':34555,'original_error_retained':True,'partial_candidate_snapshot_exact':True,'incomplete_not_scored':True})
 print('PASS real v1 failure replay: archive OK, original error retained, scoring blocked, unknown preserved')
if __name__=='__main__':main()
