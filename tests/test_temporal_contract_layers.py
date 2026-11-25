import copy
import json
from pathlib import Path
import tempfile
import unittest

from temporal_contract_analyzer import cli
from temporal_contract_analyzer.core import EvidenceError, analyze_sources, sha
from temporal_contract_analyzer.layers import (
    AUDIT_PROMPT, INCOMPLETE_REVIEW_NOTICE, OPEN_LAYER_SCHEMA,
    coverage_summary, freeze_bundle, render_layers, verify_bundle,
)


PYTHON = 'import asyncio\nasync def work(task):\n return await asyncio.shield(task)\n'
JAVASCRIPT = '''function subscribe(channel, publish) {
  channel.connect();
  channel.target.addEventListener("presence", publish);
}
function enter(channel, publish) {
  release = subscribe(channel, publish);
}
'''


class TemporalContractLayerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def report(self):
        return analyze_sources({'a.py': PYTHON, 'b.js': JAVASCRIPT})

    def test_open_review_shares_reminder_without_disclosing_case_evidence(self):
        report = self.report()
        for finding in report['findings']:
            finding.update(rule='SECRET_RULE', message='SECRET_ADVICE',
                           condition='SECRET_CONDITION', review_question='SECRET_QUESTION')
        layers = render_layers(report)
        self.assertEqual(layers['audit'], AUDIT_PROMPT)
        self.assertTrue(layers['risk'].startswith(layers['audit']))
        self.assertIn('detected temporal-related clues', layers['risk'])
        for arm in ('audit', 'risk'):
            for secret in ('SECRET_', 'a.py', 'b.js', 'channel.connect', 'L0001', 'asyncio.shield'):
                self.assertNotIn(secret, layers[arm])
        self.assertTrue(layers['audit_review'].startswith(AUDIT_PROMPT))
        self.assertIn(INCOMPLETE_REVIEW_NOTICE, layers['audit_review'])
        self.assertTrue(layers['audit_review'].endswith(layers['review']))
        for secret in ('SECRET_RULE', 'SECRET_ADVICE', 'SECRET_CONDITION', 'SECRET_QUESTION'):
            self.assertIn(secret, layers['audit_review'])
        more = copy.deepcopy(report)
        more['findings'] *= 3
        self.assertEqual(render_layers(more)['risk'], layers['risk'])

    def test_zero_findings_change_only_screening_signal_not_generic_audit(self):
        empty = analyze_sources({'plain.py': 'value = 1\n'})
        layers = render_layers(empty)
        self.assertEqual(layers['audit'], render_layers(self.report())['audit'])
        self.assertIn('did not detect', layers['risk'])
        self.assertIn('does not establish that temporal risks are absent', layers['risk'])
        self.assertEqual(coverage_summary(empty)['screening_signal'],
                         {'policy': 'any-source-finding-v1', 'status': 'not_detected'})

    def test_v2_bundle_still_verifies_without_g_layer(self):
        folder = self.root/'v2'
        manifest = freeze_bundle(self.report(), folder, layer_schema=OPEN_LAYER_SCHEMA)
        self.assertEqual(manifest['layer_schema_version'], OPEN_LAYER_SCHEMA)
        self.assertEqual(set(manifest['layers']),
                         {'none', 'locations', 'facts', 'review', 'audit', 'risk'})
        self.assertFalse((folder/'audit_review.md').exists())
        self.assertEqual(verify_bundle(folder), manifest)

    def test_risk_signal_tampering_cannot_be_hidden_by_rehashing(self):
        folder = self.root/'bundle'
        manifest = freeze_bundle(self.report(), folder)
        changed = (folder/'risk.md').read_text().replace('detected temporal-related clues', 'found high risk')
        (folder/'risk.md').write_text(changed)
        manifest['layers']['risk'].update(sha256=sha(changed.encode()), bytes=len(changed.encode()), chars=len(changed))
        (folder/'manifest.json').write_text(json.dumps(manifest))
        with self.assertRaises(EvidenceError):
            verify_bundle(folder)

    def test_same_location_prefix_in_all_active_conditions(self):
        report = self.report()
        layers = render_layers(report)
        self.assertEqual(layers['none'], '')
        self.assertTrue(layers['facts'].startswith(layers['locations']))
        self.assertTrue(layers['review'].startswith(layers['facts']))
        self.assertTrue(layers['audit_review'].startswith(layers['audit']))
        self.assertIn(INCOMPLETE_REVIEW_NOTICE, layers['audit_review'])
        self.assertTrue(layers['audit_review'].endswith(layers['review']))
        bundle = freeze_bundle(report, self.root/'bundle')
        selected = {eid for loc in bundle['selected_locations'] for eid in loc['evidence_ids']}
        expected = {eid for f in report['findings'] for eid in f['evidence']}
        self.assertEqual(selected, expected)
        self.assertEqual(len(selected), sum(len(loc['evidence_ids']) for loc in bundle['selected_locations']))

    def test_locations_contain_no_rule_or_source_and_facts_no_guidance(self):
        report = self.report()
        for finding in report['findings']:
            finding.update(rule='SECRET_RULE', message='SECRET_ADVICE', condition='SECRET_CONDITION', review_question='SECRET_QUESTION')
        for file in report['files']:
            for event in file['events']:
                event['tags'] = ['SECRET_API_TAG']
                event['api_basis'] = 'SECRET_API_BASIS'
        layers = render_layers(report)
        for secret in ('SECRET_RULE', 'SECRET_ADVICE', 'SECRET_CONDITION', 'SECRET_QUESTION', 'SECRET_API_TAG', 'SECRET_API_BASIS'):
            self.assertNotIn(secret, layers['locations'])
            self.assertNotIn(secret, layers['facts'])
        self.assertNotIn('channel.connect()', layers['locations'])
        self.assertIn('channel.connect()', layers['facts'])
        self.assertIn('SECRET_QUESTION', layers['review'])
        self.assertIn('SECRET_ADVICE', layers['review'])
        self.assertNotIn('SECRET_API_TAG', layers['review'])

    def test_facts_do_not_forward_arbitrary_relation_guidance(self):
        report = self.report()
        for r in report['relations']:
            r['qualification'] = 'DO THIS FIX NOW'
        selected = report['findings'][0]['evidence']
        report['relations'].append(dict(kind='unverified_magic_contract', before=selected[0], after=selected[-1], qualification='DO THIS FIX NOW'))
        facts = render_layers(report)['facts']
        self.assertNotIn('DO THIS FIX NOW', facts)
        self.assertNotIn('unverified_magic_contract', facts)
        self.assertIn('rhs_before_assignment', facts)

    def test_deterministic_relocated_bundles_and_no_timestamps(self):
        report = self.report()
        a, b = self.root/'a', self.root/'b'
        self.assertEqual(freeze_bundle(report, a), freeze_bundle(report, b))
        self.assertEqual({p.name: p.read_bytes() for p in a.iterdir()}, {p.name: p.read_bytes() for p in b.iterdir()})
        self.assertEqual(verify_bundle(a), verify_bundle(b))

    def test_empty_selection_is_valid_not_a_safety_verdict(self):
        report = analyze_sources({'a.py': 'value = 1\n'})
        manifest = freeze_bundle(report, self.root/'bundle')
        self.assertEqual(manifest['selected_locations'], [])
        self.assertEqual(verify_bundle(self.root/'bundle'), manifest)
        self.assertEqual(manifest['layers']['none'], dict(path=None, sha256=sha(b''), bytes=0, chars=0))

    def test_partial_empty_and_invalid_inventory_refused(self):
        partial = analyze_sources({'broken.py': 'def broken(\n'})
        for report in (partial, analyze_sources({})):
            with self.assertRaises(EvidenceError):
                freeze_bundle(report, self.root/'bundle')
        report = self.report()
        report['inputs'][0]['sha256'] = '0'*64
        with self.assertRaises(EvidenceError):
            freeze_bundle(report, self.root/'bundle')
        self.assertFalse((self.root/'bundle').exists())

    def test_missing_evidence_and_noncomplete_coverage_refused(self):
        report = self.report()
        report['findings'][0]['evidence'] = ['not-a-source-event']
        with self.assertRaises(EvidenceError):
            render_layers(report)
        report = self.report()
        report['skipped'].append(dict(path='missing.py', reason='non_utf8_source'))
        with self.assertRaises(EvidenceError):
            render_layers(report)

    def test_limit_rejects_entire_bundle_without_truncating(self):
        report = self.report()
        layers = render_layers(report)
        length = max(len(text) for text in layers.values())
        with self.assertRaises(EvidenceError):
            freeze_bundle(report, self.root/'bad', max_chars=length-1)
        self.assertFalse((self.root/'bad').exists())
        result = freeze_bundle(report, self.root/'good', max_chars=length)
        self.assertEqual(result['layers']['audit_review']['chars'], length)
        self.assertEqual(result['truncation'], 'none')

    def test_overwrite_and_symlink_output_refused(self):
        report = self.report()
        freeze_bundle(report, self.root/'bundle')
        with self.assertRaises(EvidenceError):
            freeze_bundle(report, self.root/'bundle')
        (self.root/'link').symlink_to(self.root/'bundle', target_is_directory=True)
        with self.assertRaises(EvidenceError):
            verify_bundle(self.root/'link')
        (self.root/'bundle/facts.md').unlink()
        (self.root/'bundle/facts.md').symlink_to(self.root/'bundle/review.md')
        with self.assertRaises(EvidenceError):
            verify_bundle(self.root/'bundle')

    def test_file_tampering_and_manifest_rehash_cannot_change_layer(self):
        folder = self.root/'bundle'
        manifest = freeze_bundle(self.report(), folder)
        changed = (folder/'facts.md').read_text() + '\nInjected advice\n'
        (folder/'facts.md').write_text(changed)
        with self.assertRaises(EvidenceError):
            verify_bundle(folder)
        manifest['layers']['facts'].update(sha256=sha(changed.encode()), bytes=len(changed.encode()), chars=len(changed))
        (folder/'manifest.json').write_text(json.dumps(manifest))
        with self.assertRaises(EvidenceError):
            verify_bundle(folder)

    def test_manifest_paths_extra_files_and_candidate_mismatch_refused(self):
        folder = self.root/'bundle'
        manifest = freeze_bundle(self.report(), folder)
        with self.assertRaises(EvidenceError):
            verify_bundle(folder, '0'*64)
        manifest['layers']['facts']['path'] = '../outside.md'
        (folder/'manifest.json').write_text(json.dumps(manifest))
        with self.assertRaises(EvidenceError):
            verify_bundle(folder)
        (folder/'unexpected.md').write_text('unbound')
        with self.assertRaises(EvidenceError):
            verify_bundle(folder)

    def test_renamed_generator_digest_records_provenance_not_current_equality(self):
        folder = self.root/'bundle'
        manifest = freeze_bundle(self.report(), folder)
        manifest['generator_sha256'] = '1'*64
        (folder/'manifest.json').write_text(json.dumps(manifest))
        self.assertEqual(verify_bundle(folder)['generator_sha256'], '1'*64)

    def test_cli_freeze_verify_and_no_candidate_writes(self):
        base = self.root/'base'; base.mkdir()
        (base/'a.py').write_text(PYTHON)
        folder = self.root/'bundle'
        self.assertEqual(cli.main(['freeze', str(base), '--output', str(folder)]), 0)
        self.assertEqual(cli.main(['verify-bundle', str(folder), '--candidate', str(base)]), 0)
        self.assertEqual(cli.main(['freeze', str(base), '--output', str(base/'forbidden')]), 1)
        self.assertFalse((base/'forbidden').exists())
        (base/'a.py').write_text(PYTHON+'\nvalue = 2\n')
        self.assertEqual(cli.main(['verify-bundle', str(folder), '--candidate', str(base)]), 1)


if __name__ == '__main__':
    unittest.main()
