"""Single-session adaptation of frozen research runner, with runner-owned archival.

No scheduler, implicit model execution, retry, or implicit score invocation.
Native execution requires an explicit new-protocol opt-in from its caller.
"""
import importlib.util,json,os,re,shutil,signal,subprocess,sys,tempfile,time
from pathlib import Path
from archive import Archive,inventory,digest,save,sha
from guard_server import GuardServer

O=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('archive_native',O/'native_backend.py')
backend=importlib.util.module_from_spec(spec);spec.loader.exec_module(backend);backend.OUT=O
ROLE={'extract':('gpt-6-sol','low',12,'extraction'),'repair':('gpt-5.6-terra','low',24,'maintenance'),'reflect':('gpt-5.6-terra','medium',12,'reflection')}

def command(call,folder,phase,case,*,runtime,socket_dir,copy_auth=True):
    """Original autonomous Codex CLI and role flags, no host archive bind mounts."""
    cmd=backend.command(call,folder,'reflection' if phase=='reflect' else 'extraction',copy_auth=copy_auth,runtime=runtime,socket_dir=socket_dir)
    if phase in ['repair','reflect']:
        i=cmd.index(str(folder/'workspace'));assert cmd[i-1]=='--ro-bind';cmd[i-1]='--bind'
        cmd[cmd.index('--sandbox')+1]='danger-full-access';cmd[cmd.index('-m')+1]='gpt-5.6-terra'
        cmd=[s.replace('model_reasoning_effort="low"','model_reasoning_effort="'+ROLE[phase][1]+'"') for s in cmd]
    i=cmd.index('--chdir');cmd[i:i]=['--ro-bind',case['node'],'/runtime/node']
    return cmd

def source_proof(events,original):
    # Same body-line evidence as historical runner, with both source suffixes.
    result=[]
    for n,e in enumerate(events,1):
        item=e.get('item',{})
        if e.get('type')!='item.completed' or item.get('type')!='command_execution' or item.get('exit_code')!=0:continue
        output=item.get('aggregated_output','');normalized={re.sub(r'^\s*\d+\s+','',x).strip() for x in output.splitlines()}
        for f in original.rglob('*'):
            if f.suffix not in ['.js','.py'] or f.is_symlink() or not f.is_file():continue
            matched=sorted({x.strip() for x in f.read_text().splitlines() if len(x.strip())>=20}&normalized)
            if len(matched)>=3:result.append({'event_line':n,'source':str(f.relative_to(original)),'source_sha256':sha(f),'matched_lines':matched,'tool_output_sha256':backend.sha(output)})
    return result

def verify(files):
    for path,expected in files.items():
        if sha(path)!=expected:raise ValueError('frozen source/configuration drift: '+str(path))

def stop_process(proc):
    if proc is not None and proc.poll() is None:
        try:os.killpg(proc.pid,signal.SIGKILL)
        except ProcessLookupError:pass
    if proc is not None:proc.wait()

def session(slot,prompt,*,case,candidate,task,config,run_dir,command_factory=None,score_fn=None,allow_model_execution=False,diff_runner=subprocess.run):
    """Actual lifecycle; fake CLI can exercise it offline without model/scorer calls.

    score_fn is an explicit trusted evaluation callback. It receives ONLY the
    frozen final candidate and score destination after all actor processes stop.
    """
    phase=slot['phase'];model,effort,cap,mode=ROLE[phase]
    fixture=command_factory is not None
    if not fixture and not allow_model_execution:raise RuntimeError('model execution disabled; this change is offline-only')
    if not fixture:
        if not config.get('frozen_files'):raise ValueError('a separate frozen protocol is required for native execution')
        verify(config['frozen_files'])
    seconds=config.get('seconds_per_session',600);stdout_limit=config.get('stdout_bytes',16777216)
    if not 0<seconds<=600 or not 0<stdout_limit<=16777216:raise ValueError('cannot increase original resource limits')
    frozen={**config,'slot':slot,'model':model,'effort':effort,'requests_per_session':cap,'seconds_per_session':seconds,'stdout_bytes':stdout_limit,'offline_fixture':fixture,'archiver':'runner-owned-v1','input_archive_policy':'snapshots/logs outside model workspace; no model archival duty'}
    a=Archive(run_dir).prepare(candidate,task,prompt,frozen)
    if 'candidate_files' in case and backend.hashes(a.original)!=case['candidate_files']:raise ValueError('candidate version mismatch before launch')
    if case.get('task_sha256') and sha(a.root/'input/task.md')!=case['task_sha256']:raise ValueError('task version mismatch before launch')
    runtime=Path(tempfile.mkdtemp(prefix='research-archive-runtime-'));proc=None
    outcome={**slot,'status':'LAUNCHED','started_at':time.time(),'failure_class':None,'stop_reason':None,'offline_fixture':fixture}
    events=[];answer=None
    try:
        with GuardServer(runtime/'hook-control',a.root/'meter',slot['slot'],cap,mode) as guard:
            try:
                cmd=command_factory(a,runtime,guard) if fixture else command(slot['slot'],a.run_dir,phase,case,runtime=runtime,socket_dir=guard.directory)
                save(a.root/'command.json',cmd)
                with (a.root/'input/actual-prompt.md').open('rb') as inp,(a.root/'events.jsonl').open('wb') as out,(a.root/'stderr.log').open('wb') as err:
                    proc=subprocess.Popen(cmd,stdin=inp,stdout=out,stderr=err,cwd=a.workspace,start_new_session=True)
                    while proc.poll() is None:
                        if time.time()-outcome['started_at']>=seconds:
                            outcome.update(resource_limit='timeout',failure_class='model_resource_limit',stop_reason='timeout');stop_process(proc);break
                        if (a.root/'events.jsonl').stat().st_size>stdout_limit:
                            outcome.update(resource_limit='stdout_archive_limit',failure_class='model_resource_limit',stop_reason='stdout_archive_limit');stop_process(proc);break
                        try:proc.wait(timeout=.05)
                        except subprocess.TimeoutExpired:pass
                    proc.wait()
                outcome['exit_code']=proc.returncode
                if proc.returncode!=0 and not outcome['failure_class']:outcome.update(failure_class='model_or_cli_abnormal_exit',stop_reason='nonzero_exit')
            except Exception as exc:
                outcome.update(failure_class=outcome['failure_class'] or 'runner_exception',stop_reason=outcome['stop_reason'] or 'runner_exception',exception=repr(exc))
            finally:
                stop_process(proc)
    except Exception as exc:
        outcome.update(failure_class=outcome['failure_class'] or 'runner_exception',stop_reason=outcome['stop_reason'] or 'runner_exception',exception=repr(exc))
    finally:
        stop_process(proc)
        if 'guard' in locals():save(a.root/'guard-collector-status.json',{'errors':guard.errors})
        outcome['seconds']=time.time()-outcome['started_at']
        if proc is not None:outcome['exit_code']=proc.returncode
        outcome['status']='STOPPED'
        # Original failure cause is saved before archival; archival errors stay separate.
        save(a.root/'model-outcome.json',outcome)
        profile=runtime/'.runtime'/slot['slot']
        try:
            if (profile/'config.toml').exists():save(a.root/'configuration-after.json',{'profile_sha256':sha(profile/'config.toml'),'global_config':backend.global_snapshot()})
        except Exception as exc:a.error('configuration_after',exc)
        try:shutil.rmtree(runtime)  # runner-owned temporary profile only; never candidate files
        except Exception as exc:a.error('runtime_cleanup',exc)
        archive_state=a.finalize(model_stopped=proc is None or proc.poll() is not None,diff_runner=diff_runner)
    # Reuse original role/accounting and resource-result interpretation.
    malformed=[]
    try:
        for n,line in enumerate((a.root/'events.jsonl').read_text().splitlines(),1):
            try:events.append(json.loads(line))
            except ValueError:malformed.append(n)
    except OSError:pass
    raw=(a.root/'raw-answer.txt').read_text() if (a.root/'raw-answer.txt').exists() else ''
    try:ans=json.loads(raw);format_ok=set(ans)=={'report'} and isinstance(ans['report'],str) and len(ans['report'])<=6000
    except (ValueError,TypeError):ans={};format_ok=False
    try:ledger=json.loads((a.root/'meter/ledger.json').read_text())
    except (OSError,ValueError):ledger={}
    native=ledger.get('sessions',{}).get(slot['slot'],{});budget_hit=bool(outcome.get('resource_limit')) or bool(native.get('blocked_requests') and native.get('started')==cap)
    if budget_hit and outcome['failure_class'] in [None,'model_or_cli_abnormal_exit']:outcome['failure_class']='model_resource_limit'
    model_events=[x['event'] for x in ledger.get('events',[]) if x['event'].get('hook_event_name') in ['PreModelRequest','PostModelRequest']]
    posts=[e for e in model_events if e['hook_event_name']=='PostModelRequest'];pending=native.get('started',0)-native.get('completed',0)
    accounted=bool(native.get('started')) and (pending==0 or budget_hit and pending==1) and len(posts)==native.get('completed')
    completed=outcome.get('exit_code')==0 and sum(e.get('type')=='turn.completed' for e in events)==1
    infra_ok=accounted and bool(model_events) and all(e.get('model')==model for e in model_events) and not native.get('blocked_tools') and all(e.get('status')=='completed' for e in posts) and not any(e.get('type')=='turn.failed' for e in events) and not malformed and (completed or budget_hit)
    rec={**outcome,'native':native,'output_format_valid':format_ok,'infrastructure_valid':infra_ok,'status':'VALID' if infra_ok and (completed or budget_hit) else 'INVALID','archive_status':archive_state,'archive_failure_requires_stop':archive_state['status']!='OK','archive_stop_reason':'archive_error' if archive_state['status']!='OK' else None,'scoring_status':'NOT_REQUESTED','source_body_proofs':source_proof(events,a.original),'final_candidate':str(a.final) if a.final.exists() else None,'patch_delivered':archive_state['steps'].get('diff')=='CHANGED'}
    if phase=='repair' and archive_state['status']=='OK' and score_fn is not None:
        before=inventory(a.final);save(a.root/'score-before-manifest.json',before);score_dir=a.root/'score';score_dir.mkdir()
        try:
            rec['score_result']=score_fn(a.final,score_dir);rec['scoring_status']='COLLECTED'
            if inventory(a.final)!=before:raise ValueError('external scorer changed frozen final candidate')
        except Exception as exc:rec.update(scoring_status='ERROR',scoring_error=repr(exc))
        after=inventory(a.final);save(a.root/'score-after-manifest.json',after)
        rec['scored_candidate_sha256']=digest(before);rec['scored_candidate_unchanged']=before==after
    elif score_fn is not None:rec['scoring_status']='BLOCKED_ARCHIVE_ERROR_OR_NON_REPAIR'
    if phase=='extract':
        from toolflow import validate_analysis
        full=ans.get('report','');(a.root/'preanalysis-raw.txt').write_text(full)
        try:
            analysis=json.loads(full)
            sources={str(f.relative_to(a.original)):f.read_text() for f in a.original.rglob('*') if f.is_file() and f.suffix in ['.js','.py','.md']}
            error=validate_analysis(analysis,sources)
            if error:raise ValueError(error)
            if not rec['source_body_proofs']:raise ValueError('source body not read')
            if not infra_ok:raise ValueError('invalid preanalysis infrastructure')
            if not format_ok:raise ValueError('invalid report envelope')
            save(a.root/'analysis.json',analysis)
            (a.root/'contract.md').write_text(analysis['contract'])
            rec['contract_sha256']=backend.sha(analysis['contract']);rec['preanalysis_valid']=True
        except (ValueError,TypeError,KeyError,AttributeError) as exc:
            rec.update(preanalysis_valid=False,preanalysis_error=repr(exc))
    elif phase=='reflect':(a.root/'experience.md').write_text(ans.get('report',''))
    save(a.root/'model-outcome.json',outcome);save(a.root/'receipt.json',rec);a.write_manifest();return rec
