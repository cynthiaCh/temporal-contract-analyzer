"""Fixed-pair metadata, source-visible policy audit and zero-model calibration."""
import json,subprocess,sys,shutil,time,unittest
from pathlib import Path
sys.dont_write_bytecode=True
A=Path(__file__).resolve().parent;REPO=A.parent.parent;sys.path[:0]=[str(A),str(REPO)]
from archive import save,sha
from citations import catalog,schema,fingerprint,INSTRUCTIONS
from toolflow import PREDICATES
import runner,pilot

def read(p):return json.loads(Path(p).read_text())
def main():
 assert not (A/'cases.json').exists()
 root=REPO.parent/'temporal-contract-bench-git/case-clusters/draft-autosave-handoff/arms'
 old=A.parent/'transfer-progress-one-pair-pilot-v2a-20261109_092536'
 nodes={c['alias']:c['node'] for c in read(old/'cases.json')}
 from temporal_contract_analyzer.core import scan
 cases=[];cal=[]
 for alias,cid in [('D','draft-autosave-handoff-order-example-vanilla'),('T','draft-autosave-handoff-order-example-python3')]:
  src=root/cid;m=read(src/'case.json');dest=A/'materials'/alias;dest.mkdir(parents=True,exist_ok=True)
  for origin,name in [('base','candidate'),('oracle','evaluation')]:
   if (dest/name).exists():assert runner.backend.hashes(dest/name)==runner.backend.hashes(src/origin)
   else:shutil.copytree(src/origin,dest/name)
  shutil.copy2(src/'case.json',dest/'manifest.json');shutil.copy2(src/'provenance/source-record.json',dest/'source-record.json')
  shutil.copy2(src/m['diagnostic_tasks']['maintenance']['core_prompt'],dest/'task.md')
  ast=scan(dest/'candidate',node=nodes[alias]);save(dest/'ast.json',ast)
  assert ast['summary']['files']==ast['summary']['parsed_files']>0
  text={str(f.relative_to(dest/'candidate')):f.read_text() for f in (dest/'candidate').rglob('*') if f.is_file() and f.suffix in ['.md','.js','.py']}
  text['TASK']=(dest/'task.md').read_text();cat=catalog(text);save(dest/'source-catalog.json',cat)
  save(dest/'extraction.schema.json',schema(cat,read(A/'extraction.schema.json')))
  public={'TASK':text['TASK'],'taxonomy':read(A/'taxonomy.json')['classes'],'predicates':PREDICATES,
   'AST':{'status':ast['status'],'summary':ast['summary'],'limitations':ast['limitations']},'source_catalog':cat}
  prompt='TASK is virtual task text in this prompt, not a file /workspace/TASK. Read existing candidate files separately.\n'+INSTRUCTIONS+json.dumps(public,ensure_ascii=False)
  assert cid not in prompt and 'debounced-submit-flush' not in prompt
  (dest/'preanalysis-prompt.md').write_text(prompt)
  rules=read(dest/'evaluation/effects.json');variant=rules['variants']['ungranted'];descriptions={e['id']:e['description'] for e in rules['effects']}
  standards=[{'effect':key,'expected':key in variant['required'],'description':descriptions[key],
   'policy_support':'Current task/README/source and AI-assisted policy-audit.json; scoring names are not causes.'} for key in variant['required']+variant['forbidden']]
  save(dest/'standards.json',standards)
  c={'alias':alias,'case':cid,'source_case':str(src),'node':nodes[alias],'framework':m['framework'],
   'independent_unit_id':m['independent_unit_id'],'candidate_files':runner.backend.hashes(dest/'candidate'),
   'task_sha256':sha(dest/'task.md'),'oracle_files':runner.backend.hashes(src/'oracle'),
   'extraction_schema':str(dest/'extraction.schema.json'),'source_catalog_sha256':fingerprint(cat),
   'exposure':'Outcome-informed authored source family; both sources inspected during selection, not unseen. No verified matching Terra/low headroom evidence found.'}
  cases.append(c)
  # Fresh calibration of these newly selected versions; no historical agent
  # patch replay, scoring-rule edits or model calls. Reference bodies never
  # enter reflection or maintenance payloads.
  variants=[('original',src/'base')]+[('reference-'+k,src/v) for k,v in m['references'].items()]+[('mutant-'+f.name,f) for f in sorted((src/'mutants').iterdir())]
  for label,candidate in variants:
   out=A/'calibration'/alias/label
   if (out/'receipt.json').exists():
    rec=read(out/'receipt.json');assert rec['score_valid'] and rec['oracle_files']==c['oracle_files']
    cal.append({'alias':alias,'variant':label,'verdict':rec['verdict'],'score_valid':True});continue
   if out.exists():
    rejected=A/'offline-materialization-error'/alias/label;rejected.parent.mkdir(parents=True,exist_ok=True);shutil.move(str(out),str(rejected))
   out.mkdir(parents=True)
   # References/mutants are overlays. Materialize as the benchmark does, never
   # mutate the registered base or reference, and keep the resulting full tree.
   overlay=candidate
   if label!='original':
    candidate=out/'candidate';shutil.copytree(src/'base',candidate);shutil.copytree(overlay,candidate,dirs_exist_ok=True)
   before=runner.backend.hashes(candidate)
   cmd=[c['node'],str(src/'oracle/probe.cjs'),str(candidate),'ungranted'];start=time.time()
   with (out/'stdout.json').open('wb') as o,(out/'stderr.txt').open('wb') as e:z=subprocess.run(cmd,stdout=o,stderr=e,timeout=120)
   score=read(out/'stdout.json');assert z.returncode in [0,1] and not any(v.get('runtimeError') for v in score['schedules'].values())
   assert runner.backend.hashes(candidate)==before
   assert score['verdict']==('PASS' if label=='reference-bounded' else 'OVERREACH' if label=='reference-expanded' else 'UNDERREACH')
   rec={'command':cmd,'candidate_before':before,'oracle_files':c['oracle_files'],'exit_code':z.returncode,'verdict':score['verdict'],'score_valid':True,'seconds':time.time()-start,'model_calls':0,'materialization':'Original base plus exact registered overlay' if label!='original' else 'original base','overlay_files':runner.backend.hashes(overlay)}
   save(out/'receipt.json',rec);cal.append({'alias':alias,'variant':label,'verdict':score['verdict'],'score_valid':True})
  print('CALIBRATED',alias,len(variants),'native variants',flush=True)
 save(A/'cases.json',cases);save(A/'calibration-summary.json',cal)
 policy={'reviewer':'execution_agent','AI_assisted':True,'independent_human_approval':False,
  'documents':{a:{str(f.relative_to(A/'materials'/a/'candidate')):sha(f) for f in (A/'materials'/a/'candidate').rglob('*.md')} for a in ['D','T']},
  'requirements':[
   {'topic':'coalescing','support':'Both original tasks require latest write after 120ms quiet interval, later bursts and unchanged interfaces.'},
   {'topic':'departure settlement','support':'Both README files explicitly require the departed last accepted edit available through store before close/open returns.'},
   {'topic':'navigation priority','support':'Both README files define later-started navigation precedence, with open(B)->save A->open(C) and inner close examples.'},
   {'topic':'badge retirement','support':'JS save-status.js comments specify badge retirement from start of close/open, separately from document persistence. Python host API states token removal skips removed subscribers; original Visit.depart removes badge before output.'},
   {'topic':'batch reentry','support':'Current trailing utility clears the old pending work before calling work; preserving subsequent bursts and inline onSaved edits forbids erasing a newly queued batch.'},
   {'topic':'preview counterexample','support':'Both README files retain 40ms transient preview and discard unpublished query on hide; tasks explicitly exclude changing this adjacent consumer.'}],
  'no_reference_patch_in_reflection':True,'no_policy_gap_found':True,
  'limits':'Author outcome-informed family, Python synthetic derivation and scaffold reuse. Neither current-model headroom nor independent new-source generalization is established.'}
 save(A/'policy-audit.json',policy)
 save(A/'selection.json',{'selected_before_model_calls':True,'cases':[{k:c[k] for k in ['alias','case','independent_unit_id','exposure']} for c in cases],
  'cluster':'draft-autosave-handoff','test_parent':'draft-autosave-handoff-order-example-vanilla',
  'reason':'Direct documented parent/port pair; explicit visible departure and reentrant priority policy; new source unit relative to transfer experiment, no target-model difficulty claim.',
  'rejected_options_before_freeze':['Download Vue pair already all passed in prior Terra study','Less explicit draft port lacks the same direct boundary-return wording; choose the policy-explicit parent/port'],
  'no_paid_screening':True,'no_case_change_after_results':True})
 save(A/'protocol.json',{'scope':'One fixed new training/test pair; same-source cross-language experiment, no independent generalization',
  'models':{'extract':['gpt-6-sol','low',12,600],'repair':['gpt-5.6-terra','low',24,600],'reflect':['gpt-5.6-terra','medium',12,600]},
  'maximum_sessions':11,'maximum_requests':228,'concurrency':1,'no_retry':True,
  'schedule':['D-analysis','AUTO-1','AUTO-2','reflection','development-1','development-2','T-analysis','test-B1','test-A1','test-A2','test-B2'],
  'reflection':'One fresh rules/unresolved object only; program locks positive applicable mechanisms to source-checked D analysis. No old experience seed.',
  'admission':'At least one evidenced relation/overall improvement and no unsupported policy; record all regressions, no both-full-pass requirement',
  'stop':'Two AUTO both pass: no experience, stop. Invalid/unsupported candidate or no development improvement: stop before test. First infrastructure/meter/archive/isolation/input anomaly: stop without retry.',
  'normal_failure':'Continue fixed scheduled slot; no replacement, third case or hidden search',
  'test':'B1,A1,A2,B2 from independent original copies; classify/route only after training freeze; unknown/unmet predicates fall back to AUTO',
  'no_test_learning':True,'no_extra_judge_or_connection_probe':True,'production_update':False,'create_commit':False})
 pilot.preflight()
 # Also pin all reused historical materials; the generic preflight already
 # excludes its own manifest and mutable schedule/controller journals.
 frozen=read(A/'initial-freeze.json');frozen['files'].update(read(A/'initial-state.json')['predecessor_files'])
 save(A/'initial-freeze.json',frozen);runner.verify(frozen['files'])
 print('PREPARED fixed pair, model calls 0',flush=True)

if __name__=='__main__':main()
