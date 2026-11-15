"""Prepare frozen independent trajectories; never starts a model."""
import csv,json,os,sys,shutil,datetime
from pathlib import Path
import argparse
parser=argparse.ArgumentParser(description='Zero-model Docker calibration and preparation of the selected case rank range')
parser.add_argument('--root',type=Path,required=True);parser.add_argument('--solver-image',required=True);parser.add_argument('--grader-image',required=True);parser.add_argument('--limit',type=int,default=10)
parser.add_argument('--start-rank',type=int,default=1,help='First one-based CSV rank to prepare')
parser.add_argument('--training-feedback',type=Path,help='Explicit public feedback mapping JSON, frozen in every trajectory')
parser.add_argument('--model-config',type=Path,help='Model profiles JSON file')
parser.add_argument('--model-profile',help='Named model profile; defaults to the configuration default')
parser.add_argument('--store',type=Path,help='Reviewed experience library; defaults to experience-memory/library')
parser.add_argument('--condition',choices=['structured','contract'],default='structured',help='Contract keeps Auto-Contract but never reads cross-task memory')
parser.add_argument('--training-feedback-by-family',type=Path,help='Frozen family-to-public-feedback mapping JSON')
parser.add_argument('--learning-policy',choices=['frozen','online'],default='frozen')
parser.add_argument('--online-memory',type=Path,help='Training-only shared provisional memory directory')
parser.add_argument('--mode',choices=['learning','testing'],default='learning')
parser.add_argument('--visible-evaluators',type=Path,help='Predeclared per-case public evaluator JSON for additional test families')
args=parser.parse_args()
if args.start_rank<1 or args.limit<1:parser.error('--start-rank and --limit must be positive')
if args.learning_policy=='online' and (args.condition!='structured' or not args.online_memory):parser.error('Online learning requires structured condition and --online-memory')
if args.learning_policy=='frozen' and args.online_memory:parser.error('Frozen runs cannot read an online pool')
if args.mode=='testing' and (args.learning_policy!='frozen' or args.training_feedback or args.training_feedback_by_family):parser.error('Testing forbids online memory and training-Gold feedback')
repo=Path(__file__).resolve().parents[2];sys.path.insert(0,str(repo))
store=(args.store or repo/'experience-memory/library').resolve()
from temporal_contract_analyzer.case_catalog import bench_root
bench=bench_root()
from temporal_contract_analyzer.case_catalog import case_input
from temporal_contract_analyzer.tempoevo_backend import NativeV4Backend
from temporal_contract_analyzer import experience_approval as approval
from temporal_contract_analyzer.tempoevo_v4 import Trajectory,MODEL
from temporal_contract_analyzer._session_runtime.model_settings import resolve_profile,identity
settings=resolve_profile(args.model_profile,args.model_config)
from temporal_contract_analyzer.core import sha
with (repo/'examples/tempoevo-v4/case-selections/gpt61-sol-medium-hardest50-20261029/selected_50_cases.csv').open(encoding='utf-8-sig') as selection_file:
 all_rows=list(csv.DictReader(selection_file))
rows=[row for row in all_rows if args.start_rank<=int(row['rank'])<args.start_rank+args.limit]
if len(rows)!=args.limit:parser.error('Requested rank range is not fully present in the selection CSV')
feedback=json.loads(args.training_feedback.read_text()) if args.training_feedback else {}
family_feedback=json.loads(args.training_feedback_by_family.read_text()) if args.training_feedback_by_family else {}
from temporal_contract_analyzer.training_acceptance import validate_mapping
validate_mapping(feedback)
for mapping in family_feedback.values():validate_mapping(mapping)
visible_configs=json.loads(args.visible_evaluators.read_text()) if args.visible_evaluators else {}
from temporal_contract_analyzer.evaluation_split import enforce
for row in rows:enforce(dict(task_id=row['case_id'],mode=args.mode))
root=args.root.resolve();root.mkdir()
if args.condition=='contract':
 bank=dict(schema_version='experience-active-snapshot-v1',scope='research_only',entries=[])
 from temporal_contract_analyzer.core import canonical
 bank['sha256']=sha(canonical(bank).encode())
else:bank=approval.freeze(store)
(root/'memory-snapshot.json').write_text(json.dumps(bank,indent=2)+'\n')
out=[]
solver=args.solver_image;grader=args.grader_image
for row in rows:
 cid=row['case_id'];r=root/cid;r.mkdir();entry=dict(case_id=cid,rank=int(row['rank']),root=str(r),status='preflight_running');out.append(entry);(root/'progress.json').write_text(json.dumps(out,indent=2)+'\n')
 try:
  c=case_input(cid);m=json.loads((bench/c['case_record']['manifest']).read_text());family='query' if cid.startswith('query-') else 'transfer' if cid.startswith('transfer-') else 'autosave' if cid.startswith('draft-autosave-') else 'generator' if cid.startswith('async-generator-') else 'review' if cid.startswith('review-confirmation-') else 'subscription' if cid.startswith('subscription-lifetime-') else 'other'
  if family=='other' and cid not in visible_configs:raise ValueError('A predeclared public evaluator is required for this case family; Gold cannot supply repair feedback')
  cfg=dict(manifest=c['case_record']['manifest'],runtime=m['framework']['runtime'],family=family);(r/'case.json').write_text(json.dumps(cfg)+'\n');shutil.copytree(c['candidate'],r/'public')
  (r/'public/VISIBLE_CHECKS.md').write_text('Public checks are deterministic external examples, not hidden gold. They are executed after each submitted Action. Keep original task/source obligations. '+('Checks: latest quiet burst (120ms), persistence before departure returns, retired views receive no late save status, synchronous save callback navigation stays authoritative, preview hide discards pending work and allows reuse.' if family=='autosave' else 'Checks: initial paused fetch with no remaining observer never invokes queryFn on reconnect; a remaining observer keeps the shared fetch; unconsumed active work can retain its completed cache value.' if family=='query' else 'Checks: warm cached startup progress, out-of-order frames do not roll back display while audit retains admitted frames, unchanged queue record fields.')+'\nUse the declared runtime: '+cfg['runtime']+' '+m['framework']['version']+'. The external adapter is not mounted in the model workspace; do not access scorer/reference files. Build temporary artifacts in /tmp.\n')
  if family in ('other','generator','review','subscription'):
   descriptions={'generator':'Early match and predicate error retain their result/error while awaiting retained-source cleanup; normal exhaustion preserves scan order and null result.', 'review':'Latest-only quiet bursts and subsequent bursts; synchronous submission persistence and entry receipt; queue callback navigation suppresses obsolete confirmation; transient preview remains unchanged.', 'subscription':'Open modal delivery and operation return; close suppresses late state writes while preserving operation return; independent shell survives child disposal.'}
   (r/'public/VISIBLE_CHECKS.md').write_text('Predeclared public examples: '+descriptions.get(family,'Only checks declared in the task-visible documentation.')+'\nGold and reference implementations remain unavailable during repair.\n')
  inputs={str(r/'case.json'):'/checks/case.json',str(repo/'tools/tempoevo-docker/public_checks.cjs'):'/checks/public_checks.cjs',str(repo/'tools/tempoevo-docker/public_frontend.cjs'):'/checks/public_frontend.cjs'}
  visible=dict(image=grader,inputs=inputs,command=['/opt/swe-tempoc/.swe-tempoc/toolchains/node-v16.20.2/bin/node','/checks/public_checks.cjs'],seconds=180)
  if cid in visible_configs:visible=visible_configs[cid]
  gold=dict(image=grader,inputs={str(r/'case.json'):'/checks/case.json',str(repo/'tools/tempoevo-docker/gold.py'):'/checks/gold.py'},command=['/usr/bin/python3','/checks/gold.py'],seconds=180)
  controls=[]
  control_specs=[('original',None)] if args.mode=='testing' else [('original',None),('reference',m['references']['bounded']),('negative',m['mutants'][0])]
  for name,overlay in control_specs:
   subject=r/'public' if overlay is None else r/'controls'/name
   if overlay:shutil.copytree(r/'public',subject);shutil.copytree(bench/Path(c['case_record']['manifest']).parent/overlay,subject,dirs_exist_ok=True)
   record=dict(control=name)
   for kind,ev in ([('visible',visible)] if args.mode=='testing' else [('visible',visible),('gold',gold)]):
    d=r/'checks'/name/kind;d.mkdir(parents=True);result=NativeV4Backend({}).evaluate(kind,dict(candidate=str(subject),evaluator=ev),d);(d/'result.json').write_text(json.dumps(result,indent=2)+'\n');record[kind]=dict(valid=result.get('valid'),passed=result.get('passed'),verdict=result.get('verdict'),error=result.get('error'))
    if result.get('valid') is not True:raise ValueError((name,kind,record[kind]))
    if name=='original' and kind=='visible':
     cfg['baseline_passed_checks']=[x['check'] for x in result['observations'] if x['passed']]
     (r/'case.json').write_text(json.dumps(cfg,indent=2)+'\n')
    if args.mode=='learning' and result['passed']!=(name=='reference'):raise ValueError((name,kind,'Unexpected control result',result))
   controls.append(record)
  entry['controls']=controls
  config=dict(task_id=cid,task=c['task'],candidate=str(r/'public'),store=str(store),mode='learning',condition='structured',max_attempts=3,model=MODEL,binary=shutil.which('codex'),backend=dict(kind='docker',solver_image=solver,grader_image=grader,solver_node='/runtime/node16/bin/node'),memory_snapshot=bank,visible_evaluator=visible,training_evaluator=gold,required_visible_checks=True,training_feedback=feedback,protected_paths=['README.md','VISIBLE_CHECKS.md'])
  config.update(model=identity(settings),model_profile=settings['profile'],condition=args.condition,training_feedback=family_feedback.get(family,feedback))
  config['learning_policy']=args.learning_policy
  if args.mode=='testing':
   config.update(mode='testing',gold_evaluator=config.pop('training_evaluator'))
   config.pop('training_feedback',None)
  if args.online_memory:config['online_memory']=str(args.online_memory.resolve())
  if args.model_config:config['model_config']=str(args.model_config.resolve())
  (r/'config.json').write_text(json.dumps(config,indent=2)+'\n');Trajectory(r/'trajectory').prepare(config);entry['status']='prepared'
 except Exception as e:entry.update(status='preflight_failed',error=repr(e))
 (root/'progress.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(entry),flush=True)
print(root,flush=True)
