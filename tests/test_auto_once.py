import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'tools/temporal-behavior-probe/auto_once.py'
spec = importlib.util.spec_from_file_location('auto_once', SCRIPT)
auto = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auto)


class AutoOnceTests(unittest.TestCase):
    def discover(self, text):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'index.cjs'
            path.write_text(text)
            return auto.discover(path)

    def test_recognizes_structure_without_claiming_contract(self):
        result = self.discover('module.exports=fn=>{let used;return function(){if(used)return;used=true;return fn.apply(this,arguments)}};')
        self.assertEqual(result['status'], 'candidate')
        self.assertFalse(result['obligation_inferred'])
        self.assertEqual(result['api'], {'kind': 'wrapper'})

    def test_rejects_unresolved_or_unrelated_shapes(self):
        for source in ['module.exports=require("other");',
                       'module.exports=fn=>()=>42;',
                       'module.exports=fn=>function(fn){return fn()};',
                       'module.exports=fn=>{fn();return 42};',
                       'module.exports=fn=>()=>fn();module.exports=other;',
                       'export default fn=>()=>fn();', 'module.exports = (']:
            with self.subTest(source=source):
                self.assertEqual(self.discover(source)['status'], 'unsupported')

    def test_proposal_never_executes_subject(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sentinel = root / 'executed'
            path = root / 'index.cjs'
            path.write_text(f'require("node:fs").writeFileSync({str(sentinel)!r}, "yes");module.exports=fn=>()=>fn();')
            report = auto.propose(path, path)
            self.assertEqual(report['status'], 'confirmation_required')
            self.assertFalse(report['subject_executed'])
            self.assertFalse(sentinel.exists())

    def test_confirmed_change_and_generated_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            before, after = root / 'before', root / 'after'
            before.mkdir()
            after.mkdir()
            late = 'module.exports=fn=>{let used;return function(){if(used)return;const result=fn.apply(this,arguments);used=true;return result}};'
            early = 'module.exports=fn=>{let used;return function(){if(used)return;used=true;return fn.apply(this,arguments)}};'
            (before / 'index.cjs').write_text(late)
            (after / 'index.cjs').write_text(early)
            paths = [before / 'index.cjs', after / 'index.cjs']
            output = root / 'report.json'
            command = [sys.executable, '-B', str(SCRIPT), *map(str, paths), '--confirm-at-most-once', '--output', str(output)]
            subprocess.run(command, check=True, capture_output=True)
            report = json.loads(output.read_text())
            self.assertEqual(report['behavior']['rows'][0]['transition'], 'resolved_for_generated_scene')
            subprocess.run(report['replay_command'], check=True, capture_output=True)
            replay = json.loads((root / 'report-replay.json').read_text())
            for side, count in [('before', 2), ('after', 1)]:
                self.assertEqual(report['behavior']['rows'][0][side]['observation']['calls'], count)
                self.assertEqual(replay['behavior']['rows'][0][side]['observation']['calls'], count)

    def test_runtime_failure_is_inconclusive_and_control_is_bounded(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'index.cjs'
            path.write_text('throw Error("setup failure"); module.exports=fn=>()=>fn();')
            report = auto.execute(auto.propose(path, path), path, path, root / 'out.json')
            self.assertEqual(report['status'], 'inconclusive')
            self.assertEqual(report['behavior']['rows'][0]['transition'], 'inconclusive')
            path.write_text('module.exports=fn=>{let used;return()=>{if(used)return;used=true;return fn()}};')
            report = auto.execute(auto.propose(path, path), path, path, root / 'out.json')
            self.assertEqual(report['behavior']['rows'][0]['transition'], 'both_meet_checked_contracts')

    def test_existing_output_refuses_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sentinel = root / 'executed'
            path, output = root / 'index.cjs', root / 'report.json'
            path.write_text(f'require("node:fs").writeFileSync({str(sentinel)!r}, "yes");module.exports=fn=>()=>fn();')
            output.write_text('keep')
            result = subprocess.run([sys.executable, '-B', str(SCRIPT), str(path), str(path),
                                     '--confirm-at-most-once', '--output', str(output)], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(output.read_text(), 'keep')
            self.assertFalse(sentinel.exists())

    def test_factory_callback_is_outside_declared_reentry_domain(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'index.cjs'
            path.write_text('module.exports=fn=>{fn(0);return()=>fn(0)};')
            report = auto.execute(auto.propose(path, path), path, path, Path(directory) / 'out.json')
            self.assertEqual(report['status'], 'inconclusive')
            self.assertEqual(report['behavior']['rows'][0]['transition'], 'inconclusive')
            self.assertEqual(report['behavior']['rows'][0]['before']['checks'], [])
            self.assertTrue(report['execution_validity']['before']['construction_callback'])

    def test_no_callback_does_not_claim_reentry_exercised(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'index.cjs'
            path.write_text('module.exports=fn=>()=>{if(false)fn(0)};')
            report = auto.execute(auto.propose(path, path), path, path, Path(directory) / 'out.json')
            self.assertFalse(report['execution_validity']['before']['reentry_attempted'])
            self.assertEqual(report['behavior']['rows'][0]['before']['observation']['calls'], 0)


if __name__ == '__main__':
    unittest.main()
