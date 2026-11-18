"""Admit ordinary evidence discovery while rejecting effects and namespace escapes."""
from pathlib import Path
import shlex
import tempfile
import unittest
from unittest.mock import patch
from temporal_contract_analyzer._session_runtime.read_policy import allowed


class ResearchReadPolicyTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.workspace=Path(self.tmp.name)/'workspace';self.workspace.mkdir()
        (self.workspace/'main.py').write_text('value = 0\n')

    def test_real_read_only_discovery_and_sort_pipeline(self):
        for command in ['pwd && ls -la && find . -maxdepth 3 -type f | sort',
                        "find . -type f -name '*.py' -print | sort -u",
                        'sort -nr main.py']:
            with self.subTest(command=command):self.assertTrue(allowed(command,self.workspace))

    def test_find_cannot_execute_write_or_read_outside_workspace(self):
        for command in ['find . -exec cat /etc/passwd ;','find . -delete',
                        'find . -fprint result.txt','find . -printf x',
                        'find /etc -type f','find .. -type f',
                        'find . -newer /etc/passwd','find -L . -type f',
                        'find . -maxdepth 999 -type f',
                        'find . -maxdepth 3 -type f | sort > result.txt']:
            with self.subTest(command=command):self.assertFalse(allowed(command,self.workspace))

    def test_real_denied_read_commands_and_safe_file_guard(self):
        for command in ["pwd && find . -maxdepth 3 -type f -not -path '*/node_modules/*' | sort",
                        "find . -maxdepth 2 -type f -name '*.js' -o -name '*.jsx' -o -name 'README.md' | sort",
                        r"find . -maxdepth 3 -type f -printf '%p\n' | sort",
                        'test -f main.py && cat main.py || true',
                        "find . \\( -name '*.py' -o -name '*.js' \\) -print"]:
            with self.subTest(command=command):self.assertTrue(allowed(command,self.workspace))
        for command in ['find . -not','find . -o -print','find . -print -o','find . ( -print',
                        'test -f /etc/passwd','test x = x','test -f main.py -a -f /etc/passwd',
                        "find . -printf '%p\\n' -exec sh x ;",'find . -fls output']:
            with self.subTest(command=command):self.assertFalse(allowed(command,self.workspace))

    def test_sort_cannot_write_or_spawn_helpers(self):
        for command in ['sort -o result.txt main.py','sort --output=result.txt main.py',
                        'sort --compress-program=sh main.py','sort --files0-from=/etc/passwd',
                        'sort /etc/passwd','sort ../secret']:
            with self.subTest(command=command):self.assertFalse(allowed(command,self.workspace))

    def test_current_git_status_probe_does_not_allow_history_or_configuration(self):
        self.assertTrue(allowed('git status --short',self.workspace))
        self.assertFalse(allowed('git show HEAD:secret',self.workspace))
        self.assertFalse(allowed('git -c alias.status=!sh status',self.workspace))

    def test_symlink_escape_is_rejected(self):
        outside=Path(self.tmp.name)/'outside';outside.mkdir()
        try:(self.workspace/'escape').symlink_to(outside,target_is_directory=True)
        except OSError:self.skipTest('symlink creation unavailable')
        self.assertFalse(allowed('find escape -type f',self.workspace))
        self.assertFalse(allowed('sort escape/secret',self.workspace))

    def test_long_rg_expression_is_data_not_a_filename(self):
        expression='callback|generation|pending|'*20
        with patch.object(Path,'exists',side_effect=AssertionError('Pattern must not be statted')):
            self.assertTrue(allowed('rg -n '+shlex.quote(expression)+' main.py',self.workspace))
            self.assertTrue(allowed('rg -n -e '+shlex.quote(expression)+' main.py',self.workspace))
            self.assertTrue(allowed('rg --regexp='+shlex.quote(expression)+' main.py',self.workspace))
        self.assertTrue(allowed('rg -n /etc/passwd main.py',self.workspace))

    def test_rg_globs_and_output_text_are_data_without_filesystem_stat(self):
        pattern='*callback*'*60
        with patch.object(Path,'exists',side_effect=AssertionError('Data must not be statted')):
            self.assertTrue(allowed('rg --files -g '+shlex.quote(pattern),self.workspace))
            self.assertTrue(allowed('find . -name '+shlex.quote(pattern),self.workspace))
            self.assertTrue(allowed('printf "%s" '+shlex.quote(pattern),self.workspace))

    def test_rg_file_operands_and_effectful_options_remain_restricted(self):
        for command in ['rg -n pattern /etc/passwd','rg --files /etc',
                        'rg -e pattern ../secret','rg -n pattern escape/secret',
                        'rg --pre=sh pattern .','rg --pre sh pattern .',
                        'rg --hostname-bin sh pattern .','rg --ignore-file /etc/passwd pattern .',
                        'rg -f /etc/passwd .','rg --file=/etc/passwd .',
                        'rg --follow pattern .','rg -L pattern .','rg -z pattern .',
                        'rg -n "$DEEPSEEK_API_KEY" main.py','printf -vLEAK x']:
            if 'escape/' in command:
                outside=Path(self.tmp.name)/'outside';outside.mkdir(exist_ok=True)
                try:(self.workspace/'escape').symlink_to(outside,target_is_directory=True)
                except OSError:continue
            with self.subTest(command=command):self.assertFalse(allowed(command,self.workspace))

    def test_long_actual_filename_is_denied_without_collector_exception(self):
        name='x'*560
        for command in ['cat '+name,'rg -n pattern '+name,'find '+name+' -type f']:
            with self.subTest(command=command):self.assertFalse(allowed(command,self.workspace))

    def test_common_rg_discovery_context_and_explicit_regex_forms(self):
        for command in ["rg --files --hidden -g '!node_modules/**'",
                        'rg -nH --glob=*.py pattern .','rg -n -C 3 pattern main.py',
                        'rg -n -C3 pattern main.py','rg --context=3 -e pattern main.py',
                        'rg --color never pattern main.py','rg -- --pre main.py']:
            with self.subTest(command=command):self.assertTrue(allowed(command,self.workspace))

    def test_regex_end_anchors_and_literal_dollar_are_data(self):
        for command in ["rg -n 'callback$' main.py",r"rg -n '\$' main.py",
                        "rg -e 'callback$|pending$' main.py","printf '%s' '$'",
                        "for f in main.py; do printf '%s' \"${f}\"; done"]:
            with self.subTest(command=command):self.assertTrue(allowed(command,self.workspace))

    def test_dollar_data_never_exposes_shell_parameters_or_credentials(self):
        for expression in ['$DEEPSEEK_API_KEY',r'\$DEEPSEEK_API_KEY','${DEEPSEEK_API_KEY}',
                           '${DEEPSEEK_API_KEY:-fallback}','$[1+2]','$((1+2))','$(pwd)',
                           '$?','$$','$!','$@','$*','$#','$-','$0','$9']:
            command='rg -n '+shlex.quote(expression)+' main.py'
            with self.subTest(expression=expression):self.assertFalse(allowed(command,self.workspace))
        self.assertFalse(allowed("cat 'main.py$'",self.workspace))


if __name__=='__main__':unittest.main()
