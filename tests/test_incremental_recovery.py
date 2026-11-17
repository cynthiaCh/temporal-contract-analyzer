import importlib.util,json,tempfile,unittest,hashlib
from pathlib import Path
from copy import deepcopy
from test_tempoevo_v4 import Backend
from temporal_contract_analyzer.tempoevo_v4 import Trajectory
from temporal_contract_analyzer import compact_experience as compact,experience_memory as memory,experience_approval as approval
from temporal_contract_analyzer.core import EvidenceError
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('recovery',ROOT/'tools/tempoevo-docker/recover_incremental.py');recovery=importlib.util.module_from_spec(spec);spec.loader.exec_module(recovery)
class IncrementalRecoveryTests(unittest.TestCase):
 def test_extract_recovery_reuses_accepted_action_and_spent_request(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);source=root/'source';source.mkdir();(source/'main.py').write_text('value = 0\n');store=root/'store';memory.initialize(store)
   cfg=dict(task='Preserve accepted work.',candidate=str(source),store=str(store),mode='learning',condition='contract',training_evaluator=dict(command=['fixture']),visible_evaluator=dict(command=['fixture']))
   old=Trajectory(root/'old');old.prepare(cfg);state=old.run(Backend(invalid='extract'),execute=True)
   self.assertTrue(state['training_accepted']);self.assertEqual(state['status'],'execution_invalid');old_bytes=(old.root/'state.json').read_bytes()
   cfg['candidate']=str(old.root/'original');new=root/'new';lineage=recovery.import_completed(old.root,new,cfg);self.assertTrue(lineage['extract_only'])
   backend=Backend();backend.gold_calls=0;evaluate=backend.evaluate
   def checked(*args):backend.gold_calls+=1;return evaluate(*args)
   backend.evaluate=checked
   result=Trajectory(new).run(backend,execute=True)
   self.assertEqual(result['status'],'passed',result.get('error'));self.assertEqual([c[0] for c in backend.calls],['extract']);self.assertEqual(backend.calls[0][3]['requests'],11);self.assertEqual(backend.gold_calls,0)
   self.assertEqual(len(result['attempts']),1);self.assertEqual((old.root/'state.json').read_bytes(),old_bytes)
 def test_provisional_evidence_is_archival_without_memory_admission(self):
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'library';path.mkdir();(path/'entries.json').write_text(json.dumps(dict(schema_version=compact.VERSION,experiences=[dict(id='seed',title='Seed',labels=['I'],requires=['entry_snapshot'],excludes=[],applicability='Entry identity.',event_relation='Capture entry.',preservation='Retain work.',exclusion='Check source.',verification='Check identity.',review=dict(reviewer='Fixture',decision='accept',at='2026-11-17'))])))
   before=approval.freeze(path);target=deepcopy(memory.records(path)[0]);target.update(id='online-fixture',sha256='1'*64)
   exp={k:deepcopy(target[k]) for k in ['labels','requires','excludes','rules']};record=dict(experience=exp,related_experiences=[target],reflection_update=dict(operation='evidence',target_sha256s=[target['sha256']]))
   value=compact.publish_candidate(path,record);self.assertEqual(value['publication_kind'],'provisional_evidence_proposal');self.assertEqual(approval.freeze(path),before)
   record['experience']['rules'][0]['body']='Changed rule'
   with self.assertRaises(EvidenceError):compact.publish_candidate(path,record)
if __name__=='__main__':unittest.main()
