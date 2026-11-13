"""Prepare frozen independent V4 trajectories; never starts a model."""
import csv,json,os,sys,shutil,datetime
from pathlib import Path
import argparse
parser=argparse.ArgumentParser(description='Zero-model Docker calibration and preparation of the selected case prefix')
parser.add_argument('--root',type=Path,required=True);parser.add_argument('--solver-image',required=True);parser.add_argument('--grader-image',required=True);parser.add_argument('--limit',type=int,default=10)
parser.add_argument('--start-rank',type=int,default=1,help='First one-based CSV rank to prepare')
parser.add_argument('--training-feedback',type=Path,help='Explicit public feedback mapping JSON, frozen in every trajectory')
args=parser.parse_args()
if args.start_rank<1 or args.limit<1:parser.error('--start-rank and --limit must be positive')
repo=Path(__file__).resolve().parents[2];sys.path.insert(0,str(repo))
from temporal_contract_analyzer.case_catalog import bench_root
bench=bench_root()
from temporal_contract_analyzer.case_catalog import case_input
from temporal_contract_analyzer.tempoevo_backend import NativeV4Backend
from temporal_contract_analyzer import experience_approval as approval
from temporal_contract_analyzer.tempoevo_v4 import Trajectory,MODEL
from temporal_contract_analyzer.core import sha
all_rows=list(csv.DictReader((repo/'examples/tempoevo-v4/case-selections/gpt61-sol-medium-hardest50-20261029/selected_50_cases.csv').open(encoding='utf-8-sig')))
rows=[row for row in all_rows if args.start_rank<=int(row['rank'])<args.start_rank+args.limit]
if len(rows)!=args.limit:parser.error('Requested rank range is not fully present in the selection CSV')
feedback=json.loads(args.training_feedback.read_text()) if args.training_feedback else {}
from temporal_contract_analyzer.training_acceptance import validate_mapping
validate_mapping(feedback)
root=args.root.resolve();root.mkdir();bank=approval.freeze(repo/'experience-memory');(root/'memory-snapshot.json').write_text(json.dumps(bank,indent=2)+'\n')
out=[]
solver=args.solver_image;grader=args.grader_image
for row in rows:
 cid=row['case_id'];r=root/cid;r.mkdir();entry=dict(case_id=cid,rank=int(row['rank']),root=str(r),status='preflight_running');out.append(entry);(root/'progress.json').write_text(json.dumps(out,indent=2)+'\n')
 try:
  c=case_input(cid);m=json.loads((bench/c['case_record']['manifest']).read_text());family='query' if cid.startswith('query-') else 'transfer' if cid.startswith('transfer-') else 'autosave'
  cfg=dict(manifest=c['case_record']['manifest'],runtime=m['framework']['runtime'],family=family);(r/'case.json').write_text(json.dumps(cfg)+'\n');shutil.copytree(c['candidate'],r/'public')
  (r/'public/VISIBLE_CHECKS.md').write_text('Public checks are deterministic external examples, not hidden gold. They are executed after each submitted Action. Keep original task/source obligations. '+('Checks: latest quiet burst (120ms), persistence before departure returns, synchronous save callback navigation stays authoritative, preview hide discards pending work and allows reuse.' if family=='autosave' else 'Checks: initial paused fetch with no remaining observer never invokes queryFn on reconnect; a remaining observer keeps the shared fetch; unconsumed active work can retain its completed cache value.' if family=='query' else 'Checks: warm cached startup progress, out-of-order frames do not roll back display while audit retains admitted frames, unchanged queue record fields.')+'\nUse the declared runtime: '+cfg['runtime']+' '+m['framework']['version']+'. The external adapter is not mounted in the model workspace; do not access scorer/reference files. Build temporary artifacts in /tmp.\n')
  inputs={str(r/'case.json'):'/checks/case.json',str(repo/'tools/tempoevo-docker/public_checks.cjs'):'/checks/public_checks.cjs'}
  visible=dict(image=grader,inputs=inputs,command=['/opt/swe-tempoc/.swe-tempoc/toolchains/node-v16.20.2/bin/node','/checks/public_checks.cjs'],seconds=180)
  gold=dict(image=grader,inputs={str(r/'case.json'):'/checks/case.json',str(repo/'tools/tempoevo-docker/gold.py'):'/checks/gold.py'},command=['/usr/bin/python3','/checks/gold.py'],seconds=180)
  controls=[]
  for name,overlay in [('original',None),('reference',m['references']['bounded']),('negative',m['mutants'][0])]:
   subject=r/'public' if overlay is None else r/'controls'/name
   if overlay:shutil.copytree(r/'public',subject);shutil.copytree(bench/Path(c['case_record']['manifest']).parent/overlay,subject,dirs_exist_ok=True)
   record=dict(control=name)
   for kind,ev in [('visible',visible),('gold',gold)]:
    d=r/'checks'/name/kind;d.mkdir(parents=True);result=NativeV4Backend({}).evaluate(kind,dict(candidate=str(subject),evaluator=ev),d);(d/'result.json').write_text(json.dumps(result,indent=2)+'\n');record[kind]=dict(valid=result.get('valid'),passed=result.get('passed'),verdict=result.get('verdict'),error=result.get('error'))
    if result.get('valid') is not True:raise ValueError((name,kind,record[kind]))
    if name=='original' and kind=='visible':
     cfg['baseline_passed_checks']=[x['check'] for x in result['observations'] if x['passed']]
     (r/'case.json').write_text(json.dumps(cfg,indent=2)+'\n')
    if result['passed']!=(name=='reference'):raise ValueError((name,kind,'Unexpected control result',result))
   controls.append(record)
  entry['controls']=controls
  config=dict(task_id=cid,task=c['task'],candidate=str(r/'public'),store=str(repo/'experience-memory'),mode='learning',condition='structured',max_attempts=3,model=MODEL,binary=shutil.which('codex'),backend=dict(kind='docker',solver_image=solver,grader_image=grader,solver_node='/runtime/node16/bin/node'),memory_snapshot=bank,visible_evaluator=visible,training_evaluator=gold,required_visible_checks=True,training_feedback=feedback,protected_paths=['README.md','VISIBLE_CHECKS.md'])
  (r/'config.json').write_text(json.dumps(config,indent=2)+'\n');Trajectory(r/'trajectory').prepare(config);entry['status']='prepared'
 except Exception as e:entry.update(status='preflight_failed',error=repr(e))
 (root/'progress.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(entry),flush=True)
print(root,flush=True)
