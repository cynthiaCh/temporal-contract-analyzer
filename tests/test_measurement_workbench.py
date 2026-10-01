import copy
import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from temporal_contract_analyzer import archive, cli, measurement
from temporal_contract_analyzer.core import EvidenceError, sha


SOURCE = '''export async function visit(channel) {
  channel.listen(message => publish(message));
  channel.connect();
  await refresh();
  publish('ready');
}
'''


class MeasurementWorkbenchTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.project = self.root/'project'; self.project.mkdir()
        (self.project/'channel.js').write_text(SOURCE, encoding='utf-8')
        self.store = self.root/'reports'
        env = patch.dict(os.environ, {'TCA_CONFIG': str(self.root/'config.json')})
        env.start(); self.addCleanup(env.stop)
        self.meta = archive.scan_path(self.project, self.store)['archive']

    def document(self):
        source_hash = sha(SOURCE.encode('utf-8'))
        return {
            'schema_version': measurement.SCHEMA,
            'workflow_status': 'final',
            'source_binding': {'report_id': self.meta['report_id'], 'input_sha256': self.meta['input_sha256']},
            'authorship': {'authors': ['author-1'], 'target_outcomes_seen': False,
                           'note': 'Authored from the archived source before outcome inspection.'},
            'conditions': [{
                'id': 'source-only', 'label': 'Archived candidate source', 'variant': 'ungranted',
                'materials': [],
                'policy': {'classification': 'same', 'rationale': 'Only one consumer policy is in scope.',
                           'consumers': [{'id': 'visit', 'name': 'visit',
                                          'policy': 'Register before connecting.',
                                          'evidence': ['e-listen-first']}], 'contrasts': []},
            }],
            'evidence_units': [{
                'id': 'e-listen-first', 'semantic_key': 'listener-before-connect', 'role': 'ordering-rule',
                'fact': 'The listener is registered before connect is called.',
                'sources': [{'kind': 'candidate', 'path': 'channel.js',
                             'anchor': 'channel.listen', 'sha256': source_hash,
                             'conditions': ['source-only']}],
            }],
            'sites': [{
                'id': 'commit-connect', 'kind': 'commit', 'path': 'channel.js',
                'anchor': 'channel.connect()', 'sha256': source_hash,
                'description': 'Connecting may synchronously publish the initial value.',
            }],
            'witness_artifacts': [{
                'id': 'artifact-order-review', 'kind': 'review-note',
                'label': 'Manual source-order review',
                'content': 'channel.listen appears before channel.connect in the archived visit function.',
                'sha256': sha('channel.listen appears before channel.connect in the archived visit function.'.encode('utf-8')),
            }],
            'obligations': [{
                'id': 'listen-before-connect',
                'statement': 'Install the listener before connecting.',
                'confirmation': {'status': 'confirmed', 'actor': 'author-1',
                                 'note': 'Confirmed from the call order and intended initial delivery.'},
                'predicate': {
                    'activation': 'A visit starts for a channel.',
                    'identity': 'The listener and connection belong to the same visit.',
                    'deadline': 'Registration completes before connect begins.',
                    'continuing_work': 'The listener remains active for the visit.',
                    'forbidden_effects': 'The synchronous initial delivery must not be lost.',
                },
                'witnesses': [{'id': 'w-order', 'kind': 'review', 'status': 'confirmed',
                               'reference': 'Archived source order', 'artifact_ids': ['artifact-order-review'],
                               'assertions': ['listen precedes connect']}],
                'measurements': [{
                    'condition_id': 'source-only',
                    'rule_evidence': {'status': 'provisional', 'sets': [{
                        'id': 'rule-set-1', 'units': ['e-listen-first'], 'dependencies': [],
                        'sufficiency': 'The source directly states the required order.',
                        'necessity': {'e-listen-first': 'It is the only declared ordering fact.'},
                    }]},
                    'temporal': {'status': 'provisional', 'relations': [{
                        'id': 'r-listen-connect', 'semantic_key': 'listen-before-connect',
                        'from_event': 'listener registration', 'to_event': 'connect call',
                        'scope': 'one visit', 'predicate': 'registration finishes first',
                        'kind': 'before', 'explicitness': 'explicit', 'evidence': ['e-listen-first'],
                        'enforcement': {'baseline': 'source statement order', 'maintenance': 'preserve the order'},
                        'witness_ids': ['w-order'],
                    }], 'interactions': []},
                    'ownership': {'resolution': 'not-applicable', 'responsibilities': [],
                                  'rationale': 'This measurement does not assign distributed ownership.',
                                  'competing_owners': []},
                    'application': {'status': 'annotated', 'rationale': 'The order applies at connect.',
                                    'chains': [{
                                        'id': 'apply-connect', 'units': ['e-listen-first'], 'dependencies': [],
                                        'sufficiency': 'The ordering fact identifies the affected commit.',
                                        'necessity': {'e-listen-first': 'Needed to select the call order.'},
                                        'invalidation_boundaries': [], 'affected_commit_sites': ['commit-connect'],
                                        'witness_ids': ['w-order'],
                                    }]},
                }],
            }],
        }

    def completed_review(self, report, reviewer):
        value = measurement.review_template(report, reviewer)
        value['independent_of_author'] = True; value['outcome_blinded'] = True
        value['checks'] = {key: True for key in measurement.REVIEW_CHECKS}
        for condition, expected in zip(value['conditions'], report['conditions']):
            condition['H'] = expected['H']
            for row, expected_row in zip(condition['measurements'], expected['measurements']):
                row['labels'] = copy.deepcopy(expected_row['labels'])
                row['application']['status'] = expected_row['application']['status']
                for chain, expected_chain in zip(row['application']['chains'], expected_row['application']['chains']):
                    for key in measurement.APPLICATION_COUNTS:
                        chain[key] = expected_chain[key]
        return value

    def test_template_stays_draft_and_scan_findings_never_become_obligations(self):
        value = measurement.template(self.meta['report_id'], self.store)
        self.assertEqual(value['workflow_status'], 'draft')
        self.assertEqual(value['obligations'], [])
        report = measurement.validate(value, self.meta['report_id'], self.store)
        self.assertEqual(report['obligation_count'], 0)
        self.assertEqual(report['conditions'][0]['measurements'], [])
        finding = archive.read_report(self.meta['report_id'], self.store)['report']['findings'][0]
        assisted = measurement.template(self.meta['report_id'], self.store, finding['id'])
        self.assertTrue(assisted['evidence_units'])
        self.assertEqual(assisted['obligations'], [])
        self.assertTrue(all(unit['role'] == 'candidate-syntax-clue' for unit in assisted['evidence_units']))
        self.assertEqual(measurement.validate(assisted, self.meta['report_id'], self.store)['obligation_count'], 0)

    def test_final_document_derives_labels_and_binds_archived_source(self):
        report = measurement.validate(self.document(), self.meta['report_id'], self.store)
        row = report['conditions'][0]['measurements'][0]
        self.assertEqual(row['labels'], {'E': 0, 'T': 0, 'L': 'N/A'})
        self.assertEqual(report['conditions'][0]['H'], 0)
        self.assertEqual(row['application']['chains'][0]['affected_commit_site_count'], 1)
        changed = self.document(); changed['source_binding']['input_sha256'] = '0' * 64
        with self.assertRaisesRegex(EvidenceError, 'stale'):
            measurement.validate(changed, self.meta['report_id'], self.store)

    def test_append_only_measurement_and_two_reviewer_gate(self):
        item = archive.add_measurement(self.meta['report_id'], self.document(), self.store)
        self.assertFalse(item['measurement']['review']['gate_passed'])
        for reviewer in ('reviewer-a', 'reviewer-b'):
            review = self.completed_review(item['measurement'], reviewer)
            archive.add_measurement_review(self.meta['report_id'], item['record_id'], review, self.store)
        saved = archive.read_report(self.meta['report_id'], self.store)['measurements'][0]
        self.assertTrue(saved['measurement']['review']['gate_passed'])
        self.assertEqual(saved['measurement']['review']['eligible_agreeing_reviewers'], 2)
        with self.assertRaisesRegex(EvidenceError, 'already'):
            archive.add_measurement_review(self.meta['report_id'], item['record_id'], review, self.store)

    def test_stored_document_and_derived_result_tampering_are_detected(self):
        item = archive.add_measurement(self.meta['report_id'], self.document(), self.store)
        path = next((self.store/'measurements'/self.meta['report_id']).glob('*.json'))
        value = json.loads(path.read_text())
        value['measurement']['conditions'][0]['H'] = 2
        archive.atomic_json(path, value)
        with self.assertRaisesRegex(EvidenceError, 'derived measurement checksum'):
            archive.read_report(self.meta['report_id'], self.store)

    def test_cli_template_add_and_v06_read_only_import(self):
        draft = self.root/'draft.json'
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(['reports','measurement-template',self.meta['report_id'],
                                       '--output',str(draft),'--store',str(self.store)]), 0)
        self.assertTrue(draft.exists())
        document = self.root/'measurement.json'; document.write_text(json.dumps(self.document()), encoding='utf-8')
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(['reports','measurement-add',self.meta['report_id'],str(document),
                                       '--store',str(self.store)]), 0)
        legacy = self.root/'v06.json'
        legacy.write_text(json.dumps({
            'schema_version':'0.6','mechanical_valid':True,'case_id':'legacy-case',
            'profile_sha256':'a'*64,'tool_sha256':'b'*64,'standard_sha256':'c'*64,
            'conditions':[{'id':'latent-maintenance','variant':'ungranted','H':None,
                           'measurements':[{'obligation_id':'O1','labels':{'E':0,'T':1,'L':'N/A'},
                                            'application':{'status':'unknown','chains':[]}}]}],
            'review':{'status':'pending'},
        }), encoding='utf-8')
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(['reports','measurement-import-v06',self.meta['report_id'],str(legacy),
                                       '--store',str(self.store)]), 0)
        imported = archive.read_report(self.meta['report_id'], self.store)['legacy_measurements'][0]['imported']
        self.assertEqual(imported['origin']['case_id'], 'legacy-case')
        self.assertEqual(imported['source_binding']['alignment'], 'not_verified_across_snapshot_recipes')


if __name__ == '__main__':
    unittest.main()
