"""Prepare frozen training/testing trajectories; never starts a model."""
import csv,json,os,sys,shutil,datetime
from pathlib import Path
import argparse
parser=argparse.ArgumentParser(description='Prepare training or single-submission testing trajectories; no model calls')
parser.add_argument('--root',type=Path,required=True);parser.add_argument('--solver-image',required=True);parser.add_argument('--grader-image',required=True);parser.add_argument('--limit',type=int,default=10)
parser.add_argument('--start-rank',type=int,default=1,help='First one-based CSV rank to prepare')
parser.add_argument('--selection-file',type=Path,help='Explicit ranked case CSV; defaults to final train70 or test30 for the selected mode')
parser.add_argument('--swe-tempoc-root',type=Path,help='Read public inputs from the frozen SWE-TempoC roster; regular cases support learning/testing')
parser.add_argument('--evaluation-split',type=Path,help='Explicit frozen split registry for a new incremental cohort')
parser.add_argument('--training-feedback',type=Path,help='Explicit public feedback mapping JSON, frozen in every trajectory')
parser.add_argument('--model-config',type=Path,help='Model profiles JSON file')
parser.add_argument('--model-profile',help='Named model profile; defaults to the configuration default')
parser.add_argument('--binary',type=Path,help='Linux agent executable (Codex or Qoder) mounted into the solver container')
parser.add_argument('--store',type=Path,help='Reviewed experience library; defaults to experience-memory/library')
parser.add_argument('--condition',choices=['structured','contract','baseline'],default='structured',help='Contract uses Auto-Contract without memory; baseline runs Action only without memory or Contract')
parser.add_argument('--training-feedback-by-family',type=Path,help='Frozen family-to-public-feedback mapping JSON')
parser.add_argument('--learning-policy',choices=['frozen','online'],default='frozen')
parser.add_argument('--online-memory',type=Path,help='Training-only shared provisional memory directory')
parser.add_argument('--mode',choices=['learning','testing'],default='learning')
parser.add_argument('--visible-evaluators',type=Path,help='Optional existing project evaluator mapping; omitted by default')
parser.add_argument('--training-recipe',choices=['v8-compatible-v1'],help='Restore V8 learning semantics with public checks and behavior feedback')
parser.add_argument('--retrieval-profile',choices=['semantic-v11','source-bound-v8','business-source-v1'],help='Memory router; structured testing defaults to business-source-v1, the V8 construction recipe to source-bound-v8')
parser.add_argument('--approved-supplement-store',type=Path,help='Additional reviewed memory store for frozen testing only')
parser.add_argument('--approved-supplement-snapshot',type=Path,help='Exact audited snapshot from the supplemental store')
parser.add_argument('--memory-snapshot',type=Path,help='Exact audited approved snapshot; validated against --store')
parser.add_argument('--public-checks-docs',type=Path,help='Training-only case-to-public-check-description mapping')
args=parser.parse_args()
if bool(args.approved_supplement_store)!=bool(args.approved_supplement_snapshot):parser.error('Supplement store and snapshot must be provided together')
if args.approved_supplement_store and args.mode!='testing':parser.error('Approved supplements are testing-only')
if args.start_rank<1 or args.limit<1:parser.error('--start-rank and --limit must be positive')
if args.learning_policy=='online' and (args.condition!='structured' or not args.online_memory):parser.error('Online learning requires structured condition and --online-memory')
if args.learning_policy=='frozen' and args.online_memory:parser.error('Frozen runs cannot read an online pool')
if args.mode=='testing' and (args.learning_policy!='frozen' or args.training_feedback or args.training_feedback_by_family):parser.error('Testing forbids online memory and training-Gold feedback')
if args.mode=='testing' and (args.training_recipe or args.public_checks_docs):parser.error('Testing forbids a training recipe and training-only check descriptions')
if args.training_recipe and not args.public_checks_docs:parser.error('V8 training requires explicit public check descriptions')
repo=Path(__file__).resolve().parents[2];sys.path.insert(0,str(repo))
store=(args.store or repo/'experience-memory/library').resolve()
from temporal_contract_analyzer.case_catalog import bench_root
bench=args.swe_tempoc_root.resolve() if args.swe_tempoc_root else bench_root()
from temporal_contract_analyzer.case_catalog import case_input
if args.swe_tempoc_root:
 from temporal_contract_analyzer.swe_tempoc_inputs import case_input as swe_case_input
 def case_input(case_id):
  from upstream_inputs import load
  def upstream_loader(cid,root,row,mp,m):
   if args.mode!='testing':raise ValueError('Upstream repository tasks currently support testing only; training controls are not implemented')
   return load(cid,root,row,mp,m,args.grader_image,public_destination)
  return swe_case_input(case_id,bench,upstream_loader=upstream_loader,public_destination=public_destination)
from temporal_contract_analyzer.tempoevo_backend import NativeV4Backend
from temporal_contract_analyzer import experience_approval as approval
from temporal_contract_analyzer.tempoevo_v4 import Trajectory,MODEL
from temporal_contract_analyzer._session_runtime.model_settings import resolve_profile,identity
settings=resolve_profile(args.model_profile,args.model_config)
from temporal_contract_analyzer.core import sha
selection_path=(args.selection_file or repo/'cases'/('train70.csv' if args.mode=='learning' else 'test30.csv')).resolve()
with selection_path.open(encoding='utf-8-sig') as selection_file:
 all_rows=list(csv.DictReader(selection_file))
if len({row['case_id'] for row in all_rows})!=len(all_rows) or len({int(row['rank']) for row in all_rows})!=len(all_rows):parser.error('Selection case IDs and ranks must be unique')
rows=[row for row in all_rows if args.start_rank<=int(row['rank'])<args.start_rank+args.limit]
if len(rows)!=args.limit:parser.error('Requested rank range is not fully present in the selection CSV')
expected_split='training' if args.mode=='learning' else 'testing'
if any(row.get('split',expected_split)!=expected_split for row in rows):parser.error('Selection CSV split does not match the requested mode')
feedback=json.loads(args.training_feedback.read_text()) if args.training_feedback else {}
family_feedback=json.loads(args.training_feedback_by_family.read_text()) if args.training_feedback_by_family else {}
from temporal_contract_analyzer.training_acceptance import validate_mapping
validate_mapping(feedback)
for mapping in family_feedback.values():validate_mapping(mapping)
visible_configs=json.loads(args.visible_evaluators.read_text()) if args.visible_evaluators else {}
public_docs=json.loads(args.public_checks_docs.read_text()) if args.public_checks_docs else {}
from temporal_contract_analyzer.evaluation_split import enforce
for row in rows:enforce(dict(task_id=row['case_id'],mode=args.mode,**({'evaluation_split_file':str(args.evaluation_split.resolve())} if args.evaluation_split else {})))
root=args.root.resolve();root.mkdir()
shutil.copyfile(selection_path,root/'selection.csv')
(root/'selection-source.json').write_text(json.dumps(dict(path=str(selection_path),sha256=sha(selection_path.read_bytes()),benchmark_root=str(bench),source='swe-tempoc' if args.swe_tempoc_root else 'registered-catalog'),indent=2)+'\n')
if args.condition in ('contract','baseline'):
 bank=dict(schema_version='experience-active-snapshot-v1',scope='research_only',entries=[])
 from temporal_contract_analyzer.core import canonical
 bank['sha256']=sha(canonical(bank).encode())
else:bank=approval.validate_snapshot(store,json.loads(args.memory_snapshot.read_text())) if args.memory_snapshot else approval.freeze(store)
(root/'memory-snapshot.json').write_text(json.dumps(bank,indent=2)+'\n')
out=[]
solver=args.solver_image;grader=args.grader_image
agent_binary=str(args.binary.resolve()) if args.binary else str(repo/'.tempoevo/qoder/linux/qoder') if settings['provider']['wire_api']=='qoder_cli' else shutil.which('codex')
for row in rows:
 cid=row['case_id'];r=root/cid;r.mkdir();entry=dict(case_id=cid,rank=int(row['rank']),root=str(r),status='preflight_running');out.append(entry);(root/'progress.json').write_text(json.dumps(out,indent=2)+'\n')
 try:
  public_destination=r/'upstream-public'
  c=case_input(cid);m=json.loads((bench/c['case_record']['manifest']).read_text());family='query' if cid.startswith('query-') else 'transfer' if cid.startswith('transfer-') else 'autosave' if cid.startswith('draft-autosave-') else 'generator' if cid.startswith('async-generator-') else 'review' if cid.startswith('review-confirmation-') else 'subscription' if cid.startswith('subscription-lifetime-') else 'workspace' if cid.startswith('workspace-draft-') else 'download' if cid.startswith('download-polling-') else 'other'
  cfg=dict(manifest=c['case_record']['manifest'],runtime=m.get('framework',{}).get('runtime',m.get('adapter')),family=family)
  if c['case_record'].get('projection'):cfg.update(case_id=cid,projection=c['case_record']['projection'])
  (r/'case.json').write_text(json.dumps(cfg)+'\n');shutil.copytree(c['candidate'],r/'public')
  if args.public_checks_docs:
   doc=public_docs.get(cid)
   if not isinstance(doc,str) or not doc.strip():raise ValueError('Missing public check description for '+cid)
   (r/'public/VISIBLE_CHECKS.md').write_text(doc)
  visible=visible_configs.get(cid)
  if args.training_recipe and not visible:
   visible=dict(image=grader,inputs={str(r/'case.json'):'/checks/case.json',str(repo/'tools/tempoevo-docker/public_checks.cjs'):'/checks/public_checks.cjs'},command=['/opt/swe-tempoc/.swe-tempoc/toolchains/node-v16.20.2/bin/node','/checks/public_checks.cjs'],seconds=180)
  gold=dict(image=grader,inputs={str(r/'case.json'):'/checks/case.json',str(repo/'tools/tempoevo-docker/gold.py'):'/checks/gold.py'},command=['/usr/bin/python3','/checks/gold.py'],seconds=180)
  if m.get('schema_version')=='python-pilot-0.1':gold['inputs'][str(repo/'tools/tempoevo-docker/python_gold.py')]=gold['inputs'].pop(str(repo/'tools/tempoevo-docker/gold.py'))
  if cfg.get('projection') and cfg['projection']['kind']=='frozen_base_public_projection_v1':
   gold.update(inputs={str(r/'case.json'):'/checks/case.json',str(repo/'tools/tempoevo-docker/projected_gold.py'):'/checks/gold.py'},seconds=300)
  elif cfg.get('projection'):
   gold.update(inputs={str(r/'case.json'):'/checks/case.json',str(repo/'tools/tempoevo-docker/upstream_gold.py'):'/checks/gold.py'},seconds=300)
  controls=[]
  control_specs=([('original',None)] if visible else []) if args.mode=='testing' else [('original',None),('reference',(m.get('reference') or m['references']['bounded'])),('negative',m['mutants'][0])]
  for name,overlay in control_specs:
   subject=r/'public' if overlay is None else r/'controls'/name
   if overlay:shutil.copytree(r/'public',subject);shutil.copytree(bench/Path(c['case_record']['manifest']).parent/overlay,subject,dirs_exist_ok=True)
   record=dict(control=name)
   for kind,ev in ([('visible',visible)] if args.mode=='testing' else ([('visible',visible)] if visible else [])+[('gold',gold)]):
    d=r/'checks'/name/kind;d.mkdir(parents=True);result=NativeV4Backend({}).evaluate(kind,dict(candidate=str(subject),evaluator=ev),d);(d/'result.json').write_text(json.dumps(result,indent=2)+'\n');record[kind]=dict(valid=result.get('valid'),passed=result.get('passed'),verdict=result.get('verdict'),error=result.get('error'))
    if result.get('valid') is not True:raise ValueError((name,kind,record[kind]))
    if args.training_recipe and name=='reference' and kind=='visible' and result['passed'] is not True:raise ValueError((name,kind,'Reference must pass public examples',result))
    if args.mode=='learning' and kind=='gold' and result['passed']!=(name=='reference'):raise ValueError((name,kind,'Unexpected control result',result))
   controls.append(record)
  entry['controls']=controls
  config=dict(task_id=cid,task=c['task'],candidate=str(r/'public'),store=str(store),mode='learning',condition='structured',max_attempts=3,model=MODEL,binary=agent_binary,backend=dict(kind='docker',solver_image=solver,grader_image=grader,solver_node='/runtime/node16/bin/node'),memory_snapshot=bank,training_evaluator=gold,training_feedback=feedback,protected_paths=['README.md'])
  if visible:config['visible_evaluator']=visible
  config.update(model=identity(settings),model_profile=settings['profile'],condition=args.condition,training_feedback=family_feedback.get(family,feedback))
  if args.retrieval_profile:config['retrieval_profile']=args.retrieval_profile
  if args.approved_supplement_store:config['approved_memory_supplements']=[dict(store=str(args.approved_supplement_store.resolve()),snapshot=json.loads(args.approved_supplement_snapshot.read_text()))]
  if args.training_recipe:config.update(training_recipe=args.training_recipe,required_visible_checks=True,protected_paths=['README.md','VISIBLE_CHECKS.md'])
  if args.evaluation_split:config['evaluation_split_file']=str(args.evaluation_split.resolve())
  config['public_case_record']=c['case_record']
  config['learning_policy']=args.learning_policy
  if args.mode=='testing':
   config.update(mode='testing',max_attempts=1,gold_evaluator=config.pop('training_evaluator'))
   config.pop('training_feedback',None)
  if args.online_memory:config['online_memory']=str(args.online_memory.resolve())
  if args.model_config:config['model_config']=str(args.model_config.resolve())
  (r/'config.json').write_text(json.dumps(config,indent=2)+'\n');Trajectory(r/'trajectory').prepare(config);entry['status']='prepared'
 except Exception as e:entry.update(status='preflight_failed',error=repr(e))
 (root/'progress.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(entry),flush=True)
print(root,flush=True)
if any(row['status']!='prepared' for row in out):sys.exit(1)
