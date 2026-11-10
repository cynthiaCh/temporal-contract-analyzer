"""AST-assisted analysis lifecycle; all model responses are synthetic fixtures."""
from contextlib import redirect_stdout
from copy import deepcopy
from io import StringIO
import json
from pathlib import Path
import unittest

import test_experience_evolution as fixtures
from temporal_contract_analyzer.cli import main
from temporal_contract_analyzer.core import EvidenceError
from temporal_contract_analyzer.experience_evolution import Evolution, load
from temporal_contract_analyzer.preanalysis import analyze_candidate


class AutoContractTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixtures.EvolutionTests('test_complete_develop_review_activate_and_next_task_retrieval')
        self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
        self.root=self.fixture.root

    def config(self):
        return dict(case_id='development',store=str(self.fixture.store),binary='/synthetic/codex',
                    node='/synthetic/node',calibration=dict(synthetic=True),
                    source_relationship='Synthetic source-only analysis fixture.')

    def prepare(self):
        config=self.config();config['visible']=None
        loop=Evolution(self.root/'auto-loop');loop.prepare(**config)
        return loop

    def backend(self,analysis=None,fail=None):
        output=deepcopy(self.fixture.visible()['analysis'] if analysis is None else analysis)
        class AnalysisBackend(fixtures.SyntheticBackend):
            def execute(self,protocol,role,prompt,schema,directory):
                if role!='analysis':return super().execute(protocol,role,prompt,schema,directory)
                self.calls.append((directory.name,role,prompt))
                if directory.name==self.fail:
                    return dict(completed=False,infrastructure_valid=False,usage=None,output=None)
                return dict(completed=True,infrastructure_valid=True,output=deepcopy(output),
                            usage=dict(requests_started=1,total_usage=None,usage_unknown_requests=1))
        return AnalysisBackend(fail=fail)

    def reviewed(self,loop,analysis=None):
        request=load(loop.root/'analysis/review-input.json')
        if analysis is not None:request['analysis']=analysis
        request.update(reviewer='execution_agent_visible_input_only',approved=True,
                       reason='Synthetic source-only review fixture; no actual expert approval.',
                       evidence=[dict(file='main.py',line=1,quote='accepted = True')])
        return request

    def test_prepare_cli_without_visible_generates_ast_and_prompt_without_models(self):
        config=self.root/'config.json';config.write_text(json.dumps(self.config()))
        root=self.root/'auto-loop'
        with redirect_stdout(StringIO()):
            self.assertEqual(main(['experience-evolution','prepare',str(config),'--root',str(root)]),0)
        loop=Evolution(root)
        self.assertEqual(loop.state()['status'],'analysis_prepared')
        self.assertEqual(loop.state()['jobs'],[])
        material=json.loads((root/'analysis/prompt.md').read_text().split('Public inputs:\n',1)[1])
        self.assertEqual(material['AST'],load(root/'analysis/ast-evidence.json'))
        self.assertIn('accepted = True',material['numbered_sources']['main.py'])
        self.assertFalse((root/'initial-route.json').exists())
        self.assertEqual(load(root/'analysis/ast-report.json')['status'],'parsed')

    def test_selection_keeps_rule_evidence_relations_and_coverage_without_provenance(self):
        report,selected=analyze_candidate({'main.py':
            'async def save():\n    await fetch()\n    publish()\n',
            'README.md':'This documentation remains part of the numbered source input.'})
        self.assertEqual(selected['status'],'parsed')
        self.assertEqual([f['rule'] for f in selected['findings']],['effect-after-await'])
        expected={eid for f in report['findings'] for eid in f['evidence']}
        self.assertEqual({e['id'] for e in selected['events']},expected)
        self.assertIn('publish()',str(selected['events']))
        self.assertNotIn('tool_sha256',selected)
        self.assertNotIn('input_sha256',selected)

    def test_partial_or_unavailable_ast_is_visible_and_does_not_claim_safety(self):
        report,selected=analyze_candidate({'broken.py':'def invalid(:\n','extra.go':'package extra\n'})
        self.assertEqual(selected['status'],'partial')
        self.assertEqual({f['status'] for f in selected['coverage']},{'parse_error','unsupported_language'})
        self.assertEqual(selected['findings'],[])
        self.assertTrue(selected['limitations'])

    def test_typescript_selection_preserves_target_locations_for_selected_calls(self):
        report,selected=analyze_candidate({
            'main.ts':"import {publish} from './shared';\nexport async function load() {\n const result = await fetch('/items');\n publish(result);\n}\n",
            'shared.ts':'export function publish(value: unknown) { console.log(value); }\n'})
        if report['status']!='parsed':
            self.skipTest('Locked Node parser dependencies are unavailable')
        self.assertEqual(len(selected['call_links']),1)
        self.assertEqual(selected['target_definitions'][0]['path'],'shared.ts')
        self.assertEqual(selected['target_definitions'][0]['line'],1)

    def test_malformed_analysis_is_invalid_and_preserves_raw_result_without_scoring(self):
        loop=self.prepare();backend=self.backend({'report':'Wrong output envelope.'})
        self.assertEqual(loop.run(backend=backend)['status'],'stopped')
        self.assertEqual(loop.state()['jobs'][0]['status'],'invalid')
        self.assertEqual(load(loop.root/'runs/ANALYSIS/result.json')['output'],
                         {'report':'Wrong output envelope.'})
        self.assertEqual(backend.scores,[])

    def test_analysis_review_then_training_uses_generated_contract_and_counts_budget(self):
        loop=self.prepare();backend=self.backend()
        protocol=loop.verify()
        self.assertEqual(protocol['total_request_cap'],120)
        self.assertEqual(loop.run(backend=backend)['status'],'analysis_review')
        self.assertEqual([role for _,role,_ in backend.calls],['analysis'])
        self.assertEqual(backend.scores,[])
        self.assertIsNone(load(loop.root/'analysis/review-input.json')['approved'])
        with self.assertRaises(EvidenceError):loop.run(backend=backend)
        review=self.root/'review.json';review.write_text(json.dumps(self.reviewed(loop)))
        with redirect_stdout(StringIO()):
            self.assertEqual(main(['experience-evolution','review-analysis',str(review),
                                   '--root',str(loop.root)]),0)
        self.assertEqual(loop.state()['status'],'prepared')
        self.assertEqual(loop.run(backend=backend)['status'],'awaiting_expert')
        self.assertEqual([name for name,_,_ in backend.calls],
                         ['ANALYSIS','BASE-1','BASE-2','R1-reflection','R1-DEV-1','R1-DEV-2'])
        for _,role,prompt in backend.calls:
            if role=='repair':
                self.assertIn(self.fixture.visible()['analysis']['contract'],prompt)
                self.assertNotIn('"AST"',prompt)
        self.assertEqual(load(loop.root/'summary.json')['known_requests'],6)

    def test_unfilled_review_does_not_start_repairs(self):
        loop=self.prepare();backend=self.backend();loop.run(backend=backend)
        with self.assertRaises(EvidenceError):
            loop.review_analysis(load(loop.root/'analysis/review-input.json'))
        self.assertEqual(loop.state()['status'],'analysis_review')
        self.assertFalse((loop.root/'initial-route.json').exists())
        self.assertEqual(len(backend.calls),1)

    def test_wrong_citations_can_be_explicitly_corrected_without_rewriting_raw_output(self):
        analysis=deepcopy(self.fixture.visible()['analysis'])
        analysis['facts'][0]['evidence'][0]['line']=99
        loop=self.prepare();loop.run(backend=self.backend(analysis))
        self.assertEqual(loop.state()['status'],'analysis_citation_review')
        self.assertTrue(load(loop.root/'analysis/citation-issues.json'))
        request=self.reviewed(loop,self.fixture.visible()['analysis'])
        self.assertEqual(loop.review_analysis(request)['status'],'prepared')
        self.assertEqual(load(loop.root/'analysis/raw-analysis.json'),analysis)

    def test_schema_valid_analysis_errors_remain_reviewable_before_repairs(self):
        for error_kind in ('duplicate_fact','missing_evidence'):
            with self.subTest(error_kind=error_kind):
                analysis=deepcopy(self.fixture.visible()['analysis'])
                if error_kind=='duplicate_fact':analysis['facts'].append(deepcopy(analysis['facts'][0]))
                else:analysis['facts'][0]['evidence']=[]
                config=self.config();config['visible']=None
                loop=Evolution(self.root/error_kind);loop.prepare(**config)
                backend=self.backend(analysis)
                self.assertEqual(loop.run(backend=backend)['status'],'analysis_review')
                self.assertTrue(load(loop.root/'analysis/validation-issues.json'))
                request=self.reviewed(loop,self.fixture.visible()['analysis'])
                request['blocking_issues']=[]
                self.assertEqual(loop.review_analysis(request)['status'],'prepared')
                self.assertEqual(backend.scores,[])
                self.assertEqual(load(loop.root/'analysis/raw-analysis.json'),analysis)

    def test_unresolved_development_labels_do_not_spend_repair_budget(self):
        analysis=deepcopy(self.fixture.visible()['analysis']);analysis['obligation_labels']=[]
        loop=self.prepare();backend=self.backend(analysis);loop.run(backend=backend)
        with self.assertRaisesRegex(EvidenceError,'obligation label'):
            loop.review_analysis(self.reviewed(loop))
        self.assertEqual(loop.state()['status'],'analysis_review')
        self.assertEqual(len(backend.calls),1)
        self.assertEqual(backend.scores,[])

    def test_successful_starting_repairs_stop_without_treating_analysis_as_a_score(self):
        loop=self.prepare();backend=self.backend();loop.run(backend=backend)
        loop.review_analysis(self.reviewed(loop))
        score=backend.score
        def passing_score(protocol,candidate,directory):
            outcome=score(protocol,candidate,directory)
            outcome.update(verdict='PASS',missing_required_effects=[],
                           observed_effects=dict(ordering=True,retirement=True,preserved=True))
            return outcome
        backend.score=passing_score
        self.assertEqual(loop.run(backend=backend)['status'],'starting_repairs_passed')
        self.assertEqual([name for name,_,_ in backend.calls],['ANALYSIS','BASE-1','BASE-2'])

    def test_failed_analysis_stops_without_scoring_or_retrieval(self):
        loop=self.prepare();backend=self.backend(fail='ANALYSIS')
        self.assertEqual(loop.run(backend=backend)['status'],'stopped')
        self.assertEqual(backend.scores,[])
        self.assertFalse((loop.root/'initial-route.json').exists())
        self.assertEqual(loop.state()['jobs'][0]['status'],'invalid')

    def test_automatic_evaluation_analyzes_once_then_keeps_analysis_shared(self):
        config=self.config();config.update(visible=None,kind='evaluation',case_id='test')
        loop=Evolution(self.root/'evaluation');loop.prepare(**config)
        analysis=deepcopy(self.fixture.visible()['analysis']);analysis['obligation_labels']=[]
        backend=self.backend(analysis);loop.run(backend=backend)
        loop.review_analysis(self.reviewed(loop))
        self.assertEqual(loop.run(backend=backend)['status'],'evaluation_complete')
        self.assertEqual([name for name,_,_ in backend.calls],['ANALYSIS','B1','A1','A2','B2'])
        self.assertTrue(load(loop.root/'evaluation-prompts.json')['identical'])

    def test_automatic_analysis_requires_explicit_live_execution_switch(self):
        loop=self.prepare()
        with self.assertRaisesRegex(EvidenceError,'--execute'):loop.run()
        self.assertEqual(loop.state()['status'],'analysis_prepared')


if __name__=='__main__':unittest.main()
