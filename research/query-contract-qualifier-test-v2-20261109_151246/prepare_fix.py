"""One affected extraction and four fixed slots; training and experience unchanged."""
import json,sys,shutil,subprocess,tempfile,unittest,time
from pathlib import Path
sys.dont_write_bytecode=True
A=Path(__file__).resolve().parent;sys.path.insert(0,str(A))
import pilot_test as run
from archive import save,sha
from citations import catalog,schema,fingerprint,INSTRUCTIONS
from qualifiers import cues,GUIDANCE,coverage
P=run.P
def read(p):return json.loads(Path(p).read_text())

def main():
 assert not (A/'initial-freeze.json').exists()
 run.runner.verify(read(A/'initial-state.json')['predecessor_files'])
 c=read(A/'case.json');src=Path(c['source_case'])
 assert run.runner.backend.hashes(A/'materials/T/candidate')==c['candidate_files']==run.runner.backend.hashes(src/'base')
 assert run.runner.backend.hashes(src/'oracle')==c['oracle_files']
 assert sha(A/'materials/T/task.md')==c['task_sha256']
 assert (A/'experience/experience.md').read_bytes()==(P/'development/experience.md').read_bytes()
 assert (A/'frozen-library.json').read_bytes()==(P/'frozen-library.json').read_bytes()
 calibrations=[]
 for folder in sorted((A/'calibration/T').iterdir()):
  rec=read(folder/'receipt.json');score=read(folder/'stdout.json')
  assert rec['score_valid'] and rec['verdict']==score['verdict'] and not rec['runtime_errors']
  assert run.runner.backend.hashes(Path(rec['command'][2]))==rec['candidate_before']
  calibrations.append({'variant':folder.name,'verdict':score['verdict'],'receipt_sha256':sha(folder/'receipt.json'),
    'oracle_version_correspondence':'Original cohort oracle hash matches current case; receipt itself omits oracle hashes, not fabricated.',
    'rerun':False})
 save(A/'calibration-reuse.json',calibrations)
 sources=run.sources();cat=catalog(sources);assert fingerprint(cat)==c['source_catalog_sha256']
 save(A/'materials/T/source-catalog.json',cat);save(A/'materials/T/extraction.schema.json',schema(cat,read(A/'extraction.schema.json')))
 ast=read(A/'materials/T/ast.json')
 public={'TASK':sources['TASK'],'taxonomy':read(A/'taxonomy.json')['classes'],'predicates':run.PREDICATES,
  'AST':{'status':ast['status'],'summary':ast['summary'],'limitations':ast['limitations']},
  'source_catalog':cat,'qualifier_cues':cues(sources['TASK'],cat)}
 prompt='TASK is virtual text in this prompt, not /workspace/TASK. Read current candidate files separately.\n'+GUIDANCE+INSTRUCTIONS+json.dumps(public,ensure_ascii=False)
 assert c['case'] not in prompt and c['independent_unit_id'] not in prompt
 assert 'rejection.json' not in prompt and 'expected_class' not in prompt
 (A/'materials/T/preanalysis-prompt.md').write_text(prompt)
 save(A/'materials/T/qualifier-cues.json',public['qualifier_cues'])
 old=read(A/'historical-extraction/rejection.json')
 replay=coverage(old['candidate_visible_task'],old['raw_automatic_contract'],cat)
 assert any('live' in r['missing_literal_words'] for r in replay['findings'])
 save(A/'offline-old-failure-replay.json',{'fixture_origin':'Exact historical failure; no new model candidate','old_rejection_retained':True,
  'raw_failure_response_sha256':sha(A/'historical-extraction/raw-answer.txt'),'advisory_coverage':replay,
  'not_a_semantic_proof':'Lexical flags alone do not prove a violation; old AI-assisted rejection is retained separately.'})
 save(A/'protocol.json',{'version':'qualifier-preserving-extraction-v2','parent_stopped_batch':str(P),
  'authorization':'User fix: repair generic extraction qualifier loss; one new affected T analysis then four fixed test slots after semantic admission.',
  'scope':'Only query-paused-initial-fetch-10266-python3 testing; no new train/reflect/baseline or case replacement',
  'models':{'extract':['gpt-6-sol','low',12,600],'repair':['gpt-5.6-terra','low',24,600]},
  'maximum_sessions':5,'maximum_requests':108,'concurrency':1,'no_retry':True,'schedule':run.ORDER,
  'sampling_randomness_controlled':False,'fixed_experience_text_sha256':sha(A/'experience/experience.md'),
  'extraction_fix':'Generic action/modifier/negation scope instructions plus deterministic source-only lexical cue contexts. Existing typed output and exact source-ID normalization unchanged.',
  'coverage_lint':'Advisory only; synonyms/translations and semantic entailment require execution-agent review; never rewrite or automatically approve/reject Contract.',
  'classifier_input':'Only original task, candidate-visible docs/source, AST, taxonomy, predicates and exact source cue/catalog. No old Contract/error critique, training outcome/experience, grader or reference patch.',
  'test_conditions':'A original task/source + one fixed admitted automatic Contract + public requirements. B only appends 0/1 exact frozen routed experience. Fallback identical inputs retained.',
  'freeze':'Experimental inputs/code guarded before new extraction; admitted Contract/route/A-B prompts frozen before first repair. Report generator is derived reporting code, versioned in final artifact manifest, not an actor input.',
  'normal_failure':'Continue fixed next slot','stop':'Core semantic conflict or first service/archive/isolation/input/meter anomaly: archive and stop; no retries/replacement.',
  'production_update':False,'create_commit':False,'no_reflection_or_extra_judge':True,'no_learning_from_test':True})
 save(A/'actual-schedule.json',[])
 import test_toolflow,test_runtime_v2,test_citations,test_source_proof,test_qualifiers
 suite=unittest.TestSuite()
 for m in [test_toolflow,test_runtime_v2,test_citations,test_source_proof,test_qualifiers]:suite.addTests(unittest.TestLoader().loadTestsFromModule(m))
 with (A/'offline-tests.log').open('w') as f:result=unittest.TextTestRunner(stream=f,verbosity=2).run(suite)
 assert result.wasSuccessful()
 with tempfile.TemporaryDirectory(prefix='qualifier-test-offline-') as td:
  rt=Path(td);folder=rt/'fixture';folder.mkdir();(folder/'archive').mkdir();shutil.copytree(A/'materials/T/candidate',folder/'workspace');sock=rt/'control';sock.mkdir()
  for phase in ['extract','repair']:
   cmd=run.runner.command('offline-'+phase,folder,phase,c,runtime=rt,socket_dir=sock,copy_auth=False)
   assert cmd[cmd.index('-m')+1]==('gpt-6-sol' if phase=='extract' else 'gpt-5.6-terra')
   assert cmd[cmd.index(str(folder/'workspace'))-1]==('--ro-bind' if phase=='extract' else '--bind')
   test="set -eu\ncat /workspace/src/workflow.py\ntest ! -e /home/sribd\n/usr/bin/python3 -B -c 'import ast,pathlib; ast.parse(pathlib.Path(\"/workspace/src/workflow.py\").read_text())'\n/runtime/node --version"
   z=subprocess.run(cmd[:cmd.index('/opt/codex')]+['/bin/sh','-c',test],capture_output=True,timeout=30)
   assert z.returncode==0 and (A/'materials/T/candidate/src/workflow.py').read_bytes() in z.stdout
 files=run.frozen_input_files(A)
 # Report rendering is not an experimental input. Keep its initial hash as a
 # reporting provenance item instead of a run-stop condition.
 files.pop(str(A/'report.py'),None)
 files.update(read(A/'initial-state.json')['predecessor_files'])
 for name in ['base','oracle']:
  files.update({str(f):sha(f) for f in (src/name).rglob('*') if f.is_file()})
 files[str(Path.home()/'.codex/config.toml')]=sha(Path.home()/'.codex/config.toml')
 save(A/'initial-freeze.json',{'time':time.time(),'files':files,'offline_checks':result.testsRun,
  'new_calibration_calls':0,'new_model_calls':0,'reporting_code_initial_sha256':sha(A/'report.py')})
 run.check();print('OFFLINE PASS',result.testsRun,'checks, qualifier fix and frozen query experience',flush=True)

if __name__=='__main__':main()
