"""Fresh V12 checkpoint orchestration; all solving stays in the existing engine."""
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
from copy import deepcopy
import csv
from datetime import datetime,timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import threading
import time
import tempfile

from temporal_contract_analyzer import archive,delegated_review,experience_memory
from temporal_contract_analyzer.balance_budget import BalanceBudget
from temporal_contract_analyzer.core import EvidenceError,canonical,sha
from temporal_contract_analyzer.frozen_benchmark import FrozenBenchmark,syntax_evaluator,gold_evaluator
from temporal_contract_analyzer.tempoevo_backend import NativeV4Backend
from temporal_contract_analyzer.tempoevo_v4 import Trajectory,LIMITS
from temporal_contract_analyzer._session_runtime.model_settings import resolve_profile,identity

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
POINTS=list(range(0,71,10))


def read(path):return json.loads(Path(path).read_text(encoding='utf8'))
def now():return datetime.now(timezone.utc).isoformat()
def file_sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def immutable(path,value):
    path=Path(path);raw=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf8')
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if path.read_bytes()!=raw:raise EvidenceError('Immutable receipt differs: '+str(path))
    else:
        fd,temp=tempfile.mkstemp(prefix='.receipt-',dir=path.parent)
        try:
            with os.fdopen(fd,'wb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
            os.replace(temp,path)
        finally:
            if os.path.exists(temp):os.unlink(temp)
    return value


def bindings():
    paths=list((REPO/'temporal_contract_analyzer').rglob('*.py'))
    paths+=list((REPO/'temporal_contract_analyzer/_session_runtime').glob('*.json'))
    paths+=list((REPO/'temporal_contract_analyzer/_session_runtime').glob('*.toml'))
    paths+=[REPO/'temporal_contract_analyzer/contract-taxonomy.json']
    paths+=[REPO/'tools/tempoevo-docker'/n for n in ('gold.py','projected_gold.py','python_gold.py','public_syntax.py')]
    paths+=[HERE/'run_growth.py',HERE/'controller.py',HERE/'admission/runtime.json',HERE/'admission/controller-runtime.json']
    paths+=[REPO/'experiments/incremental-runs/tempoevo-incremental100-workers4-20261117_011424/public-checks-docs.json']
    paths += [p for p in (REPO/'temporal_contract_analyzer/javascript').glob('*') if p.suffix in ('.js','.json')]
    paths+=list((HERE/'inputs').glob('*'))
    return {p.relative_to(REPO).as_posix():file_sha(p) for p in paths if p.is_file()}


class MeteredBackend:
    def __init__(self,run,protocol,job):
        self.run=run;self.backend=NativeV4Backend(protocol);self.job=job

    def execute(self,kind,payload,model,limits,directory):
        self.run.verify();directory=Path(directory)
        sid=directory.relative_to(self.run.root).as_posix()
        receipt=directory/'metered-result.json'
        if receipt.exists():
            sealed=read(receipt)
            if sealed['input_sha256']!=sha(canonical(payload).encode()) or sealed['model']!=model or sealed['limits']!=limits:
                raise EvidenceError('Completed execution identity changed')
            self.run.budget.observe(sealed['result'],sid)
            return sealed['result']
        gate=self.run.budget.before_stage(sid)
        if not gate['allowed']:raise EvidenceError('Model stage admission stopped: '+str(gate['reason']))
        self.run.event('stage_intent',job=self.job,stage=sid,kind=kind,model=model,limits=limits,
            input_sha256=sha(canonical(payload).encode()))
        self.run.active(self.job,kind)
        result=self.backend.execute(kind,payload,model,limits,directory)
        immutable(receipt,dict(input_sha256=sha(canonical(payload).encode()),model=model,limits=limits,result=result))
        self.run.budget.observe(result,sid)
        self.run.event('stage_settled',job=self.job,stage=sid,kind=kind,valid=result.get('valid'),
            requests=result.get('requests'),usage_incomplete=result.get('usage_incomplete'),failure_type=result.get('failure_type'))
        return result

    def evaluate(self,kind,payload,directory):
        self.run.verify();self.run.active(self.job,kind)
        # Exactly the engine's evaluation endpoint. No candidate choice or Gold repair.
        result=self.backend.evaluate(kind,payload,directory)
        self.run.event('evaluation_finished',job=self.job,stage=str(directory.relative_to(self.run.root)),
            kind=kind,valid=result.get('valid'),purpose=payload.get('purpose'))
        return result


class Run:
    def __init__(self,run_id,pilot=False):
        if not re.fullmatch(r'[a-zA-Z0-9_-]{1,100}',run_id):raise ValueError('Invalid run identifier')
        self.run_id=run_id;self.pilot=pilot;self.root=HERE/'runs'/run_id
        self.store=self.root/'store';self.lock=threading.RLock();self.current={};self.stopping=threading.Event()
        os.environ['TCA_STOP_FILE']=str(self.root/'STOP_REQUESTED')
        self.runtime=read(HERE/'admission/runtime.json')
        self.controller_runtime=read(HERE/'admission/controller-runtime.json')
        if not self.controller_runtime.get('valid'):raise EvidenceError('Controller runtime requires verified admission')
        report=read(self.runtime['admission_report'])
        if report['status']!='passed' or report['verified']!=100 or file_sha(self.runtime['admission_report'])!=self.runtime['admission_report_sha256']:
            raise EvidenceError('All 100 cases require current dynamic admission')
        self.frozen=FrozenBenchmark(self.runtime)
        self.training=list(csv.DictReader((HERE/'inputs/training-order.csv').open(encoding='utf8')))
        self.testing=list(csv.DictReader((HERE/'inputs/testing-cases.csv').open(encoding='utf8')))
        self.settings=resolve_profile('deepseek-flash-high');self.model=identity(self.settings)
        if self.model['model']!='deepseek-flash' or self.model['reasoning_effort']!='high':raise EvidenceError('Model profile drift')
        self.root.mkdir(parents=True,exist_ok=True)
        self.writer=(self.root/'writer.lock').open('a')
        fcntl.flock(self.writer,fcntl.LOCK_EX|fcntl.LOCK_NB)
        self.budget=BalanceBudget(self.root/'balance.json',authorized_total_cny=None,max_inflight_stages=2,max_requests=30000)
        manifest=self.root/'manifest.json'
        if manifest.exists():
            self.manifest=read(manifest)
            if not (self.root/'balance.json').exists() or not (self.root/'events.jsonl').exists():
                raise EvidenceError('Initialized run is missing an accounting ledger')
            if self.manifest['pilot']!=pilot:raise EvidenceError('Run purpose changed')
            self.verify()
        else:
            if any(self.root.iterdir()) and set(p.name for p in self.root.iterdir())!={'writer.lock'}:
                raise EvidenceError('Unrecognized partial initialization requires inspection')
            experience_memory.initialize(self.store)
            bank=delegated_review.freeze(self.store)
            if bank['entries']:raise EvidenceError('Fresh run must start empty')
            self.manifest=dict(schema_version='experience-growth-v12-run-v1',run_id=run_id,pilot=pilot,created_at=now(),
                bindings=bindings(),runtime=deepcopy(self.runtime),controller_runtime=self.controller_runtime,model=self.model,model_settings=self.settings,
                authorization='User confirmed current master V12 priority, AI delegated review, fresh 70/30, DeepSeek Flash/high and M0-M70 on 2026-11-18; paper differences are documentation only.',
                checkpoints=POINTS,training_ids=[r['case_id'] for r in self.training],testing_ids=[r['case_id'] for r in self.testing],
                testing_workers=2,training_workers=1,initial_snapshot=bank,
                policy=dict(training_recipe='v8-compatible-v1',training_retrieval='source-bound-v8',
                    testing_retrieval='business-source-v1',review_policy='ai_delegated',learning_policy='frozen',
                    analysis_tools=True,limits=LIMITS,review_limits=dict(requests=12,seconds=600),
                    recovery='Reuse verified completed receipts only; interrupted model execution requires evidence reconciliation, never automatic replay',
                    behavioral_failure='Record without extra Action or test-driven tuning',
                    public_check='master public_syntax.py; training requires public and Oracle acceptance',
                    gold='One final candidate and one independent Gold; invalid scoring is not behavioral failure',
                    monetary_policy='Observed available balance with 10 CNY cash reserve and 10 CNY per active stage; no historical 250 CNY cap'))
            immutable(manifest,self.manifest)
            self.event('run_initialized',pilot=pilot,initial_entries=0)
            self.budget.initialize()
        self.approved_entries=len(delegated_review.freeze(self.store)['entries'])
        self.heartbeat=threading.Thread(target=self._heartbeats,daemon=True);self.heartbeat.start()

    def verify(self):
        if self.stopping.is_set():raise EvidenceError('Run dispatch stopped; inspect last event before resuming')
        if (self.root/'STOP_REQUESTED').exists():raise EvidenceError('User or supervisor stop requested')
        for relative,digest in self.manifest['bindings'].items():
            if file_sha(REPO/relative)!=digest:raise EvidenceError('Frozen source/input changed: '+relative)
        if self.runtime!=self.manifest['runtime']:raise EvidenceError('Runtime identity changed')

    def event(self,event_name,**fields):
        item=dict(at=now(),run_id=self.run_id,event=event_name,**fields)
        with self.lock:
            with (self.root/'events.jsonl').open('a',encoding='utf8') as stream:
                stream.write(json.dumps(item,ensure_ascii=False)+'\n');stream.flush();os.fsync(stream.fileno())
        if event_name in ('run_initialized','job_closed','run_stopped','run_completed','checkpoint_frozen'):
            with (HERE/'EVENTS.jsonl').open('a',encoding='utf8') as stream:
                stream.write(json.dumps(item,ensure_ascii=False)+'\n');stream.flush();os.fsync(stream.fileno())

    def active(self,job,stage):
        with self.lock:self.current[job]=stage

    def results(self):
        return [read(p) for p in sorted((self.root/'jobs').glob('*/completion.json'))]

    def progress(self,status='running',reason=None):
        with self.lock:
            receipts=self.results();money=self.budget.summary();state=read(HERE/'LIVE_PROGRESS.json')
            training=[r for r in receipts if r['mode']=='learning'];testing=[r for r in receipts if r['mode']=='testing']
            state.update(status=status,run_id=self.run_id,updated_at=now(),protocol_status='pilot_frozen' if self.pilot else 'formal_frozen',
                current_checkpoint=getattr(self,'checkpoint','pilot' if self.pilot else 'M0'),current_case=dict(self.current),
                current_stage='; '.join(sorted(set(self.current.values()))) or None,stop_reason=reason)
            state['training']['closed']=0 if self.pilot else len(training)
            state['testing']['completed']=0 if self.pilot else len(testing)
            state['finance'].update(confirmed_start_balance_cny=read(self.root/'balance.json')['baseline_balance_cny'],
                observed_spend_cny=money['observed_decrease_cny'],latest_balance_cny=money['last_balance_cny'],
                unknown_usage_events=money['unknown_request_count'],usage_incomplete=money['incomplete_usage'])
            state['approved_experience_count']=self.approved_entries
            for row,n in zip(state['checkpoints'],POINTS):
                records=[] if self.pilot else [r for r in testing if r['checkpoint']==n]
                valid=[r for r in records if r['gold_valid']];passed=sum(r['passed'] is True for r in valid)
                invalid_pending=[] if self.pilot else [p for p in (self.root/'jobs').glob('M'+str(n)+'-T*/trajectory/state.json')
                    if not (p.parent.parent/'completion.json').exists() and read(p).get('status')=='execution_invalid']
                snap=self.root/'checkpoints'/('M'+str(n)+'.json')
                row.update(completed=len(records),valid_gold=len(valid) if records else None,passed=passed if records else None,
                    behavioral_failed=len(valid)-passed if records else None,
                    invalid=len(records)-len(valid)+len(invalid_pending) if records or invalid_pending else None,
                    status='complete' if len(records)==30 and len(valid)==30 else 'incomplete' if records else 'not_started',
                    snapshot_sha256=read(snap)['sha256'] if snap.exists() else None)
            archive.atomic_json(HERE/'LIVE_PROGRESS.json',state)
            # Use the one existing public view, never create a competing latest status.
            import importlib.util
            spec=importlib.util.spec_from_file_location('growth_monitor',HERE/'monitor.py')
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.refresh(HERE)
            archive.atomic_json(self.root/'status.json',dict(status=status,at=now(),reason=reason,active=dict(self.current),
                training_closed=len(training),testing_closed=len(testing),finance=money,pilot=self.pilot))

    def _heartbeats(self):
        while not self.stopping.wait(30):
            try:self.progress()
            except Exception as error:
                self.event('heartbeat_error',error=repr(error));self.stopping.set()

    def prepare(self,row,mode,checkpoint,snapshot):
        name=('pilot-' if self.pilot else '')+('D'+str(row['rank']).zfill(2) if mode=='learning' else 'M'+str(checkpoint)+'-T'+str(row['rank']).zfill(2))
        folder=self.root/'jobs'/name;root=folder/'trajectory'
        if (folder/'completion.json').exists():return name,folder,Trajectory(root)
        if root.exists():
            trajectory=Trajectory(root);protocol=trajectory.verify()
            if protocol['task_id']!=row['case_id'] or protocol['memory_snapshot_sha256']!=snapshot['sha256']:
                raise EvidenceError('Prepared job snapshot or identity differs')
            return name,folder,trajectory
        folder.mkdir(parents=True,exist_ok=True)
        if any(folder.iterdir()):raise EvidenceError('Partial job preparation must be inspected before reuse')
        projection=self.frozen.export(row['case_id'],folder/'public',project=True)
        if mode=='learning':
            docs=read(REPO/'experiments/incremental-runs/tempoevo-incremental100-workers4-20261117_011424/public-checks-docs.json')
            texts=set(docs.values())
            if len(texts)!=1:raise EvidenceError('Master public check descriptions are not unambiguous')
            (folder/'public/VISIBLE_CHECKS.md').write_text(next(iter(texts)),encoding='utf8')
        cfg=self.frozen.case_config(row['case_id']);archive.atomic_json(folder/'case.json',cfg)
        _,manifest=self.frozen.manifest(row['case_id'])
        gold=gold_evaluator(REPO,self.runtime['backend']['grader_image'],folder/'case.json',manifest,cfg)
        config=dict(task_id=row['case_id'],task=self.frozen.task(row['case_id']),candidate=str(folder/'public'),
            store=str(self.store),mode=mode,condition='structured',model_profile='deepseek-flash-high',model=self.model,
            binary=str(Path(os.environ['TCA_PUBLIC_CLI'])/'codex'),backend=self.runtime['backend'],
            review_policy='ai_delegated',memory_snapshot=snapshot,learning_policy='frozen',analysis_tools=True,
            evaluation_split_file=str(HERE/'inputs/evaluation-split.json'),limits=deepcopy(LIMITS),
            protected_paths=['README.md','PROJECTION.md']+(['VISIBLE_CHECKS.md'] if mode=='learning' else []))
        if mode=='learning':config.update(training_recipe='v8-compatible-v1',retrieval_profile='source-bound-v8',
            max_attempts=3,training_evaluator=gold,training_feedback={},visible_evaluator=syntax_evaluator(REPO,self.runtime['backend']['grader_image']))
        else:config.update(retrieval_profile='business-source-v1',max_attempts=1,gold_evaluator=gold)
        archive.atomic_json(folder/'config.json',config)
        trajectory=Trajectory(root);trajectory.prepare(config)
        expected=132 if mode=='learning' else 48
        if read(root/'protocol.json')['total_request_cap']!=expected:raise EvidenceError('Prepared budget differs from fixed policy')
        self.event('job_prepared',job=name,case_id=row['case_id'],mode=mode,snapshot=snapshot['sha256'],request_cap=expected)
        return name,folder,trajectory

    def review(self,trajectory,backend,folder):
        state=trajectory.state();directory=folder/'review';directory.mkdir(exist_ok=True)
        if (directory/'closure.json').exists():return read(directory/'closure.json')
        model=self.model;limits=dict(requests=12,seconds=600)
        if state['status']=='awaiting_expert_summary':
            result=delegated_review.reflect_failure(backend,trajectory.root,self.store,directory/'failure',model,limits)
            if result['decision']=='candidate':
                result=delegated_review.review_candidate(backend,trajectory.root,self.store,result['candidate_sha256'],directory/'candidate',model,limits)
        elif (trajectory.root/'candidate-pool/success.json').exists():
            code=trajectory.publish_candidate('success');record=read(trajectory.root/'candidate-pool/success.json')
            if record.get('publication_kind')=='evidence_proposal':
                # Content is unchanged; source-review its target and separately bind the evidence proposal.
                target=record['reflection_update']['target_sha256s'][0]
                result=delegated_review.review_candidate(backend,trajectory.root,self.store,target,directory/'evidence',model,limits,evidence_only=True)
                result=dict(result,evidence_proposal_sha256=code,content_changed=False)
                immutable(self.store/'workflow/ai-evidence-reviews'/(code+'.json'),result)
            else:result=delegated_review.review_candidate(backend,trajectory.root,self.store,code,directory/'candidate',model,limits)
        elif state['status']=='execution_invalid':
            raise EvidenceError('Training execution invalid: '+str(state.get('error')))
        else:result=delegated_review.record_no_update(self.store,trajectory.root,'No candidate was produced by the completed training trajectory.',directory/'none',model)
        immutable(directory/'closure.json',result)
        if state['status']=='awaiting_expert_summary':
            trajectory.status('awaiting_content_review',ai_expert_summary_closed=True,ai_review_closure=str(directory/'closure.json'))
        return result

    def job(self,row,mode,checkpoint,snapshot):
        self.verify();name,folder,trajectory=self.prepare(row,mode,checkpoint,snapshot)
        done=folder/'completion.json'
        if done.exists():
            receipt=read(done)
            if receipt['case_id']!=row['case_id'] or receipt['snapshot_sha256']!=snapshot['sha256']:raise EvidenceError('Completed job identity differs')
            if file_sha(trajectory.root/'state.json')!=receipt['state_sha256']:raise EvidenceError('Completed trajectory state changed')
            if receipt.get('review_closure_sha256') and file_sha(folder/'review/closure.json')!=receipt['review_closure_sha256']:
                raise EvidenceError('Completed review closure changed')
            return receipt
        self.active(name,'prepare');protocol=trajectory.verify();backend=MeteredBackend(self,protocol,name)
        initial=trajectory.state()
        if any(s['status']=='started' for s in initial['stages']):raise EvidenceError('Interrupted stage needs reconciliation; no redispatch')
        started=time.monotonic()
        state=initial if initial.get('finalized') else trajectory.run(backend,execute=True)
        if state['status']=='execution_invalid':raise EvidenceError('Execution invalid for '+name+': '+str(state.get('error')))
        review=self.review(trajectory,backend,folder) if mode=='learning' else None
        if review:
            with self.lock:self.approved_entries=len(delegated_review.freeze(self.store)['entries'])
        state=trajectory.state();gold=state.get('gold_result') or {}
        stages=[s for s in read(self.root/'balance.json')['stages'] if s['stage_id'].startswith('jobs/'+name+'/')]
        receipt=dict(schema_version='experience-growth-job-receipt-v1',run_id=self.run_id,job=name,case_id=row['case_id'],
            mode=mode,rank=int(row['rank']),core_case=row['core_case'],source_unit=row['source_unit'],runtime=row['runtime'],
            checkpoint=checkpoint,snapshot_sha256=snapshot['sha256'],status=state['status'],
            training_accepted=state.get('training_accepted'),gold_valid=gold.get('valid') is True,
            passed=gold.get('passed') if gold.get('valid') is True else None,verdict=gold.get('verdict'),
            attempts=len(state['attempts']),review=review,approved_entries_after=self.approved_entries,
            requests=sum(s['requests'] for s in stages) if all(type(s.get('requests')) is int for s in stages) else None,
            unknown_usage_requests=sum(s.get('unknown_request_count') or 0 for s in stages),
            elapsed_seconds=time.monotonic()-started,closed_at=now(),trajectory=str(trajectory.root),
            state_sha256=file_sha(trajectory.root/'state.json'),review_closure_sha256=file_sha(folder/'review/closure.json') if review else None)
        immutable(done,receipt)
        with self.lock:self.current.pop(name,None)
        self.event('job_closed',job=name,case_id=row['case_id'],mode=mode,checkpoint=checkpoint,status=receipt['status'],
            passed=receipt['passed'],gold_valid=receipt['gold_valid'],approved_entries=receipt['approved_entries_after'])
        self.progress();return receipt

    def test_checkpoint(self,n):
        self.checkpoint='M'+str(n);path=self.root/'checkpoints'/(self.checkpoint+'.json')
        snapshot=read(path) if path.exists() else immutable(path,delegated_review.freeze(self.store))
        if n==0 and snapshot['entries']:raise EvidenceError('M0 must have no guidance')
        self.event('checkpoint_frozen',checkpoint=n,snapshot_sha256=snapshot['sha256'],entries=len(snapshot['entries']))
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures=[pool.submit(self.job,row,'testing',n,snapshot) for row in self.testing]
            try:
                for future in as_completed(futures):future.result()
            except BaseException:
                self.stopping.set()
                for future in futures:future.cancel()
                raise

    def execute(self):
        try:
            if (self.root/'completion.json').exists():
                # A completed run is audit-only; it must not make further paid calls.
                self.verify()
                for receipt in self.results():
                    folder=self.root/'jobs'/receipt['job']
                    if file_sha(folder/'trajectory/state.json')!=receipt['state_sha256']:
                        raise EvidenceError('Completed trajectory state changed')
                self.stopping.set();self.progress('pilot_completed' if self.pilot else 'completed');return
            self.progress()
            if self.pilot:
                snapshot=self.manifest['initial_snapshot']
                with ThreadPoolExecutor(max_workers=2) as pool:
                    futures=[pool.submit(self.job,self.training[0],'learning',0,snapshot),
                             pool.submit(self.job,self.testing[0],'testing',0,snapshot)]
                    try:
                        for future in as_completed(futures):future.result()
                    except BaseException:
                        self.stopping.set()
                        for future in futures:future.cancel()
                        raise
                receipts=self.results()
                if len(receipts)!=2 or not all(r['gold_valid'] for r in receipts):raise EvidenceError('Pilot needs both valid independent evaluators')
                if self.budget.summary()['incomplete_usage']:raise EvidenceError('Pilot usage reconciliation incomplete')
            else:
                self.test_checkpoint(0)
                for index,row in enumerate(self.training,1):
                    name='D'+str(row['rank']).zfill(2);done=self.root/'jobs'/name/'completion.json'
                    if done.exists():
                        # Revalidate old training against its original snapshot, not the later bank.
                        snapshot=read(done.parent/'trajectory/memory-snapshot.json')
                    else:snapshot=delegated_review.freeze(self.store)
                    self.job(row,'learning',((index-1)//10)*10,snapshot)
                    if index%10==0:self.test_checkpoint(index)
            self.budget.audit_balance()
            immutable(self.root/'completion.json',dict(run_id=self.run_id,pilot=self.pilot,completed_at=now(),
                jobs=len(self.results()),finance=self.budget.summary()))
            self.event('run_completed',pilot=self.pilot,jobs=len(self.results()))
            self.stopping.set();self.progress('pilot_completed' if self.pilot else 'completed')
        except BaseException as error:
            self.stopping.set();self.event('run_stopped',error=repr(error))
            self.progress('paused_by_user' if (self.root/'STOP_REQUESTED').exists() else 'needs_engineering_attention',repr(error));raise
        finally:
            self.stopping.set();self.heartbeat.join(timeout=1);self.writer.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id',required=True);parser.add_argument('--pilot',action='store_true')
    args=parser.parse_args();Run(args.run_id,args.pilot).execute()


if __name__=='__main__':main()
