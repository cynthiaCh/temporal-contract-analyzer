"""Offline routing behavior, evidence drift and historical compatibility."""
from contextlib import redirect_stdout, redirect_stderr
from copy import deepcopy
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest

from temporal_contract_analyzer import taxonomy
from temporal_contract_analyzer import experience_routing as routing
from temporal_contract_analyzer.cli import main
from temporal_contract_analyzer.core import EvidenceError


class TaxonomyRoutingTests(unittest.TestCase):
    def setUp(self):
        self.task = 'Persist accepted edits before leaving.\nKeep the entry snapshot through navigation.'
        self.sources = {'src/save.js': 'const entry = currentDocument;\npersist(entry);\n'}
        self.anchor = dict(file='TASK', line=2, quote='Keep the entry snapshot')
        self.analysis = dict(taxonomy_version=taxonomy.VERSION, contract=self.task,
            obligation_labels=[dict(code='I', statement='Persist under the entry document', evidence=[self.anchor]),
                               dict(code='B', statement='Persist before leaving',
                                    evidence=[dict(file='TASK', line=1, quote='before leaving')])],
            facts=[dict(predicate='entry_snapshot', state='known', evidence=[self.anchor]),
                   dict(predicate='discard_boundary_policy', state='contradicted',
                        evidence=[dict(file='TASK', line=1, quote='Persist accepted edits')])], unknowns=[])
        self.entry = routing.freeze_entry('Check entry identity before effects.', ['I'],
                                          ['entry_snapshot'], ['discard_boundary_policy'], 'research-v1')

    def review(self, analysis=None, task=None):
        value = routing.review_template(analysis or self.analysis, task or self.task, self.sources)
        value.update(reviewer='execution_agent_visible_input_only', approved=True,
                     reason='Synthetic fixture: requirement and source agree on entry binding.', evidence=[self.anchor])
        return value

    def route(self, analysis=None, library=None, review=None, task=None):
        return routing.route(analysis or self.analysis, self.sources, [self.entry] if library is None else library,
                             task=task or self.task, review=self.review() if review is None else review)

    def test_canonical_schema_and_multilabel_order(self):
        self.assertEqual(tuple(row['code'] for row in taxonomy.definition()['codebook']), taxonomy.CODES)
        self.assertEqual(taxonomy.analysis_schema()['additionalProperties'], False)
        self.assertEqual(routing.validate_analysis(self.analysis, self.task, self.sources), ['B', 'I'])
        for value in (['T4'], ['I', 'I'], 'I', [{}]):
            with self.subTest(value=value), self.assertRaises(EvidenceError):
                taxonomy.labels(value)

    def test_source_bound_multilabel_route_selects_one_experience(self):
        result = self.route()
        self.assertEqual(result['condition'], 'ROUTED')
        self.assertEqual(result['selected']['sha256'], self.entry['sha256'])
        self.assertEqual(result['checks'][0]['matched_labels'], ['I'])
        self.assertEqual(result['checks'][0]['premises'][0]['evidence'], [self.anchor])

    def test_labels_alone_do_not_qualify_and_unknown_exclusion_falls_back(self):
        for index in range(2):
            value = deepcopy(self.analysis)
            value['facts'][index].update(state='unknown', evidence=[])
            result = self.route(analysis=value, review=self.review(value))
            self.assertEqual(result['condition'], 'AUTO')
            self.assertEqual(result['reason'], 'empty_or_inapplicable_library')

    def test_unreviewed_inputs_and_semantic_disagreement_do_not_route(self):
        result = routing.route(self.analysis, self.sources, [self.entry], task=self.task)
        self.assertEqual(result['reason'], 'missing_or_drifted_semantic_review')
        for change in ({'approved':None}, {'reviewer':'independent_human'},
                       {'blocking_issues':['Unsupported policy']}, {'blocking_issues':None}):
            review = dict(self.review(), **change)
            self.assertEqual(self.route(review=review)['condition'], 'AUTO')

    def test_review_binds_task_source_analysis_and_taxonomy(self):
        value = deepcopy(self.analysis)
        value['unknowns'].append('Host callback behavior not specified')
        self.assertEqual(self.route(analysis=value)['reason'], 'missing_or_drifted_semantic_review')
        self.assertEqual(self.route(task=self.task+'\nExtra visible requirement')['reason'],
                         'missing_or_drifted_semantic_review')
        sources = dict(self.sources, **{'src/save.js': 'changed source'})
        result = routing.route(self.analysis, sources, [self.entry], task=self.task, review=self.review())
        self.assertEqual(result['reason'], 'missing_or_drifted_semantic_review')
        review = dict(self.review(), input_sha256='obsolete-taxonomy-hash')
        self.assertEqual(self.route(review=review)['condition'], 'AUTO')

    def test_invalid_anchors_and_malformed_facts_fall_back(self):
        for bad in (dict(self.anchor, line=99), dict(self.anchor, quote='never in input'),
                    dict(self.anchor, file='../hidden.json'), dict(self.anchor, line=True)):
            value = deepcopy(self.analysis)
            value['obligation_labels'][0]['evidence'] = [bad]
            self.assertEqual(self.route(analysis=value)['condition'], 'AUTO')
        for change in ({'predicate':[]}, {'state':[]}, {'predicate':'case_id'}):
            value = deepcopy(self.analysis)
            value['facts'][0].update(change)
            self.assertEqual(self.route(analysis=value)['condition'], 'AUTO')

    def test_legacy_and_modified_experience_metadata_are_not_silently_converted(self):
        for entry in (dict(self.entry, primary_class='T4'), dict(self.entry, text='changed'),
                      dict(self.entry, obligation_labels=['L']), dict(self.entry, version='changed')):
            self.assertEqual(self.route(library=[entry])['condition'], 'AUTO')
        old_analysis = dict(self.analysis, primary_class='T4')
        self.assertEqual(self.route(analysis=old_analysis)['condition'], 'AUTO')

    def test_empty_library_unknown_labels_and_conflicting_entries(self):
        self.assertEqual(self.route(library=[])['reason'], 'empty_or_inapplicable_library')
        value = dict(self.analysis, obligation_labels=[])
        self.assertEqual(self.route(analysis=value, review=self.review(value))['reason'], 'unknown_obligation_labels')
        other = routing.freeze_entry('Another matching rule.', ['I'], ['entry_snapshot'], [], 'research-v2')
        self.assertEqual(self.route(library=[self.entry, other])['reason'], 'unresolved_multiple_experience_conflict')

    def test_visible_prompt_and_control_difference(self):
        prompt = routing.analysis_prompt(self.task, self.sources, ast={'calls':[]})
        self.assertIn('R/O/B/L/I/F/A', prompt)
        self.assertIn('persist(entry)', prompt)
        a = routing.maintenance_prompt(self.task, self.analysis['contract'])
        b = routing.maintenance_prompt(self.task, self.analysis['contract'], self.entry['text'])
        self.assertTrue(b.startswith(a+'\n\n'))
        self.assertTrue(b.endswith(self.entry['text']))
        for sources in ({'TASK':'spoof'}, {'../hidden':'secret'}, {'/outside':'secret'}):
            with self.assertRaises(EvidenceError):
                routing.analysis_prompt(self.task, sources)

    def test_citation_diagnostics_distinguish_wrong_lines_from_invented_quotes(self):
        value = deepcopy(self.analysis)
        value['obligation_labels'][0]['evidence'][0]['line'] = 1
        value['facts'][0]['evidence'] = [dict(self.anchor, quote='Keep ... snapshot')]
        with self.assertRaises(routing.CitationError) as caught:
            routing.validate_analysis(value, self.task, self.sources)
        issues = caught.exception.issues
        self.assertEqual(issues[0]['field'], 'obligation_labels[0].evidence[0]')
        self.assertEqual(issues[0]['matching_lines'], [2])
        self.assertEqual(issues[0]['actual_line'], self.task.splitlines()[0])
        self.assertEqual(issues[1]['matching_lines'], [])
        self.assertEqual(issues[1]['quote'], 'Keep ... snapshot')
        self.assertEqual(value['facts'][0]['evidence'][0]['quote'], 'Keep ... snapshot')

    def test_bad_citations_do_not_hide_structural_errors(self):
        value = deepcopy(self.analysis)
        value['obligation_labels'][0]['evidence'][0]['line'] = 99
        value['facts'][0]['predicate'] = 'invented'
        try:
            routing.validate_analysis(value, self.task, self.sources)
        except EvidenceError as error:
            self.assertNotIsInstance(error, routing.CitationError)
        else:
            self.fail('Malformed analysis must be rejected')

    def test_citation_correction_preserves_all_claim_content(self):
        raw = deepcopy(self.analysis)
        raw['obligation_labels'][0]['evidence'][0]['line'] = 99
        self.assertEqual(routing.validate_citation_correction(raw, self.analysis, self.task, self.sources), ['B', 'I'])
        for key, value in [('contract','Different policy'), ('unknowns',[])]:
            edited = deepcopy(self.analysis)
            edited[key] = value if key == 'contract' else ['New uncertainty']
            with self.assertRaisesRegex(EvidenceError, '仅允许修改'):
                routing.validate_citation_correction(raw, edited, self.task, self.sources)
        prompt = routing.analysis_prompt('Header\n\nKeep the condition.', self.sources)
        self.assertIn('3 | Keep the condition.', prompt)
        self.assertIn('2 | persist(entry);', prompt)

    def test_cli_rejects_metadata_and_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            input_path, output = Path(directory)/'input.json', Path(directory)/'route.json'
            data = dict(task=self.task, sources=self.sources, analysis=self.analysis,
                        library=[self.entry], review=self.review())
            input_path.write_text(json.dumps(data), encoding='utf-8')
            with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                self.assertEqual(main(['route-experience', str(input_path), '--output', str(output)]), 0)
                before = output.read_bytes()
                self.assertEqual(main(['route-experience', str(input_path), '--output', str(output)]), 1)
                self.assertEqual(output.read_bytes(), before)
                input_path.write_text(json.dumps(dict(data, case_id='hidden-id')), encoding='utf-8')
                self.assertEqual(main(['route-experience', str(input_path)]), 1)
            self.assertEqual(json.loads(before)['condition'], 'ROUTED')

    def test_cli_exports_definition_schema_and_unapproved_review(self):
        for option in ('json', 'schema'):
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(main(['taxonomy', '--format', option]), 0)
            self.assertIsInstance(json.loads(output.getvalue()), dict)
        template = routing.review_template(self.analysis, self.task, self.sources)
        self.assertIsNone(template['approved'])
        self.assertIsNone(template['reviewer'])


if __name__ == '__main__':
    unittest.main()
