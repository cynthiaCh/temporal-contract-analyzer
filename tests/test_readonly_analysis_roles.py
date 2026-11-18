"""Structured roles consume supplied sources without disabling Action evidence tools."""
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


SOURCE_BODY=('first_public_body_marker = True\n'
             'second_public_body_marker = True\n'
             'third_public_body_marker = True\n')


COMMAND_DRIVER=r'''
import json,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import runner
from model_settings import resolve_profile
root=Path(sys.argv[2]);phase=sys.argv[3];readonly=json.loads(sys.argv[4]);folder=root/'call'
public=root/'public';public.mkdir()
for name in ['codex','codex-code-mode-host']:(public/name).write_text('offline fixture binary')
runner.backend.BINARY=public/'codex';runner.backend.global_snapshot=lambda:{}
runtime=root/'runtime'
case=dict(node='/runtime/node16/bin/node',model_settings=resolve_profile('deepseek-flash-high'),readonly_no_tools=readonly)
cmd=runner.command('call',folder,phase,case,runtime=runtime,socket_dir=root/'hooks',copy_auth=False)
def values(flag):return [cmd[i+1] for i,x in enumerate(cmd[:-1]) if x==flag]
catalog=json.loads((runtime/'.runtime/call/models.json').read_text())['models'][0]
original=root/'original';original.mkdir();source=original/'main.py';source.write_text(sys.argv[5])
events=[dict(type='item.completed',item=dict(type='command_execution',command='cat main.py',exit_code=0,aggregated_output=source.read_text()))]
print(json.dumps(dict(disabled=values('--disable'),enabled=values('--enable'),
 workspace_mode=cmd[cmd.index(str(folder/'workspace'))-1],sandbox=cmd[cmd.index('--sandbox')+1],
 schema=Path(cmd[cmd.index('/format.json')-1]).name,
 apply_patch_type=catalog['apply_patch_tool_type'],shell_type=catalog['shell_type'],
 instructions=catalog['base_instructions'],source_proof_count=len(runner.source_proof(events,original)))))
'''


@unittest.skipIf(os.name=='nt','packaged native runner uses Linux fcntl')
class ReadonlyAnalysisRoleTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        from temporal_contract_analyzer._session_runtime.model_settings import identity,resolve_profile
        self.settings=resolve_profile('deepseek-flash-high');self.model=identity(self.settings)
        self.protocol=dict(binary='/public/codex',model_settings=self.settings,analysis_tools=False)
        self.payload=dict(task='Preserve public behavior.',sources={'src/main.py':SOURCE_BODY},schema=dict(type='object'))
        final=self.root/'final';final.mkdir();(final/'main.py').write_text(SOURCE_BODY)
        self.reply=dict(completed=True,infrastructure_valid=True,scoring_admissible=True,
            output={},final_candidate=str(final),receipt={},
            usage=dict(requests_started=1,total_usage=dict(input_tokens=100,output_tokens=10),usage_incomplete=False))
        self.sequence=0

    def dispatch(self,kind,protocol=None,payload=None,reply=None):
        from temporal_contract_analyzer.execution_backend import NativeBackend
        from temporal_contract_analyzer.tempoevo_backend import NativeV4Backend
        self.sequence+=1;directory=self.root/('stage-'+str(self.sequence));directory.mkdir()
        with patch.object(NativeBackend,'execute',return_value=reply or self.reply) as execute:
            out=NativeV4Backend(protocol or self.protocol).execute(kind,payload or self.payload,self.model,
                dict(requests=12 if kind!='action' else 24,seconds=600),directory)
        return out,execute.call_args

    def test_every_structured_role_receives_complete_sources_without_tools(self):
        for kind in ['routing','contract','selection','diagnosis','extract','ai_summary','ai_review']:
            with self.subTest(kind=kind):
                out,call=self.dispatch(kind)
                protocol,role,prompt,schema,_=call.args
                self.assertTrue(out['valid']);self.assertEqual(role,'analysis')
                self.assertIs(protocol['readonly_no_tools'],True)
                self.assertIn('Tools are disabled',prompt)
                self.assertIn('first_public_body_marker',prompt)
                self.assertIn('third_public_body_marker',prompt)
                self.assertIn('src/main.py',prompt)
                self.assertEqual(schema,self.payload['schema'])
                self.assertEqual((Path(protocol['input_path'])/'src/main.py').read_text(),SOURCE_BODY)

    def test_action_keeps_tools_current_source_and_admissibility_requirement(self):
        current=SOURCE_BODY.replace('True','False')
        payload=dict(self.payload,candidate_sources={'src/main.py':current})
        out,call=self.dispatch('action',payload=payload)
        protocol,role,prompt,_,_=call.args
        self.assertTrue(out['valid']);self.assertEqual(role,'repair')
        self.assertIs(protocol['readonly_no_tools'],False)
        self.assertNotIn('READ-ONLY STAGE: Tools are disabled',prompt)
        self.assertEqual((Path(protocol['input_path'])/'src/main.py').read_text(),current)
        bad=dict(self.reply,scoring_admissible=False)
        invalid,_=self.dispatch('action',payload=payload,reply=bad)
        self.assertFalse(invalid['valid']);self.assertIn('Candidate or archive validation failed',invalid['error'])

    def test_legacy_configuration_retains_read_only_tool_policy(self):
        for setting in [None,True]:
            protocol=dict(self.protocol)
            if setting is None:protocol.pop('analysis_tools')
            else:protocol['analysis_tools']=setting
            _,call=self.dispatch('contract',protocol=protocol)
            self.assertIs(call.args[0]['readonly_no_tools'],False)

    def test_bridge_request_and_driver_preserve_explicit_role_flag(self):
        from temporal_contract_analyzer.execution_backend import DRIVER,NativeBackend
        from temporal_contract_analyzer.tempoevo_v4 import VERSION
        directory=self.root/'bridge';directory.mkdir()
        candidate=self.root/'candidate';candidate.mkdir();(candidate/'main.py').write_text(SOURCE_BODY)
        protocol=dict(execution_policy=VERSION,binary='/public/codex',node='/runtime/node16/bin/node',
            input_path=str(candidate),visible=dict(task='Preserve public behavior.'),case=dict(id='fixture'),
            boundary_preflight_complete=True,readonly_no_tools=True,model_settings=self.settings,
            session_limits=dict(requests=12,seconds=600))
        requests=[]
        class Process:
            returncode=1
            def __init__(self,*args,**kwargs):pass
            def communicate(self,input=None,timeout=None):
                requests.append(json.loads(input));return '','offline fixture stopped before any provider'
        with patch('temporal_contract_analyzer.execution_backend.subprocess.Popen',Process):
            NativeBackend().execute(protocol,'analysis','Full supplied source',dict(type='object'),directory)
        request=requests[0]
        self.assertIs(request['config']['readonly_no_tools'],True)
        self.assertEqual(request['slot']['phase'],'analysis')
        self.assertTrue((directory/'backend/analysis.schema.json').is_file())
        session=types.SimpleNamespace(backend=types.SimpleNamespace(BINARY=None))
        captured=[]
        def fake_session(*args,**kwargs):captured.append(kwargs);return {}
        session.session=fake_session
        with patch.dict(sys.modules,{'runner':session}),patch('sys.stdin',io.StringIO(json.dumps(request))),redirect_stdout(io.StringIO()):
            exec(DRIVER,{'__name__':'__main__'})
        self.assertIs(captured[0]['case']['readonly_no_tools'],True)
        self.assertIs(captured[0]['case']['reflection_readonly'],False)

    def command(self,phase,readonly):
        from temporal_contract_analyzer.execution_backend import DEPENDENCIES,SOURCE
        root=self.root/(phase+'-'+str(readonly));root.mkdir();backend=root/'backend';backend.mkdir()
        for name in DEPENDENCIES:shutil.copyfile(SOURCE/name,backend/name)
        (backend/'analysis.schema.json').write_text('{}');(backend/'reflection.schema.json').write_text('{}')
        r=subprocess.run([sys.executable,'-B','-c',COMMAND_DRIVER,str(backend),str(root),phase,
                          json.dumps(readonly),SOURCE_BODY],capture_output=True,text=True,timeout=15)
        self.assertEqual(r.returncode,0,r.stderr)
        return json.loads(r.stdout)

    def test_actual_runner_separates_no_tools_analysis_from_action(self):
        analysis=self.command('analysis',True)
        self.assertEqual(analysis['schema'],'analysis.schema.json')
        self.assertEqual(analysis['workspace_mode'],'--ro-bind');self.assertEqual(analysis['sandbox'],'read-only')
        self.assertIsNone(analysis['apply_patch_type'])
        for tool in ['shell_tool','code_mode_host']:
            self.assertIn(tool,analysis['disabled']);self.assertNotIn(tool,analysis['enabled'])
        action=self.command('repair',False)
        self.assertEqual(action['schema'],'maintenance.schema.json')
        self.assertEqual(action['workspace_mode'],'--bind');self.assertEqual(action['sandbox'],'danger-full-access')
        self.assertEqual(action['apply_patch_type'],'freeform');self.assertGreater(action['source_proof_count'],0)
        for tool in ['shell_tool','code_mode_host']:self.assertIn(tool,action['enabled'])

    def test_actual_runner_legacy_analysis_still_has_readers(self):
        legacy=self.command('analysis',False)
        self.assertEqual(legacy['schema'],'analysis.schema.json')
        self.assertEqual(legacy['workspace_mode'],'--ro-bind')
        self.assertIsNone(legacy['apply_patch_type'])
        self.assertIn('shell_tool',legacy['enabled'])


if __name__=='__main__':unittest.main()
