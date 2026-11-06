"""One frozen skill evolution round with bounded synchronous native lifecycle hooks."""
import argparse, hashlib, importlib.util, json, os, random, re, shutil, subprocess, sys, threading, time
from pathlib import Path
from difflib import unified_diff
OUT=Path(__file__).resolve().parent;REPO=OUT.parents[1];PRIOR=REPO/'research/prompt-evolution-experiment-v1-20261106'
sys.path[:0]=[str(OUT),str(REPO)]
os.environ['PYTHONDONTWRITEBYTECODE']='1';os.environ['TCA_BENCH_ROOT']=str(REPO.parent/'temporal-contract-bench-git');os.environ['TCA_PYTHON_BIN']='/home/sribd/anaconda3/bin/python3.11'
from temporal_contract_analyzer import archive
from temporal_contract_analyzer.workbench import Workbench,capture,file_modes,write_files
from temporal_contract_analyzer.case_catalog import case_input,case_root
from temporal_contract_analyzer.case_evaluation import runtime,invoke
from source_retrieval import retrieve
from retriever import load,render
spec=importlib.util.spec_from_file_location('previous_runtime',REPO/'research/staged-react-experiment-v1-20261105/run.py');rt=importlib.util.module_from_spec(spec);spec.loader.exec_module(rt);rt.OUT=OUT
NODE=rt.NODE;MODEL='gpt-6-sol';EFFORT='low';SEED=2026110603
DEV=['transfer-progress-composition-v4-vanilla','download-polling-restoration-low-cue-react18']
HOLD=['document-submit-snapshot-vanilla','feature-flag-readiness-vue3'];BANK=REPO/'research/temporal-contract-question-bank-v1/questions.jsonl'
read=lambda p:json.loads(Path(p).read_text());sha=lambda b:hashlib.sha256(b if isinstance(b,bytes) else b.encode()).hexdigest();save=archive.atomic_json
HOOKS=['SessionStart','PreToolUse','PostToolUse','Stop','PreModelRequest','PostModelRequest']


class ControlledWorkbench(rt.IsolatedWorkbench):
    def command(self,manifest,workspace,answer):
        cmd=super().command(manifest,workspace,answer)
        profile=OUT/'.runtime'/manifest['id'];control=answer.parent/'control';control.mkdir(exist_ok=True)
        active=bool(manifest.get('react_control',False))
        files,_=capture(workspace)
        save(control/'config.json',dict(active=active,initial_files={k:sha(v) for k,v in files.items()}))
        hooks={'description':'Reviewed study-local bounded controller; same executable for passive and active conditions','hooks':{name:[{'hooks':[dict(type='command',command='/usr/bin/python3 /controller.py',timeout=10)]}] for name in HOOKS}}
        save(profile/'hooks.json',hooks);save(answer.parent/'hooks.definition.json',hooks)
        i=cmd.index('--');cmd[i:i]=['--ro-bind',str(OUT/'controller.py'),'/controller.py','--bind',str(control),'/control']
        i=cmd.index('exec');cmd[i+1:i+1]=['--dangerously-bypass-hook-trust']
        return cmd


def wb():return ControlledWorkbench(OUT/'trials/reports',node=str(NODE))


def frozen():
    p=read(OUT/'protocol.json');assert sha((OUT/'protocol.json').read_bytes())==(OUT/'protocol.sha256').read_text().strip()
    for path,h in p['frozen_files'].items():assert sha(Path(path).read_bytes())==h,path
    return p


def prompt(case,skill,active):
    return (OUT/'materials'/case/'common.md').read_text()+'\n<base-execution>\n'+(OUT/'BASE.md').read_text()+'\n</base-execution>\n\n<temporal-contract-skill>\n'+skill+'\n</temporal-contract-skill>\n'+('\n<external-control>\n'+(OUT/'CONTROL.md').read_text()+'\n</external-control>\n' if active else '')


def prepare():
    assert not (OUT/'protocol.json').exists();meta={};rng=random.Random(SEED)
    initial=dict(head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),status=subprocess.check_output(['git','status','--short'],cwd=REPO,text=True),diff=subprocess.check_output(['git','diff'],cwd=REPO,text=True));save(OUT/'initial-git.json',initial)
    shutil.copyfile(BANK,OUT/'questions.snapshot.jsonl')
    for c in DEV+HOLD:
        ci=case_input(c);cp=case_root(ci['case_record'])/ci['case_record']['manifest'];cm=read(cp);files,_=capture(Path(ci['candidate']));modes=file_modes(Path(ci['candidate']),files);folder=OUT/'materials'/c
        write_files(folder/'input',files,modes);packet,source=retrieve(ci['task'],files);questions=render([q['id'] for q in load(BANK)],BANK)
        common='Work only on the candidate-visible files in this workspace. Do not inspect sibling experiment jobs, original repositories or report stores.\n\n'+ci['task'].strip()+'\n\n<candidate-assistance>\n'+source+'\n'+questions+'\n</candidate-assistance>\n'
        for n,t in [('task.md',ci['task']),('source.md',source),('questions.md',questions),('common.md',common)]: (folder/n).write_text(t)
        save(folder/'source-retrieval.json',packet)
        meta[c]=dict(split='development' if c in DEV else 'exploratory-heldout',case_record=ci['case_record'],manifest=str(cp),manifest_sha256=sha(cp.read_bytes()),independent_unit_id=cm.get('independent_unit_id'),source_cluster=str(cp.parent.relative_to(REPO.parent/'temporal-contract-bench-git')).split('/arms/')[0],provenance=cm.get('provenance'),validation=cm.get('validation'),exposure='research exposed; not independent generalization',input_files={k:sha(v) for k,v in files.items()},file_modes=modes,common_sha256=sha(common),oracle_files={str(f):sha(f.read_bytes()) for f in (cp.parent/'oracle').rglob('*') if f.is_file()})
        for arm in ['A','B']:(folder/(arm+'-K0.prompt.md')).write_text(prompt(c,(OUT/'K0.md').read_text(),arm=='B'))
    assert not {meta[c]['independent_unit_id'] for c in DEV}&{meta[c]['independent_unit_id'] for c in HOLD}
    assert not {meta[c]['source_cluster'] for c in DEV}&{meta[c]['source_cluster'] for c in HOLD}
    devorder={}
    for k in ['K0','K1']:
        order=list(DEV);rng.shuffle(order);devorder[k]=order
    first={}
    for c in HOLD:
        arms=list('ABC');rng.shuffle(arms);first[c]=arms
    schedule=[]
    for rep in [1,2]:
        cases=list(HOLD);rng.shuffle(cases)
        for c in cases:
            for arm in (first[c] if rep==1 else first[c][::-1]):schedule.append(dict(case=c,arm=arm,replicate=rep))
    # Entire preexisting tracked repository and all four preexisting untracked studies are protected.
    protected=[REPO/s for s in subprocess.check_output(['git','ls-files'],cwd=REPO,text=True).splitlines() if (REPO/s).is_file()]
    for root in [REPO/'research'/n for n in ['staged-react-experiment-v1-20261105','question-selection-experiment-v1-20261105','prompt-evolution-experiment-v1-20261106','failure-mechanism-diagnosis-v1-20261106']]+[Path(m['manifest']).parent for m in meta.values()]:protected.extend(f for f in root.rglob('*') if f.is_file() and '__pycache__' not in f.parts)
    protected += [f for f in (OUT/'materials').rglob('*') if f.is_file()]+list(OUT.glob('*.py'))+list(OUT.glob('*.md'))+[OUT/'initial-git.json',OUT/'questions.snapshot.jsonl']
    p=dict(schema='react-skill-evolution-v1',created_at=archive.now(),model=MODEL,effort=EFFORT,timeout=600,maximum_formal_sessions=18,development_planned=5,development_reserve=1,reserve_default_unused=True,holdout_maximum=12,seed=SEED,model_sampling_seed=None,dev_order=devorder,holdout_schedule=schedule,cases=meta,independent_generalization_cases=0,ast_delivery=False,output_limit='inherited CLI no added output-token cap',hooks=HOOKS,selection='strict whole-pass increase, no baseline/incumbent passed check/assertion loss, no forbidden or unimplemented maintenance; ties retain K0',frozen_files={str(f):sha(f.read_bytes()) for f in sorted(set(protected))})
    save(OUT/'protocol.json',p);(OUT/'protocol.sha256').write_text(sha((OUT/'protocol.json').read_bytes())+'\n')
    save(OUT/'versions.json',[dict(version='K0',parent=None,sha256=sha((OUT/'K0.md').read_bytes()),source='visible contract questions and narrow diagnostic scope; no case-specific patch',at=archive.now())]);print('FROZEN',flush=True)


def register(kind,label):
    rows=read(OUT/'invocations.json');assert len(rows)<17,'reserve never automatic';assert label not in [r['label'] for r in rows]
    rows.append(dict(sequence=len(rows)+1,kind=kind,label=label,at=archive.now()));save(OUT/'invocations.json',rows)


def normalize(case,raw):
    p=read(OUT/'protocol.json');cp=Path(p['cases'][case]['manifest']);cm=read(cp);effects=read(cp.parent/cm['oracle']['effects'])['variants']['ungranted'];base=read(OUT/'calibration'/case/'unchanged/oracle/stdout.json')
    def checks(r):return {**{'required:'+k:r['observed_effects'][k] is True for k in effects['required']},**{'forbidden:'+k:r['observed_effects'][k] is False for k in effects['forbidden']}}
    def assertions(r):return {s+'/'+a['id']:a.get('passed') is True for s,x in r.get('schedules',{}).items() for a in x.get('assertions',[])}
    x=checks(raw);b=checks(base);a=assertions(raw);ba=assertions(base)
    return dict(whole_pass=raw['verdict']=='PASS',verdict=raw['verdict'],checks=x,assertions=a,required_passed=sum(raw['observed_effects'][k] is True for k in effects['required']),required_total=len(effects['required']),original_check_losses=[k for k,v in b.items() if v and not x.get(k)],original_assertion_losses=[k for k,v in ba.items() if v and not a.get(k)],forbidden=raw.get('observed_forbidden_effects',[]))


def repair(case,skill,split,arm='B',rep=1):
    p=frozen();w=wb();m=w.prepare_case(dict(case_id=case,model=MODEL,effort=EFFORT,timeout=600,repeats=1,conditions=['none'],use_local_config=True));assert m['input_files']==p['cases'][case]['input_files']
    folder=w.folder(m['id']);d=folder/'jobs/j-001';text=prompt(case,(OUT/(skill+'.md')).read_text(),arm!='A');(d/'prompt.md').write_text(text);common=(OUT/'materials'/case/'common.md').read_text();(d/'report.md').write_text(common)
    m['react_control']=arm!='A';m['jobs'][0].update(prompt_sha256=sha(text),report_sha256=sha(common),report_characters=len(common));save(folder/'manifest.json',m)
    label=split+'/'+case+'/'+arm+'/'+skill+'/'+str(rep);register('repair',label);r=dict(label=label,id=m['id'],path=str(folder),case=case,split=split,arm=arm,skill=skill,skill_sha256=sha((OUT/(skill+'.md')).read_bytes()),replicate=rep,input_files=m['input_files'],common_sha256=sha(common),prompt_sha256=sha(text),active=arm!='A');start=time.monotonic()
    try:
        w.start(m['id']);w.thread.join();m=w.read(m['id']);j=m['jobs'][0];ep=w.latest_evaluation(m['id']);ev=read(ep) if ep else {};e=ev.get('jobs',{}).get('j-001',{})
        category='execution-failure' if j['status']!='completed' else 'behavior' if ev.get('calibration_verdict')=='PASS' and e.get('status') in ['passed','failed'] else 'validation-unverified'
        events=(d/'events.jsonl').read_text()
        if 'failed to spawn code-mode host' in events:category='execution-tool-unavailable'
        hookpath=d/'control/hook-events.jsonl';hookevents=[json.loads(l) for l in hookpath.read_text().splitlines()] if hookpath.exists() else []
        if not any(h['event'].get('hook_event_name')=='PostModelRequest' for h in hookevents):r['hook_runtime_unverified']=True
        if arm!='A' and not any(h['event'].get('hook_event_name')=='PostToolUse' for h in hookevents):r['controller_runtime_unverified']=True
        r.update(category=category,process=j['status'],evaluation=str(ep) if ep else None,usage=j.get('usage'),started_at=j.get('started_at'),completed_at=j.get('completed_at'),changed_files=j.get('changed_files'),score=None)
        if category=='behavior':
            raw_path=folder/e['result_path'];r.update(raw_oracle=str(raw_path),score=normalize(case,read(raw_path)))
    except Exception as err:r.update(category='execution-error',error=repr(err),score=None)
    finally:shutil.rmtree(OUT/'.runtime'/m['id'],ignore_errors=True)
    r['including_score_seconds']=time.monotonic()-start;rows=read(OUT/'results.json');rows.append(r);save(OUT/'results.json',rows)
    print(json.dumps(dict(event='repair_done',label=label,category=r['category'],verdict=r['score']['verdict'] if r['score'] else None)),flush=True);return r


def feedback_packet():
    target=OUT/'evolution/workspace';target.mkdir(parents=True);shutil.copyfile(OUT/'K0.md',target/'K0.md');records=[];mapping={}
    rows=[r for r in read(OUT/'results.json') if r['split']=='development' and r['skill']=='K0'];assert len(rows)==2
    for index,r in enumerate(rows,1):
        assert r['case'] in DEV;src=OUT/'materials'/r['case'];dest=target/'development-source'/('task-'+str(index));shutil.copytree(src/'input',dest);shutil.copyfile(src/'task.md',dest/'TASK.md')
        d=Path(r['path'])/'jobs/j-001';commands=[];tools=[]
        for n,l in enumerate((d/'events.jsonl').read_text().splitlines(),1):
            e=json.loads(l);i=e.get('item',{})
            if e.get('type')!='item.completed':continue
            if i.get('type')=='command_execution':
                out=i.get('aggregated_output','');commands.append(dict(event_line=n,command=i.get('command'),exit_code=i.get('exit_code'),output=out[:8000],truncated=len(out)>8000))
            elif i.get('type')=='file_change':tools.append(dict(event_line=n,changes=i.get('changes'),status=i.get('status')))
        scored=r['score'];keys=sorted(scored['checks']);anonymous={f'criterion-{k+1:02d}':scored['checks'][name] for k,name in enumerate(keys)};mapping['task-'+str(index)]={f'criterion-{k+1:02d}':name for k,name in enumerate(keys)}
        hooks=[json.loads(l) for l in (d/'control/hook-events.jsonl').read_text().splitlines()] if (d/'control/hook-events.jsonl').exists() else []
        observations=[{k:h.get(k) for k in ['controller_state_before','controller_state_after','decision','reason','changed_paths','exit_code','citations']} for h in hooks if h['event'].get('hook_event_name') in ['PostToolUse','Stop','PreToolUse']]
        records.append(dict(task='task-'+str(index),actual_prompt=(d/'prompt.md').read_text(),commands=commands,file_changes=tools,patch=read(d/'changes.json'),controller_observations=observations,feedback=dict(whole_pass=scored['whole_pass'],criteria=anonymous,original_check_loss_count=len(scored['original_check_losses']),original_assertion_loss_count=len(scored['original_assertion_losses']),forbidden_count=len(scored['forbidden']))))
    save(target/'development-feedback.json',dict(boundary='only current development runs and visible source; no oracle IDs/assertions/reference/heldout or history',rows=records));save(OUT/'feedback-private-mapping.json',mapping)
    save(OUT/'evolution/packet-hashes.json',{str(f.relative_to(target)):sha(f.read_bytes()) for f in target.rglob('*') if f.is_file()})
    return target


def candidate_check(obj):
    errors=[]
    if not isinstance(obj,dict):return dict(valid=False,errors=['proposal not object'])
    text=obj.get('skill','');changes=obj.get('changes',[])
    if not isinstance(text,str) or not text.strip() or len(text)>5000:errors.append('skill empty/non-text/over character cap')
    if obj.get('parent')!='K0':errors.append('invalid parent')
    if not isinstance(changes,list) or not changes:errors.append('missing concrete changes')
    else:
        for change in changes:
            if not isinstance(change,dict) or not all(change.get(k) for k in ['failure_evidence','step_changed','observable_action_change','preserved_behavior_risk']):errors.append('incomplete change metadata')
    for k in range(1,7):
        if 'S'+str(k) not in text:errors.append('missing S'+str(k))
    if '```' in text or re.search(r'\b[\w.-]+\.(?:js|jsx|vue|json|cjs|mjs|md)\b|/workspace|/stage|src/|criterion-\d+',text,re.I):errors.append('code/path/file/feedback identifier')
    bans=DEV+HOLD+['usePreparation','watchTransferProgress','progressAttemptId','checkPreparation','getPageConfig','PersonnelEditor','SchemaForm','initialPacket','makeQueueRecord','enqueueTransfer','recordProgress','showProgress','download-waits-after-pending','start-switch-admission','retry-preserved','ungranted']
    p=read(OUT/'protocol.json')
    for c in DEV+HOLD:
        cp=Path(p['cases'][c]['manifest']);cm=read(cp);eff=read(cp.parent/cm['oracle']['effects'])['variants']['ungranted'];bans += eff['required']+eff['forbidden']
    for token in set(bans):
        if token.lower() in text.lower():errors.append('task/program/check identifier: '+token)
    return dict(valid=not errors,errors=errors,characters=len(text),sha256=sha(text),mechanical_only=True,semantic_leakage_review_required=True)


def evolve():
    frozen();work=feedback_packet();d=OUT/'evolution';instruction=(OUT/'EVOLVER.md').read_text();(d/'prompt.md').write_text(instruction)
    w=wb();m=dict(id='skill-evolver-K1',mode='workspace-write',local_codex=True,model_override=MODEL,effort=EFFORT,react_control=False)
    command=w.command(m,work,d/'answer.md');register('evolver','evolve/K0-K1');start=archive.now();status='completed'
    with (d/'prompt.md').open('rb') as inp,(d/'events.jsonl').open('wb') as out,(d/'stderr.log').open('wb') as err:
        process=subprocess.Popen(command,cwd=work,stdin=inp,stdout=out,stderr=err,start_new_session=True)
        try:process.wait(timeout=600)
        except subprocess.TimeoutExpired:status='timed_out';Workbench.terminate(process)
    usage=None;completed=False
    for l in (d/'events.jsonl').read_text().splitlines():
        e=json.loads(l)
        if e.get('type')=='turn.completed':completed=True;usage=e.get('usage')
    answer=d/'cli-output/answer.md';text=answer.read_text() if answer.exists() else '';(d/'raw-answer.txt').write_text(text)
    try:obj=json.loads(text)
    except ValueError:obj=None
    validation=candidate_check(obj);expected=read(d/'packet-hashes.json');mutated=[f for f,h in expected.items() if not (work/f).is_file() or sha((work/f).read_bytes())!=h]
    if mutated or status!='completed' or process.returncode!=0 or not completed:validation.update(valid=False,packet_mutations=mutated,process_status=status)
    if isinstance(obj,dict) and isinstance(obj.get('skill'),str):
        (OUT/'K1.md').write_text(obj['skill']);save(OUT/'K1.proposal.json',obj);(OUT/'K1.diff').write_text(''.join(unified_diff((OUT/'K0.md').read_text().splitlines(True),obj['skill'].splitlines(True),fromfile='K0',tofile='K1')))
        versions=read(OUT/'versions.json');versions.append(dict(version='K1',parent='K0',parent_sha256=sha((OUT/'K0.md').read_bytes()),sha256=sha(obj['skill']),changes=obj.get('changes'),at=archive.now()));save(OUT/'versions.json',versions)
    save(d/'validation.json',validation);save(d/'result.json',dict(status=status,exit_code=process.returncode,turn_completed=completed,usage=usage,started_at=start,completed_at=archive.now(),command=command));shutil.rmtree(OUT/'.runtime'/m['id'],ignore_errors=True)
    print('EVOLVED_PENDING_RESEARCH_LEAKAGE_REVIEW',json.dumps(validation),flush=True)


def development():
    frozen();assert read(OUT/'preflight.json')['status']=='PASS';assert not (OUT/'invocations.json').exists();save(OUT/'invocations.json',[]);save(OUT/'results.json',[])
    for c in read(OUT/'protocol.json')['dev_order']['K0']:
        r=repair(c,'K0','development')
        if r['category']!='behavior' or r.get('controller_runtime_unverified') or r.get('hook_runtime_unverified'):
            save(OUT/'completion.json',dict(status='STOPPED_BASELINE_OR_CONTROLLER_UNVERIFIED',at=archive.now()));return
    evolve()


def select():
    rows=read(OUT/'results.json');old=[r for r in rows if r['split']=='development' and r['skill']=='K0'];new=[r for r in rows if r['split']=='development' and r['skill']=='K1'];decision=dict(accept=False,selected='K0',reason='candidate invalid or review rejected / missing valid scores')
    if len(new)==2 and all(r['category']=='behavior' and not r.get('controller_runtime_unverified') and not r.get('hook_runtime_unverified') for r in new):
        losses=[]
        for c in DEV:
            x=next(r for r in old if r['case']==c);y=next(r for r in new if r['case']==c);a=x['score'];b=y['score']
            for field in ['checks','assertions']:
                losses += [dict(case=c,kind=field,key=k) for k,v in a[field].items() if v and not b[field].get(k)]
            losses += [dict(case=c,kind=k,key=z) for k in ['original_check_losses','original_assertion_losses','forbidden'] for z in b[k]]
            if not y.get('changed_files') and not b['whole_pass']:losses.append(dict(case=c,kind='unimplemented-maintenance'))
        oldkey=sum(r['score']['whole_pass'] for r in old);newkey=sum(r['score']['whole_pass'] for r in new)
        accept=not losses and newkey>oldkey;decision=dict(accept=accept,selected='K1' if accept else 'K0',reason='strict whole-task improvement without preservation loss' if accept else 'preservation/implementation loss' if losses else 'whole-pass tie or no increase; keep K0',losses=losses,old_whole=oldkey,new_whole=newkey)
    save(OUT/'selection.json',decision);selected=decision['selected'];shutil.copyfile(OUT/(selected+'.md'),OUT/'Kstar.md')
    save(OUT/'selected.freeze.json',dict(selected=selected,sha256=sha((OUT/'Kstar.md').read_bytes()),at=archive.now(),basis='development only; no heldout execution yet',C_cancelled=selected=='K0'))
    schedule=[r for r in read(OUT/'protocol.json')['holdout_schedule'] if selected!='K0' or r['arm']!='C'];save(OUT/'holdout.schedule.json',schedule)
    prompts={}
    for c in HOLD:
        for arm in 'ABC':
            skill='K0' if arm in 'AB' else selected;text=prompt(c,(OUT/(skill+'.md')).read_text(),arm!='A');path=OUT/'materials'/c/(arm+'-final.prompt.md');path.write_text(text);prompts[str(path)]=sha(text)
        if selected=='K0':assert (OUT/'materials'/c/'B-final.prompt.md').read_bytes()==(OUT/'materials'/c/'C-final.prompt.md').read_bytes()
    save(OUT/'holdout.prompts.freeze.json',dict(at=archive.now(),sha256=prompts,selected=selected,C_executed=selected!='K0'))
    print('SELECTED',selected,'HOLDOUT_SLOTS',len(schedule),flush=True)


def candidate_runs():
    frozen();assert not (OUT/'selection.json').exists();validation=read(OUT/'evolution/validation.json');review=read(OUT/'evolution/research-review.json')
    if validation['valid'] and review['allow_execution']:
        assert sha((OUT/'K1.md').read_bytes())==review['skill_sha256']==validation['sha256']
        for c in read(OUT/'protocol.json')['dev_order']['K1']:repair(c,'K1','development')
    select()


def holdout():
    frozen();decision=read(OUT/'selected.freeze.json');assert not any(r['split']=='holdout' for r in read(OUT/'results.json'))
    for path,h in read(OUT/'holdout.prompts.freeze.json')['sha256'].items():assert sha(Path(path).read_bytes())==h
    for slot in read(OUT/'holdout.schedule.json'):
        assert sha((OUT/'Kstar.md').read_bytes())==decision['sha256']
        skill='K0' if slot['arm'] in 'AB' else decision['selected'];repair(slot['case'],skill,'holdout',slot['arm'],slot['replicate'])
    save(OUT/'completion.json',dict(status='COMPLETE',at=archive.now(),formal_sessions=len(read(OUT/'invocations.json')),selected=decision['selected'],C_cancelled=decision['C_cancelled'],reserve_used=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','development','candidate_runs','holdout']);args=parser.parse_args();globals()[args.action]()
