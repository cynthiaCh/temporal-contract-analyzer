import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from temporal_contract_analyzer import cli
from temporal_contract_analyzer.core import EvidenceError, analyze_sources, sha
from temporal_contract_analyzer.profile import build_profile_evidence, packet_sha256, verify_profile_evidence


SOURCE = '''class Worker:
 async def run(self):
  value = await request()
  if self.closed: return
  scheduleRetry(self.run)
  save(value)
 def close(self):
  self.closed = True
'''


def file(path, text, role='candidate'):
    return dict(path=path, text=text, sha256=sha(text.encode()), role=role)


def packet():
    return dict(id='worker', manifest_sha256='a' * 64, base_sha256='b' * 64,
                condition='latent-maintenance', files=[file('base/worker.py', SOURCE),
                    file('TASK.md', 'Keep preparing until ready.'),
                    file('oracle/check.py', 'await missing_hidden_contract()', 'evaluator'),
                    file('REVIEW-GUIDE.md', 'Post-review interpretation', 'evaluator')],
                obligations=[dict(id='lifetime', statement='After closing, delivery is invalid.',
                                  acceptable_evidence_paths=['base/worker.py']),
                             dict(id='unspecified', statement='An additional obligation')])


class ProfileEvidenceTests(unittest.TestCase):
    def test_candidate_only_scanner_and_separate_primary_indexes(self):
        p = packet()
        with patch('temporal_contract_analyzer.profile.analyze_sources', wraps=analyze_sources) as scan:
            evidence = build_profile_evidence(p)
        self.assertEqual(set(scan.call_args.args[0]), {'base/worker.py'})
        self.assertEqual([x['path'] for x in evidence['candidate_text_index']], ['TASK.md'])
        self.assertEqual([x['path'] for x in evidence['evaluator_artifact_index']], ['oracle/check.py'])
        self.assertFalse(evidence['agent_input_eligible'])
        self.assertNotIn('REVIEW-GUIDE', json.dumps(evidence))
        self.assertTrue(evidence['observations'])
        for observation in evidence['observations']:
            for ref in observation['refs']:
                self.assertEqual(ref['path'], 'base/worker.py')
                self.assertEqual(ref['sha256'], p['files'][0]['sha256'])
                self.assertGreaterEqual(ref['start']['line'], 1)
                self.assertGreaterEqual(ref['end']['line'], ref['start']['line'])

    def test_ten_dimensions_unknown_even_with_guards_and_hints(self):
        evidence = build_profile_evidence(packet())
        self.assertEqual(len(evidence['dimensions']), 10)
        self.assertFalse(evidence['coverage']['zero_hits'])
        for card in evidence['cards']:
            for dimension in card['dimensions'].values():
                self.assertIsNone(dimension['suggestion'])
                self.assertEqual(dimension['status'], 'unreviewed')
        self.assertNotIn('total_score', evidence)

    def test_explicit_path_is_only_relevance_and_otherwise_unassigned(self):
        evidence = build_profile_evidence(packet())
        self.assertEqual(evidence['cards'][0]['association'], 'explicit_source_paths')
        self.assertEqual(evidence['cards'][1]['association'], 'workspace_unassigned')
        p = packet()
        p['obligations'][0]['acceptable_evidence_paths'] = ['missing.py']
        evidence = build_profile_evidence(p)
        self.assertEqual(evidence['cards'][0]['association'], 'unresolved_source_paths')
        self.assertEqual(evidence['cards'][0]['candidate_observation_ids'], [])
        self.assertEqual(evidence['cards'][0]['unresolved_paths'], ['missing.py'])

    def test_zero_matches_still_unknown_and_preserves_all_cards(self):
        p = packet()
        p['files'][0] = file('base/worker.py', 'answer = 42\n')
        evidence = build_profile_evidence(p)
        self.assertTrue(evidence['coverage']['zero_hits'])
        self.assertEqual(len(evidence['cards']), 2)
        for card in evidence['cards']:
            for d in card['dimensions'].values():
                self.assertEqual(d['coverage'], 'unknown')
                self.assertIsNone(d['suggestion'])

    def test_partial_analysis_is_not_low_difficulty(self):
        p = packet()
        p['files'][0] = file('base/worker.py', 'async def broken(\n')
        evidence = build_profile_evidence(p)
        self.assertEqual(evidence['coverage']['status'], 'partial')
        self.assertEqual(evidence['coverage']['unparsed_files'][0]['path'], 'base/worker.py')
        self.assertEqual(evidence['coverage']['semantic_coverage'], 'unknown')

    def test_identical_inputs_deterministic_and_order_independent(self):
        p = packet()
        a = build_profile_evidence(p)
        p['files'].reverse()
        p['obligations'].reverse()
        self.assertEqual(a, build_profile_evidence(p))
        self.assertTrue(verify_profile_evidence(p, a)['verified'])

    def test_source_bytes_hash_and_role_drift_rejected(self):
        p = packet()
        evidence = build_profile_evidence(p)
        for mutation in ('bytes', 'rehashed', 'role', 'removed', 'condition', 'manifest', 'statement', 'paths'):
            with self.subTest(mutation=mutation):
                changed = copy.deepcopy(p)
                if mutation == 'bytes':
                    changed['files'][0]['text'] += '\n'
                elif mutation == 'rehashed':
                    changed['files'][0] = file('base/worker.py', SOURCE + '\n')
                elif mutation == 'role':
                    changed['files'][0]['role'] = 'evaluator'
                elif mutation == 'removed':
                    changed['files'].pop(0)
                elif mutation == 'condition':
                    changed['condition'] = 'explicit'
                elif mutation == 'manifest':
                    changed['manifest_sha256'] = 'c' * 64
                elif mutation == 'statement':
                    changed['obligations'][0]['statement'] += '!'
                elif mutation == 'paths':
                    changed['obligations'][0]['acceptable_evidence_paths'] = []
                with self.assertRaises(EvidenceError):
                    verify_profile_evidence(changed, evidence)

    def test_sidecar_mutation_rejected_and_original_packet_not_changed(self):
        p = packet()
        original = copy.deepcopy(p)
        evidence = build_profile_evidence(p)
        self.assertEqual(p, original)
        evidence['cards'][0]['dimensions']['TR']['suggestion'] = 2
        with self.assertRaises(EvidenceError):
            verify_profile_evidence(p, evidence)

    def test_results_old_labels_and_analysis_do_not_enter_profile(self):
        p = packet()
        a = build_profile_evidence(p)
        p['results'] = {'PASS': 10000}
        p['profile_evidence'] = {'pretend': 'already confirmed'}
        p['old_profile'] = {'TR': 2, 'baseline_protection': 'full'}
        p['scope_note'] = 'An interpretation written later'
        p['files'].append(file('TEMPORAL-EVIDENCE.md', 'TR=2; PASS', 'analysis'))
        p['files'][-2] = file('REVIEW-GUIDE.md', 'Different post-review interpretation', 'evaluator')
        self.assertEqual(a, build_profile_evidence(p))

    def test_report_from_evaluator_or_stale_source_rejected(self):
        p = packet()
        report = analyze_sources({'worker.py': SOURCE})
        with self.assertRaises(EvidenceError):
            build_profile_evidence(p, report)
        report = analyze_sources({'base/worker.py': SOURCE})
        self.assertEqual(build_profile_evidence(p, report), build_profile_evidence(p))

    def test_malformed_paths_and_duplicate_obligations_rejected(self):
        for bad in ('../../source.py', '/tmp/source.py', 'base//source.py'):
            p = packet()
            p['files'][0] = file(bad, SOURCE)
            with self.assertRaises(EvidenceError):
                build_profile_evidence(p)
        p = packet()
        p['obligations'].append(p['obligations'][0])
        with self.assertRaises(EvidenceError):
            build_profile_evidence(p)

    def test_no_condition_not_guessed(self):
        p = packet()
        p.pop('condition')
        evidence = build_profile_evidence(p)
        self.assertIsNone(evidence['context']['condition'])
        self.assertEqual(evidence['context']['condition_status'], 'not_declared')

    def test_malformed_packet_and_sidecar_fail_with_domain_error(self):
        for malformed in ([], {}, {'files': None}, {'files': [None]}, {'files': [], 'obligations': [None]}):
            with self.subTest(value=malformed), self.assertRaises(EvidenceError):
                build_profile_evidence(malformed)
        with self.assertRaises(EvidenceError):
            verify_profile_evidence(packet(), [])

    def test_cli_frozen_profile_verify_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'packet.json'
            target = root / 'profile.json'
            source.write_text(json.dumps(packet()), encoding='utf-8')
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(cli.main(['profile', str(source), '--output', str(target)]), 0)
                self.assertEqual(cli.main(['verify-profile', str(target), str(source)]), 0)
                self.assertEqual(cli.main(['profile', str(source), '--output', str(target)]), 1)
                changed = packet()
                changed['condition'] = 'different'
                source.write_text(json.dumps(changed), encoding='utf-8')
                self.assertEqual(cli.main(['verify-profile', str(target), str(source)]), 1)


if __name__ == '__main__':
    unittest.main()
