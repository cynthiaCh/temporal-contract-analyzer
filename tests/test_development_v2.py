"""Offline control-flow fixtures; no model, real expert or repair-benefit evidence."""
from copy import deepcopy
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import evolution_fixtures as fixtures
from temporal_contract_analyzer import experience_memory as memory, experience_approval as approval
from temporal_contract_analyzer import experience_routing as routing, experience_updates as updates
from temporal_contract_analyzer import experience_screening as screening, taxonomy
from temporal_contract_analyzer.experience_development import Development
from temporal_contract_analyzer.experience_evaluation import Evaluation
from temporal_contract_analyzer.core import EvidenceError
from temporal_contract_analyzer.cli import main


def outcome(passed=False, preserved=True, unknown=False):
    return dict(verdict='PASS' if passed and preserved else 'UNDERREACH',
        behavior_states={'target':None if unknown else passed,'preserved':preserved},
        observed_effects={'negative_expectation':False},
        schedules={'synthetic':{'checks':[{'actual':False,'expected':False,'passed':True}]}},
        origin='synthetic_fixture_not_model_result')


class Backend:
    kind='synthetic_fixture_not_model_or_effectiveness_evidence'

    def __init__(self, no_update=False, success=False, fail=None, source_loss=False,
                 no_gain=False, source_unresolved=False, invalid=False, unknown_usage=False):
        self.calls=[];self.scores=[];self.preflights=[]
        self.no_update=no_update;self.success=success;self.fail=fail;self.source_loss=source_loss
        self.no_gain=no_gain;self.source_unresolved=source_unresolved;self.invalid=invalid;self.unknown_usage=unknown_usage

    def preflight(self,p):self.preflights.append(p['case']['id'])

    def execute(self,p,role,prompt,schema,directory):
        self.calls.append(dict(slot=directory.name,role=role,prompt=prompt,cap=p['session_limits']['requests'],
                               input_path=p['input_path'],visible=deepcopy(p['visible'])))
        if directory.name==self.fail:
            (directory/'partial.txt').write_text('SYNTHETIC_SERVICE_PARTIAL')
            return dict(completed=False,infrastructure_valid=False,usage=None,output=None)
        usage=dict(requests_started=None if self.unknown_usage else 1,total_usage=None,usage_unknown_requests=1)
        if role=='analysis':
            anchor=dict(file='main.py',line=1,quote='accepted = True')
            return dict(completed=True,infrastructure_valid=True,usage=usage,output=dict(taxonomy_version=taxonomy.VERSION,
                contract='Preserve accepted work.',obligation_labels=[dict(code='I',statement='Entry identity.',evidence=[anchor])],
                facts=[dict(predicate='entry_snapshot',state='known',evidence=[anchor])],unknowns=[]))
        if role=='reflect':
            value=dict(action='no_update' if self.no_update else 'new',reason='Synthetic supported extraction.',basis=['TASK'],
                parent_sha256=None,labels=None if self.no_update else ['I'],
                requires=None if self.no_update else ['entry_snapshot'],excludes=None if self.no_update else [],
                changes=[] if self.no_update else [dict(operation='add',rule_id=None,category='event_relation',
                    body='Capture accepted entry data before callbacks, retain accepted results, and verify reentry without retargeting.',
                    support=['TASK'],causal_status='documented_relation')],unresolved=['Synthetic evidence only.'])
            if 'increment_review' in schema['properties']:
                versions=schema['properties']['increment_review']['properties']['compared_versions']['items'].get('enum',[])
                value['increment_review']=dict(compared_versions=versions,comparisons=[dict(
                    change_index=None if self.no_update else 0,matches=[],uncovered_increment='' if self.no_update else 'Synthetic new verification requirement.',
                    classification='insufficient_evidence' if self.no_update else 'independent_new',reason='Synthetic comparison, not actual novelty evidence.')])
            if self.invalid:value['basis']=['NONEXISTENT']
            return dict(completed=True,infrastructure_valid=True,usage=usage,output=value,patch='')
        final=directory/'final';final.mkdir()
        for name,text in p['visible']['sources'].items():
            f=final/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(text)
        return dict(completed=True,infrastructure_valid=True,scoring_admissible=True,usage=usage,
                    output={'report':'Synthetic unverified self-report'},patch='Synthetic actual diff record',final_candidate=str(final))

    def score(self,p,candidate,directory):
        self.scores.append(str(candidate));directory.mkdir(parents=True,exist_ok=True)
        name=Path(candidate).parent.name
        if name.startswith('START-'):return outcome(self.success)
        if name.startswith('SOURCE-NEW-'):return outcome(not self.source_unresolved,not self.source_loss)
        if name.startswith('transfer-'):return outcome('-NEW-' in name and not self.no_gain)
        if name.startswith('task-'):return outcome('AUTO' not in name)
        return outcome(False)


class DevelopmentTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        fixtures.synthetic_bench(self.root/'bench',('source','transfer-a','transfer-b','holdout','boundary'))
        self.env=patch.dict(os.environ,{'TCA_BENCH_ROOT':str(self.root/'bench')});self.env.start();self.addCleanup(self.env.stop)
        self.store=self.root/'memory';memory.initialize(self.store)

    def visible(self,name):
        from temporal_contract_analyzer.case_catalog import case_input
        from temporal_contract_analyzer.candidate_files import capture
        data=case_input(name);files,_=capture(Path(data['candidate']));sources={n:b.decode() for n,b in files.items()}
        anchor=dict(file='main.py',line=1,quote='accepted = True')
        analysis=dict(taxonomy_version=taxonomy.VERSION,contract='Preserve accepted work.',
            obligation_labels=[dict(code='I',statement='Entry identity.',evidence=[anchor])],
            facts=[dict(predicate='entry_snapshot',state='known',evidence=[anchor])],unknowns=[])
        review=routing.review_template(analysis,data['task'],sources)
        review.update(reviewer='execution_agent_visible_input_only',approved=True,reason='Synthetic review.',evidence=[anchor])
        return dict(task=data['task'],sources=sources,analysis=analysis,review=review)

    def lineage(self,name):
        return dict(source_unit=name,derived_from=[],prior_exposure='Synthetic source, not real held-out evidence.',
            critical=[dict(relation='preserved',basis=[dict(file='main.py',line=1,quote='accepted = True')])])

    def config(self):
        boundary=self.visible('boundary')
        boundary['analysis']['facts'][0].update(state='unknown',evidence=[])
        review=routing.review_template(boundary['analysis'],boundary['task'],boundary['sources'])
        review.update(reviewer='execution_agent_visible_input_only',approved=True,reason='Synthetic unknown-premise boundary fixture.',
                      evidence=[dict(file='main.py',line=1,quote='accepted = True')])
        boundary['review']=review
        return dict(case_id='source',store=str(self.store),binary='/synthetic/codex',node='/synthetic/node',
            calibration={'synthetic':True},visible=self.visible('source'),source_relationship='Synthetic independent sources.',
            cohort=dict(source=self.lineage('source'),transfers=[dict(case_id=name,visible=self.visible(name),
                calibration={'synthetic':True},lineage=self.lineage(name)) for name in ('transfer-a','transfer-b')],
                boundaries=[dict(visible=boundary,lineage=dict(source_unit='boundary-source',derived_from=[],
                    prior_exposure='Synthetic unknown-premise fixture, not real boundary evidence.'))]))

    def prepare(self,name='batch',config=None):
        loop=Development(self.root/name);loop.prepare_config(config or self.config());return loop

    def candidate_review(self,loop,approved=True):
        request=json.loads((loop.root/'candidate-review-input.json').read_text())
        request.update(reviewer='execution_agent_visible_input_only',approved=approved,novelty_reason='Synthetic novelty/source check.')
        for r in request['rules']:r.update(supported=approved,reason='Synthetic source support check, not expert approval.')
        return loop.review_candidate(request)

    def test_success_can_extract_and_no_update_is_normal(self):
        for success,cap in [(True,2),(False,12)]:
            loop=self.prepare('success' if success else 'failure');backend=Backend(no_update=True,success=success)
            result=loop.run(backend=backend)
            self.assertEqual(result['status'],'no_update',result.get('error'))
            self.assertEqual(len(backend.calls),3)
            self.assertEqual(backend.calls[-1]['cap'],cap)
            self.assertEqual(memory.records(self.store),[])

    def test_ai_approved_candidate_is_recorded_before_any_validation(self):
        loop=self.prepare();backend=Backend()
        self.assertEqual(loop.run(backend=backend)['status'],'candidate_review')
        self.assertEqual(memory.records(self.store),[])
        state=self.candidate_review(loop)
        self.assertEqual(state['status'],'candidate_approved')
        bundle=memory.records(self.store)[0]
        self.assertEqual(state['candidate_sha256'],bundle['sha256'])
        self.assertEqual(len(backend.calls),3)
        self.assertFalse((self.store/'screening').exists())
        self.assertEqual(approval.decisions(self.store),[])
        before=(loop.root/'candidate.json').read_bytes()
        summary=json.loads((loop.root/'summary.json').read_text())
        self.assertTrue(summary['candidate_handoff']['content_review_available'])
        self.assertEqual(summary['candidate_handoff']['record_store'],str(self.store))
        self.assertIn('--from-store',summary['candidate_handoff']['submit_argv_template'])
        self.assertEqual(loop.run(backend=backend)['status'],'awaiting_review')
        self.assertEqual((loop.root/'candidate.json').read_bytes(),before)
        self.assertEqual(len(memory.records(self.store)),1)
        self.assertEqual(len(backend.calls),13)

    def test_full_screening_requires_expert_and_changes_next_task_only(self):
        loop=self.prepare();backend=Backend()
        self.assertEqual(loop.run(backend=backend)['status'],'candidate_review')
        self.assertEqual(len(backend.calls),3)
        self.candidate_review(loop)
        result=loop.run(backend=backend)
        self.assertEqual(result['status'],'awaiting_review',result.get('error'))
        self.assertEqual(len(backend.calls),13)
        boundary=json.loads((loop.root/'boundary-checks.json').read_text())[0]
        self.assertTrue(boundary['identical'])
        self.assertEqual(boundary['model_status'],'not_run')
        self.assertIsNone(boundary['effect_equivalence'])
        self.assertEqual([r['slot'] for r in backend.calls[-8:]],
            [key+'-'+s for key in ('transfer-1','transfer-2') for s in ('NEW-1','OLD-1','OLD-2','NEW-2')])
        for key in ('transfer-1','transfer-2'):
            rows=[r for r in backend.calls if r['slot'].startswith(key)]
            self.assertTrue(all(r['visible']==rows[0]['visible'] and r['input_path']==rows[0]['input_path'] for r in rows))
        self.assertEqual(approval.freeze(self.store)['entries'],[])
        code=result['candidate_sha256'];self.assertTrue(screening.qualified(self.store,code))
        bundle=memory.records(self.store)[0]
        self.assertEqual(len(bundle['rules']),1)
        approval.decide(self.store,code,dict(reviewer='SYNTHETIC_EXPERT',decision='accept',reason='Synthetic content review.',
            scope='research',rules=[dict(rule_id='R01',supported=True,reason='Synthetic source check.')]), activate_version=True)
        self.assertEqual(len(approval.freeze(self.store)['entries']),1)
        self.assertEqual(json.loads((loop.root/'M-old.json').read_text())['entries'],[])
        for call in backend.calls:
            if call['role']=='repair':
                for forbidden in ('O-START','missing_required_effects','candidate-review','SYNTHETIC_EXPERT'):
                    self.assertNotIn(forbidden,call['prompt'])

    def test_source_unresolved_does_not_impose_two_pass_gate(self):
        loop=self.prepare();b=Backend(source_unresolved=True)
        loop.run(backend=b);self.candidate_review(loop)
        self.assertEqual(loop.run(backend=b)['status'],'awaiting_review')
        self.assertEqual(len(b.calls),13)

    def test_source_critical_loss_stops_before_transfer(self):
        loop=self.prepare();b=Backend(source_loss=True)
        loop.run(backend=b);self.candidate_review(loop)
        self.assertEqual(loop.run(backend=b)['status'],'source_blocked')
        self.assertEqual(len(b.calls),5)
        self.assertFalse(screening.qualified(self.store,loop.state()['candidate_sha256']))

    def test_no_gain_report_does_not_block_approved_retrieval(self):
        loop=self.prepare();b=Backend(no_gain=True)
        loop.run(backend=b);self.candidate_review(loop)
        self.assertEqual(loop.run(backend=b)['status'],'pending_validation')
        code=loop.state()['candidate_sha256']
        approval.decide(self.store,code,dict(reviewer='SYNTHETIC_EXPERT',decision='accept',reason='',scope='exploratory',
            rules=[dict(rule_id='R01',supported=True,reason='')]), activate_version=True)
        self.assertEqual(len(approval.freeze(self.store)['entries']),1)
        self.assertFalse(screening.qualified(self.store,code))
        self.assertEqual(loop.sync_review()['status'],'accepted')
        approval.activate(self.store,code,code,'SYNTHETIC_OPERATOR')

    def test_rejected_candidate_or_invalid_reflection_never_starts_validation(self):
        loop=self.prepare();b=Backend()
        loop.run(backend=b);self.assertEqual(self.candidate_review(loop,False)['status'],'candidate_rejected')
        with self.assertRaises(EvidenceError):loop.run(backend=b)
        self.assertEqual(len(b.calls),3)
        invalid=self.prepare('invalid');bad=Backend(invalid=True)
        self.assertEqual(invalid.run(backend=bad)['status'],'reflection_incomplete')
        self.assertTrue((invalid.root/'runs/EXTRACT/result.json').exists())
        self.assertEqual(len(bad.calls),3)

    def test_infrastructure_and_unknown_metering_stop_without_retry(self):
        for suffix,b in [('infra',Backend(fail='START-1')),('meter',Backend(unknown_usage=True))]:
            loop=self.prepare(suffix)
            self.assertEqual(loop.run(backend=b)['status'],'stopped')
            self.assertEqual(len(b.calls),1)
            summary=json.loads((loop.root/'summary.json').read_text())
            self.assertIsNone(summary['whole_pass_rate'])
            with self.assertRaises(EvidenceError):loop.run(backend=b)

    def test_derivative_sources_are_rejected_before_execution(self):
        config=self.config();config['cohort']['transfers'][0]['lineage']['derived_from']=['source']
        with self.assertRaises(EvidenceError):self.prepare(config=config)

    def test_management_metadata_cannot_enter_prospective_routing(self):
        for key in ('case_id','cluster','historical_score','expected_label'):
            with self.subTest(key=key),self.assertRaises(EvidenceError):
                updates.route_view(dict(self.visible('source'),**{key:'forbidden'}),[])

    def test_automatic_analysis_once_per_case_and_common_review(self):
        config=self.config();config['visible']=None
        for row in config['cohort']['transfers']:row['visible']=None
        loop=self.prepare(config=config);b=Backend(no_update=True)
        self.assertEqual(loop.run(backend=b)['status'],'analysis_review')
        for key in ('source',):
            request=json.loads((loop.root/'cases'/key/'analysis/review-input.json').read_text())
            request.update(reviewer='execution_agent_visible_input_only',approved=True,reason='Synthetic source review.',
                           evidence=[dict(file='main.py',line=1,quote='accepted = True')])
            path=self.root/'public-review.json';path.write_text(json.dumps(request))
            with redirect_stdout(StringIO()),redirect_stderr(StringIO()):
                self.assertEqual(main(['experience-evolution','review-analysis',str(path),'--root',str(loop.root)]),0)
        self.assertEqual(loop.state()['status'],'prepared')
        self.assertEqual(loop.run(backend=b)['status'],'no_update')
        self.assertEqual(sum(c['role']=='analysis' for c in b.calls),1)

    def test_transfer_analysis_is_deferred_until_source_checks_pass(self):
        cfg=self.config()
        for row in cfg['cohort']['transfers']:row['visible']=None
        loop=self.prepare(config=cfg);b=Backend()
        loop.run(backend=b);self.candidate_review(loop)
        self.assertEqual(loop.run(backend=b)['status'],'transfer_analysis_prepared')
        self.assertEqual(sum(c['role']=='analysis' for c in b.calls),0)
        self.assertEqual(loop.run(backend=b)['status'],'analysis_review')
        for key in ('transfer-1','transfer-2'):
            request=json.loads((loop.root/'cases'/key/'analysis/review-input.json').read_text())
            request.update(reviewer='execution_agent_visible_input_only',approved=True,reason='Synthetic review.',
                           evidence=[dict(file='main.py',line=1,quote='accepted = True')])
            loop.review_analysis(request)
        self.assertEqual(loop.run(backend=b)['status'],'awaiting_review')
        self.assertEqual(len(b.calls),15)
        self.assertEqual(sum(c['slot'].startswith('START-') for c in b.calls),2)

    def test_evaluation_merges_empty_milestone_and_never_learns(self):
        v=self.visible('holdout');line=self.lineage('independent-holdout');line.pop('critical')
        config=dict(kind='evaluation',store=str(self.store),binary='/synthetic/codex',node='/synthetic/node',
            tasks=[dict(case_id='holdout',visible=v,calibration={'synthetic':True},lineage=line,
                        holdout=dict(used_for_generation=False,used_for_selection=False,used_for_tuning=False))],
            milestones=[dict(name='M0',snapshot=approval.freeze(self.store))],excluded_source_units=[])
        loop=Evaluation(self.root/'eval');loop.prepare_config(config);b=Backend()
        self.assertEqual(loop.run(backend=b)['status'],'evaluation_complete')
        self.assertEqual(len(b.calls),2)
        summary=json.loads((loop.root/'summary.json').read_text())
        self.assertEqual(summary['condition_aliases']['M0'],'AUTO')
        self.assertFalse(summary['groups']['M0']['actual_condition_executed'])
        self.assertEqual(memory.records(self.store),[])

    def test_final_holdout_cannot_reuse_development_source(self):
        self.prepare()
        for case,unit in [('transfer-a','transfer-a'),('boundary','boundary-source')]:
            line=self.lineage(unit);line.pop('critical')
            cfg=dict(store=str(self.store),binary='/synthetic/codex',node='/synthetic/node',milestones=[],excluded_source_units=[],
                tasks=[dict(case_id=case,visible=self.visible(case),calibration={},lineage=line,
                    holdout=dict(used_for_generation=False,used_for_selection=False,used_for_tuning=False))])
            with self.subTest(case=case),self.assertRaises(EvidenceError):Evaluation(self.root/'eval').prepare_config(cfg)

    def test_cli_defaults_to_v3_with_same_cohort_guards_and_no_model_preparation(self):
        cfg=self.config();cfg['visible']=None
        path=self.root/'config.json';path.write_text(json.dumps(cfg))
        with redirect_stdout(StringIO()),redirect_stderr(StringIO()):
            self.assertEqual(main(['experience-evolution','prepare',str(path),'--root',str(self.root/'cli')]),0)
        from temporal_contract_analyzer.experience_workflow import Workflow
        loop=Workflow(self.root/'cli')
        self.assertEqual(loop.state()['jobs'],[])
        self.assertEqual(loop.state()['status'],'prepared')
        self.assertTrue((loop.root/'cases/source/analysis/ast-evidence.json').exists())
        self.assertEqual(loop.verify()['branch_caps']['success'],290)
        self.assertEqual(loop.verify()['schema_version'],'experience-development-v3')
        self.assertEqual(loop.verify()['global_request_cap'],552)
        with self.assertRaises(EvidenceError):loop.run()
        invalid=self.config();del invalid['cohort'];path.write_text(json.dumps(invalid))
        with redirect_stdout(StringIO()),redirect_stderr(StringIO()):
            self.assertEqual(main(['experience-evolution','prepare',str(path),'--root',str(self.root/'invalid-cli')]),1)

    def test_docker_factory_and_boundary_failure_before_any_dispatch(self):
        from test_docker_backend import CONFIG
        cfg=self.config();cfg.update(backend=CONFIG,node='/runtime/node16/bin/node')
        loop=self.prepare(config=cfg);agent=Backend(no_update=True)
        with patch('temporal_contract_analyzer.docker_backend.DockerBackend',return_value=agent) as factory:
            self.assertEqual(loop.run(execute=True)['status'],'no_update')
        self.assertEqual(factory.call_count,1)
        self.assertIn('/runtime/node16/bin/node',agent.calls[0]['prompt'])
        other=self.prepare('blocked');broken=Backend()
        with patch.object(broken,'preflight',side_effect=EvidenceError('Synthetic missing runtime')):
            self.assertEqual(other.run(backend=broken)['status'],'stopped')
        self.assertEqual(broken.calls,[])
        self.assertEqual(other.state()['jobs'],[])

    def test_milestone_comparison_shared_analysis_costs_and_no_memory_update(self):
        loop=self.prepare();b=Backend();loop.run(backend=b);self.candidate_review(loop);loop.run(backend=b)
        bundle=memory.records(self.store)[0]
        approval.decide(self.store,bundle['sha256'],dict(reviewer='SYNTHETIC_EXPERT',decision='accept',scope='research',
            reason='Synthetic content review.',rules=[dict(rule_id='R01',supported=True,reason='Synthetic support.')]), activate_version=True)
        index_before=(self.store/'active.json').read_bytes();usage_before=(self.store/'development-usage.json').read_bytes()
        provenance=self.lineage('independent-holdout');provenance.pop('critical')
        cfg=dict(store=str(self.store),binary='/synthetic/codex',node='/synthetic/node',excluded_source_units=[],
            milestones=[dict(name='M1',snapshot=approval.freeze(self.store))],
            tasks=[dict(case_id='holdout',visible=self.visible('holdout'),calibration={'synthetic':True},lineage=provenance,
                holdout=dict(used_for_generation=False,used_for_selection=False,used_for_tuning=False))])
        evaluation=Evaluation(self.root/'eval');evaluation.prepare_config(cfg);agent=Backend()
        self.assertEqual(evaluation.run(backend=agent)['status'],'evaluation_complete')
        self.assertEqual(len(agent.calls),4)
        self.assertTrue(all(c['visible']==agent.calls[0]['visible'] for c in agent.calls))
        summary=json.loads((evaluation.root/'summary.json').read_text())
        self.assertEqual(summary['groups']['M1']['newly_solved_cases'],['task-1'])
        self.assertEqual(summary['groups']['M1']['cases'][0]['known_requests'],2)
        self.assertIsNone(summary['groups']['M1']['cases'][0]['known_tokens'])
        self.assertEqual(index_before,(self.store/'active.json').read_bytes())
        self.assertEqual(usage_before,(self.store/'development-usage.json').read_bytes())

    def test_real_conflict_is_auto_and_boundary_has_no_fake_effect_score(self):
        loop=self.prepare();b=Backend();loop.run(backend=b);self.candidate_review(loop);loop.run(backend=b)
        existing=memory.records(self.store)[0]
        other=dict(existing,id='independent-other',sha256='f'*64)
        visible=self.visible('source')
        conflict=updates.route_view(visible,[existing,other])
        self.assertEqual(conflict['route']['reason'],'unresolved_multiple_experience_conflict')
        self.assertIsNone(conflict['experience_text'])


class DeltaTests(unittest.TestCase):
    def test_unknown_mechanism_can_return_no_update_without_empty_enum(self):
        visible=dict(analysis=dict(obligation_labels=[],facts=[]))
        ledger={'TASK':{'kind':'original_task'}}
        value=dict(action='no_update',reason='No established temporal mechanism.',basis=['TASK'],
            parent_sha256=None,labels=None,requires=None,excludes=None,changes=[],unresolved=[])
        self.assertIsNone(updates.compose(value,visible,ledger,{}))
        self.assertEqual(updates.schema(visible,ledger,{})['properties']['requires']['maxItems'],0)

    def test_revision_preserves_untouched_rules_and_replaces_parent_view(self):
        parent=dict(id='one',sha256='a'*64,labels=['I'],requires=['entry_snapshot'],excludes=[],rules=[
            dict(id='R01',category='event_relation',body='Keep this exact original.'),
            dict(id='R02',category='verification',body='Old verification.')])
        visible=dict(analysis=dict(obligation_labels=[{'code':'I'}],facts=[{'predicate':'entry_snapshot','state':'known'}]))
        value=dict(action='revise',reason='Synthetic delta',basis=['TASK'],parent_sha256=parent['sha256'],labels=None,
            requires=None,excludes=None,changes=[dict(operation='replace',rule_id='R02',category='verification',
                body='New bounded verification.',support=['TASK'],causal_status='documented_relation')],unresolved=[])
        result=updates.compose(value,visible,{'TASK':{'kind':'original_task'}},{parent['sha256']:parent})
        self.assertEqual(result['rules'][0],parent['rules'][0]);self.assertEqual(result['requires'],parent['requires'])
        metadata_only=deepcopy(value);metadata_only['changes']=[];metadata_only['labels']=['I','B']
        other_visible=deepcopy(visible);other_visible['analysis']['obligation_labels'].append({'code':'B'})
        narrowed=updates.compose(metadata_only,other_visible,{'TASK':{'kind':'original_task'}},{parent['sha256']:parent})
        self.assertEqual(narrowed['rules'],parent['rules'])
        self.assertEqual(narrowed['labels'],['I','B'])
        child=dict(parent,sha256='b'*64,rules=result['rules'])
        self.assertEqual(updates.new_view([parent],child),[child])
        value['changes'][0]['support']=['explanation pretending to be an ID']
        with self.assertRaises(EvidenceError):updates.compose(value,visible,{'TASK':{'kind':'original_task'}},{parent['sha256']:parent})

    def test_critical_false_expectation_and_unknown_are_not_rewritten(self):
        report=dict(schema_version=screening.VERSION,candidate_sha256='a'*64,
            source=dict(source_unit='source',critical_relations=['preserved'],old=[outcome(),outcome()],new=[outcome(True),outcome(True)]),
            transfers=[dict(source_unit='t'+str(i),critical_relations=['preserved'],prompts_identical=False,
                            old=[outcome(),outcome()],new=[outcome(True),outcome(True)]) for i in (1,2)],
            budget=dict(within=True,complete=True,requests=13,cap=300,unknown_requests=0))
        self.assertEqual(screening.evaluate(report)['status'],'qualified')
        report['transfers'][0]['new'][0]=outcome(True,unknown=True)
        self.assertEqual(screening.evaluate(report)['status'],'pending')
        report['transfers'][0]['new'][0]=outcome(True,preserved=False)
        self.assertEqual(screening.evaluate(report)['status'],'blocked')

    def test_engineering_gate_needs_two_gains_and_cannot_use_identical_prompt_wins(self):
        report=dict(schema_version=screening.VERSION,candidate_sha256='a'*64,
            source=dict(source_unit='s',critical_relations=['preserved'],old=[outcome(),outcome()],new=[outcome(True),outcome(True)]),
            transfers=[dict(source_unit='t'+str(i),critical_relations=['preserved'],prompts_identical=False,
                old=[outcome(),outcome(True)],new=[outcome(True),outcome(True)]) for i in (1,2)],
            budget=dict(within=True,complete=True,requests=13,cap=300,unknown_requests=0))
        self.assertEqual(screening.evaluate(report)['status'],'qualified')
        report['transfers'][0]['prompts_identical']=True
        self.assertEqual(screening.evaluate(report)['status'],'pending')
        report['transfers'][0]['prompts_identical']=False
        report['transfers'][1]['new'][0]=outcome()
        self.assertEqual(screening.evaluate(report)['status'],'pending')
        report['transfers'][1]['new'].pop()
        self.assertEqual(screening.evaluate(report)['status'],'pending')
        report['budget']['requests']=301
        self.assertEqual(screening.evaluate(report)['status'],'pending')

    def test_legacy_acceptance_is_not_default_qualification(self):
        self.assertEqual(screening.evaluate({'schema_version':'old-source-only'})['status'],'pending')
        self.assertEqual(screening.evaluate({'schema_version':screening.VERSION,'source':None})['status'],'pending')
