"""Synthetic schema/composer parity regressions; no model or store operations."""
from copy import deepcopy
import unittest

from temporal_contract_analyzer import experience_updates as updates
from temporal_contract_analyzer._session_runtime.schema_validator import validate
from temporal_contract_analyzer.core import EvidenceError


class DeltaSchemaTests(unittest.TestCase):
    def setUp(self):
        self.visible=dict(analysis=dict(obligation_labels=[dict(code='I')],
            facts=[dict(predicate='entry_snapshot',state='known')]))
        self.ledger=dict(TASK=dict(kind='original_task'))
        self.parent=dict(rules=[dict(id='R01',category='verification',body='Synthetic old rule.')],labels=['I'],requires=['entry_snapshot'],excludes=[])
        self.parents={'a'*64:self.parent}
        self.value=dict(action='new',reason='Synthetic evidence.',basis=['TASK'],parent_sha256=None,
            labels=['I'],requires=['entry_snapshot'],excludes=[],unresolved=[],changes=[dict(operation='add',rule_id=None,
                category='verification',body='Synthetic new rule.',support=['TASK'],causal_status='documented_relation')])

    def test_add_rejects_model_numbering_in_schema_and_composer(self):
        value=deepcopy(self.value);value['changes'][0]['rule_id']='R01'
        with self.assertRaises(ValueError):validate(value,updates.schema(self.visible,self.ledger,self.parents))
        with self.assertRaises(EvidenceError):updates.compose(value,self.visible,self.ledger,self.parents)

    def test_add_numbering_is_deterministic_and_raw_body_is_unchanged(self):
        before=deepcopy(self.value);result=updates.compose(self.value,self.visible,self.ledger,self.parents)
        self.assertEqual(result['rules'],[dict(id='R01',category='verification',body='Synthetic new rule.')])
        self.assertEqual(self.value,before)

    def test_no_update_can_reference_existing_guidance_without_mutating_it(self):
        value=deepcopy(self.value)
        value.update(action='no_update',parent_sha256='a'*64,changes=[],
                     labels=None,requires=None,excludes=None)
        before=deepcopy(value);parents=deepcopy(self.parents)
        self.assertIsNone(updates.compose(value,self.visible,self.ledger,self.parents))
        self.assertEqual(value,before)
        self.assertEqual(self.parents,parents)
        value['parent_sha256']='b'*64
        with self.assertRaises(EvidenceError):
            updates.compose(value,self.visible,self.ledger,self.parents)

    def test_no_update_context_cannot_modify_guidance_or_hide_rule_operations(self):
        value=deepcopy(self.value)
        value.update(action='no_update',parent_sha256='a'*64,changes=[],
                     labels=None,requires=None,excludes=None)
        for field,context in [('labels',['I']),('requires',['entry_snapshot']),('excludes',[])]:
            supplied=deepcopy(value);supplied[field]=context;before=deepcopy(supplied);parents=deepcopy(self.parents)
            with self.subTest(field=field):
                self.assertIsNone(updates.compose(supplied,self.visible,self.ledger,self.parents))
                self.assertEqual(supplied,before);self.assertEqual(self.parents,parents)
        value['changes']=self.value['changes']
        with self.assertRaises(EvidenceError):
            updates.compose(value,self.visible,self.ledger,self.parents)

    def test_parent_replacement_requires_actual_parent_id(self):
        value=deepcopy(self.value);value.update(action='revise',parent_sha256='a'*64)
        value['changes'][0].update(operation='replace',rule_id='R01')
        self.assertEqual(updates.compose(value,self.visible,self.ledger,self.parents)['rules'][0]['body'],'Synthetic new rule.')
        for wrong in (None,'R99'):
            value['changes'][0]['rule_id']=wrong
            with self.assertRaises(ValueError):validate(value,updates.schema(self.visible,self.ledger,self.parents))

    def test_independent_new_can_cite_prior_guidance_without_inheriting_it(self):
        value=deepcopy(self.value);value['parent_sha256']='a'*64;before=deepcopy(value)
        result=updates.compose(value,self.visible,self.ledger,self.parents)
        self.assertIsNone(result['parent'])
        self.assertEqual(len(result['rules']),1)
        self.assertEqual(result['rules'][0]['body'],value['changes'][0]['body'])
        self.assertEqual(value,before)
        value['changes'][0].update(operation='replace',rule_id='R01')
        with self.assertRaisesRegex(EvidenceError,'Independent new guidance'):
            updates.compose(value,self.visible,self.ledger,self.parents)

    def test_removal_cannot_also_carry_new_text(self):
        value=deepcopy(self.value);value.update(action='revise',parent_sha256='a'*64)
        value['changes'][0].update(operation='remove',rule_id='R01')
        schema=updates.schema(self.visible,self.ledger,self.parents)
        with self.assertRaises(ValueError):validate(value,schema)
        value['changes'][0].update(body=None,category=None)
        validate(value,schema)
        with self.assertRaises(EvidenceError):updates.compose(value,self.visible,self.ledger,self.parents)

    def test_anyof_still_enforces_branch_types_fields_and_siblings(self):
        schema=dict(anyOf=[dict(type='string',enum=['ok']),dict(type='integer',minimum=2)],enum=['ok',2])
        for value in ('ok',2):self.assertEqual(validate(value,schema),value)
        for value in ('other',1,3,True,None):
            with self.assertRaises(ValueError):validate(value,schema)


if __name__=='__main__':unittest.main()
