"""Business retrieval uses synthetic judgments/public evidence, never benchmark scores."""
from copy import deepcopy
from pathlib import Path
import json
import tempfile
import unittest

from temporal_contract_analyzer import business_retrieval as retrieval,compact_experience as compact,experience_approval as approval
from temporal_contract_analyzer.core import EvidenceError
from temporal_contract_analyzer.tempoevo_v4 import Trajectory,MODEL
from test_tempoevo_v4 import Backend

TASK='Preserve accepted work. Coalesce document edits; preserve existing submission and departure behavior.'
ANCHOR=dict(file='TASK',quote='Preserve accepted work.')


def item(code,text):
    return dict(id=code,title=text,labels=['O','L','I'],requires=['deferred_batch'],excludes=['different_ownership_policy'],
        applicability=text,event_relation=text,preservation='Preserve original public behavior.',exclusion='Check current policy.',verification='Exercise callbacks.',
        review=dict(reviewer='Synthetic fixture reviewer',decision='accept',at='2026-11-17T00:00:00Z'))


def assessment(candidate,coverage,relevance='direct'):
    return dict(sha256=candidate['sha256'],relevance=relevance,
        premises=[dict(condition='Current operation maps to the proposed rule.',status='supported',evidence=[ANCHOR])],
        predicate_findings=[dict(kind=k,predicate=p,state='known' if k=='requires' else 'contradicted',evidence=[ANCHOR]) for k in ('requires','excludes') for p in candidate[k]],
        object_mapping='Current document owner and save callback.',contribution='Preserve the stated operation.',covered_obligations=coverage,
        supporting_evidence=[ANCHOR],redundant_with=[],reason='Synthetic source-backed judgment.')


class BusinessRetrievalTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.library=self.root/'library';self.library.mkdir()
        (self.library/'entries.json').write_text(json.dumps(dict(schema_version=compact.VERSION,experiences=[
            item('save-rule','Coalesce document edits and retain accepted saves.'),
            item('progress-rule','Decode progress packets and preserve audit history.'),
            item('departure-rule','Preserve document saves at departure.')])))
        self.snapshot=approval.freeze(self.library);self.bundles=[x['bundle'] for x in self.snapshot['entries']]
        self.recalled=retrieval.recall(TASK,{'main.py':'value = 0\n'},self.bundles)

    def response(self):
        obligations=[dict(id='O1',text='Preserve accepted edits.',evidence=[ANCHOR]),dict(id='O2',text='Preserve departure behavior.',evidence=[ANCHOR])]
        candidates={c['id']:c for c in self.recalled['candidates']}
        rows=[assessment(candidates['save-rule'],['O1']),assessment(candidates['departure-rule'],['O2']),assessment(candidates['progress-rule'],['O1'],relevance='not_applicable')]
        return dict(business_obligations=obligations,assessments=rows)

    def select(self,value):return retrieval.select(value,self.recalled,TASK,{'main.py':'value = 0\n'},self.bundles)

    def test_all_approved_candidates_are_assessed_without_a_label_or_unknown_prefilter(self):
        self.assertEqual(len(self.recalled['candidates']),3)
        out=self.select(self.response());ids={b['sha256']:b['id'] for b in self.bundles}
        self.assertEqual({ids[c] for c in out['selected_sha256s']},{'save-rule','departure-rule'})
        self.assertEqual(out['covered_obligations'],['O1','O2']);self.assertFalse(out['effectiveness_verified'])

    def test_unknown_or_incomplete_applicability_is_not_promoted_to_supported(self):
        for kind in ('unknown_requires','unknown_exclusion','missing_finding','unknown_business_premise'):
            value=self.response();row=value['assessments'][0]
            if kind=='unknown_requires':row['predicate_findings'][0]['state']='unknown'
            elif kind=='unknown_exclusion':row['predicate_findings'][1]['state']='unknown'
            elif kind=='missing_finding':row['predicate_findings'].pop()
            else:row['premises'][0]['status']='unknown'
            self.assertNotIn(row['sha256'],self.select(value)['selected_sha256s'])

    def test_unmatched_quotes_or_foreign_coverage_cannot_admit_guidance(self):
        value=self.response();value['assessments'][0]['supporting_evidence'][0]=dict(ANCHOR,quote='Invented source statement')
        with self.assertRaises(EvidenceError):self.select(value)
        value=self.response();value['assessments'][0]['covered_obligations']=['not-an-obligation']
        with self.assertRaises(EvidenceError):self.select(value)
        value=self.response();value['assessments'][0]['predicate_findings'].append(deepcopy(value['assessments'][0]['predicate_findings'][0]))
        with self.assertRaises(EvidenceError):self.select(value)

    def test_complementary_coverage_precedes_high_text_score_repetition(self):
        value=self.response();row=value['assessments'][2];row['relevance']='direct'
        for c in self.recalled['candidates']:c['lexical_score']={'save-rule':100,'progress-rule':99,'departure-rule':1}[c['id']]
        out=self.select(value);ids={b['sha256']:b['id'] for b in self.bundles}
        self.assertEqual([ids[c] for c in out['selected_sha256s']],['save-rule','departure-rule'])
        self.assertEqual(next(x for x in out['decisions'] if x['sha256']==row['sha256'])['selection_reason'],'no_new_obligation_coverage')

    def test_every_candidate_and_unique_business_obligations_are_required(self):
        value=self.response();value['assessments'].pop()
        with self.assertRaises((EvidenceError,ValueError)):self.select(value)
        value=self.response();value['business_obligations'].append(deepcopy(value['business_obligations'][0]))
        with self.assertRaises(EvidenceError):self.select(value)

    def test_pipeline_has_selection_draft_action_and_one_gold_without_review_or_routing(self):
        source=self.root/'source';source.mkdir();(source/'main.py').write_text('value = 0\n')
        loop=Trajectory(self.root/'trajectory');cfg=dict(task=TASK,candidate=str(source),store=str(self.library),mode='testing',condition='structured',
            retrieval_profile='business-source-v1',memory_snapshot=self.snapshot,gold_evaluator=dict(command=['synthetic-gold']))
        loop.prepare(cfg);protocol=loop.verify();self.assertEqual(protocol['total_request_cap'],48);self.assertIsNone(protocol['contract_review_policy'])
        expected=self.response()
        class Selector(Backend):
            def execute(inner,kind,payload,model,limits,directory):
                if kind=='selection':
                    inner.calls.append((kind,deepcopy(payload),model,limits))
                    return dict(valid=True,requests=1,model=model,output=deepcopy(expected))
                return super().execute(kind,payload,model,limits,directory)
        backend=Selector();state=loop.run(backend,execute=True)
        self.assertEqual(state['status'],'scored',state.get('error'));self.assertEqual([x[0] for x in backend.calls],['selection','contract','action'])
        self.assertEqual(sum(x['kind']=='gold' for x in state['stages']),1);self.assertEqual(len(state['attempts']),1)
        self.assertEqual(approval.freeze(self.library),self.snapshot)
        self.assertEqual(len(next(x[1] for x in backend.calls if x[0]=='contract')['business_obligations']),2)
        self.assertNotIn('SECRET_GOLD',json.dumps(backend.calls))


if __name__=='__main__':unittest.main()
