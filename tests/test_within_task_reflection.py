"""Task-local diagnoses must reach the next Action without approval or retrieval."""
import unittest
import test_tempoevo_v4 as fixtures
from temporal_contract_analyzer.tempoevo_v4 import read
from temporal_contract_analyzer import experience_approval as approval

class WithinTaskReflectionTests(unittest.TestCase):
    setUp=fixtures.V4Tests.setUp
    prepare=fixtures.V4Tests.prepare

    def test_second_and_third_actions_receive_cumulative_reflections(self):
        loop=self.prepare();backend=fixtures.Backend(passes=3,diagnosis='implementation_gap')
        state=loop.run(backend,execute=True);self.assertEqual(state['status'],'passed',state.get('error'))
        actions=[p for role,p,_,_ in backend.calls if role=='action']
        self.assertEqual([len(p['within_task_reflections']) for p in actions],[0,1,2])
        self.assertEqual([d['source_attempt'] for d in actions[2]['within_task_reflections']],[1,2])
        self.assertTrue(all(p['experience'] is None for p in actions))
        self.assertTrue(all(p['contract']==fixtures.contract() for p in actions))
        self.assertEqual([p['candidate_sources']['main.py'] for p in actions],['value = 0\n','value = 1\n','value = 2\n'])
        for n in [2,3]:
            payload=read(loop.root/('stages/action-'+str(n)+'/input.json'))
            for d in payload['within_task_reflections']:
                self.assertEqual(d['explanation'],'Synthetic diagnosis.')
                self.assertFalse(d['contract_changed']);self.assertEqual(d['status'],'unverified_task_local_reflection')
        self.assertEqual(approval.freeze(self.store)['entries'],[])
        self.assertEqual(len([c for c in backend.calls if c[0]=='diagnosis']),2)

    def test_unknown_explanation_and_open_questions_are_not_dropped(self):
        class Backend(fixtures.Backend):
            def execute(self,kind,*args):
                out=super().execute(kind,*args)
                if kind=='diagnosis':out['output'].update(explanation='Cause is unknown; inspect subscription lifetime.',remaining_unknowns=['No event trace yet.'])
                return out
        loop=self.prepare();b=Backend(passes=2,diagnosis='unknown');state=loop.run(b,execute=True)
        self.assertEqual(state['status'],'passed',state.get('error'))
        action=[p for kind,p,_,_ in b.calls if kind=='action'][1]
        r=action['within_task_reflections'][0];self.assertEqual(r['diagnosis'],'unknown')
        self.assertEqual(r['remaining_unknowns'],['No event trace yet.']);self.assertIn('Cause is unknown',r['explanation'])

    def test_testing_has_no_outer_diagnosis_or_gold_feedback(self):
        loop=self.prepare(mode='testing',memory_snapshot=approval.freeze(self.store),gold_evaluator=dict(command=['synthetic-gold']))
        b=fixtures.Backend(passes=2);state=loop.run(b,execute=True);self.assertEqual(state['status'],'scored',state.get('error'))
        actions=[p for kind,p,_,_ in b.calls if kind=='action'];self.assertEqual(len(actions),1)
        self.assertEqual(actions[0]['within_task_reflections'],[])
        self.assertNotIn('diagnosis',[c[0] for c in b.calls])
        import json
        self.assertNotIn('SECRET_GOLD',json.dumps(actions));self.assertNotIn('extract',[c[0] for c in b.calls])
        self.assertEqual(approval.freeze(self.store)['entries'],[])
