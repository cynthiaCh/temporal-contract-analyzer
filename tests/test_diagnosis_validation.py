"""Regressions for diagnosis metadata, candidate citations and atomic revisions."""
import unittest

import test_tempoevo_v4 as fixtures
from temporal_contract_analyzer.core import EvidenceError
from temporal_contract_analyzer.tempoevo_v4 import validate_diagnosis




def diagnostic():
    return dict(diagnosis='implementation_gap', contract_after=fixtures.contract(),
                structured_delta=[], supporting_evidence=[dict(file='TASK', quote='Preserve accepted work.')],
                remaining_unknowns=[], explanation='Implementation needs another attempt.')


class DiagnosisValidationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.V4Tests('test_first_pass_stops_and_is_staged_not_approved')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def check(self, value, condition='structured'):
        return validate_diagnosis(value, fixtures.contract(), 'Preserve accepted work.',
                                  {'main.py': 'value = 0\n'}, {'main.py': 'value = 1\n'}, condition)

    def test_metadata_only_revision_does_not_request_delta_or_rerouting(self):
        # Metadata changes must not trigger experience reselection.
        for condition in ('contract', 'structured', 'fixed_contract'):
            for kind in ('implementation_gap', 'unknown'):
                with self.subTest(condition=condition, diagnosis=kind):
                    class MetadataBackend(fixtures.Backend):
                        def execute(inner, stage, payload, *args):
                            result = super().execute(stage, payload, *args)
                            if stage == 'diagnosis':
                                out = result['output']
                                out['contract_after']['supporting_evidence'] = [dict(file='TASK', quote='accepted work.')]
                                out['contract_after']['unknowns'] = ['Acceptance does not identify a failure cause.']
                            return result
                    loop = self.fixture.prepare(condition=condition)
                    backend = MetadataBackend(2, diagnosis=kind)
                    state = loop.run(backend, execute=True)
                    self.assertEqual(state['status'], 'passed', state.get('error'))
                    self.assertFalse(state['diagnoses'][0]['contract_changed'])
                    self.assertFalse((loop.root/'revisions/2-delivery.json').exists())
                    self.assertEqual(len([c for c in backend.calls if c[0] == 'action']), 2)

    def test_original_and_previous_candidate_citations_are_bound_separately(self):
        for path in ('main.py', 'PREVIOUS_CANDIDATE:main.py'):
            with self.subTest(path=path):
                value = diagnostic()
                value['supporting_evidence'] = [dict(file=path, quote='value = 1')]
                checked = self.check(value)
                self.assertEqual(checked['supporting_evidence_bindings'][0]['source_versions'], ['previous_candidate'])
        value = diagnostic()
        value['supporting_evidence'] = [dict(file='main.py', quote='value = 0')]
        self.assertEqual(self.check(value)['supporting_evidence_bindings'][0]['source_versions'], ['original'])

    def test_candidate_evidence_reaches_next_action_with_version_binding(self):
        class CandidateBackend(fixtures.Backend):
            def execute(inner, stage, payload, *args):
                result = super().execute(stage, payload, *args)
                if stage == 'diagnosis':
                    result['output']['supporting_evidence'] = [dict(file='main.py', quote='value = 1')]
                return result
        loop = self.fixture.prepare()
        backend = CandidateBackend(2)
        state = loop.run(backend, execute=True)
        self.assertEqual(state['status'], 'passed', state.get('error'))
        actions = [c[1] for c in backend.calls if c[0] == 'action']
        bindings = actions[1]['within_task_reflections'][0]['supporting_evidence_bindings']
        self.assertEqual(bindings[0]['source_versions'], ['previous_candidate'])

    def test_explicit_candidate_version_mislabel_is_corrected_only_by_original_text(self):
        value = diagnostic()
        value['supporting_evidence'] = [dict(file='PREVIOUS_CANDIDATE:main.py', quote='value = 0')]
        binding = self.check(value)['supporting_evidence_bindings'][0]
        self.assertEqual(binding['source_versions'], ['original'])
        self.assertTrue(binding['source_version_corrected'])
        self.assertEqual(binding['claimed_source_version'], 'previous_candidate')

    def test_candidate_cannot_supply_original_contract_or_routing_evidence(self):
        value = diagnostic()
        value['contract_after']['supporting_evidence'] = [dict(file='main.py', quote='value = 1')]
        checked = self.check(value)
        self.assertTrue(checked['restored_original_contract_evidence'])
        self.assertEqual(checked['contract_after'], fixtures.contract())
        self.assertEqual(value['contract_after']['supporting_evidence'][0]['quote'], 'value = 1')
        self.assertEqual(checked['candidate_only_contract_evidence'][0]['source_versions'], ['previous_candidate'])
        value['contract_after']['checkpoints'] = ['A new requirement.']
        with self.assertRaisesRegex(EvidenceError, 'Unsupported public-source citation'):
            self.check(value)
    def test_candidate_only_contract_citations_do_not_stop_unchanged_diagnosis(self):
        class CandidateContractBackend(fixtures.Backend):
            def execute(inner, stage, payload, *args):
                result = super().execute(stage, payload, *args)
                if stage == 'diagnosis':
                    result['output']['contract_after']['supporting_evidence'] = [dict(file='main.py', quote='value = 1')]
                return result
        loop = self.fixture.prepare()
        state = loop.run(CandidateContractBackend(2), execute=True)
        self.assertEqual(state['status'], 'passed', state.get('error'))
        self.assertEqual(state['contract'], fixtures.contract())
        self.assertTrue(state['diagnoses'][0]['restored_original_contract_evidence'])

    def test_ungrounded_contract_citation_is_not_silently_discarded(self):
        value = diagnostic()
        value['contract_after']['supporting_evidence'] = [dict(file='main.py', quote='fabricated text')]
        with self.assertRaisesRegex(EvidenceError, 'Unsupported public-source citation'):
            self.check(value)

    def test_stopped_execution_is_not_left_marked_as_running(self):
        loop = self.fixture.prepare()
        state = loop.run(fixtures.Backend(invalid='contract'), execute=True)
        self.assertEqual(state['status'], 'execution_invalid')
        self.assertEqual(state['stages'][0]['status'], 'invalid')

    def test_nonexistent_or_fabricated_diagnostic_quotes_are_rejected(self):
        for file, quote in [('main.py', 'value = 99'), ('missing.py', 'value = 1'),
                            ('PREVIOUS_CANDIDATE:missing.py', 'value = 1'),
                            ('PREVIOUS_CANDIDATE:TASK', 'Preserve accepted work.')]:
            with self.subTest(file=file):
                value = diagnostic()
                value['supporting_evidence'] = [dict(file=file, quote=quote)]
                with self.assertRaises(EvidenceError):
                    self.check(value)

    def test_real_changes_still_require_delta_and_allowed_diagnosis(self):
        value = diagnostic()
        value['contract_after']['checkpoints'] = ['Check completion.']
        with self.assertRaisesRegex(EvidenceError, 'Implementation-only'):
            self.check(value)
        value['diagnosis'] = 'contract_gap'
        with self.assertRaisesRegex(EvidenceError, 'Missing Contract delta'):
            self.check(value)
        value['structured_delta'] = ['Add checkpoint.']
        self.assertTrue(self.check(value)['contract_changed'])
        with self.assertRaisesRegex(EvidenceError, 'fixed condition'):
            self.check(value, 'fixed_contract')
        value['contract_after']['obligations'][0]['text'] = 'A different requirement.'
        with self.assertRaisesRegex(EvidenceError, 'weaken'):
            self.check(value)

    def test_invalid_revision_is_discarded_without_committing_behavior_change(self):
        class MissingDelta(fixtures.Backend):
            def execute(inner,*args):
                result=super().execute(*args)
                if args[0]=='diagnosis':result['output']['structured_delta']=[]
                return result
        loop = self.fixture.prepare(condition='structured')
        state = loop.run(MissingDelta(2, diagnosis='contract_gap', revise=True), execute=True)
        self.assertEqual(state['status'], 'passed', state.get('error'))
        self.assertTrue(any('Missing Contract delta' in (w.get('error') or '') for w in state['preparation_warnings']))
        self.assertEqual(state['contract'], fixtures.contract())
        self.assertTrue(state['diagnoses'][0]['diagnostic_fallback'])
        self.assertFalse(state['diagnoses'][0]['contract_changed'])
        self.assertEqual(fixtures.read(loop.root/'revisions/2.json')['contract_after'], fixtures.contract())

    def test_failed_reselection_does_not_commit_revision(self):
        loop = self.fixture.prepare(condition='structured')
        original_retrieve = loop.retrieve
        def failed_retrieve(protocol, backend=None, selection_key='selection-1'):
            if selection_key == 'selection-2':
                raise EvidenceError('Synthetic selection failure')
            return original_retrieve(protocol, backend, selection_key)
        loop.retrieve = failed_retrieve
        state = loop.run(fixtures.Backend(2, diagnosis='contract_gap', revise=True), execute=True)
        self.assertEqual(state['status'], 'execution_invalid')
        self.assertIn('Synthetic selection failure', state['error'])
        self.assertEqual(state['contract'], fixtures.contract())
        self.assertEqual(state['diagnoses'], [])
