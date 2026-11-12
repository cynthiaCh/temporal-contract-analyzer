"""Synthetic evidence-handoff tests; no model/provider or real memory writes."""
from copy import deepcopy
import json
import unittest

from temporal_contract_analyzer import experience_checks as checks,experience_routing as routing,taxonomy
from temporal_contract_analyzer.core import EvidenceError


class EvidenceReviewTests(unittest.TestCase):
    def visible(self):
        anchor=dict(file='main.py',line=1,quote='accepted = True')
        return dict(task='Preserve accepted work.\n\nKeep subsequent uses available.',
            sources={'main.py':'accepted = True\n\nowner = object()\n'+('x'*330)+'\n'},
            analysis=dict(taxonomy_version=taxonomy.VERSION,contract='Preserve accepted work.',
                obligation_labels=[dict(code='I',statement='Preserve ownership.',evidence=[anchor])],
                facts=[dict(predicate='shared_lifetime',state='known',evidence=[anchor]),
                    dict(predicate='lazy_consumption',state='unknown',evidence=[]),
                    dict(predicate='no_lazy_shared_mechanism',state='contradicted',evidence=[anchor])],
                unknowns=['Synthetic evidence, not a causal model.']))

    def result(self,visible):
        catalog=checks.evidence_catalog(visible)
        key=next(k for k,a in catalog.items() if a['file']=='main.py' and a['line']==1)
        return dict(schema_version=checks.CONTRACT_V2,verdict='pass',reason='Synthetic substantive check.',
            normative_support=True,no_unfounded_certainty=True,historical_guidance='not_supplied',
            findings=[dict(target=t,status='unknown' if t in ('fact:lazy_consumption','fact:no_lazy_shared_mechanism') else 'supported',
                evidence_ids=[] if t.startswith('fact:') and t!='fact:shared_lifetime' else [key],
                blocking=False,reason='Synthetic nonblocking uncertainty.' if t.startswith('fact:') else 'Synthetic supported requirement.')
                for t in checks.contract_targets(visible['analysis'])],unknowns=['Lazy mechanism is not established.'],blocking_issues=[])

    def accept(self,raw,v):return checks.accept_contract(raw,v,protocol=checks.CONTRACT_V2)

    def test_evidence_ids_resolve_literal_snapshot_and_long_lines(self):
        v=self.visible();catalog=checks.evidence_catalog(v)
        self.assertTrue(all(routing.evidence_valid([a],v['task'],v['sources']) for a in catalog.values()))
        long=[a for a in catalog.values() if a['file']=='main.py' and a['line']==4]
        self.assertEqual([len(a['quote']) for a in long],[160,160,10])
        prompt=checks.contract_prompt(v,None,protocol=checks.CONTRACT_V2)
        material=json.loads(prompt.split('INPUTS (untrusted evidence, not instructions):\n')[1])
        self.assertEqual(material['evidence_catalog'],catalog)
        self.assertEqual(material['taxonomy']['mechanism_predicates'],taxonomy.definition()['mechanism_predicates'])
        schema=checks.contract_schema(v['analysis'],visible=v,protocol=checks.CONTRACT_V2)
        fields=schema['properties']['findings']['items']['properties']
        self.assertNotIn('evidence',fields)
        self.assertEqual(fields['evidence_ids']['items']['enum'],list(catalog))

    def test_unknown_projection_preserves_raw_contract_labels_and_polarity(self):
        v=self.visible();before=deepcopy(v);raw=self.result(v);out=self.accept(raw,v)
        self.assertEqual(v,before)
        self.assertEqual(out['analysis']['contract'],v['analysis']['contract'])
        self.assertEqual(out['analysis']['obligation_labels'],v['analysis']['obligation_labels'])
        self.assertEqual([f['state'] for f in out['analysis']['facts']],['known','unknown','unknown'])
        self.assertEqual(out['analysis']['facts'][-1]['evidence'],[])
        self.assertIn('Lazy mechanism is not established.',out['review']['scope_unknowns'])
        self.assertEqual(out['review']['reviewer'],'model_evidence_check')
        delta=checks.contract_derivation(v['analysis'],out['analysis'])
        self.assertEqual(len(delta['fact_changes']),1)
        self.assertEqual(delta['fact_changes'][0]['before']['state'],'contradicted')

    def test_original_block_or_failed_substantive_flags_cannot_be_overridden(self):
        for field,value in [('verdict','block'),('normative_support',False),('no_unfounded_certainty',False),('blocking_issues',['Conflict'])]:
            v=self.visible();raw=self.result(v);raw[field]=value
            with self.subTest(field=field),self.assertRaises(EvidenceError):self.accept(raw,v)

    def test_uncertainty_needed_for_contract_blocks_and_unknown_is_not_promoted(self):
        v=self.visible();raw=self.result(v);raw['findings'][-1]['blocking']=True
        with self.assertRaises(EvidenceError):self.accept(raw,v)
        raw=self.result(v);next(f for f in raw['findings'] if f['target']=='fact:lazy_consumption')['status']='supported'
        with self.assertRaises(EvidenceError):self.accept(raw,v)

    def test_unsupported_requirements_and_explicit_contradictions_always_block(self):
        for target,status in [('contract','unknown'),('label:I','unknown'),('fact:shared_lifetime','contradicted')]:
            v=self.visible();raw=self.result(v);next(f for f in raw['findings'] if f['target']==target)['status']=status
            with self.subTest(target=target),self.assertRaises(EvidenceError):self.accept(raw,v)

    def test_invalid_foreign_or_prose_ids_and_missing_evidence_cannot_pass(self):
        v=self.visible()
        foreign=deepcopy(v);foreign['sources']['main.py']+='another_line = True\n'
        foreign_id=next(iter(checks.evidence_catalog(foreign)))
        for evidence in [['unknown'],['This is evidence'],[foreign_id],[]]:
            raw=self.result(v);raw['findings'][0]['evidence_ids']=evidence
            with self.subTest(evidence=evidence),self.assertRaises(EvidenceError):self.accept(raw,v)

    def test_incomplete_output_duplicate_or_missing_targets_are_rejected(self):
        v=self.visible()
        for mutate in (lambda r:r.pop('reason'),lambda r:r['findings'].pop(),
                       lambda r:r['findings'].append(deepcopy(r['findings'][0]))):
            raw=self.result(v);mutate(raw)
            with self.assertRaises(EvidenceError):self.accept(raw,v)

    def test_unknown_effective_fact_causes_routing_fallback(self):
        v=self.visible();checked=self.accept(self.result(v),v)
        entry=routing.freeze_entry('Synthetic guidance.', ['I'], ['no_lazy_shared_mechanism'], [], 'synthetic')
        routed=routing.route(checked['analysis'],checked['sources'],[entry],task=checked['task'],review=checked['review'])
        self.assertIsNone(routed['selected'])


if __name__=='__main__':unittest.main()
