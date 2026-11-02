import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT/'tools/temporal-behavior-probe/probe.py'
spec = importlib.util.spec_from_file_location('behavior_probe', SCRIPT)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
NODE = '/Applications/Visual Studio Code.app/Contents/MacOS/Code'


class BehaviorProbeTests(unittest.TestCase):
    def test_contracts_distinguish_observation_change_from_required_behavior(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ['before', 'after']: (root/name).mkdir()
            (root/'before/index.cjs').write_text('module.exports=fn=>{let used=false;return(...a)=>{if(used)return;const r=fn(...a);used=true;return r;}};')
            (root/'after/index.cjs').write_text('module.exports=fn=>{let used=false;return(...a)=>{if(used)return;used=true;return fn(...a);}};')
            plan = dict(api=dict(kind='wrapper'), before=dict(root='before', entry='index.cjs'), after=dict(root='after', entry='index.cjs'))
            report = probe.compare_plan(plan, NODE, root, 'reentry')
            self.assertTrue(report['rows'][0]['behavior_changed'])
            self.assertEqual(report['rows'][0]['transition'], 'observation_only')
            plan['contracts'] = dict(at_most_once=True)
            report = probe.compare_plan(plan, NODE, root, 'reentry')
            self.assertEqual(report['rows'][0]['transition'], 'resolved_for_generated_scene')
            self.assertIn('<subject>/index.cjs', str(report['rows'][0]['before']['trace']))
            plan['before'], plan['after'] = plan['after'], plan['before']
            introduced = probe.compare_plan(plan, NODE, root, 'reentry')
            self.assertEqual(introduced['rows'][0]['transition'], 'introduced_for_generated_scene')
            plan['before'] = plan['after']
            persistent = probe.compare_plan(plan, NODE, root, 'reentry')
            self.assertEqual(persistent['rows'][0]['transition'], 'violates_on_both')

    def test_introduced_and_persistent_violations_are_reported(self):
        observed = dict(status='observed', observation=dict(calls=2, counts={'callback': 2}, operations=[]))
        scene = dict(kind='reentry')
        self.assertFalse(probe.evaluate(scene, observed, dict(at_most_once=True))[0]['passed'])
        self.assertEqual(probe.evaluate(scene, observed, {}), [])
        with self.assertRaises(ValueError):
            probe.validate_plan(dict(api=dict(kind='wrapper'), contracts=dict(not_a_contract=True), before={}, after={}))

    def test_loader_failure_and_timeout_are_inconclusive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root/'source').mkdir()
            (root/'source/index.cjs').write_text('module.exports = 42;')
            subject = dict(root='source', entry='index.cjs')
            result = probe.run_scene(subject, dict(kind='wrapper'), dict(kind='repeat'), NODE, root)
            self.assertEqual(result['status'], 'inconclusive')
            self.assertEqual(probe.evaluate(dict(kind='repeat'), result, dict(cache_repeated=True)), [])
            (root/'source/index.cjs').write_text('while(true){}')
            result = probe.run_scene(subject, dict(kind='wrapper'), dict(kind='repeat'), NODE, root, timeout=0.3)
            self.assertEqual(result['reason'], 'timeout')

    def test_correct_cache_post_compute_is_not_a_violation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root/'source').mkdir()
            (root/'source/index.cjs').write_text('module.exports=fn=>{let key,result,valid=false;return x=>{if(valid&&x===key)return result;const next=fn(x);key=x;result=next;valid=true;return result;}};')
            subject = dict(root='source', entry='index.cjs')
            plan = dict(api=dict(kind='wrapper'), contracts=dict(cache_repeated=True,failure_rethrows=True,preserve_success_after_failure=True), before=subject, after=subject)
            report = probe.compare_plan(plan, NODE, root)
            self.assertEqual(report['summary']['resolved_scenes'], 0)
            self.assertFalse(any(not check['passed'] for row in report['rows'] for side in ['before','after'] for check in row[side]['checks']))

    def test_emitter_mutation_and_once_reentry_use_method_bindings(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ['before','after']: (root/name).mkdir()
            template = '''module.exports=()=>{let items=[];return{listen:(e,f)=>items.push(f),detach:(e,f)=>items.splice(items.indexOf(f),1),send:()=>COPY.forEach(f=>f())}};'''
            (root/'before/index.cjs').write_text(template.replace('COPY','items'))
            (root/'after/index.cjs').write_text(template.replace('COPY','items.slice()'))
            plan=dict(api=dict(kind='emitter',methods=dict(on='listen',off='detach',emit='send')),contracts=dict(snapshot_delivery=True),before=dict(root='before',entry='index.cjs'),after=dict(root='after',entry='index.cjs'))
            report=probe.compare_plan(plan,NODE,root,'remove-self-2')
            self.assertEqual(report['rows'][0]['transition'],'resolved_for_generated_scene')

    def test_declarative_export_and_replay_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'source').mkdir()
            (root/'source/index.cjs').write_text('module.exports={wrap:fn=>(...a)=>fn(...a)};')
            subject=dict(root='source',entry='index.cjs')
            plan=dict(api=dict(kind='wrapper',export='default.wrap'),before=subject,after=subject)
            report=probe.compare_plan(plan,NODE,root,'repeat')
            self.assertEqual(report['rows'][0]['before']['observation']['calls'],2)
            with self.assertRaises(ValueError): probe.compare_plan(plan,NODE,root,'not-generated')

    def test_generation_is_api_based_and_does_not_accept_case_test_code(self):
        wrapper = probe.scenarios(dict(kind='wrapper'), {})
        self.assertEqual({x['kind'] for x in wrapper}, {'repeat', 'reentry', 'failure-retry', 'failure-first', 'failure-restore', 'overlap'})
        emitter = probe.scenarios(dict(kind='emitter', methods=dict(on='listen', off='detach', emit='send', once='single')), {})
        self.assertTrue(any(x.get('listeners') == 2 and x.get('registration') == 'once' for x in emitter))
        self.assertTrue(any(x.get('remove') == 'self' for x in emitter))
        self.assertEqual(len(probe.scenarios(dict(kind='keyed_completion'), {})), 3)
        with self.assertRaises(ValueError):
            probe.validate_plan(dict(api=dict(kind='wrapper'), contracts={}, before={}, after={}, test_code='anything'))

    def test_generation_reentry_observes_a_difference_without_handwritten_scenario(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ['before', 'after']: (root/name).mkdir()
            (root/'before/index.cjs').write_text('module.exports = fn => {let used=false;return (...args)=>{if(used)return;const r=fn(...args);used=true;return r;}};')
            (root/'after/index.cjs').write_text('module.exports = fn => {let used=false;return (...args)=>{if(used)return;used=true;return fn(...args);}};')
            scene = next(x for x in probe.scenarios(dict(kind='wrapper'), {}) if x['id'] == 'reentry')
            counts = [probe.run_scene(dict(root=name, entry='index.cjs'), dict(kind='wrapper'), scene, NODE, root)['observation']['calls'] for name in ['before', 'after']]
            self.assertEqual(counts, [2, 1])

    def test_spine_real_cli_executes_modules_and_writes_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'source').mkdir()
            (root/'source/index.cjs').write_text('module.exports = fn => (...args) => fn(...args);')
            subject = dict(root='source', entry='index.cjs')
            plan = dict(api=dict(kind='wrapper'), before=subject, after=subject)
            (root/'plan.json').write_text(json.dumps(plan))
            result = subprocess.run(['python3', str(SCRIPT), str(root/'plan.json'), '--node', NODE,
                                     '--output', str(root/'spine_smoke.json')], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((root/'spine_smoke.json').read_text())
            for side in ['before', 'after']:
                self.assertEqual(report['rows'][0][side]['status'], 'observed')
                self.assertEqual(report['rows'][0][side]['observation']['calls'], 2)


if __name__ == '__main__':
    unittest.main()
