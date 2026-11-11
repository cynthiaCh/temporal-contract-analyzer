"""Synthetic interface fixtures only; these are not model/repair effect results."""
from copy import deepcopy
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest

from temporal_contract_analyzer.core import EvidenceError, sha
from temporal_contract_analyzer import experience_memory as memory, taxonomy
from temporal_contract_analyzer import experience_routing as routing
from temporal_contract_analyzer import experience_approval as approval


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = self.root/'memory'
        memory.initialize(self.store)
        self.source = self.root/'synthetic-evidence.json'
        self.source.write_text(json.dumps({'origin':'synthetic_fixture_not_model_output',
            'rules':[{'supported':True} for _ in range(5)], 'review':{'synthetic':True}}))
        code = sha(self.source.read_bytes())
        self.payload = dict(schema_version=memory.BUNDLE_VERSION, id='entry-binding', version='v1',
            parent_sha256=None, taxonomy_version=taxonomy.VERSION, labels=['I'],
            requires=['entry_snapshot'], excludes=[], rules=[
                dict(id=f'R{i:02d}', category=category, body=body)
                for i, (category, body) in enumerate([
                    ('applicability','Use where accepted actions retain entry identity.'),
                    ('event_relation','Capture entry before callback reentry.'),
                    ('preservation','Retain accepted results after navigation.'),
                    ('exclusion','Do not transfer entry obligations to a later visit.'),
                    ('verification','Exercise synchronous callback navigation.')], 1)],
            review=dict(status='research_admitted', kind='synthetic', source_sha256=code,
                        limitations=['Synthetic interface fixture; no effectiveness evidence.']),
            audit=dict(sources=[dict(path=str(self.source), sha256=code)],
                rule_links=[dict(rule_id=f'R{i:02d}', source_sha256=code, pointer=f'/rules/{i-1}')
                            for i in range(1,6)], notes=['Synthetic fixture.'], outcome_refs=[]))

    def add(self, payload=None):
        bundle = memory.add(self.store, self.payload if payload is None else payload, [self.source])
        if bundle['review']['status'] == 'research_admitted':
            if bundle['taxonomy_version'] == taxonomy.VERSION:
                from evolution_fixtures import synthetic_screen
                synthetic_screen(self.store,bundle['sha256'])
            approval.decide(self.store, bundle['sha256'], dict(reviewer='SYNTHETIC_EXPERT_FIXTURE',
                decision='accept', reason='Synthetic operator-action fixture, not real expert approval.',
                scope='exploratory', rules=[dict(rule_id=r['id'], supported=True,
                    reason='Synthetic fixture.') for r in bundle['rules']]), activate_version=True)
        return bundle

    def test_storage_preserves_single_source_body_and_evidence(self):
        bundle = self.add()
        self.assertEqual(memory.records(self.store), [bundle])
        self.assertEqual(memory.render(bundle), memory.render(deepcopy(bundle)))
        self.assertNotIn('source_sha256', memory.render(bundle))
        self.assertNotIn('synthetic-evidence', memory.render(bundle))
        self.assertTrue(memory.render(bundle).startswith('R01 [Applicability]\n'))

    def test_immutable_versions_and_rejected_tip(self):
        first = self.add()
        with self.assertRaises(EvidenceError):
            self.add()
        child = dict(deepcopy(self.payload), version='v2', parent_sha256=first['sha256'])
        child['review']['status'] = 'rejected'
        second = self.add(child)
        self.assertEqual(memory.tips(memory.records(self.store)), [second])
        self.assertEqual(len(memory.records(self.store)), 2)

    def test_invalid_evidence_conditions_and_categories(self):
        for change in ('pointer', 'rule', 'condition', 'missing_category', 'conflict'):
            bad = deepcopy(self.payload)
            if change == 'pointer':bad['audit']['rule_links'][0]['pointer']='/missing'
            if change == 'rule':bad['audit']['rule_links'][0]['rule_id']='R99'
            if change == 'condition':bad['requires']=['This is explanatory prose']
            if change == 'missing_category':bad['rules'][0]['category']='preservation'
            if change == 'conflict':bad['excludes']=['entry_snapshot']
            with self.subTest(change=change), self.assertRaises(EvidenceError):
                self.add(bad)
        self.assertEqual(memory.records(self.store), [])

    def test_hash_and_source_tampering_fail(self):
        bundle = self.add()
        path = self.store/'records'/(bundle['sha256']+'.json')
        value = json.loads(path.read_text())
        value['rules'][0]['body']='Changed policy'
        path.write_text(json.dumps(value))
        with self.assertRaises(EvidenceError):memory.records(self.store)
        path.write_text(json.dumps(bundle))
        (self.store/'sources'/bundle['review']['source_sha256']).write_bytes(b'altered')
        with self.assertRaises(EvidenceError):memory.records(self.store)

    def test_missing_parent_and_invisible_fields_rejected(self):
        for bad in (dict(self.payload, parent_sha256='a'*64), dict(self.payload, cluster='shortcut')):
            with self.assertRaises(EvidenceError):self.add(bad)

    def visible(self, state='known'):
        task = 'Keep the accepted entry snapshot through synchronous navigation.'
        anchor = dict(file='TASK', line=1, quote='entry snapshot')
        analysis = dict(taxonomy_version=taxonomy.VERSION, contract=task,
            obligation_labels=[dict(code='I', statement='Retain entry identity.', evidence=[anchor])],
            facts=[dict(predicate='entry_snapshot', state=state,
                        evidence=[anchor] if state != 'unknown' else [])], unknowns=[])
        review = routing.review_template(analysis, task, {})
        review.update(reviewer='execution_agent_visible_input_only', approved=True,
                      reason='Synthetic source-bound interface fixture.', evidence=[anchor])
        return dict(task=task, sources={}, analysis=analysis, review=review)

    def test_real_entry_to_delivery_path_and_correct_nonfirst_selection(self):
        other = deepcopy(self.payload)
        other.update(id='other-category', labels=['L'])
        first = self.add(other)
        selected = self.add()
        result = memory.retrieve(self.store, self.visible())
        self.assertEqual(result['route']['condition'], 'ROUTED')
        self.assertEqual(result['selected_memory_record']['sha256'], selected['sha256'])
        self.assertNotEqual(result['selected_memory_record']['sha256'], first['sha256'])
        self.assertEqual(result['experience_text'], memory.render(selected))
        self.assertNotIn('source_sha256', result['experience_text'])

    def test_unknown_contradictory_premises_and_unreviewed_input_fall_back(self):
        self.add()
        for state in ('unknown', 'contradicted'):
            result = memory.retrieve(self.store, self.visible(state))
            self.assertEqual(result['route']['condition'], 'AUTO')
            self.assertIsNone(result['experience_text'])
        visible = self.visible()
        del visible['review']
        self.assertEqual(memory.retrieve(self.store, visible)['route']['condition'], 'AUTO')

    def test_exclusions_must_be_explicitly_absent(self):
        payload = deepcopy(self.payload)
        payload['excludes'] = ['discard_boundary_policy']
        self.add(payload)
        visible = self.visible()
        self.assertIsNone(memory.retrieve(self.store, visible)['experience_text'])
        visible['analysis']['facts'].append(dict(predicate='discard_boundary_policy', state='contradicted',
            evidence=[dict(file='TASK', line=1, quote='Keep the accepted entry snapshot')]))
        visible['review'] = routing.review_template(visible['analysis'], visible['task'], {})
        visible['review'].update(reviewer='execution_agent_visible_input_only', approved=True,
            reason='Synthetic explicit exclusion check.', evidence=[dict(file='TASK', line=1, quote='Keep')])
        self.assertEqual(memory.retrieve(self.store, visible)['route']['condition'], 'ROUTED')

    def test_conflict_does_not_get_resolved_by_lexical_rank(self):
        self.add()
        other = deepcopy(self.payload)
        other.update(id='other-guidance', version='v2')
        self.add(other)
        self.assertEqual(memory.retrieve(self.store, self.visible())['route']['reason'],
                         'unresolved_multiple_experience_conflict')

    def test_metadata_excluded_from_search_and_query_contract(self):
        payload = deepcopy(self.payload)
        payload['audit']['notes'].append('secretclusterword historicalsuccessword')
        self.add(payload)
        self.assertEqual(memory.search(self.store, 'secretclusterword historicalsuccessword')['results'], [])
        hits = memory.search(self.store, 'entry snapshot')['results']
        self.assertTrue(hits)
        self.assertNotIn('audit', hits[0])
        for key in ('case_id', 'cluster', 'score', 'expected_class'):
            with self.assertRaises(EvidenceError):
                memory.retrieve(self.store, dict(self.visible(), **{key:'forbidden'}))

    def test_legacy_discovery_does_not_recode_or_deliver(self):
        payload = deepcopy(self.payload)
        payload.update(taxonomy_version=memory.LEGACY_TAXONOMY, labels=['T3'])
        self.add(payload)
        self.assertTrue(memory.search(self.store, 'entry', memory.LEGACY_TAXONOMY)['results'])
        self.assertEqual(memory.search(self.store, 'entry', taxonomy.VERSION)['results'], [])
        result = memory.retrieve(self.store, self.visible())
        self.assertIsNone(result['experience_text'])
        self.assertEqual(approval.active(self.store), [])
        self.assertEqual(result['route']['reason'], 'no_expert_activated_experience')

    def test_snapshot_guard_and_empty_library(self):
        self.assertEqual(memory.retrieve(self.store, self.visible())['route']['condition'], 'AUTO')
        empty = approval.freeze(self.store)['sha256']
        self.add()
        with self.assertRaises(EvidenceError):
            memory.retrieve(self.store, self.visible(), empty)
        state = approval.freeze(self.store)['sha256']
        self.assertEqual(memory.retrieve(self.store, self.visible(), state)['route']['condition'], 'ROUTED')

    def test_rejected_and_candidate_records_are_discoverable_but_not_delivered(self):
        for state in ('candidate', 'rejected'):
            payload = deepcopy(self.payload)
            payload.update(id='entry-'+state)
            payload['review']['status'] = state
            self.add(payload)
        self.assertEqual(len(memory.search(self.store, 'entry')['results']), 2)
        self.assertIsNone(memory.retrieve(self.store, self.visible())['experience_text'])

    def test_legacy_import_is_exact_and_retains_false_unknown_and_review_identity(self):
        rendered = memory.render(self.payload)
        entry = dict(text=rendered, version='legacy-v1', primary_class='T3',
                     requires=['entry_snapshot'], excludes=[], text_sha256=memory.digest(rendered))
        entry['sha256'] = memory.digest(memory.canonical(entry))
        registry = self.root/'synthetic-registry.json'
        registry.write_text(json.dumps([entry]))
        review = self.root/'synthetic-review.json'
        review.write_text(json.dumps(dict(origin='synthetic_fixture', rules=[{}]*5,
            expected=False, actual=None, prior_success=True, regression=True, cause='unknown')))
        payload = memory.legacy_payload(entry, 'legacy-guidance', registry, review, admitted=True)
        bundle = memory.add(self.store, payload, [registry, review])
        self.assertEqual(memory.render(bundle), rendered)
        self.assertEqual(bundle['body_sha256'], entry['text_sha256'])
        stored = json.loads((self.store/'sources'/bundle['review']['source_sha256']).read_bytes())
        self.assertIs(stored['expected'], False)
        self.assertIsNone(stored['actual'])
        self.assertTrue(stored['prior_success'] and stored['regression'])
        self.assertEqual(stored['cause'], 'unknown')
        self.assertEqual(bundle['review']['kind'], 'ai_assisted_historical')
        entry['text'] = rendered.rstrip('\n')
        entry['text_sha256'] = memory.digest(entry['text'])
        entry['sha256'] = memory.digest(memory.canonical({k:v for k,v in entry.items() if k!='sha256'}))
        with self.assertRaises(EvidenceError):
            memory.legacy_payload(entry, 'partial', registry, review)

    def test_malformed_and_incomplete_objects_are_not_completed(self):
        for change in (dict(rules=None), dict(rules=[None]), dict(review=None), dict(rules=[])):
            with self.subTest(change=change), self.assertRaises(EvidenceError):
                self.add(dict(self.payload, **change))
        bad = deepcopy(self.payload)
        del bad['rules'][0]['body']
        with self.assertRaises(EvidenceError):self.add(bad)
        self.assertEqual(memory.records(self.store), [])

    def test_new_candidate_does_not_replace_active_parent(self):
        parent = self.add()
        child = deepcopy(self.payload)
        child.update(version='v2', parent_sha256=parent['sha256'])
        child['review']['status'] = 'candidate'
        self.add(child)
        self.assertEqual(memory.retrieve(self.store, self.visible())['selected_memory_record']['sha256'], parent['sha256'])
        self.assertEqual({b['version'] for b in memory.search(self.store, 'entry')['results']}, {'v1','v2'})
        active_hits=[b['version'] for b in memory.search(self.store,'entry')['results'] if b['expert_active']]
        self.assertEqual(active_hits,['v1'])

    def test_cli_full_path_and_no_overwrites(self):
        from temporal_contract_analyzer.cli import main
        bundle = self.add()
        query = self.root/'query.json'
        query.write_text(json.dumps(self.visible()))
        delivered = self.root/'delivery.json'
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            self.assertEqual(main(['experience-memory','retrieve',str(query),'--store',str(self.store),
                                   '--output',str(delivered)]), 0)
            self.assertEqual(main(['experience-memory','retrieve',str(query),'--store',str(self.store),
                                   '--output',str(delivered)]), 1)
        value = json.loads(delivered.read_text())
        self.assertEqual(value['experience_text'], memory.render(bundle))
        self.assertEqual(value['selected_memory_record']['sha256'], bundle['sha256'])
        with self.assertRaises(EvidenceError):memory.initialize(self.store)


if __name__ == '__main__':
    unittest.main()
