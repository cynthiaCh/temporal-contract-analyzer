"""Verify genuine same-input low-effort failures before any fresh model call."""
import json,shutil,sys
from pathlib import Path
sys.dont_write_bytecode=True
A=Path(__file__).resolve().parent;sys.path.insert(0,str(A))
import pilot
from archive import save,sha
from citations import catalog,schema,fingerprint,INSTRUCTIONS
from toolflow import PREDICATES
from evidence import verify_ledger
B=A.parent/'two-class-experience-pilot-v2r4-20261108_221657'

def read(p):return json.loads(Path(p).read_text())
def main():
 assert not (A/'initial-freeze.json').exists()
 pilot.runner.verify(read(A/'initial-state.json')['predecessor_files'])
 cases=read(A/'cases.json');base_contract=(A/'derived/D/automatic-contract.md').read_text()
 expected=pilot.maintenance_prompt((A/'materials/D/task.md').read_text(),base_contract)
 assert expected==(A/'development/AUTO-prompt.md').read_text()
 evidence=[]
 for i,r in enumerate(read(A/'development/baselines.json'),1):
  arc=A/'runs'/r['slot']/'archive';cfg=read(arc/'input/config.json');score=read(arc/'score/stdout.json')
  assert cfg['model']=='gpt-5.6-terra' and cfg['effort']=='low' and cfg['requests_per_session']==24 and cfg['seconds_per_session']==600
  assert r['infrastructure_valid'] and r['candidate_complete'] and r['scoring_admissible'] and r['scoring_status']=='COLLECTED' and r['scored_candidate_unchanged']
  assert (arc/'input/actual-prompt.md').read_text()==expected
  assert pilot.runner.backend.hashes(arc/'input/original')==cases[0]['candidate_files']
  assert read(arc/'score/receipt.json')['oracle_sha256']==cases[0]['oracle_files']
  assert score['missing_required_effects']==['cached-paused-background','cached-later-consumption']
  assert read(A/f'training/inputs/auto{i}/score.json')==score
  assert (A/f'training/inputs/auto{i}/patch.diff').read_bytes()==(arc/'patch.diff').read_bytes()
  evidence.append({'origin':r['reuse_origin'],'source_receipt_sha256':sha(arc/'receipt.json'),'actual_started_at':r.get('started_at'),
   'same_candidate_task_auto_prompt_model_effort_tools_budget_scorer':True,'whole_task':'UNDERREACH','satisfied':27,'total':29,
   'failures':score['missing_required_effects'],'reused_not_rerun_or_recharged':True})
 assert sha(A/'read_policy.py')==sha(B/'read_policy.py') and sha(A/'request_guard.py')==sha(B/'request_guard.py')
 verify_ledger(A/'training',read(A/'training/evidence-ledger.json'))
 for c in cases:
  alias=c['alias'];src=Path(c['source_case']);root=A/'materials'/alias/'candidate'
  assert pilot.runner.backend.hashes(root)==c['candidate_files']==pilot.runner.backend.hashes(src/'base')
  assert pilot.runner.backend.hashes(src/'oracle')==c['oracle_files']
  assert sha(A/'materials'/alias/'task.md')==c['task_sha256']
  cat=catalog(pilot.sources(alias));save(A/'materials'/alias/'source-catalog.json',cat)
  save(A/'materials'/alias/'extraction.schema.json',schema(cat,read(A/'extraction.schema.json')))
  c['extraction_schema']=str(A/'materials'/alias/'extraction.schema.json');c['source_catalog_sha256']=fingerprint(cat)
  ast=read(A/'materials'/alias/'ast.json')
  public={'TASK':pilot.sources(alias)['TASK'],'taxonomy':read(A/'taxonomy.json')['classes'],'predicates':PREDICATES,
   'AST':{'status':ast['status'],'summary':ast['summary'],'limitations':ast['limitations']},'source_catalog':cat}
  text='TASK is virtual text supplied here, not /workspace/TASK; read candidate files separately.\n'+INSTRUCTIONS+json.dumps(public,ensure_ascii=False)
  assert all(x['case'] not in text for x in cases)
  (A/'materials'/alias/'preanalysis-prompt.md').write_text(text)
  for folder in (A/'calibration'/alias).iterdir():
   rec=read(folder/'receipt.json');s=read(folder/'stdout.json')
   assert rec['score_valid'] and rec['verdict']==s['verdict'] and not rec['runtime_errors']
   assert pilot.runner.backend.hashes(Path(rec['command'][2]))==rec['candidate_before']
  c['calibration_version_note']='Per-score receipts omit oracle hash; associated original cohort pins full oracle hash, identical to current case and reused scored-baseline receipts. Exact version correspondence was recorded and rechecked; no historical score rerun.'
 save(A/'cases.json',cases);save(A/'headroom-evidence.json',evidence)
 save(A/'selection.json',{'training':cases[0]['case'],'test':cases[1]['case'],'cluster':'query-paused-initial-fetch-10266',
  'reason':'Use verified current-version AUTO/low failures, not unmeasured complexity or another-model failures. Both correct-Contract JS baselines are 27/29.',
  'prior_python_failure_evidence_excluded':'Historical Python automatic Contract overrestricted no-live-signal to no execution. It is not reused or claimed to prove correct-Contract difficulty.',
  'exposure':'Both cases extensively exposed. Former JS training/Python test roles retained; fresh learner sees only JS training evidence, no test traces/patches/scores.',
  'no_published_independent_generalization':True,'pair_fixed_before_new_model_calls':True})
 save(A/'protocol.json',{'scope':'Known-hard JS training with same-cluster Python test; same-source exploratory, not unseen',
  'reused':['Source-checked correct JS automatic Contract and classification','Two exact-condition valid 27/29 AUTO baselines','Repaired evidence ledger without old experience','22 current-version calibrations'],
  'new_schedule':['reflection','development-1','development-2','T-analysis','test-B1','test-A1','test-A2','test-B2'],
  'maximum_new_sessions':8,'maximum_new_requests':168,'concurrency':1,'no_retry':True,
  'models':{'extract':['gpt-6-sol','low',12,600],'repair':['gpt-5.6-terra','low',24,600],'reflect':['gpt-5.6-terra','medium',12,600]},
  'same_public_inputs':'Development uses byte-identical historical AUTO prompt, original source and scorer; only exact frozen new experience is appended.',
  'reflection':'One rules/unresolved object, no tools/seed/reference patch. Typed existing-ID constraints; applicability derived only from reviewed D mechanisms.',
  'admission':'At least one grounded target/overall improvement, no unsupported policy, record all regressions; no both-full-pass requirement',
  'test':'Only after training library freeze: independently analyze current Python source, route conservatively and execute B1/A1/A2/B2 with shared fixed Contract.',
  'stop':'Invalid or unsupported candidate, no development improvement, or first infrastructure/archive/input/isolation/meter anomaly. No retries/replacement/next candidate.',
  'production_update':False,'create_commit':False})
 pilot.approved('D');pilot.preflight()
 frozen=read(A/'initial-freeze.json');frozen['files'].update(read(A/'initial-state.json')['predecessor_files'])
 # Preserve immutable input ledgers separately. The predeclared reflection
 # builder derives augmented ledger/feedback, protected by reflection-freeze.
 for name in ['evidence-ledger.json','feedback.json']:
  source=A/'training-source'/name;source.parent.mkdir(exist_ok=True)
  shutil.copy2(A/'training'/name,source)
  frozen['files'].pop(str(A/'training'/name),None);frozen['files'][str(source)]=sha(source)
 save(A/'initial-freeze.json',frozen)
 pilot.check();print('HEADROOM VERIFIED: two exact-condition 27/29 AUTO baselines; no fresh model or scoring calls',flush=True)

if __name__=='__main__':main()
