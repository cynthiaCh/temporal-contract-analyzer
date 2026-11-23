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

    def latent_loop(self,selection,**changes):
        source=self.root/'source';source.mkdir(exist_ok=True);(source/'main.py').write_text('value = 0\n')
        config=dict(task=TASK,candidate=str(source),store=str(self.library),mode='testing',
                    condition='latent_experience',memory_snapshot=self.snapshot,frozen_selection=selection,
                    gold_evaluator=dict(command=['synthetic-gold']))
        config.update(changes)
        loop=Trajectory(self.root/'latent');loop.prepare(config);return loop

    def test_latent_experience_reuses_exact_guidance_with_action_only_and_final_gold(self):
        from temporal_contract_analyzer.core import canonical,sha
        output=self.response();delivery=self.select(output);delivery['provisional_sha256s']=[]
        frozen=dict(output=output,delivery_sha256=sha(canonical(delivery).encode()))
        loop=self.latent_loop(frozen);protocol=loop.verify()
        self.assertEqual(protocol['total_request_cap'],24)
        backend=Backend();state=loop.run(backend,execute=True)
        self.assertEqual(state['status'],'scored',state.get('error'))
        self.assertEqual([role for role,*_ in backend.calls],['action'])
        payload=backend.calls[0][1]
        self.assertIsNone(payload['contract']);self.assertEqual(payload['experience'],delivery['experience_text'])
        self.assertNotIn('business_obligations',payload);self.assertNotIn('frozen_selection',payload)
        self.assertEqual([s['kind'] for s in state['stages']],['action','gold'])
        self.assertEqual(json.loads((loop.root/'delivery.json').read_text()),delivery)

    def test_frozen_experience_rejects_drift_and_unbound_delivery(self):
        from temporal_contract_analyzer.core import canonical,sha
        output=self.response();delivery=self.select(output);delivery['provisional_sha256s']=[]
        frozen=dict(output=output,delivery_sha256=sha(canonical(delivery).encode()))
        with self.assertRaisesRegex(EvidenceError,'mismatch'):
            self.latent_loop(dict(frozen,delivery_sha256='0'*64))
        with self.assertRaisesRegex(EvidenceError,'derived'):
            self.latent_loop(frozen,frozen_experience_delivery=delivery)
        with self.assertRaisesRegex(EvidenceError,'frozen testing'):
            self.latent_loop(frozen,mode='learning')
        altered=deepcopy(frozen);altered['output']['assessments'][0]['supporting_evidence'][0]['quote']='Fabricated evidence'
        with self.assertRaises(EvidenceError):
            self.latent_loop(altered)

    def test_frozen_invalid_selection_remains_empty_without_contract_fallback(self):
        from temporal_contract_analyzer.core import canonical,sha
        delivery=dict(selected_sha256s=[],experience_text=None,reason='invalid_business_selection_discarded',provisional_sha256s=[])
        loop=self.latent_loop(dict(output=None,delivery_sha256=sha(canonical(delivery).encode())))
        backend=Backend();state=loop.run(backend,execute=True)
        self.assertEqual(state['status'],'scored',state.get('error'))
        self.assertEqual([role for role,*_ in backend.calls],['action'])
        self.assertIsNone(backend.calls[0][1]['experience']);self.assertIsNone(backend.calls[0][1]['contract'])

    def test_small_banks_are_assessed_without_a_label_or_unknown_prefilter(self):
        self.assertEqual(len(self.recalled['candidates']),3)
        out=self.select(self.response());ids={b['sha256']:b['id'] for b in self.bundles}
        self.assertEqual({ids[c] for c in out['selected_sha256s']},{'save-rule','departure-rule'})
        self.assertEqual(out['covered_obligations'],['O1','O2']);self.assertFalse(out['effectiveness_verified'])

    def test_summary_prefilter_limits_candidates_and_preserves_full_rules(self):
        bundles=[]
        for i in range(12):
            b=deepcopy(self.bundles[0]);b.update(id='rule-'+str(i),sha256=format(i,'064x'))
            for r in b['rules']:
                r['body']='Unrelated operation. Historical example mentions quiescence.'
            if i==11:
                b['rules'][0]['body']='Quiescence must precede resource release. '+('Historical detail. '*100)
            bundles.append(b)
        before=deepcopy(bundles)
        recalled=retrieval.recall('quiescence',{},bundles)
        self.assertEqual(recalled['candidates'][0]['id'],'rule-11')
        self.assertEqual(len(recalled['candidates']),6)
        self.assertEqual(len(recalled['omitted_candidate_sha256s']),6)
        self.assertEqual(recalled,retrieval.recall('quiescence',{},list(reversed(bundles))))
        self.assertEqual(bundles,before)
        self.assertIn('Historical detail.',recalled['candidates'][0]['text'])
        self.assertNotIn('Historical detail.',recalled['candidates'][0]['summary'])
        self.assertLessEqual(len(recalled['candidates'][0]['summary']),900)
        self.assertEqual(retrieval.recall('quiescence',{},[])['candidates'],[])

    def test_summary_bounds_long_conditions_and_keeps_exclusion_preview(self):
        b=deepcopy(self.bundles[0])
        for r in b['rules']:r['body']='x'*1000
        preview=retrieval.summary(b)
        self.assertIn('Applicability:',preview)
        self.assertIn('Exclusion:',preview)
        self.assertLessEqual(len(preview),900)

    def test_concise_negative_rows_do_not_admit_experience(self):
        from temporal_contract_analyzer._session_runtime.schema_validator import validate
        output=self.response()
        output['assessments'][2]={k:output['assessments'][2][k] for k in ('sha256','relevance','reason')}
        validate(output,retrieval.schema(self.recalled['candidates'],concise=True))
        selected=self.select(output)
        self.assertEqual(len(selected['selected_sha256s']),2)
        output['assessments'][2]['relevance']='direct'
        with self.assertRaises(ValueError):validate(output,retrieval.schema(self.recalled['candidates'],concise=True))
        self.assertEqual(len(self.select(output)['selected_sha256s']),2)

    def test_concise_schema_rejects_long_prose_and_repeated_quotes(self):
        from temporal_contract_analyzer._session_runtime.schema_validator import validate
        output=self.response();output['assessments']=output['assessments'][:2]
        schema=retrieval.schema(self.recalled['candidates'],concise=True)
        validate(output,schema)
        for field in ('reason','object_mapping','contribution'):
            bad=deepcopy(output);bad['assessments'][0][field]='x'*241
            with self.subTest(field=field),self.assertRaises(ValueError):validate(bad,schema)
        bad=deepcopy(output);bad['assessments'][0]['supporting_evidence']=[ANCHOR]*3
        with self.assertRaises(ValueError):validate(bad,schema)


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
        self.assertEqual(self.select(value)['selected_sha256s'],[value['assessments'][1]['sha256']])
        value=self.response();value['assessments'][0]['covered_obligations']=['not-an-obligation']
        self.assertEqual(self.select(value)['selected_sha256s'],[value['assessments'][1]['sha256']])
        value=self.response();value['assessments'][0]['predicate_findings'].append(deepcopy(value['assessments'][0]['predicate_findings'][0]))
        self.assertEqual(self.select(value)['selected_sha256s'],[value['assessments'][1]['sha256']])

    def test_complementary_coverage_precedes_high_text_score_repetition(self):
        value=self.response();row=value['assessments'][2];row['relevance']='direct'
        for c in self.recalled['candidates']:c['lexical_score']={'save-rule':100,'progress-rule':99,'departure-rule':1}[c['id']]
        out=self.select(value);ids={b['sha256']:b['id'] for b in self.bundles}
        self.assertEqual([ids[c] for c in out['selected_sha256s']],['save-rule','departure-rule'])
        self.assertEqual(next(x for x in out['decisions'] if x['sha256']==row['sha256'])['selection_reason'],'no_new_obligation_coverage')

    def test_missing_candidates_are_not_inferred_and_identical_obligations_are_deduplicated(self):
        value=self.response();value['assessments'].pop()
        out=self.select(value);self.assertEqual(len(out['selected_sha256s']),2)
        self.assertTrue(any(x['selection_reason']=='missing_assessment' for x in out['decisions']))
        value=self.response();value['business_obligations'].append(deepcopy(value['business_obligations'][0]))
        out=self.select(value);self.assertEqual(len(out['selected_sha256s']),2)
        self.assertEqual(len(out['business_obligations']),2)

    def test_identical_candidate_duplicates_are_deduplicated_and_conflicts_are_rejected(self):
        value=self.response();value['assessments'].append(deepcopy(value['assessments'][0]))
        self.assertEqual(len(self.select(value)['selected_sha256s']),2)
        value['assessments'][-1]['relevance']='unknown'
        for rows in (value['assessments'],list(reversed(value['assessments']))):
            out=self.select(dict(value,assessments=rows))
            self.assertEqual(out['selected_sha256s'],[value['assessments'][1]['sha256']])
            self.assertTrue(any(x['selection_reason']=='conflicting_assessments' for x in out['decisions']))

    def test_invalid_obligations_only_reject_dependent_candidates(self):
        for kind in ('conflict','bad_quote'):
            value=self.response()
            if kind=='conflict':value['business_obligations'].append(dict(value['business_obligations'][0],text='Conflicting definition'))
            else:value['business_obligations'][0]['evidence']=[dict(ANCHOR,quote='Invented')]
            out=self.select(value)
            self.assertEqual(out['selected_sha256s'],[value['assessments'][1]['sha256']])
            self.assertEqual([x['id'] for x in out['business_obligations']],['O2'])

    def test_malformed_foreign_and_wrong_predicate_rows_are_quarantined(self):
        for kind in ('malformed','foreign','predicate','unexpected_predicate'):
            value=self.response();row=value['assessments'][0]
            if kind=='malformed':row.pop('premises')
            elif kind=='foreign':row['sha256']='foreign'
            elif kind=='predicate':row['predicate_findings'][0]['predicate']='invented-predicate'
            else:row['predicate_findings'][0]['predicate']='shared_lifetime'
            out=self.select(value)
            self.assertEqual(out['selected_sha256s'],[value['assessments'][1]['sha256']])
            self.assertTrue(out['validation']['partial'])

    def test_entirely_unusable_output_still_requires_correction(self):
        for value in ({},dict(self.response(),assessments=[]),dict(self.response(),business_obligations=[])):
            with self.assertRaises((EvidenceError,ValueError)):self.select(value)

    def test_training_uses_frozen_abstracts_and_reselects_without_taxonomy_analysis(self):
        for file,value in compact.documents(self.library):
            for record in value['experiences']:
                compact.save_summary(self.library,dict(id=record['id'],expected_record=compact._bundle(file,record)[0]['sha256'],
                    expected_summary=None,text='Accepted abstract for '+record['id'],expert_questions='None.',
                    reviewer='Synthetic fixture reviewer',decision='accept'))
        snapshot=approval.freeze(self.library)
        abstracts={entry['bundle']['sha256']:entry['retrieval_summary']['text'] for entry in snapshot['entries']}
        source=self.root/'source';source.mkdir();(source/'main.py').write_text('value = 0\n')
        for condition,recipe in [('structured',None),('structured','v8-compatible-v1'),('fixed_contract','v8-compatible-v1')]:
            with self.subTest(condition=condition,recipe=recipe):
                config=dict(task=TASK,candidate=str(source),store=str(self.library),mode='learning',condition=condition,
                    visible_evaluator=dict(command=['synthetic-visible']),training_evaluator=dict(command=['synthetic-training']),
                    memory_snapshot=snapshot)
                if recipe:config['training_recipe']=recipe
                loop=Trajectory(self.root/('training-'+condition+'-'+str(recipe)));loop.prepare(config)
                protocol=loop.verify()
                self.assertEqual(protocol['retrieval_profile'],'business-source-v1')
                self.assertEqual(protocol['total_request_cap'],156 if condition=='structured' else 132)
                self.assertEqual(protocol['max_attempts'],3)
                backend=Backend(2,diagnosis='contract_gap' if condition=='structured' else 'implementation_gap',revise=condition=='structured')
                state=loop.run(backend,execute=True)
                self.assertEqual(state['status'],'passed',state.get('error'))
                self.assertEqual(len(state['attempts']),2)
                self.assertTrue((loop.root/'candidate-pool/success.json').is_file())
                self.assertEqual(protocol['memory_snapshot'],snapshot)
                kinds=[kind for kind,*_ in backend.calls]
                self.assertNotIn('routing',kinds)
                self.assertEqual(kinds.count('selection'),2 if condition=='structured' else 1)
                self.assertEqual(kinds[-1],'extract')
                for kind,payload,*_ in backend.calls:
                    if kind=='selection':
                        for candidate in payload['candidates']:
                            self.assertEqual(candidate['summary'],abstracts[candidate['sha256']])
                            self.assertIn('Preserve original public behavior.',candidate['text'])
                    if kind=='diagnosis':self.assertNotIn('routing_recheck_required',payload)
                    if kind=='action':self.assertTrue(payload['experience'])
                if condition=='structured':
                    self.assertTrue((loop.root/'revisions/2-delivery.json').is_file())
                    self.assertNotIn('routing_analysis',state['diagnoses'][0])
                if recipe:
                    for kind,payload,*_ in backend.calls:
                        if kind=='action':self.assertNotIn('within_task_reflections',payload)

    def test_pipeline_has_selection_draft_action_and_one_gold_without_review_or_routing(self):
        source=self.root/'source';source.mkdir();(source/'main.py').write_text('value = 0\n')
        loop=Trajectory(self.root/'trajectory');cfg=dict(task=TASK,candidate=str(source),store=str(self.library),mode='testing',condition='structured',
            retrieval_profile='business-source-v1',memory_snapshot=self.snapshot,gold_evaluator=dict(command=['synthetic-gold']))
        loop.prepare(cfg);protocol=loop.verify();self.assertEqual(protocol['total_request_cap'],48);self.assertIsNone(protocol['contract_review_policy'])
        expected=self.response()
        expected['assessments'][2]['predicate_findings'].append(deepcopy(expected['assessments'][2]['predicate_findings'][0]))
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
        delivery=json.loads((loop.root/'delivery.json').read_text())
        self.assertEqual(len(delivery['selected_sha256s']),2)
        self.assertTrue(delivery['validation']['partial'])
        self.assertTrue((loop.root/'retrieval/selection-1-validation.json').is_file())
        self.assertTrue(any(w['code']=='business_selection_partial' for w in state['preparation_warnings']))
        for kind,payload,_,_ in backend.calls:
            if kind in ('contract','action'):
                self.assertEqual(payload['experience'],delivery['experience_text'])
                self.assertTrue(payload['experience'])


if __name__=='__main__':unittest.main()
