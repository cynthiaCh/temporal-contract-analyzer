"""Explicit zero-model recovery into NEW roots; retain old scores and usage errors."""
import argparse,json,hashlib,shutil,sys,datetime,csv
from pathlib import Path
REPO=Path(__file__).resolve().parents[2];sys.path.insert(0,str(REPO))
from temporal_contract_analyzer.tempoevo_v4 import Trajectory
from temporal_contract_analyzer.candidate_files import capture,inventory
from temporal_contract_analyzer import archive,experience_routing,taxonomy,prompt_context
from temporal_contract_analyzer.core import canonical

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def save(p,x):archive.atomic_json(Path(p),x)
def sealed_history(t):
 p=read(t/'protocol.json');s=read(t/'state.json');b=read(t/'binding.json')
 assert sha(t/'protocol.json')==b['protocol'] and sha(t/'memory-snapshot.json')==b['bank'] and sha(t/'ast-evidence.json')==b['ast']
 assert inventory(capture(t/'original')[0])==p['original_inventory']
 assert all(sha(f)==h for f,h in b['evaluators'].items()),'Evaluator bytes changed; cannot reuse controls'
 for a in s['attempts']:assert inventory(capture(t/'attempts'/str(a['number'])/'candidate')[0])==a['candidate_inventory']
 for stage in s['stages']:
  if stage['status']=='complete':assert sha(t/'stages'/stage['key']/'result.json')==stage['result_sha256']
 return p,s

def import_completed(old,new,config):
 p,s=sealed_history(old)
 assert s['status'] in ['passed','awaiting_expert_summary','execution_invalid']
 extract_recovery=s['status']=='execution_invalid'
 if extract_recovery:
  assert s.get('training_accepted') is True and len(s['attempts'])>=1 and s['attempts'][-1]['acceptance_passed'] is True
  bad=[z for z in s['stages'] if z['status']!='complete'];assert len(bad)==1 and bad[0]['kind']=='extract' and bad[0]['status']=='invalid' and type(bad[0]['requests']) is int
 else:assert s.get('finalized') is True
 loop=Trajectory(new);loop.prepare(config)
 assert loop.verify()['original_inventory']==p['original_inventory']
 for directory in ['attempts','candidate-pool','revisions','validation']:
  if (old/directory).exists():shutil.copytree(old/directory,new/directory,dirs_exist_ok=True)
 for f in old.glob('*.json'):
  if f.name not in ['protocol.json','binding.json','state.json','memory-snapshot.json','ast-report.json','ast-evidence.json','summary.json','cancellation.json']:shutil.copy2(f,new/f.name)
 for stage in s['stages']:
  before=stage['key'];after='historical-extract-error' if extract_recovery and stage['kind']=='extract' else before
  directory=new/'stages'/after;directory.mkdir(parents=True,exist_ok=True)
  for name in ['result.json','input.json','prompt-context.json']:
   if (old/'stages'/before/name).exists():shutil.copy2(old/'stages'/before/name,directory/name)
  stage['key']=after
 if extract_recovery:
  s.update(status='passed',finalized=False,stop_reason='oracle_accepted',error=None)
 save(new/'state.json',s)
 lineage=dict(kind='explicit_operator_recovery_import',original_root=str(old),original_protocol_sha256=sha(old/'protocol.json'),original_state_sha256=sha(old/'state.json'),new_model_calls=0,new_gold_calls=0,accepted_repairs_reused=True,extract_only=extract_recovery,historical_stage_results_retained=True,prior_usage_errors_not_reclassified=True)
 save(new/'recovery-lineage.json',lineage);loop.verify();loop.report()
 if extract_recovery:
  limit=loop._remaining_limit(loop.verify(),'extract','extract');assert limit['requests']==11,limit
 return lineage

def prepare(source,root):
 assert not (root/'preflight.json').exists()
 for p in list(source.glob('*.csv'))+[source/n for n in ['plan.json','reuse.json','authorization.json','split.json','model-profiles.json','initial-memory-snapshot.json','initial-lineage.json','public-checks-docs.json','visible-evaluators.json','selected-case-image-verification.json']]:shutil.copy2(p,root/p.name)
 for name in ['initial-library','experience-library','provisional']:shutil.copytree(source/name,root/name)
 oldrows=read(source/'train-batch/progress.json');items=[];imports=[]
 for item in oldrows:
  old=Path(item['root'])/'trajectory';p=read(old/'protocol.json');s=read(old/'state.json');config=read(old.parent/'config.json')
  config.update(candidate=str(old/'original'),store=str(root/'experience-library'),memory_snapshot=read(root/'initial-memory-snapshot.json'),online_memory=str(root/'provisional'),evaluation_split_file=str(root/'split.json'),model_config=str(root/'model-profiles.json'))
  destination=root/'training'/item['case_id'];destination.mkdir(parents=True);save(destination/'config.json',config);new=destination/'trajectory'
  if s['attempts']:imports.append(import_completed(old,new,config))
  else:
   assert s['status']=='execution_invalid' and p['task_id'].startswith('rxjs-asyncsubject-')
   err=list(old.glob('stages/routing/**/stderr.log'));assert any('input_too_large' in f.read_text() for f in err)
   Trajectory(new).prepare(config);sources={k:v.decode() for k,v in capture(new/'original')[0].items()};ast=read(new/'ast-evidence.json');payload=dict(task=p['task'],sources=sources,ast=ast,schema=taxonomy.analysis_schema(),instruction=experience_routing.analysis_prompt(p['task'],sources,ast,embed_sources=False))
   wire,report=prompt_context.compact(payload);assert len(canonical(wire))+2000<1048576;save(destination/'prompt-size-preflight.json',report)
   save(new/'recovery-lineage.json',dict(kind='fresh_replacement_for_pre_model_input_rejection',original_root=str(old),prior_usage='retained unknown in original run; not silently set to zero',prior_actions=0,new_actions_allowed=3))
   Trajectory(new).verify()
  items.append(dict(item,root=str(destination),status='prepared'))
 (root/'train-batch').mkdir();save(root/'train-batch/progress.json',items)
 plan=read(root/'plan.json');plan.update(run_root=str(root),status='recovery_prepared',resumed_from=str(source),reused_completed_current_training=len(imports),new_repair_cases=4,extract_only_cases=1);save(root/'plan.json',plan)
 save(root/'preflight.json',dict(valid=True,model_calls=0,new_gold_calls=0,current_bindings=len(items),sealed_completed_imports=len(imports),new_repairs=4,extract_only=1,controls_reused_from=str(source/'preflight.json'),evaluator_hashes_unchanged=True,imports=imports))

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--source',type=Path,required=True);a.add_argument('--root',type=Path,required=True);a.add_argument('--prepare-only',action='store_true',required=True);v=a.parse_args();prepare(v.source.resolve(),v.root.resolve())
