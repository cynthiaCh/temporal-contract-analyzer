"""Corrective repair control flow over synthetic cases; no live model calls."""
from pathlib import Path
import json
import unittest

import test_development_v2 as fixtures
from test_workflow_v3 import FakeBackend
from temporal_contract_analyzer.experience_workflow import Workflow
from temporal_contract_analyzer import experience_memory as memory,experience_approval as approval


class CorrectingBackend(FakeBackend):
    def __init__(self,fix_after=1,mixed=False,regression=False,**kwargs):
        super().__init__(**kwargs);self.fix_after=fix_after;self.mixed=mixed;self.regression=regression

    def execute(self,*args,**kwargs):
        result=super().execute(*args,**kwargs)
        if args[1]=='repair' and result.get('completed'):
            slot=args[4].name;path=Path(result['final_candidate'])/'main.py'
            with path.open('a') as stream:stream.write('\n# '+slot+'\n')
        return result

    def score(self,p,candidate,directory):
        name=Path(candidate).parent.name
        if name.startswith('FIX-'):
            self.scores.append(str(candidate));directory.mkdir(parents=True,exist_ok=True)
            return fixtures.outcome(int(name.rsplit('-',1)[1])>=self.fix_after,not self.regression)
        if name=='START-1' and self.mixed:
            self.scores.append(str(candidate));directory.mkdir(parents=True,exist_ok=True)
            return fixtures.outcome(True)
        return super().score(p,candidate,directory)


class BugfixLoopTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixtures.DevelopmentTests('test_success_can_extract_and_no_update_is_normal')
        self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)

    def prepare(self):
        config=self.fixture.config();config.pop('max_fix_attempts')
        loop=Workflow(self.fixture.root/'automatic');loop.prepare_config(config);return loop

    def test_default_fixes_failed_implementations_before_reflection(self):
        loop=self.prepare();p=loop.verify();backend=CorrectingBackend(no_update=True)
        self.assertEqual(p['max_fix_attempts'],2)
        self.assertEqual(p['initial_request_cap'],396);self.assertEqual(p['global_request_cap'],636)
        state=loop.run(execute=True,backend=backend)
        self.assertEqual(state['status'],'repaired',state.get('error'))
        self.assertFalse(state['followup_required'])
        self.assertEqual([c['slot'] for c in backend.calls],['START-1','START-2','FIX-START-1-1','FIX-START-2-1','EXTRACT'])
        self.assertEqual([j['outcome']['verdict'] for j in state['jobs'] if j['slot'].startswith('START-')],['UNDERREACH']*2)
        record=json.loads((loop.root/'failure-learning.json').read_text())
        self.assertEqual(record['status'],'fixed');self.assertTrue(all(r['fixed'] for r in record['repairs']))
        self.assertFalse(memory.records(self.fixture.store))
        context=json.loads((loop.root/'reflection-input.json').read_text())
        self.assertIn('R-FIX-START-1-1',context['ledger'])
        count=len(backend.calls);loop.run(execute=True,backend=backend);self.assertEqual(len(backend.calls),count)

    def test_only_failed_start_is_repaired_and_second_attempt_uses_the_first_patch(self):
        loop=self.prepare();backend=CorrectingBackend(no_update=True,mixed=True,fix_after=2)
        state=loop.run(execute=True,backend=backend)
        self.assertEqual(state['status'],'repaired',state.get('error'))
        self.assertFalse(any(c['slot'].startswith('FIX-START-1') for c in backend.calls))
        first=next(c for c in backend.calls if c['slot']=='FIX-START-2-1')
        second=next(c for c in backend.calls if c['slot']=='FIX-START-2-2')
        self.assertIn('# START-2',first['visible']['sources']['main.py'])
        self.assertIn('# FIX-START-2-1',second['visible']['sources']['main.py'])
        self.assertNotIn('behavior_states',first['prompt'])
        original=Path(json.loads((loop.root/'runs/START-2/result.json').read_text())['final_candidate'])/'main.py'
        self.assertNotIn('# FIX-',original.read_text())
        summary=json.loads((loop.root/'summary.json').read_text())
        self.assertEqual(len(summary['starting_repairs']),2);self.assertEqual(len(summary['corrective_repairs']),2)

    def test_exhaustion_reports_unfixed_bug_without_more_dispatch(self):
        loop=self.prepare();backend=CorrectingBackend(no_update=True,fix_after=3)
        state=loop.run(execute=True,backend=backend)
        self.assertEqual(state['status'],'repair_exhausted',state.get('error'))
        self.assertTrue(state['followup_required'])
        self.assertEqual(sum(c['slot'].startswith('FIX-') for c in backend.calls),4)
        count=len(backend.calls);loop.run(execute=True,backend=backend);self.assertEqual(len(backend.calls),count)

    def test_infrastructure_error_is_not_retried_as_a_bugfix(self):
        loop=self.prepare();backend=CorrectingBackend(no_update=True,fail='FIX-START-1-1')
        state=loop.run(execute=True,backend=backend)
        self.assertEqual(state['status'],'infrastructure_error',state.get('error'))
        self.assertFalse(any(c['role']=='reflect' for c in backend.calls))
        count=len(backend.calls);loop.run(execute=True,backend=backend);self.assertEqual(len(backend.calls),count)

    def test_a_fix_that_loses_preserved_behavior_is_not_marked_fixed(self):
        loop=self.prepare();backend=CorrectingBackend(no_update=True,regression=True)
        state=loop.run(execute=True,backend=backend)
        self.assertEqual(state['status'],'repair_exhausted',state.get('error'))
        record=json.loads((loop.root/'failure-learning.json').read_text())
        self.assertFalse(any(r['fixed'] for r in record['repairs']))

    def test_bugfix_does_not_automatically_approve_a_proposed_experience(self):
        loop=self.prepare();backend=CorrectingBackend()
        state=loop.run(execute=True,backend=backend)
        self.assertEqual(state['status'],'awaiting_human_review',state.get('error'))
        self.assertEqual(state['bugfix_status'],'fixed')
        self.assertEqual(approval.decisions(self.fixture.store),[])
        self.assertEqual(approval.freeze(self.fixture.store)['entries'],[])


if __name__=='__main__':unittest.main()
