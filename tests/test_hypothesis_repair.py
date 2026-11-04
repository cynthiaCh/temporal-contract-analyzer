"""Synthetic integration checks; no live model calls or measured model results."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from temporal_contract_analyzer import archive
from temporal_contract_analyzer.core import ROOT, EvidenceError
from temporal_contract_analyzer.repair import checks, hypothesis_material
from temporal_contract_analyzer.workbench import Workbench, capture, file_modes, write_files


CODE = 'export async function run() {\n await fetch();\n publish();\n}\n// kept=true\n// fixed=false\n'


class HypothesisRepairTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);self.root=Path(temp.name)
        self.code=self.root/'candidate';self.code.mkdir();(self.code/'main.js').write_text(CODE)
        self.benchroot=self.root/'bench';case=self.benchroot/'synthetic';oracle=case/'oracle';oracle.mkdir(parents=True)
        base=case/'base';base.mkdir();(base/'main.js').write_text(CODE)
        reference=case/'reference';reference.mkdir();(reference/'main.js').write_text(CODE.replace('fixed=false','fixed=true'))
        archive.atomic_json(case/'case.json',dict(id='synthetic',runtime={'minimum_version':'3.8'},
            reference='reference',oracle={'probe':'oracle/probe.py','effects':'oracle/effects.json'}))
        archive.atomic_json(oracle/'effects.json',dict(variants={'ungranted':dict(
            required=['kept-check','decode-after-close'],forbidden=['scope-expanded'])}))
        (oracle/'probe.py').write_text('''import json,sys,pathlib
code=(pathlib.Path(sys.argv[1])/'main.js').read_text()
effects={'kept-check':'kept=true' in code,'decode-after-close':'fixed=true' in code,'scope-expanded':False}
missing=[k for k in ['kept-check','decode-after-close'] if not effects[k]]
verdict='UNDERREACH' if missing else 'PASS'
print(json.dumps(dict(case_id='synthetic',verdict=verdict,observed_effects=effects,missing_required_effects=missing,observed_forbidden_effects=[],schedules={},private_expected='PRIVATE_EXPECTED_PAYLOAD')))
sys.exit(1 if missing else 0)
''')
        fake=self.root/'fake-codex';fake.write_text('#!'+sys.executable+'\n'+'''import json,pathlib,sys
args=sys.argv[1:]
if args==['--version']:
 print('SYNTHETIC_ONLY');sys.exit()
prompt=sys.stdin.read();root=pathlib.Path(args[args.index('-C')+1]);code=(root/'main.js').read_text()
assert 'parent-patch' in code
assert 'MUTATED_WORKSPACE' not in code
if 'Failure-specific repair hypotheses' in prompt:
 code=code.replace('fixed=false','fixed=true')
else:
 code=code.replace('kept=true','kept=false')
(root/'main.js').write_text(code)
pathlib.Path(args[args.index('-o')+1]).write_text('SYNTHETIC_ONLY')
print(json.dumps({'type':'turn.completed','usage':{'input_tokens':10,'output_tokens':2}}))
''');fake.chmod(0o755)
        env=patch.dict(os.environ,{'TCA_BENCH_ROOT':str(self.benchroot),'TCA_CONFIG':str(self.root/'config.json'),'CODEX_BIN':str(fake)})
        env.start();self.addCleanup(env.stop)
        self.wb=Workbench(self.root/'reports',codex=str(fake));self.addCleanup(self.wb.close)
        m=self.wb.prepare(dict(candidate=str(self.code),task='Maintain source behavior.',model='SYNTHETIC_ONLY',
            effort='low',mode='workspace-write',conditions=['review'],timeout=10))
        m['case']=dict(id='synthetic',manifest='synthetic/case.json',adapter='python',source='bench',authorization='ungranted')
        m['status']='completed';m['jobs'][0]['status']='completed'
        self.parent=m;self.folder=self.wb.folder(m['id'])
        files,_=capture(self.code);files['main.js']+=b'// parent-patch\n'
        write_files(self.folder/'jobs/j-001/workspace',files,file_modes(self.code,files))
        archive.atomic_json(self.folder/'manifest.json',m)
        self.wb.evaluate(m['id'])

    def test_cli_pair_runs_same_scored_patch_and_rejects_regression(self):
        # A mutable original workspace must not replace the scored snapshot.
        (self.folder/'jobs/j-001/workspace/main.js').write_text('MUTATED_WORKSPACE')
        before={p:p.read_bytes() for p in self.folder.rglob('*') if p.is_file()}
        result=subprocess.run([sys.executable,'-B','-m','temporal_contract_analyzer','reports','repair',
            self.parent['id'],'--job','j-001','--run','--store',str(self.wb.store)],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        m=json.loads(result.stdout);folder=self.wb.folder(m['id'])
        self.assertEqual(m['input_files'],json.loads((folder/'retry-source.json').read_text())['candidate_files'])
        self.assertEqual((m['model'],m['effort'],m['timeout']),('SYNTHETIC_ONLY','low',10))
        self.assertIn('parent-patch',(folder/'input/main.js').read_text())
        control=next(j for j in m['jobs'] if j['condition']=='review')
        treatment=next(j for j in m['jobs'] if j['condition']=='hypothesis_review')
        self.assertEqual(control['evaluation']['status'],'failed')
        self.assertEqual(control['evaluation']['regression']['lost'],['required:kept-check'])
        self.assertFalse(control['evaluation']['regression']['eligible'])
        self.assertTrue(treatment['evaluation']['regression']['fully_repaired'])
        for j in m['jobs']:
            prompt=(folder/'jobs'/j['id']/'prompt.md').read_text()
            self.assertNotIn('PRIVATE_EXPECTED_PAYLOAD',prompt)
        self.assertNotIn('decode-after-close',(folder/'jobs'/control['id']/'prompt.md').read_text())
        self.assertIn('decode-after-close',(folder/'jobs'/treatment['id']/'prompt.md').read_text())
        self.assertEqual({p:p.read_bytes() for p in self.folder.rglob('*') if p.is_file()},before)

    def test_hypotheses_change_with_failure_and_recover_cross_file_callers(self):
        source=self.root/'chain';source.mkdir()
        (source/'start.js').write_text('export function start(owner) {\n owner.current = true;\n owner.connect();\n}\n')
        (source/'main.js').write_text('import { start } from "./start.js";\nexport function select(owner) {\n owner.current = false;\n start(owner);\n}\n')
        meta=archive.scan_path(source,self.wb.store)['archive']
        p,text=hypothesis_material(meta['report_id'],{'required:start-switch-admission':False},set(),self.wb.store)
        q,other=hypothesis_material(meta['report_id'],{'required:decode-after-close':False},set(),self.wb.store)
        self.assertNotEqual(p['hypotheses'][0]['cause'],q['hypotheses'][0]['cause'])
        self.assertIn('Falsification procedure:',text)
        self.assertTrue(p['hypotheses'][0]['state_evidence'])
        self.assertTrue(any(r['from_file']=='main.js' and r['target_file']=='start.js' and r['symbol']=='start' for r in p['call_relations']))
        self.assertLessEqual(p['code_chars'],p['max_code_chars'])
        p,_=hypothesis_material(meta['report_id'],{'required:start-switch-admission':False},set(),self.wb.store,max_chars=1)
        self.assertFalse(p['snippets']);self.assertTrue(p['omitted'])
        self.assertEqual(p['hypotheses'][0]['status'],'insufficient-source-evidence')

    def test_reject_snapshot_tampering_success_and_uncalibrated_parent(self):
        latest=self.wb.latest_evaluation(self.parent['id']);s=json.loads(latest.read_text())
        snapshot=latest.parent/'j-001/candidate/main.js';snapshot.write_text('changed')
        with self.assertRaisesRegex(EvidenceError,'候选快照'):self.wb.prepare_repair(self.parent['id'],'j-001')
        s['jobs']['j-001']['status']='passed';archive.atomic_json(latest,s)
        with self.assertRaisesRegex(EvidenceError,'语义失败'):self.wb.prepare_repair(self.parent['id'],'j-001')
        s['jobs']['j-001']['status']='failed';s['calibration_verdict']='UNDERREACH';archive.atomic_json(latest,s)
        with self.assertRaisesRegex(EvidenceError,'参考校准'):self.wb.prepare_repair(self.parent['id'],'j-001')

    def test_frozen_feedback_and_oracle_provenance_are_checked(self):
        m=self.wb.prepare_repair(self.parent['id'],'j-001');folder=self.wb.folder(m['id'])
        (folder/'hypotheses.json').write_text('{}')
        with self.assertRaisesRegex(EvidenceError,'冻结修复反馈'):self.wb.start(m['id'])
        latest=self.wb.latest_evaluation(self.parent['id']);s=json.loads(latest.read_text())
        s['oracle_files']['effects.json']='different';archive.atomic_json(latest,s)
        with self.assertRaisesRegex(EvidenceError,'效果规则'):self.wb.prepare_repair(self.parent['id'],'j-001')

    def test_local_default_configuration_is_preserved_without_overrides(self):
        self.parent.update(model='local-default',effort='local-default',local_codex=True,config_source='local_codex_config')
        archive.atomic_json(self.folder/'manifest.json',self.parent)
        m=self.wb.prepare_repair(self.parent['id'],'j-001')
        self.assertEqual(m['effort'],'local-default');self.assertTrue(m['local_codex'])
        command=self.wb.command(m,self.root/'workspace',self.root/'answer.md')
        self.assertNotIn('-m',command);self.assertNotIn('--ignore-user-config',command)
        self.assertFalse(any('model_reasoning_effort' in arg for arg in command))

    def test_changed_oracle_during_repair_cannot_claim_no_regression(self):
        m=self.wb.prepare_repair(self.parent['id'],'j-001')
        probe=self.benchroot/'synthetic/oracle/probe.py';probe.write_text(probe.read_text()+'\n# NEW_ORACLE_VERSION\n')
        self.wb.start(m['id']);self.wb.thread.join(15);self.assertFalse(self.wb.thread.is_alive())
        view=self.wb.read(m['id'])
        self.assertTrue(all(j['evaluation']['regression']['status']=='unverified' for j in view['jobs']))
        self.assertTrue(all(not j['evaluation']['regression']['eligible'] for j in view['jobs']))

    def test_regression_checks_include_forbidden_effects_and_missing_values(self):
        rules=dict(required=['keep'],forbidden=['expand'])
        passed=dict(verdict='PASS',observed_effects={'keep':True,'expand':False},missing_required_effects=[],observed_forbidden_effects=[])
        self.assertEqual(checks(passed,rules),{'required:keep':True,'forbidden:expand':True})
        passed['observed_effects'].pop('expand')
        with self.assertRaisesRegex(EvidenceError,'逐效果布尔'):checks(passed,rules)


if __name__=='__main__':unittest.main()
