"""Location drift must not discard literal source evidence or invent applicability."""
from copy import deepcopy
import unittest
from temporal_contract_analyzer import experience_routing as r, taxonomy


class GroundingTests(unittest.TestCase):
    def view(self, task='Keep the entry\nsnapshot after navigation.', quote='entry snapshot', path='TASK', state='known'):
        anchor=dict(file=path,line=99,quote=quote)
        analysis=dict(taxonomy_version=taxonomy.VERSION,contract='Retain entry identity.',
            obligation_labels=[dict(code='I',statement='Retain entry identity.',evidence=[anchor])],
            facts=[dict(predicate='entry_snapshot',state=state,evidence=[anchor])],unknowns=[])
        review=dict(input_sha256=r.input_digest(analysis,task,{}),reviewer='unreviewed_model_analysis',
            approved=False,blocking_issues=[],scope_unknowns=[],evidence=[],reason='Raw model analysis.')
        entry=r.freeze_entry('Capture the accepted entry.', ['I'],['entry_snapshot'],[],'fixture')
        return analysis,task,review,[entry]

    def decision(self, values):
        a,t,v,library=values
        return r.route(a,{},library,task=t,review=v)

    def test_literal_wrapped_quote_routes_without_rewriting_or_approval(self):
        values=self.view();before=deepcopy(values)
        self.assertEqual(self.decision(values)['condition'],'ROUTED')
        self.assertEqual(values,before)
        a,t,_,_=values
        with self.assertRaises(r.CitationError):r.validate_analysis(a,t,{})

    def test_line_offset_routes(self):
        self.assertEqual(self.decision(self.view(task='Keep the entry snapshot.'))['condition'],'ROUTED')

    def test_absent_words_missing_file_or_empty_quote_do_not_route(self):
        for change in (dict(quote='invented promise'),dict(path='missing.js'),dict(quote=' ')):
            with self.subTest(change=change):
                self.assertEqual(self.decision(self.view(**change))['condition'],'AUTO')

    def test_unknown_premise_still_does_not_route(self):
        self.assertEqual(self.decision(self.view(state='unknown'))['condition'],'AUTO')

    def test_reviewed_analysis_and_review_quotes_also_tolerate_location_drift(self):
        values=self.view();values[2].update(reviewer='human_visible_input_only',approved=True,
                         evidence=[dict(file='TASK',line=99,quote='entry snapshot')])
        self.assertEqual(self.decision(values)['condition'],'ROUTED')

    def test_label_mismatch_is_not_promoted_by_valid_quotation(self):
        values=self.view()
        values[3][0]=r.freeze_entry('Different lifecycle rule.', ['L'],['entry_snapshot'],[],'other')
        self.assertEqual(self.decision(values)['condition'],'AUTO')

    def test_confirmed_exclusion_still_prevents_matching(self):
        values=self.view()
        values[3][0]=r.freeze_entry('Excluded here.', ['I'],['entry_snapshot'],['inline_reentry'],'other')
        values[0]['facts'].append(dict(predicate='inline_reentry',state='known',
            evidence=[dict(file='TASK',line=99,quote='entry snapshot')]))
        values[2]['input_sha256']=r.input_digest(values[0],values[1],{})
        self.assertEqual(self.decision(values)['condition'],'AUTO')

    def test_changed_analysis_cannot_reuse_snapshot(self):
        values=self.view();values[0]['contract']='Changed contract.'
        self.assertEqual(self.decision(values)['condition'],'AUTO')
