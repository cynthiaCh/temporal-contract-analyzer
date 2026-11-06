"""Study-local bridge to the unchanged autonomous executor and trusted scorer."""
import hashlib,importlib.util,json,os,re,shutil,subprocess,sys,time
from datetime import datetime
from pathlib import Path
OUT=Path(__file__).resolve().parent;REPO=OUT.parents[1]
sys.path[:0]=[str(OUT),str(REPO)]
os.environ['PYTHONDONTWRITEBYTECODE']='1';os.environ['TCA_BENCH_ROOT']=str(REPO.parent/'temporal-contract-bench-git');os.environ['TCA_PYTHON_BIN']='/home/sribd/anaconda3/bin/python3.11'
from temporal_contract_analyzer import archive
from temporal_contract_analyzer.workbench import Workbench,capture,file_modes,write_files
from temporal_contract_analyzer.case_catalog import case_input,case_root
from temporal_contract_analyzer.case_evaluation import invoke,runtime
from source_retrieval import retrieve
from retriever import load,render
spec=importlib.util.spec_from_file_location('original_autonomous_runtime',REPO/'research/staged-react-experiment-v1-20261105/run.py');rt=importlib.util.module_from_spec(spec);spec.loader.exec_module(rt);rt.OUT=OUT
NODE=rt.NODE;MODEL='gpt-6-sol';SEED=2026110604
TRAIN=['transfer-progress-composition-v4-vanilla','download-polling-restoration-low-cue-react18']
VAL=['document-submit-snapshot-vanilla','feature-flag-readiness-vue3']
TEST=['local-config-readiness-low-cue-vue2','listener-registration-order-vanilla','commit-ack-boundary-vanilla']
BANK=REPO/'research/temporal-contract-question-bank-v1/questions.jsonl'
read=lambda p:json.loads(Path(p).read_text());save=archive.atomic_json;sha=lambda b:hashlib.sha256(b if isinstance(b,bytes) else b.encode()).hexdigest()


def frozen():
    p=read(OUT/'protocol.json');assert sha((OUT/'protocol.json').read_bytes())==(OUT/'protocol.sha256').read_text().strip()
    for path,h in p['frozen_files'].items():assert sha(Path(path).read_bytes())==h,path
    return p


class AutonomousWorkbench(rt.IsolatedWorkbench):
    def command(self,manifest,workspace,answer):
        command=super().command(manifest,workspace,answer);profile=OUT/'.runtime'/manifest['id']
        meter=OUT/'reflection-meter' if manifest.get('reflection') else answer.parent/'model-meter';meter.mkdir(exist_ok=True)
        if not (meter/'config.json').exists():save(meter/'config.json',dict(max_requests=6 if manifest.get('reflection') else None))
        hooks=dict(hooks={event:[dict(hooks=[dict(type='command',command='/usr/bin/python3 /request_meter.py',timeout=10)])] for event in ['PreModelRequest','PostModelRequest']})
        save(profile/'hooks.json',hooks);save(answer.parent/'request-hooks.json',hooks)
        index=command.index('--');command[index:index]=['--ro-bind',str(OUT/'request_meter.py'),'/request_meter.py','--bind',str(meter),'/meter']
        command.insert(command.index('exec')+1,'--dangerously-bypass-hook-trust')
        return command


def wb():return AutonomousWorkbench(OUT/'trials/reports',node=str(NODE))


def full_prompt(case,skill):
    return (OUT/'materials'/case/'common.md').read_text()+'\n<base-execution>\n'+(OUT/'BASE.md').read_text()+'\n</base-execution>\n\n<temporal-contract-skill>\n'+skill+'\n</temporal-contract-skill>\n\n<fixed-ending>\n'+(OUT/'END.md').read_text()+'\n</fixed-ending>\n'


def requests_used():
    path=OUT/'reflection-meter/ledger.json'
    return read(path)['started'] if path.exists() else 0


def usage(events):
    tools=[];commands=[];messages=[];receipts=[];errors=[]
    for n,line in enumerate(events.splitlines(),1):
        e=json.loads(line);i=e.get('item',{});kind=i.get('type')
        if e.get('type')=='turn.completed':receipts.append(e.get('usage',{}))
        if e.get('type') in ['turn.failed','error']:errors.append(dict(line=n,event=e))
        if e.get('type')!='item.completed':continue
        if kind=='agent_message':messages.append(dict(line=n,text=i.get('text','')))
        elif kind=='error':errors.append(dict(line=n,item=i))
        elif kind not in ['reasoning',None]:
            tools.append(dict(line=n,type=kind,item=i))
            if kind=='command_execution':commands.append(dict(line=n,command=i.get('command',''),exit_code=i.get('exit_code'),output=i.get('aggregated_output','')))
    totals={k:sum(r.get(k,0) for r in receipts) for k in ['input_tokens','cached_input_tokens','output_tokens','reasoning_output_tokens']}
    return dict(tools=tools,commands=commands,messages=messages,receipts=receipts,totals=totals,errors=errors)


def normalize(case,raw):
    p=read(OUT/'protocol.json');cp=Path(p['cases'][case]['manifest']);cm=read(cp);effects=read(cp.parent/cm['oracle']['effects'])['variants']['ungranted'];base=read(OUT/'calibration'/case/'unchanged/oracle/stdout.json')
    def checks(x):return {**{'required:'+k:x['observed_effects'][k] is True for k in effects['required']},**{'forbidden:'+k:x['observed_effects'][k] is False for k in effects['forbidden']}}
    def assertions(x):return {s+'/'+a['id']:a.get('passed') is True for s,v in x.get('schedules',{}).items() for a in v.get('assertions',[])}
    c=checks(raw);b=checks(base);a=assertions(raw);ba=assertions(base)
    return dict(whole_pass=raw['verdict']=='PASS',metric=1.0 if raw['verdict']=='PASS' else 0.0,verdict=raw['verdict'],checks=c,assertions=a,required_passed=sum(raw['observed_effects'][k] is True for k in effects['required']),required_total=len(effects['required']),original_check_losses=[k for k,v in b.items() if v and not c.get(k)],original_assertion_failures=[k for k,v in ba.items() if v and k in a and not a[k]],original_assertion_not_emitted=[k for k,v in ba.items() if v and k not in a],forbidden=raw.get('observed_forbidden_effects',[]))


def run_task(case,skill,phase,arm=None,replicate=None):
    p=frozen();assert phase in ['opt','test'];ledger=read(OUT/'task-ledger.json');count=sum(r['phase']==phase for r in ledger);cap=24 if phase=='opt' else 12
    if count>=cap:raise RuntimeError('Hard task execution budget exhausted before launch')
    w=wb();m=w.prepare_case(dict(case_id=case,model=MODEL,effort='low',timeout=600,repeats=1,conditions=['none'],use_local_config=True));assert m['input_files']==p['cases'][case]['input_files']
    folder=w.folder(m['id']);d=folder/'jobs/j-001';prompt=full_prompt(case,skill);(d/'prompt.md').write_text(prompt);common=(OUT/'materials'/case/'common.md').read_text();(d/'report.md').write_text(common)
    m['jobs'][0].update(prompt_sha256=sha(prompt),report_sha256=sha(common),report_characters=len(common));save(folder/'manifest.json',m)
    row=dict(sequence=len(ledger)+1,id=m['id'],phase=phase,split=p['cases'][case]['split'],case=case,path=str(folder),skill_sha256=sha(skill),prompt_sha256=sha(prompt),common_sha256=sha(common),arm=arm,replicate=replicate,at=archive.now());ledger.append(row);save(OUT/'task-ledger.json',ledger);start=time.monotonic()
    try:
        w.start(m['id']);w.thread.join();m=w.read(m['id']);job=m['jobs'][0];ep=w.latest_evaluation(m['id']);evaluation=read(ep) if ep else {};entry=evaluation.get('jobs',{}).get('j-001',{})
        category='execution-failure' if job['status']!='completed' else 'behavior' if evaluation.get('calibration_verdict')=='PASS' and entry.get('status') in ['passed','failed'] else 'validation-unverified'
        events=(d/'events.jsonl').read_text();tr=usage(events);changes=read(d/'changes.json') if (d/'changes.json').exists() else dict(files=[])
        if 'failed to spawn code-mode host' in events:category='execution-tool-unavailable'
        meter=read(d/'model-meter/ledger.json') if (d/'model-meter/ledger.json').exists() else None
        row.update(category=category,status=job['status'],evaluation=str(ep) if ep else None,usage=tr['totals'],started_at=job.get('started_at'),completed_at=job.get('completed_at'),score=None,metric=0.0,changed_paths=[f['path'] for f in changes.get('files',[])],tool_calls=len(tr['tools']),shell_failures=[dict(line=c['line'],exit_code=c['exit_code'],command=c['command']) for c in tr['commands'] if c['exit_code'] not in [0,None]],model_requests=meter['started'] if meter else None,model_request_statuses=[e['event'].get('status') for e in meter['events'] if e['event'].get('hook_event_name')=='PostModelRequest'] if meter else [])
        if category=='behavior':
            path=folder/entry['result_path'];row.update(raw_oracle=str(path),score=normalize(case,read(path)));row['metric']=row['score']['metric']
        (d/'patch.diff').write_text('\n'.join(f.get('diff','') for f in changes.get('files',[])));save(d/'trajectory-index.json',tr)
    except Exception as e:row.update(category='execution-error',error=repr(e),score=None,metric=0.0)
    finally:shutil.rmtree(OUT/'.runtime'/m['id'],ignore_errors=True)
    row['including_score_seconds']=time.monotonic()-start;rows=read(OUT/'task-results.json');rows.append(row);save(OUT/'task-results.json',rows)
    print(json.dumps(dict(event='task_done',sequence=row['sequence'],case=case,split=row['split'],metric=row['metric'],category=row['category'])),flush=True)
    return row


def skill_check(candidate):
    errors=[];text=candidate.get('temporal_skill','') if isinstance(candidate,dict) else ''
    if not isinstance(candidate,dict) or set(candidate)!= {'temporal_skill'}:errors.append('candidate must contain exactly the single optimized skill')
    if not isinstance(text,str) or not text.strip() or len(text)>6000:errors.append('invalid text/length')
    if re.search(r'```|\b[\w.-]+\.(?:js|jsx|vue|cjs|mjs|md|json)\b|/workspace|src/|</temporal-contract-skill>|criterion-\d+|train-eval-\d+',text,re.I):errors.append('code/file/path/feedback marker in skill')
    if re.search(r'(?i)(?:ignore|replace|override|bypass) (?:the )?(?:original task|fixed ending|tool permissions|scor(?:e|ing))',text):errors.append('attempt to override fixed perimeter')
    bans=read(OUT/'skill-banned-identifiers.json')
    if any(token.lower() in text.lower() for token in bans):errors.append('case/program/private scorer identifier in skill')
    return dict(valid=not errors,errors=errors,characters=len(text),sha256=sha(text),scope='mechanical boundary; researcher semantic boundary review required for generated skills')


def candidate_record(candidate):
    text=candidate.get('temporal_skill','') if isinstance(candidate,dict) else '';key=sha(json.dumps(candidate,sort_keys=True));folder=OUT/'candidates'/key;folder.mkdir(parents=True,exist_ok=True)
    if not (folder/'candidate.json').exists():
        save(folder/'candidate.json',candidate);(folder/'skill.md').write_text(text);save(folder/'validation.json',skill_check(candidate))
    return key,folder


def ensure_review(candidate):
    key,folder=candidate_record(candidate);check=read(folder/'validation.json')
    if not check['valid']:return False,check
    if candidate['temporal_skill']==(OUT/'K0.md').read_text():return True,check
    review=folder/'review.json'
    if not review.exists():
        print('PENDING_BOUNDARY_REVIEW '+key,flush=True);start=time.monotonic()
        while not review.exists():
            if time.monotonic()-start>1200:raise RuntimeError('Boundary review not supplied; no task execution allowed')
            time.sleep(.5)
    decision=read(review);assert decision['skill_sha256']==sha(candidate['temporal_skill'])
    return bool(decision['allow_execution']),check


def reflection_lm(message):
    frozen()
    if requests_used()>=6:raise RuntimeError('Reflection request cap reached; no additional CLI call')
    calls=read(OUT/'reflection-calls.json');index=len(calls)+1;folder=OUT/'reflections'/('call-'+str(index).zfill(2));work=folder/'workspace';work.mkdir(parents=True)
    text=message if isinstance(message,str) else json.dumps(message,ensure_ascii=False)
    (folder/'official-prompt.json').write_text(json.dumps(message,ensure_ascii=False,indent=2));(folder/'prompt.md').write_text(text)
    w=wb();manifest=dict(id='reflection-'+str(index),mode='read-only',local_codex=True,model_override=MODEL,effort='low',reflection=True);command=w.command(manifest,work,folder/'answer.md')
    before=requests_used();record=dict(call=index,at=archive.now(),model=MODEL,effort='low',native_requests_before=before,path=str(folder),command=command);calls.append(record);save(OUT/'reflection-calls.json',calls);start=time.monotonic();status='completed'
    try:
        with (folder/'prompt.md').open('rb') as inp,(folder/'events.jsonl').open('wb') as out,(folder/'stderr.log').open('wb') as err:
            process=subprocess.Popen(command,cwd=work,stdin=inp,stdout=out,stderr=err,start_new_session=True)
            try:process.wait(timeout=600)
            except subprocess.TimeoutExpired:status='timed_out';Workbench.terminate(process)
        tr=usage((folder/'events.jsonl').read_text());answer=folder/'cli-output/answer.md';raw=answer.read_text() if answer.exists() else '';(folder/'raw-answer.txt').write_text(raw)
        record.update(status=status,exit_code=process.returncode,usage=tr['totals'],tool_calls=len(tr['tools']),native_requests_after=requests_used(),seconds=time.monotonic()-start,completed_at=archive.now());save(folder/'result.json',record)
        calls=read(OUT/'reflection-calls.json');calls[-1]=record;save(OUT/'reflection-calls.json',calls)
        if process.returncode!=0 or not tr['receipts'] or not raw.strip():raise RuntimeError('Reflection CLI failed; no model/account substitution')
        return raw
    finally:shutil.rmtree(OUT/'.runtime'/manifest['id'],ignore_errors=True)
