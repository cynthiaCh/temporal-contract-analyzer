"""Synthetic novelty/coverage gates; these tests are not model review or effect evidence."""
from copy import deepcopy
import unittest

from temporal_contract_analyzer import experience_checks as checks, experience_updates as updates
from temporal_contract_analyzer import experience_comparison as comparison
from temporal_contract_analyzer.core import EvidenceError
from temporal_contract_analyzer._session_runtime.schema_validator import validate


class IncrementComparisonTests(unittest.TestCase):
    def setUp(self):
        self.sha='a'*64
        self.priors={self.sha:dict(rules=[dict(id=k,category='event_relation',body='Synthetic '+k)
                                         for k in ('R03','R04','R06')],labels=['I'],requires=['entry_snapshot'],excludes=[])}
        self.visible=dict(analysis=dict(obligation_labels=[dict(code='I')],facts=[dict(predicate='entry_snapshot',state='known')]))
        self.context=dict(ledger=dict(TASK=dict(kind='original_task')),prior_experiences=self.priors)
        self.bundle=dict(parent_sha256=None,labels=['I'],requires=['entry_snapshot'],excludes=[],
                         rules=[dict(id='R01',category='event_relation',body='Synthetic merged reminder.')])
        self.row=dict(rule_id='R01',matches=[dict(experience_sha256=self.sha,rule_id=k,covered='Synthetic covered obligation.')
                                           for k in ('R03','R04','R06')],
                      uncovered_increment='',classification='duplicate',reason='Synthetic old rules jointly entail this reminder.')
        self.raw=dict(verdict='pass',reason='Synthetic review.',novelty_reason='Synthetic claim, not proof.',
            novelty_supported=True,conflict_free=True,boundaries_supported=True,no_unfounded_causality=True,
            unknowns=[],blocking_issues=[],rules=[dict(rule_id='R01',supported=True,support=['TASK'],reason='Synthetic normative support.')],
            increment_review=dict(compared_versions=[self.sha],comparisons=[deepcopy(self.row)]))

    def accept(self,raw):
        return checks.accept_candidate(raw,self.bundle,self.context,self.visible,protocol=checks.CANDIDATE_V2)

    def test_boolean_novelty_cannot_override_duplicate_evidence(self):
        before=deepcopy(self.raw)
        with self.assertRaisesRegex(EvidenceError,'duplicate'):self.accept(self.raw)
        self.assertEqual(before,self.raw)

    def test_supported_independent_increment_can_pass_without_human_acceptance(self):
        row=self.raw['increment_review']['comparisons'][0]
        row.update(classification='independent_new',uncovered_increment='Synthetic distinct requirement.')
        self.assertTrue(self.accept(self.raw))
        self.assertNotIn('human_acceptance',self.raw)

    def test_parentless_local_revision_is_blocked_without_reparenting(self):
        self.raw['increment_review']['comparisons'][0].update(classification='local_revision',uncovered_increment='Synthetic correction.')
        with self.assertRaisesRegex(EvidenceError,'local revision'):self.accept(self.raw)
        self.assertIsNone(self.bundle['parent_sha256'])

    def test_invalid_version_rule_pairs_and_incomplete_coverage_are_rejected(self):
        cases=[]
        value=deepcopy(self.raw);value['increment_review']['comparisons'][0]['matches'][0]['rule_id']='R99';cases.append(value)
        value=deepcopy(self.raw);value['increment_review']['compared_versions']=[];cases.append(value)
        value=deepcopy(self.raw);value['increment_review']['compared_versions']*=2;cases.append(value)
        value=deepcopy(self.raw);value['increment_review']['comparisons']=[];cases.append(value)
        value=deepcopy(self.raw);value['increment_review']['comparisons']*=2;cases.append(value)
        value=deepcopy(self.raw);value['increment_review']['comparisons'][0]['matches']*=2;cases.append(value)
        value=deepcopy(self.raw);value['increment_review']['comparisons'][0]['matches'][0]['experience_sha256']='b'*64;cases.append(value)
        for value in cases:
            with self.subTest(value=value),self.assertRaises(EvidenceError):self.accept(value)

    def test_pair_existence_is_checked_not_only_separate_id_enums(self):
        priors=deepcopy(self.priors);priors['b'*64]=dict(rules=[dict(id='R99')])
        value=dict(compared_versions=list(priors),comparisons=[deepcopy(self.row)])
        value['comparisons'][0]['matches'][0]['rule_id']='R99'
        validate(value,comparison.schema(priors,'rule_id',['R01']))
        with self.assertRaisesRegex(EvidenceError,'nonexistent'):comparison.check(value,priors,'rule_id',['R01'])

    def test_classifications_require_specific_increment_or_covered_rules(self):
        for kind,matches,increment in [('duplicate',[],''),('duplicate',self.row['matches'],'New words'),
                ('local_revision',self.row['matches'],''),('independent_new',[],''),('unchanged',[],''),
                ('insufficient_evidence',[],'Unsupported extra policy')]:
            value=dict(compared_versions=[self.sha],comparisons=[dict(self.row,classification=kind,matches=matches,uncovered_increment=increment)])
            with self.subTest(kind=kind),self.assertRaises(EvidenceError):comparison.check(value,self.priors,'rule_id',['R01'])

    def reflection(self):
        return dict(action='new',reason='Synthetic increment.',basis=['TASK'],parent_sha256=None,labels=['I'],
            requires=['entry_snapshot'],excludes=[],unresolved=[],changes=[dict(operation='add',rule_id=None,
            category='event_relation',body='Synthetic added rule.',support=['TASK'],causal_status='documented_relation')],
            increment_review=dict(compared_versions=[self.sha],comparisons=[dict(self.row,change_index=0)]))

    def compose(self,value):
        return updates.compose(value,self.visible,self.context['ledger'],self.priors,protocol=updates.DELTA_V2)

    def test_reflection_new_requires_increment_not_paraphrase(self):
        value=self.reflection();value['increment_review']['comparisons'][0].pop('rule_id')
        with self.assertRaisesRegex(EvidenceError,'substantive increment'):self.compose(value)
        value['increment_review']['comparisons'][0].update(classification='independent_new',uncovered_increment='Synthetic new boundary.')
        self.assertEqual(self.compose(value)['rules'][0]['body'],'Synthetic added rule.')

    def test_reflection_local_revision_must_name_parent_and_compare_affected_rule(self):
        value=self.reflection();row=value['increment_review']['comparisons'][0];row.pop('rule_id')
        row.update(classification='local_revision',uncovered_increment='Synthetic correction.')
        with self.assertRaisesRegex(EvidenceError,'exact parent'):self.compose(value)
        value.update(action='revise',parent_sha256=self.sha);value['changes'][0].update(operation='replace',rule_id='R03')
        self.assertEqual(len(self.compose(value)['rules']),3)
        row['matches']=[m for m in row['matches'] if m['rule_id']!='R03']
        with self.assertRaisesRegex(EvidenceError,'direct comparison'):self.compose(value)

    def test_no_update_records_duplicate_or_unknown_without_rewriting_proposal(self):
        value=self.reflection();value.update(action='no_update',changes=[],parent_sha256=None,labels=None,requires=None,excludes=None)
        row=value['increment_review']['comparisons'][0];row.pop('rule_id');row['change_index']=None
        self.assertIsNone(self.compose(value))
        row.update(matches=[],classification='insufficient_evidence',reason='Synthetic uncertainty retained.')
        self.assertIsNone(self.compose(value))
        row.update(classification='independent_new',uncovered_increment='Synthetic new requirement.')
        with self.assertRaisesRegex(EvidenceError,'no_update'):self.compose(value)

    def test_v1_receipts_remain_readable_but_do_not_satisfy_v2(self):
        value=self.reflection();value.pop('increment_review')
        self.assertIsNotNone(updates.compose(value,self.visible,self.context['ledger'],self.priors))
        with self.assertRaises(EvidenceError):self.compose(value)
        legacy=deepcopy(self.raw);legacy.pop('increment_review')
        self.assertTrue(checks.accept_candidate(legacy,self.bundle,self.context,self.visible))
        with self.assertRaises(EvidenceError):self.accept(legacy)

    def test_prompts_request_semantic_joint_coverage_and_preserve_original_action(self):
        prompt=checks.candidate_prompt(self.bundle,self.context,protocol=checks.CANDIDATE_V2)
        for term in ('every supplied prior','jointly imply','retained audit','startup-window','retrospective no_update'):
            self.assertIn(term,prompt)


if __name__=='__main__':unittest.main()
