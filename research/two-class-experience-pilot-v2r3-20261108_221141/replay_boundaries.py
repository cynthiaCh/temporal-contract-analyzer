"""Replay exact stopped v2 output through typed parser/archiver; zero model calls."""
import json,sys
from pathlib import Path
A=Path(__file__).resolve().parent;V=A.parent/'two-class-experience-pilot-v2-20261108_205648'
sys.path.insert(0,str(A));import runner
from archive import save

def main():
 src=V/'runs/D1-preanalysis-v2/archive';case=json.loads((A/'cohort.json').read_text())[0];slot='replay-v2-6000';score_calls=[]
 def fake(a,runtime,guard):
  ledger=json.loads((src/'meter/ledger.json').read_text());ledger['sessions']={slot:next(iter(ledger['sessions'].values()))};save(guard.meter/'ledger.json',ledger)
  return [sys.executable,'-B','-c','import sys\nsys.stdout.write('+repr((src/'events.jsonl').read_text())+');sys.stdout.flush()\n']
 def score(final,out):score_calls.append(str(final));raise AssertionError('invalid material may not be scored')
 rec=runner.session({'slot':slot,'phase':'extract','condition':'OFFLINE_BOUNDARY_REPLAY'},'historical fixture only',case=case,candidate=A/'materials/D1/candidate',task=A/'materials/D1/task.md',config={'seconds_per_session':30},run_dir=A/'offline'/slot,command_factory=fake,score_fn=score)
 root=A/'offline'/slot/'archive';assert rec['archive_status']['status']=='OK' and not rec['preanalysis_valid'] and not rec['output_format_valid'] and not score_calls
 assert (root/'raw-answer.txt').read_bytes()==(src/'raw-answer.txt').read_bytes()
 assert not (root/'analysis.json').exists() and not (root/'contract.md').exists()
 save(A/'offline/boundary-replay-receipt.json',{'status':'PASS','experimental_model_calls':0,'raw_original_preserved':True,'invalid_legacy_nested_payload_rejected':True,'no_automatic_salvage':True,'score_calls':0,'source':str(src)})
 print('PASS exact 6000-character legacy output: retained, rejected, no Contract/score')
if __name__=='__main__':main()
