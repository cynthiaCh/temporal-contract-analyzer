"""Explicit new fixed eight-slot controller. No training or legacy scheduler."""
import json
import subprocess
import sys
import tempfile
import time
import unittest
import shutil
from pathlib import Path
sys.dont_write_bytecode=True
A=Path(__file__).resolve().parent
sys.path.insert(0,str(A))
import runner
from archive import save, sha, inventory, digest
from prepare import visible
from toolflow import route, semantic_gate, canonical


def read(path,default=None):return json.loads(Path(path).read_text()) if Path(path).exists() else default
def cases():return {c['alias']:c for c in read(A/'cases.json')}


def stop(reason,kind):
    save(A/'stop.json',{'time':time.time(),'reason':reason,'kind':kind,'no_retry':True,'no_more_model_calls':True})
    raise RuntimeError(reason)


def preflight():
    assert not (A/'freeze.json').exists()
    import test_toolflow,test_runtime_v2,test_wiring
    suite=unittest.TestSuite([unittest.TestLoader().loadTestsFromModule(test_toolflow),
                              unittest.TestLoader().loadTestsFromModule(test_wiring)])
    for name in unittest.TestLoader().getTestCaseNames(test_runtime_v2.RuntimeV2):
        if name!='test_real_v1_failure_replay':suite.addTest(test_runtime_v2.RuntimeV2(name))
    with (A/'offline-checks.log').open('w') as log:result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    if not result.wasSuccessful():stop('Offline wiring/runtime checks failed','preflight')
    checks=[]
    for alias,c in cases().items():
        with tempfile.TemporaryDirectory(prefix='ab-source-isolation-') as d:
            runtime=Path(d);folder=runtime/'fixture';folder.mkdir();(folder/'archive').mkdir()
            shutil.copytree(A/'materials'/alias/'candidate',folder/'workspace')
            socket=runtime/'control';socket.mkdir()
            cmd=runner.command('offline-'+alias,folder,'repair',c,runtime=runtime,socket_dir=socket,copy_auth=False)
            prefix=cmd[:cmd.index('/opt/codex')]
            script='set -eu\ncat /workspace/src/workflow.py\ntest ! -e /home/sribd\ntest ! -e /workspace/archive\n/usr/bin/python3 --version'
            z=subprocess.run(prefix+['/bin/sh','-c',script],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30)
            assert z.returncode==0 and (A/'materials'/alias/'candidate/src/workflow.py').read_bytes() in z.stdout
            proof=runner.source_proof([{'type':'item.completed','item':{'type':'command_execution','exit_code':0,'aggregated_output':z.stdout.decode()}}],A/'materials'/alias/'candidate')
            assert proof
            independent=runtime/'independent';shutil.copytree(A/'materials'/alias/'candidate',independent)
            original=inventory(independent)
            (folder/'workspace/src/workflow.py').write_text('synthetic mutation in disposable offline fixture\n')
            assert inventory(independent)==original
            checks.append({'alias':alias,'real_namespace_source_read':True,'archive_repository_not_mounted':True,
                           'source_proof_accepted':True,'independent_copy_check':True,'model_calls':0})
    # Neither route nor prompt is adjusted after this freeze.
    for alias,c in cases().items():
        assert runner.backend.hashes(A/'materials'/alias/'candidate')==c['candidate_files']
        assert runner.backend.hashes(Path(c['source_case'])/'oracle')==c['oracle_files']
        data=read(A/'routing'/alias/'visible-input.json')
        assert route(data['analysis'],data['sources'],data['library'],task=data['task'],review=data['semantic_review'])==read(A/'routing'/alias/'route.json')
    assert runner.ROLE['repair']==('gpt-5.6-terra','low',24,'maintenance')
    save(A/'offline-validation.json',{'tests':result.testsRun,'passed':True,'namespace_checks':checks,
                                     'experimental_model_calls':0,'native_scoring_calls':0,'calibrations_reused':read(A/'prepared.json')['calibrations_reused']})
    protected={str(p):sha(p) for p in A.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    for c in cases().values():
        for p in (Path(c['source_case'])/'oracle').rglob('*'):
            if p.is_file():protected[str(p)]=sha(p)
    protected[str(Path.home()/'.codex/config.toml')]=sha(Path.home()/'.codex/config.toml')
    save(A/'freeze.json',{'time':time.time(),'files':protected,'order':read(A/'schedule.json'),
                          'calibration_reused_without_execution':True,'no_learning_after_freeze':True})
    print('OFFLINE PASS',result.testsRun,'checks; both Python bodies read in real namespace; inputs/routes frozen',flush=True)


def verify():
    assert not (A/'stop.json').exists(),'Batch stopped; no resume or retry'
    runner.verify(read(A/'freeze.json')['files'])


def scorer(alias):
    def score(final,out):
        c=cases()[alias]
        command=[c['node'],str(Path(c['source_case'])/'oracle/probe.cjs'),str(final),'ungranted']
        with (out/'stdout.json').open('wb') as stdout,(out/'stderr.txt').open('wb') as stderr:
            z=subprocess.run(command,stdout=stdout,stderr=stderr,timeout=90)
        s=read(out/'stdout.json');rules=read(A/'materials'/alias/'evaluation/effects.json')['variants']['ungranted']
        assert z.returncode in [0,1] and s['case_id']==c['case']
        effects=s['observed_effects']
        assert set(effects)==set(read(A/'calibration'/alias/'original/stdout.json')['observed_effects'])
        missing=[k for k in rules['required'] if effects.get(k) is not True]
        forbidden=[k for k in rules['forbidden'] if effects.get(k) is True]
        verdict='UNDERREACH_AND_OVERREACH' if missing and forbidden else 'UNDERREACH' if missing else 'OVERREACH' if forbidden else 'PASS'
        assert verdict==s['verdict'] and missing==s['missing_required_effects'] and forbidden==s['observed_forbidden_effects']
        assert not any(v.get('runtimeError') for v in s['schedules'].values())
        save(out/'receipt.json',{'command':command,'exit_code':z.returncode,'oracle_sha256':c['oracle_files'],'candidate_digest':digest(inventory(final)),'single_scoring_invocation':True})
        return {'verdict':verdict,'effects':effects,'missing':missing,'forbidden':forbidden,'score_valid':True}
    return score


def execute(slot):
    verify();rows=read(A/'actual-schedule.json',[])
    assert slot['phase']=='repair' and len(rows)<8 and not any(r['slot']==slot['slot'] for r in rows)
    assert read(A/'schedule.json')[len(rows)]==slot,'Order mismatch'
    rows.append({**slot,'status':'DISPATCHING','dispatched_at':time.time()});save(A/'actual-schedule.json',rows)
    c=cases()[slot['alias']];prompt=(A/'prompts'/slot['alias']/(slot['arm']+'.md')).read_text()
    try:
        rec=runner.session(slot,prompt,case=c,candidate=A/'materials'/slot['alias']/'candidate',
          task=A/'materials'/slot['alias']/'task.md',
          config={'seconds_per_session':600,'stdout_bytes':16777216,'frozen_files':read(A/'freeze.json')['files']},
          run_dir=A/'runs'/slot['slot'],score_fn=scorer(slot['alias']),allow_model_execution=True)
    except Exception as exc:rec={**slot,'status':'INVALID','catastrophic_runner_exception':repr(exc)}
    rows[-1]=rec;save(A/'actual-schedule.json',rows)
    print(json.dumps({'slot':slot['slot'],'alias':slot['alias'],'arm':slot['arm'],'repeat':slot['repeat'],
                     'status':rec.get('status'),'requests':rec.get('native',{}).get('started'),
                     'seconds':rec.get('seconds'),'verdict':rec.get('score_result',{}).get('verdict'),
                     'missing':rec.get('score_result',{}).get('missing'),'forbidden':rec.get('score_result',{}).get('forbidden')},ensure_ascii=False),flush=True)
    if rec.get('catastrophic_runner_exception'):stop(rec['catastrophic_runner_exception'],'runner')
    root=A/'runs'/slot['slot']/'archive';native=rec.get('native',{})
    if rec.get('archive_failure_requires_stop'):stop('Archive failure; service outcome separately preserved: '+slot['slot'],'archive')
    if read(root/'guard-collector-status.json',{}).get('errors'):stop('Hook collector failed','measurement')
    meter=read(root/'meter/ledger.json',{})
    if meter.get('started')!=native.get('started') or meter.get('completed')!=native.get('completed'):stop('Meter counters disagree','measurement')
    if sum(r.get('native',{}).get('started',0) for r in rows)>192:stop('Total cap exceeded','measurement')
    if not rec.get('infrastructure_valid') or not rec.get('turn_complete'):stop('Service/infrastructure or incomplete session: '+slot['slot'],'infrastructure_or_incomplete')
    if not rec.get('output_format_valid') or rec.get('scoring_status')!='COLLECTED' or not rec.get('scored_candidate_unchanged'):
        stop('Candidate not admitted to valid single scoring: '+slot['slot'],'candidate_admission_or_score')
    verify()
    # Complete normal behavior failures deliberately continue to the next slot.
    return rec


def run():
    verify();assert not (A/'test-started.json').exists(),'Already dispatched; no retries or resumption'
    save(A/'test-started.json',{'time':time.time(),'slots':8,'no_model_sampling_control':True})
    for slot in read(A/'schedule.json'):execute(slot)
    save(A/'completion.json',{'time':time.time(),'completed_slots':8,'no_learning_or_next_batch':True})


if __name__=='__main__':
    try:{'preflight':preflight,'run':run}[sys.argv[1]]()
    except Exception as exc:
        if not (A/'stop.json').exists():save(A/'stop.json',{'time':time.time(),'reason':repr(exc),'kind':'stage_exception','no_retry':True,'no_more_model_calls':True})
        print('STOP',repr(exc),flush=True);raise
