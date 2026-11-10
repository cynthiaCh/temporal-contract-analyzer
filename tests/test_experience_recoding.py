"""Synthetic annotation-interface tests, not classifier accuracy or repair evidence."""
from copy import deepcopy
from contextlib import redirect_stdout,redirect_stderr
from io import StringIO
import json
import os
from pathlib import Path
import unittest

import test_experience_memory as fixtures
from temporal_contract_analyzer import experience_memory as memory,experience_approval as approval,taxonomy
from temporal_contract_analyzer.experience_recoding import candidate
from temporal_contract_analyzer.core import EvidenceError,sha


class RecodingTests(unittest.TestCase):
    def setUp(self):
        self.f=fixtures.MemoryTests('test_storage_preserves_single_source_body_and_evidence')
        self.f.setUp();self.addCleanup(self.f.doCleanups)
        payload=deepcopy(self.f.payload)
        payload.update(taxonomy_version=memory.LEGACY_TAXONOMY,labels=['T3'])
        self.parent=memory.add(self.f.store,payload,[self.f.source])
        self.source=self.f.root/'visible-source.py';self.source.write_text('accepted = True\n')
        anchor=dict(file=str(self.source),sha256=sha(self.source.read_bytes()),line=1,quote='accepted = True')
        self.review=dict(schema_version='experience-source-label-review-v1',taxonomy_version=taxonomy.VERSION,
            taxonomy_sha256=taxonomy.fingerprint(),parent_sha256=self.parent['sha256'],body_sha256=self.parent['body_sha256'],
            reviewer='SYNTHETIC_AI_REVIEW_FIXTURE',AI_assisted=True,independent_human_approval=False,
            scope='taxonomy_only_no_policy_or_effect_claim',sources=[dict(file=str(self.source),sha256=anchor['sha256'],kind='original_source')],
            rules=[dict(rule_id=r['id'],body_sha256=memory.digest(r['body']),labels=[dict(code=code,basis='source_fact',
                reason='Synthetic field-validation fixture, not a supported real-world label.',evidence=[anchor]) for code in ('O','I')],notes=[])
                for r in self.parent['rules']],
            unassigned_labels=[dict(code=code,reason='Not established in synthetic fixture.') for code in taxonomy.CODES if code not in ('O','I')],
            limitations=['Synthetic interface fixture; no ground truth or expert acceptance.'])
        self.path=self.f.root/'label-review.json'

    def put(self,review=None):
        self.path.write_text(json.dumps(self.review if review is None else review))

    def test_explicit_multilabel_child_preserves_rules_and_stays_inactive(self):
        self.put();child=candidate(self.f.store,self.parent['sha256'],self.path,'seven-v1')
        self.assertEqual(child['labels'],['O','I'])
        self.assertEqual(child['parent_sha256'],self.parent['sha256'])
        for key in ('rules','requires','excludes','body_sha256'):self.assertEqual(child[key],self.parent[key])
        self.assertEqual(child['review']['status'],'candidate')
        self.assertEqual(approval.active(self.f.store),[])

    def test_no_mapping_or_score_metadata_and_no_fabricated_human_approval(self):
        for bad in (dict(self.review,primary_class='T3'),dict(self.review,case_id='shortcut'),
                    dict(self.review,historical_score=1),dict(self.review,independent_human_approval=True)):
            self.put(bad)
            with self.assertRaises(EvidenceError):candidate(self.f.store,self.parent['sha256'],self.path,'bad')
        self.assertEqual(len(memory.records(self.f.store)),1)

    def test_invalid_citations_labels_or_changed_body_reject(self):
        for kind in ('quote','line','body','legacy_label','duplicate','missing_rule','score_source'):
            bad=deepcopy(self.review)
            if kind=='quote':bad['rules'][0]['labels'][0]['evidence'][0]['quote']='not present'
            if kind=='line':bad['rules'][0]['labels'][0]['evidence'][0]['line']=99
            if kind=='body':bad['rules'][0]['body_sha256']='0'*64
            if kind=='legacy_label':bad['rules'][0]['labels'][0]['code']='T3'
            if kind=='duplicate':bad['rules'][0]['labels'].append(bad['rules'][0]['labels'][0])
            if kind=='missing_rule':bad['rules'].pop()
            if kind=='score_source':bad['sources'][0]['kind']='historical_score'
            self.put(bad)
            with self.subTest(kind=kind),self.assertRaises(EvidenceError):
                candidate(self.f.store,self.parent['sha256'],self.path,'bad')

    def test_changed_source_and_taxonomy_are_not_silently_corrected(self):
        self.put();self.source.write_text('changed\n')
        with self.assertRaises(EvidenceError):candidate(self.f.store,self.parent['sha256'],self.path,'bad')
        self.source.write_text('accepted = True\n');bad=deepcopy(self.review);bad['taxonomy_sha256']='0'*64;self.put(bad)
        with self.assertRaises(EvidenceError):candidate(self.f.store,self.parent['sha256'],self.path,'bad')

    def test_relative_and_absolute_review_paths_have_identical_derivations(self):
        self.put()
        absolute=candidate(self.f.store,self.parent['sha256'],self.path,'seven-v1',install=False)
        relative=candidate(self.f.store,self.parent['sha256'],Path(os.path.relpath(self.path,Path.cwd())),
                           'seven-v1',install=False)
        self.assertEqual(absolute,relative)

    def test_cli_import_and_label_intersection_share_one_store(self):
        from temporal_contract_analyzer.cli import main
        self.put()
        with redirect_stdout(StringIO()),redirect_stderr(StringIO()):
            self.assertEqual(main(['experience-memory','recode',str(self.path),'--parent',self.parent['sha256'],
                '--version','seven-v1','--store',str(self.f.store)]),0)
        matching=memory.search(self.f.store,'entry',required_labels=['O','I'])['results']
        self.assertEqual(len(matching),1)
        self.assertFalse(matching[0]['expert_active'])
        self.assertEqual(memory.search(self.f.store,'entry',required_labels=['O','B'])['results'],[])
        output=StringIO()
        with redirect_stdout(output):
            self.assertEqual(main(['experience-memory','list','--label','O','--label','I','--store',str(self.f.store)]),0)
        self.assertEqual(len(json.loads(output.getvalue())),1)
        with self.assertRaises(EvidenceError):memory.search(self.f.store,'entry',required_labels=['T3'])


if __name__=='__main__':unittest.main()
