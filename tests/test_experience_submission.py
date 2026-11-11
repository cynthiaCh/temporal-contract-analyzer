"""Synthetic candidate handoff tests; no real approval, model or effect evidence."""
from contextlib import redirect_stdout
from copy import deepcopy
from io import StringIO
import json
from pathlib import Path
import threading
import unittest
from urllib.request import build_opener, ProxyHandler

import test_experience_memory as fixtures
from temporal_contract_analyzer import experience_memory as memory, experience_approval as approval
from temporal_contract_analyzer import experience_screening as screening
from temporal_contract_analyzer.experience_submission import submit
from temporal_contract_analyzer.memory_review import ReviewServer
from temporal_contract_analyzer.core import EvidenceError
from temporal_contract_analyzer.cli import main


class SubmissionTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixtures.MemoryTests('test_storage_preserves_single_source_body_and_evidence')
        self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
        self.source=self.fixture.store
        self.parent=self.fixture.add()
        payload=deepcopy(self.fixture.payload)
        payload.update(version='synthetic-development',parent_sha256=self.parent['sha256'])
        payload['review']['status']='candidate'
        payload['rules'][1]['body']='Capture accepted entry identity before the callback begins.'
        self.child=memory.add(self.source,payload,[self.fixture.source])
        def outcome(passed):
            return dict(verdict='PASS' if passed else 'UNDERREACH',behavior_states={'target':passed,'preserved':True})
        self.screen=dict(schema_version=screening.VERSION,candidate_sha256=self.child['sha256'],
            origin='synthetic_fixture_not_model_or_effect_evidence',
            source=dict(source_unit='synthetic-source',critical_relations=['preserved'],
                old=[outcome(False)]*2,new=[outcome(True)]*2),
            transfers=[dict(source_unit='synthetic-transfer-'+str(i),critical_relations=['preserved'],
                prompts_identical=True,old=[outcome(False)]*2,new=[outcome(False)]*2) for i in (1,2)],
            budget=dict(within=True,complete=True,requests=13,cap=300,unknown_requests=0))
        screening.save(self.source,self.screen)
        self.usage=dict(batch_id=self.child['version'],cases={'source':dict(case_id='synthetic',
            lineage=dict(source_unit='synthetic-source',derived_from=[],prior_exposure='Synthetic fixture only.'))})
        (self.source/'development-usage.json').write_text(json.dumps([self.usage]))
        self.target=self.fixture.root/'review-memory';memory.initialize(self.target)
        (self.target/'decision.lock').touch()

    def snapshot(self,store):
        return {str(p.relative_to(store)):p.read_bytes() for p in store.rglob('*') if p.is_file()}

    def test_exact_record_evidence_pending_screen_and_exposure_without_approval(self):
        # A decision in the source store must never become a target approval.
        approval.decide(self.source,self.child['sha256'],dict(reviewer='SYNTHETIC_REVIEWER',
            decision='accept',scope='exploratory',reason='Synthetic approval transport fixture.',
            rules=[dict(rule_id=r['id'],supported=True,reason='Synthetic.') for r in self.child['rules']]))
        source_before=self.snapshot(self.source);active=(self.target/'active.json').read_bytes()
        result=submit(self.source,self.target,self.child['sha256'])
        self.assertEqual(len(result['added_records']),2)
        self.assertEqual(memory.records(self.target),sorted([self.parent,self.child],key=lambda b:b['sha256']))
        for bundle in (self.parent,self.child):
            name=bundle['sha256']+'.json'
            self.assertEqual((self.target/'records'/name).read_bytes(),(self.source/'records'/name).read_bytes())
            for src in bundle['audit']['sources']:
                self.assertEqual((self.target/'sources'/src['sha256']).read_bytes(),(self.source/'sources'/src['sha256']).read_bytes())
        self.assertEqual(screening.read(self.target,self.child['sha256']),screening.read(self.source,self.child['sha256']))
        self.assertEqual(result['screening_status'],'pending')
        self.assertEqual(json.loads((self.target/'development-usage.json').read_text()),[self.usage])
        self.assertEqual(approval.decisions(self.target),[])
        self.assertEqual((self.target/'active.json').read_bytes(),active)
        self.assertEqual(approval.freeze(self.target)['entries'],[])
        self.assertEqual(self.snapshot(self.source),source_before)

    def test_idempotent_submission_and_no_unrelated_exposure_copy(self):
        usage=[dict(batch_id='unrelated',cases={}),self.usage]
        (self.source/'development-usage.json').write_text(json.dumps(usage))
        submit(self.source,self.target,self.child['sha256']);before=self.snapshot(self.target)
        result=submit(self.source,self.target,self.child['sha256'])
        self.assertTrue(result['already_recorded'])
        self.assertEqual(result['added_records'],[])
        self.assertEqual(self.snapshot(self.target),before)
        self.assertEqual(json.loads((self.target/'development-usage.json').read_text()),[self.usage])

    def test_tampered_source_fails_before_publication(self):
        (self.source/'sources'/self.child['audit']['sources'][0]['sha256']).write_bytes(b'TAMPERED')
        before=self.snapshot(self.target)
        with self.assertRaises(EvidenceError):submit(self.source,self.target,self.child['sha256'])
        self.assertEqual(self.snapshot(self.target),before)

    def test_immutable_identity_conflict_does_not_partially_copy(self):
        sources=[self.source/'sources'/s['sha256'] for s in self.parent['audit']['sources']]
        memory.add(self.target,self.parent,sources)
        other={k:deepcopy(v) for k,v in self.child.items() if k in memory.FIELDS}
        other['rules'][1]['body']='A different synthetic policy under the same version.'
        memory.add(self.target,other,sources)
        before=self.snapshot(self.target)
        with self.assertRaisesRegex(EvidenceError,'version conflicts'):
            submit(self.source,self.target,self.child['sha256'])
        self.assertEqual(self.snapshot(self.target),before)

    def test_conflicting_screen_does_not_publish_record(self):
        path=self.target/'screening'/(self.child['sha256']+'.json');path.parent.mkdir()
        path.write_text(json.dumps(dict(candidate_sha256=self.child['sha256'],different=True)))
        before=self.snapshot(self.target)
        with self.assertRaisesRegex(EvidenceError,'Screening already exists'):
            submit(self.source,self.target,self.child['sha256'])
        self.assertEqual(self.snapshot(self.target),before)

    def test_review_page_sees_record_and_review_only_is_allowed_while_pending(self):
        submit(self.source,self.target,self.child['sha256'])
        server=ReviewServer(self.target);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            with build_opener(ProxyHandler({})).open(server.url+'/api/library',timeout=5) as response:
                row=next(r for r in json.load(response)['records'] if r['sha256']==self.child['sha256'])
            self.assertFalse(row['reviewed']);self.assertFalse(row['active']);self.assertFalse(row['default_eligible'])
            approval.decide(self.target,self.child['sha256'],dict(reviewer='SYNTHETIC_REVIEWER',decision='accept',
                scope='exploratory',reason='Synthetic review-only fixture.',
                rules=[dict(rule_id=r['id'],supported=True,reason='Synthetic.') for r in self.child['rules']]))
            self.assertEqual(len(approval.decisions(self.target)),1)
            self.assertEqual(approval.active(self.target),[])
            with self.assertRaises(EvidenceError):
                approval.activate(self.target,self.child['sha256'],None,'SYNTHETIC_REVIEWER','Synthetic blocked activation.')
        finally:
            server.shutdown();server.server_close();thread.join(3)

    def test_cli_submit_and_wrong_store_are_explicit(self):
        out=StringIO()
        with redirect_stdout(out):
            self.assertEqual(main(['experience-memory','submit',self.child['sha256'],
                '--from-store',str(self.source),'--store',str(self.target)]),0)
        self.assertEqual(json.loads(out.getvalue())['candidate_sha256'],self.child['sha256'])
        with self.assertRaises(EvidenceError):submit(self.source,self.source,self.child['sha256'])
        with self.assertRaises(EvidenceError):submit(self.source,self.target,'f'*64)

