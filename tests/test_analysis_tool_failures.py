"""Closed read grammar and honest attribution of hook-terminated analysis stages."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from temporal_contract_analyzer._session_runtime.read_policy import allowed, read_command
from temporal_contract_analyzer.tempoevo_backend import NativeV4Backend
from temporal_contract_analyzer.tempoevo_v4 import MODEL
from temporal_contract_analyzer.stage_retry import transient_transport


class AnalysisToolFailureTests(unittest.TestCase):
    def test_recorded_sort_and_multiline_numbered_reads_are_allowed(self):
        commands=[
            "pwd && rg --files -g 'src/**' | sort && sed -n '1,120p' README.md",
            "nl -ba src/workflow.rb | sed -n '1,140p'\nnl -ba README.md | sed -n '1,80p'",
            "pwd;\n\nrg --files |\nsort -u",
            "pwd # inspect public files\nnl -ba README.md",
            "rg --fi\\\nles | sort",
            "printf '# literal comment marker\\n'",
        ]
        for command in commands:
            with self.subTest(command=command):self.assertTrue(allowed(command))

    def test_sort_output_and_newline_writes_remain_rejected(self):
        commands=[
            'sort -o src/output.txt README.md', 'sort -oout README.md',
            'sort --output=src/output.txt README.md', 'sort --output out README.md',
            'sort --compress-program=sh README.md', 'sort -T /tmp README.md',
            'sort --files0-from=/etc/passwd', 'sort /etc/passwd',
            'rg --files | sort > out', 'echo ok\nrm README.md',
            'echo ok # read-only comment\nrm README.md',
            'echo ok;\nrm README.md', 'echo ok\\\\\nrm README.md',
            'pwd\npython3 -c pass',
        ]
        for command in commands:
            with self.subTest(command=command):self.assertFalse(allowed(command))

    def test_recorded_workspace_status_and_source_reads_are_allowed(self):
        command="git status --short && sed -n '1,140p' src/workflow.py && sed -n '1,120p' README.md"
        self.assertTrue(allowed(command))
        self.assertTrue(allowed('git --no-optional-locks status --short'))
        self.assertTrue(read_command(dict(tool_name='Bash',tool_input=dict(command=command),cwd='/workspace')))

    def test_git_execution_options_writes_and_outside_paths_remain_rejected(self):
        for command in ['git status --short /etc', 'git -C /etc status --short',
                        'git -c core.fsmonitor=evil status --short', 'git status --short --ignored',
                        'git diff --no-index /etc/passwd src/workflow.py', 'git checkout .',
                        'git reset --hard', 'git status --short > out.txt',
                        'git status --short && cat /etc/passwd', 'git status --short && python3 -c pass']:
            with self.subTest(command=command):
                self.assertFalse(allowed(command))

    def test_recorded_literal_file_guard_is_a_read_only_command(self):
        self.assertTrue(allowed("if [ -f 'docs/host-api.md' ]; then cat 'docs/host-api.md'; fi"))
        self.assertTrue(allowed('if [ -e README.md ]; then head -n 5 README.md; fi'))
        for command in ['if [ -f README.md ]; then rm README.md; fi',
                        'if [ -f README.md ]; then cat README.md &; fi',
                        'if [ -f README.md ]; then cat README.md & fi',
                        'if [ -f README.md ]; then cat README.md; else python3 -c pass; fi',
                        'if [ -f /etc/passwd ]; then cat README.md; fi',
                        'if [ -f README.md ]; then cat /etc/passwd; fi',
                        'if [ -f $(touch evil) ]; then cat README.md; fi',
                        'if [ -f README.md ]; then cat README.md > out; fi']:
            with self.subTest(command=command):self.assertFalse(allowed(command))
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'link').symlink_to('/etc/passwd')
            self.assertFalse(allowed('if [ -f link ]; then cat link; fi',root))

    def test_tool_denial_is_not_reported_as_just_bad_json_or_retried(self):
        with tempfile.TemporaryDirectory() as temp:
            directory=Path(temp)
            meter=directory/'native-stage/native/archive/meter/events.jsonl'
            meter.parent.mkdir(parents=True)
            meter.write_text(json.dumps(dict(denied=True,reason='closed read grammar',event=dict(
                hook_event_name='PreToolUse',tool_name='Bash',tool_input=dict(command='git reset --hard'))))+'\n')
            # NativeV4Backend itself creates native-stage before dispatch.
            events=meter.read_text();meter.unlink()
            def fake_execute(*args):
                meter.parent.mkdir(parents=True,exist_ok=True);meter.write_text(events)
                return dict(completed=False,infrastructure_valid=False,output=None,
                    output_parse_error='Incomplete or non-JSON answer; raw bytes retained',
                    receipt=dict(failure_class='model_or_cli_abnormal_exit',archive_failure_requires_stop=False,
                        native=dict(blocked_tools=1)),usage=dict(requests_started=1,total_usage=None))
            # Remove just-created empty directories so the adapter owns their lifecycle.
            for path in [meter.parent,meter.parent.parent,meter.parent.parent.parent,directory/'native-stage']:
                path.rmdir()
            with patch('temporal_contract_analyzer.execution_backend.NativeBackend.execute',side_effect=fake_execute):
                result=NativeV4Backend(dict(binary='/synthetic/codex')).execute('contract',
                    dict(task='Public task',sources={'main.py':'value = 0\n'}),MODEL,
                    dict(requests=12,seconds=600),directory)
            self.assertEqual(result['failure_type'],'tool_policy_denied')
            self.assertIn('git reset --hard',result['error'])
            self.assertIn('non-JSON',result['output_parse_error'])
            self.assertFalse(result['valid'])
            self.assertFalse(transient_transport(dict(receipt=result['native_receipt']),result['error']))
