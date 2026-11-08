"""One E2 candidate only. No retries, tools, manual rewrite or alternative candidate."""
import sys,json,time
from pathlib import Path
sys.dont_write_bytecode=True
A=Path(__file__).resolve().parent;sys.path.insert(0,str(A))
import runner as r
from archive import save,sha
read=lambda p:json.loads(Path(p).read_text())
def main():
 assert not (A/'training-runs').exists() and not (A/'NEW_EXPERIENCE.md').exists()
 assert sha(A/'reflection-protocol.json')==(A/'reflection-protocol.sha256').read_text().strip()
 r.verify(read(A/'reflection-protocol.json')['files']);r.verify(read(A/'protected-files.json'))
 c=read(A/'cohort.json');slot={'slot':'reflection-E2','phase':'reflect','condition':'REFLECTION','repeat':None,'case':c['case']}
 rec=r.session(slot,(A/'reflection-input.md').read_text(),case=c,candidate=A/'materials/candidate',task=A/'materials/task.md',config={'seconds_per_session':600,'stdout_bytes':16777216,'frozen_files':read(A/'reflection-protocol.json')['files']},run_dir=A/'training-runs/reflection',allow_model_execution=True)
 save(A/'reflection-receipt.json',rec)
 r.verify(read(A/'reflection-protocol.json')['files']);r.verify(read(A/'protected-files.json'))
 d=A/'training-runs/reflection/archive'
 if not rec['infrastructure_valid'] or not rec['output_format_valid'] or rec['archive_status']['status']!='OK' or rec['native'].get('tool_attempts',0):
  save(A/'stop.json',{'stage':'reflection','reason':'single reflection invalid; no retry or second candidate','receipt':rec,'unstarted':read(A/'schedule.json')['slots']});return
 e=(d/'experience.md').read_text();raw=json.loads((d/'raw-answer.txt').read_text())['report'];assert e==raw
 forbidden=[c['case'],'src/session.js','queryFn','AbortController','AbortSignal','q.consumed','a.consumed','fetchStatus','refetchOnReconnect']+list(c['calibration'][0]['effects'])
 leaks=[x for x in forbidden if x in e]
 if not e.strip() or len(e)>6000 or leaks:
  save(A/'stop.json',{'stage':'experience_review','reason':'empty/oversize or case/API/scoring-name leakage; no manual rewrite','leaks':leaks,'unstarted':read(A/'schedule.json')['slots']});return
 (A/'NEW_EXPERIENCE.md').write_text(e)
 save(A/'experience-review.json',{'candidate':'E2','one_candidate_only':True,'source':str(d/'experience.md'),'raw_report_exact':True,'mechanical_specific_name_check':'PASS','manual_content_review_pending':True,'no_reflection_retry':True,'no_manual_edit':True,'requests':rec['native']['started'],'time':time.time()})
 print(json.dumps({'E2_generated':True,'requests':rec['native']['started'],'seconds':rec['seconds'],'sha256':sha(A/'NEW_EXPERIENCE.md')},ensure_ascii=False))
if __name__=='__main__':main()
