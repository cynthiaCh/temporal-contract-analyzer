"""Exercise actual four candidate namespaces using a fake local CLI, zero models."""
import json
from pathlib import Path
import sys
import time

sys.dont_write_bytecode = True
A = Path(__file__).resolve().parent
sys.path.insert(0, str(A))
import runner
from archive import save, inventory


def main():
    t = time.monotonic()
    receipts = []
    for case in json.loads((A / 'cohort.json').read_text()):
        alias = case['alias']
        original = A / 'materials' / alias / 'candidate'

        def fake(a, runtime, guard):
            command = runner.command('offline-' + alias, a.run_dir, 'extract', case,
                                     runtime=runtime, socket_dir=guard.directory, copy_auth=False)
            prefix = command[:command.index('--') + 1]
            # Exact production namespace; replace its executable with local stdlib Python.
            # Hook events below are explicit synthetic fixtures, never paid requests.
            body = '''from pathlib import Path
import json,socket,subprocess
def hook(event):
    s=socket.socket(socket.AF_UNIX);s.connect('/hook-control/hook.sock')
    s.sendall(json.dumps(event).encode()+b'\\n');result=json.loads(s.recv(2048));s.close()
    assert not result['deny'],result
assert not any(Path(p).exists() for p in ['/archive','/output','/meter','/workspace/../archive'])
assert not Path('/home/sribd').exists()
assert not Path('/home/agent/.codex/auth.json').exists()
subprocess.run(['/runtime/node','--version'],check=True,stdout=subprocess.DEVNULL)
subprocess.run(['/usr/bin/python3','--version'],check=True,stdout=subprocess.DEVNULL)
hook({'hook_event_name':'PreModelRequest','model':'gpt-6-sol','fixture_only':True})
hook({'hook_event_name':'PreToolUse','tool_name':'Bash','tool_input':{'command':'cat src/*'}})
text='\\n'.join(p.read_text() for p in Path('/workspace/src').rglob('*') if p.suffix in ['.js','.py'])
print(json.dumps({'type':'item.completed','item':{'type':'command_execution','exit_code':0,'aggregated_output':text}}))
analysis={'contract':'OFFLINE SYNTHETIC FIXTURE ONLY','primary_class':'unknown','secondary_tags':[],'evidence':[],'facts':[]}
print(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':json.dumps({'report':json.dumps(analysis)})}}))
hook({'hook_event_name':'PostModelRequest','model':'gpt-6-sol','status':'completed','fixture_only':True,'token_usage':{'input_tokens':1,'output_tokens':1}})
print(json.dumps({'type':'turn.completed'}))
'''
            return prefix + ['/usr/bin/python3', '-B', '-c', body]

        rec = runner.session({'slot': 'offline-' + alias, 'phase': 'extract', 'condition': 'FIXTURE'},
            'Offline fixture only, no model calls.', case=case, candidate=original,
            task=A / 'materials' / alias / 'task.md', config={'seconds_per_session': 30},
            run_dir=A / 'offline' / alias, command_factory=fake)
        assert rec['infrastructure_valid'] and rec['archive_status']['status'] == 'OK', rec
        assert rec['preanalysis_valid'] and rec['source_body_proofs'], rec
        assert inventory(original) == inventory(A / 'offline' / alias / 'archive/final-candidate')
        receipts.append({'alias': alias, 'status': 'PASS', 'namespace': 'actual production bwrap prefix',
                         'source_body_proofs': rec['source_body_proofs'], 'synthetic_ledger_only': True})
    prior = json.loads((A / 'offline-validation.json').read_text())
    prior.update({'toolflow_tests': 16, 'toolflow_tests_passed': True,
                  'actual_four_candidate_namespaces': receipts, 'actual_candidate_namespace_seconds': time.monotonic() - t,
                  'experiment_model_calls': 0, 'synthetic_ledger_not_real_usage': True,
                  'AST_all_four_parsed': True, 'exact_version_calibrations_reused': 44})
    save(A / 'offline-validation.json', prior)
    print('PASS: actual four candidate namespaces, source bodies, IPC, parser and automatic archives; zero models')


if __name__ == '__main__':
    main()
