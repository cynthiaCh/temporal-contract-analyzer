"""Two serial prompt revisions; development-only selection; fixed held-out test."""
import argparse
from difflib import unified_diff
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import re
import shutil
import subprocess
import sys
import threading
import time

OUT=Path(__file__).resolve().parent
REPO=OUT.parents[1]
PRIOR=REPO/'research/staged-react-experiment-v1-20261105'
sys.path[:0]=[str(OUT),str(REPO)]
os.environ['TCA_BENCH_ROOT']=str(REPO.parent/'temporal-contract-bench-git')
os.environ['TCA_PYTHON_BIN']='/home/sribd/anaconda3/bin/python3.11'
from temporal_contract_analyzer import archive
from temporal_contract_analyzer.workbench import Workbench,capture,file_modes,write_files
from temporal_contract_analyzer.case_catalog import case_input,case_root
from temporal_contract_analyzer.case_evaluation import invoke,runtime
from source_retrieval import retrieve
from retriever import load,render

# Reuse the verified corrected runtime; change its runtime-profile destination only.
spec=importlib.util.spec_from_file_location('prior_isolated_runtime',PRIOR/'run.py')
rtmod=importlib.util.module_from_spec(spec);spec.loader.exec_module(rtmod);rtmod.OUT=OUT
IsolatedWorkbench=rtmod.IsolatedWorkbench
NODE=rtmod.NODE
BANK=REPO/'research/temporal-contract-question-bank-v1/questions.jsonl'
DEV=['download-polling-restoration-low-cue-react18','transfer-progress-composition-v4-vanilla']
HOLDOUT=['document-submit-snapshot-vanilla','local-config-readiness-low-cue-vue2']
MODEL='gpt-6-sol';EFFORT='low';TIMEOUT=600;SEED=2026110601
read=lambda p:json.loads(Path(p).read_text())
sha=lambda b:hashlib.sha256(b if isinstance(b,bytes) else b.encode()).hexdigest()
save=archive.atomic_json


def wb():return IsolatedWorkbench(OUT/'trials/reports',node=str(NODE))


def normalize_effects(case,raw,baseline):
    meta=read(OUT/'protocol.json')['cases'][case];cp=Path(meta['manifest']);cm=read(cp)
    effects=read(cp.parent/cm['oracle']['effects'])['variants']['ungranted']
    def vector(obs):
        return {**{'required:'+k:obs[k] is True for k in effects['required']},
                **{'forbidden:'+k:obs[k] is False for k in effects['forbidden']}}
    check=vector(raw['observed_effects']);before=vector(baseline['observed_effects'])
    return dict(verdict=raw['verdict'],whole_pass=raw['verdict']=='PASS',checks=check,
       required_passed=sum(raw['observed_effects'][k] is True for k in effects['required']),required_total=len(effects['required']),
       forbidden=[k for k in effects['forbidden'] if raw['observed_effects'][k]],
       lost_original=[k for k,v in before.items() if v and not check[k]])


def decide(current,candidate):
    """Strict development-only monotonic behavioral selection; ties keep incumbent."""
    if len(candidate)!=2 or any(not r.get('score') or r['category']!='behavior' for r in candidate):
        return dict(accept=False,reason='candidate lacks two valid development scores')
    losses=[]
    for c in DEV:
        old=next(r['score'] for r in current if r['case']==c)
        new=next(r['score'] for r in candidate if r['case']==c)
        losses += [dict(case=c,check=k) for k,v in old['checks'].items() if v and not new['checks'].get(k,False)]
        if new['forbidden'] or new['lost_original']:
            return dict(accept=False,reason='forbidden or original-pass loss',case=c)
    key=lambda rows:(sum(r['score']['whole_pass'] for r in rows),sum(r['score']['required_passed'] for r in rows))
    if losses:return dict(accept=False,reason='lost incumbent-passed development checks',losses=losses,old_key=key(current),new_key=key(candidate))
    return dict(accept=key(candidate)>key(current),reason='strict behavioral improvement' if key(candidate)>key(current) else 'tie or no strict improvement; keep incumbent',old_key=key(current),new_key=key(candidate),losses=[])


def candidate_check(text):
    violations=[]
    if not text.strip() or len(text)>5000:violations.append('empty or over 5000 characters')
    if '```' in text:violations.append('fenced content')
    bans=DEV+HOLDOUT+['usePreparation','watchTransferProgress','progressAttemptId','checkPreparation','getPageConfig','setValue','PersonnelEditor','SchemaForm','start-switch-admission','download-waits-after-pending','retry-preserved','src/','/workspace','/stage','oracle/','reference/','gpt-6']
    for token in bans:
        if token.lower() in text.lower():violations.append('task/runtime token: '+token)
    if re.search(r'\b[\w-]+\.(?:js|jsx|vue|json|cjs|mjs)\b',text,re.I):violations.append('source filename')
    for k in [1,2,3]:
        if not re.search(r'(?:stage|phase)\s*'+str(k)+r'\b',text,re.I):violations.append('missing stage '+str(k))
    return dict(valid=not violations,characters=len(text),violations=violations,
                limitation='mechanical hygiene only, not evidence of semantic correctness')


def check_frozen():
    p=read(OUT/'protocol.json')
    assert sha((OUT/'protocol.json').read_bytes())==(OUT/'protocol.sha256').read_text().strip()
    for path,h in p['frozen_files'].items():assert sha(Path(path).read_bytes())==h,path
    return p


def prepare():
    assert not (OUT/'protocol.json').exists(),'refuse overwrite'
    w=wb();meta={};base_prompts={}
    for case in DEV+HOLDOUT:
        ci=case_input(case);record=ci['case_record'];cp=case_root(record)/record['manifest'];cm=read(cp)
        folder=OUT/'cases'/case;files,_=capture(Path(ci['candidate']));modes=file_modes(Path(ci['candidate']),files)
        write_files(folder/'input',files,modes)
        packet,source=retrieve(ci['task'],files);questions=render([q['id'] for q in load(BANK)],BANK)
        common='Work only on the candidate-visible files in this workspace. Do not inspect sibling experiment jobs, original repositories or report stores.\n\n'+ci['task'].strip()+'\n\n<candidate-assistance>\n'+source+'\n'+questions+'\n</candidate-assistance>\n'
        (folder/'task.md').write_text(ci['task']);(folder/'common.md').write_text(common)
        save(folder/'source-retrieval.json',packet)
        meta[case]=dict(split='development' if case in DEV else 'optimizer-heldout',manifest=str(cp),manifest_sha256=sha(cp.read_bytes()),
          case_record=record,provenance=cm.get('provenance'),independent_unit_id=cm.get('independent_unit_id'),validation=cm.get('validation'),
          exposure='research-exposed; not independent generalization',input_files={k:sha(v) for k,v in files.items()},file_modes=modes,
          common_sha256=sha(common),ast_delivery=False,
          oracle_files={str(f):sha(f.read_bytes()) for f in (cp.parent/'oracle').rglob('*') if f.is_file()})
    rng=random.Random(SEED);dev_order={}
    for v in ['P0','P1','P2']:
        order=list(DEV);rng.shuffle(order);dev_order[v]=order
    first={c:['P0','Pstar'] if rng.randrange(2)==0 else ['Pstar','P0'] for c in HOLDOUT};schedule=[]
    for rep in [1,2]:
        order=list(HOLDOUT);rng.shuffle(order)
        for c in order:
            for arm in (first[c] if rep==1 else list(reversed(first[c]))):schedule.append(dict(case=c,arm=arm,replicate=rep))
    save(OUT/'initial-git.json',dict(head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
      diff=subprocess.check_output(['git','diff'],cwd=REPO,text=True),status=subprocess.check_output(['git','status','--short'],cwd=REPO,text=True)))
    shutil.copyfile(BANK,OUT/'questions.snapshot.jsonl')
    protected=list((REPO/'temporal_contract_analyzer').glob('*.py'))+list((REPO/'tools/temporal-contract-analyzer').rglob('*.cjs'))+[BANK]
    for prior in [PRIOR,REPO/'research/question-selection-experiment-v1-20261105']:
        protected += [f for f in prior.rglob('*') if f.is_file()]
    protected += [Path(m['manifest']) for m in meta.values()]+[Path(f) for m in meta.values() for f in m['oracle_files']]
    protected += [f for f in (OUT/'cases').rglob('*') if f.is_file()]
    protected += list(OUT.glob('*.py'))+list(OUT.glob('*.md'))+[OUT/'questions.snapshot.jsonl',OUT/'initial-git.json']
    p=dict(schema='prompt-evolution-v1',created_at=archive.now(),client_date='2026-11-06',model=MODEL,effort=EFFORT,timeout=600,
      maximum_model_calls=16,planned_optimizer_calls=2,planned_development_repairs=6,planned_heldout_repairs=8,
      development=DEV,optimizer_heldout=HOLDOUT,independent_generalization_cases=0,cases=meta,dev_order=dev_order,holdout_schedule=schedule,
      seed=SEED,model_sampling_seed=None,output_limit='same inherited CLI limits; no explicit output-token cap',
      initial_prompt_sha256=sha((OUT/'P0.md').read_bytes()),optimizer_instruction_sha256=sha((OUT/'OPTIMIZER.md').read_bytes()),
      record_guard_sha256=sha((OUT/'RECORD_GUARD.md').read_bytes()),selection='strict lexicographic (whole PASS, required total), no incumbent-passed check losses; ties keep incumbent',
      frozen_files={str(f):sha(f.read_bytes()) for f in sorted(set(protected))})
    save(OUT/'protocol.json',p);(OUT/'protocol.sha256').write_text(sha((OUT/'protocol.json').read_bytes())+'\n')
    print('FROZEN',flush=True)


def preflight():
    p=check_frozen();w=wb();s=OUT/'offline'
    for n in ['workspace','output','stage','profile']:(s/n).mkdir(parents=True,exist_ok=True)
    cmd=rtmod.isolation(s/'workspace',s/'output',s/'stage',s/'profile',w.codex)
    script="""set -eu
test ! -e /home/sribd
test ! -e /proc/1/root/home/sribd
test -x /opt/codex-code-mode-host
/opt/codex --version
/opt/codex-code-mode-host --help
echo 'const x = 1;' > /workspace/synthetic.js
node --check /workspace/synthetic.js
echo '{"stage":1}' > /stage/records.jsonl
test ! -e /workspace/records.jsonl
echo ISOLATION_PASS
"""
    r=subprocess.run(cmd+['/bin/bash','-c',script],capture_output=True,text=True,timeout=30)
    save(OUT/'offline-isolation.json',dict(exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr));assert r.returncode==0,r.stderr
    # Synthetic selection/hygiene assertions only; no formal hidden results tune prompts.
    def row(c,passed,whole=False,forbidden=None):return dict(case=c,category='behavior',score=dict(whole_pass=whole,required_passed=int(passed),checks={'required:x':passed},forbidden=forbidden or [],lost_original=[]))
    cur=[row(c,False) for c in DEV];better=[row(c,True,True) for c in DEV]
    assert decide(cur,better)['accept'];assert not decide(cur,cur)['accept'];assert not decide(better,cur)['accept']
    assert not decide(cur,[row(DEV[0],True,True,['bad']),row(DEV[1],True,True)])['accept']
    assert candidate_check((OUT/'P0.md').read_text())['valid']
    assert not candidate_check('Stage 1 usePreparation\nStage 2 src/a.js\nStage 3')['valid']
    cal=[]
    for case,meta in p['cases'].items():
        cp=Path(meta['manifest']);cm=read(cp);rt=runtime(cm,'legacy-js',str(NODE))
        for label in ['unchanged','reference']:
            files,_=capture(cp.parent/'base');modes=file_modes(cp.parent/'base',files)
            if label=='reference':
                ref=cp.parent/cm['references']['bounded'];overlay,_=capture(ref);files.update(overlay);modes.update(file_modes(ref,overlay))
            dest=OUT/'calibration'/case/label/'candidate';write_files(dest,files,modes)
            raw=invoke([rt['path'],str(cp.parent/cm['oracle']['probe']),str(dest),'ungranted'],dest.parent/'oracle',threading.Event(),Workbench.terminate,case)
            assert raw['verdict']==('PASS' if label=='reference' else 'UNDERREACH')
            cal.append(dict(case=case,label=label,verdict=raw['verdict'],runtime=rt))
    save(OUT/'preflight.json',dict(status='PASS',at=archive.now(),calibration=cal,synthetic_selection_checks=4,hygiene_checks=2,
       runtime_helper_checked=True,no_model_calls=True,split_isolation='optimizer packet built only from DEV; heldout not mounted'))
    print('PREFLIGHT_PASS',flush=True)


def register(kind,label):
    p=check_frozen();ledger=read(OUT/'invocations.json');assert len(ledger)<16
    assert label not in [r['label'] for r in ledger]
    ledger.append(dict(sequence=len(ledger)+1,kind=kind,label=label,at=archive.now()));save(OUT/'invocations.json',ledger)


def repair(case,variant,split,rep=1,arm=None):
    check_frozen();w=wb();m=w.prepare_case(dict(case_id=case,model=MODEL,effort=EFFORT,timeout=600,repeats=1,conditions=['none'],use_local_config=True))
    folder=w.folder(m['id']);d=folder/'jobs/j-001';meta=read(OUT/'protocol.json')['cases'][case]
    assert m['input_files']==meta['input_files']
    expected_common='Work only on the candidate-visible files in this workspace. Do not inspect sibling experiment jobs, original repositories or report stores.\n\n'+m['task'].strip()+'\n'
    assert (d/'prompt.md').read_text()==expected_common
    common=(OUT/'cases'/case/'common.md').read_text();assert sha(common)==meta['common_sha256']
    vpath=OUT/(variant+'.md');text=vpath.read_text();vsha=sha(text)
    if variant!='P0':assert vsha==read(OUT/'candidates'/variant/'validation.json')['sha256']
    prompt=common+'\n<execution-workflow>\n'+text+'\n'+(OUT/'RECORD_GUARD.md').read_text()+'\n</execution-workflow>\n'
    (d/'prompt.md').write_text(prompt);(d/'report.md').write_text(common)
    m['jobs'][0].update(prompt_sha256=sha(prompt),report_sha256=sha(common),report_characters=len(common))
    m['evolution_study']=dict(split=split,variant=variant,arm=arm or variant,replicate=rep,feedback_to_repair_agent=False)
    save(folder/'manifest.json',m)
    label=split+'/'+case+'/'+(arm or variant)+'/'+str(rep)
    register('repair',label)
    record=dict(label=label,id=m['id'],case=case,split=split,variant=variant,arm=arm or variant,replicate=rep,path=str(folder),
                variant_sha256=vsha,common_sha256=sha(common),prompt_sha256=sha(prompt),input_files=meta['input_files'])
    try:
        w.start(m['id']);w.thread.join();m=w.read(m['id']);j=m['jobs'][0];ep=w.latest_evaluation(m['id']);ev=read(ep) if ep else {};e=ev.get('jobs',{}).get('j-001',{})
        category='execution-failure' if j['status']!='completed' else 'behavior' if ev.get('calibration_verdict')=='PASS' and e.get('status') in ['passed','failed'] else 'validation-unverified'
        events=(d/'events.jsonl').read_text();tool_unavailable='failed to spawn code-mode host' in events
        if tool_unavailable:category='execution-tool-unavailable'
        record.update(category=category,process=j['status'],evaluation=str(ep) if ep else None,usage=j.get('usage'),started_at=j.get('started_at'),completed_at=j.get('completed_at'))
        if category=='behavior':
            raw=read(folder/e['result_path']);base=read(OUT/'calibration'/case/'unchanged/oracle/stdout.json')
            record['score']=normalize_effects(case,raw,base);record['raw_oracle']=str(folder/e['result_path'])
        else:record['score']=None
    except Exception as e:record.update(category='execution-error',error=str(e),score=None)
    finally:shutil.rmtree(OUT/'.runtime'/m['id'],ignore_errors=True)
    rows=read(OUT/'results.json');rows.append(record);save(OUT/'results.json',rows)
    print(json.dumps(dict(event='repair_done',label=label,category=record['category'],score=record.get('score',{}).get('verdict') if record.get('score') else None)),flush=True)
    return record


def feedback_packet(target,current):
    target.mkdir(parents=True)
    (target/'current-prompt.md').write_text((OUT/(current+'.md')).read_text())
    data=[]
    for case in DEV:
        src=OUT/'cases'/case
        shutil.copytree(src/'input',target/'development-source'/case)
        shutil.copyfile(src/'task.md',target/'development-source'/case/'TASK.md')
    rows=[r for r in read(OUT/'results.json') if r['split']=='development']
    assert all(r['case'] in DEV for r in rows)
    for r in rows:
        d=Path(r['path'])/'jobs/j-001';commands=[]
        for n,line in enumerate((d/'events.jsonl').read_text().splitlines(),1):
            e=json.loads(line);i=e.get('item',{})
            if e.get('type')=='item.completed' and i.get('type')=='command_execution':
                output=i.get('aggregated_output','');commands.append(dict(line=n,command=i.get('command'),exit_code=i.get('exit_code'),output=output[:6000],output_truncated=len(output)>6000))
        data.append(dict(case=r['case'],variant=r['variant'],category=r['category'],score=r['score'],
             patch=read(d/'changes.json'),actual_commands=commands,
             evidence_note='Original trusted checks summarized as booleans only; no hidden schedules/test inputs/scorer/reference code. Command output explicitly clipped at 6000 characters each.'))
    save(target/'development-feedback.json',dict(current_incumbent=current,rows=data))
    versions={r['variant'] for r in rows}
    for v in sorted(versions):shutil.copyfile(OUT/(v+'.md'),target/('evaluated-'+v+'.md'))
    # No holdout data in any payload or instruction.
    serialized='\n'.join(f.read_text(errors='replace') for f in target.rglob('*') if f.is_file())
    assert not any(c in serialized for c in HOLDOUT)
    save(target.parent/'packet-hashes.json',{str(f.relative_to(target)):sha(f.read_bytes()) for f in target.rglob('*') if f.is_file()})


def optimize(round_id,current):
    variant='P'+str(round_id);d=OUT/'candidates'/variant;work=d/'workspace';feedback_packet(work,current)
    instruction=(OUT/'OPTIMIZER.md').read_text();(d/'prompt.md').write_text(instruction)
    w=wb();m=dict(id='optimizer-'+variant,mode='workspace-write',local_codex=True,model_override=MODEL,effort=EFFORT)
    cmd=w.command(m,work,d/'answer.md');register('optimizer',variant)
    start=archive.now();status='completed';exitcode=None
    try:
        with (d/'prompt.md').open('rb') as inp,(d/'events.jsonl').open('wb') as out,(d/'stderr.log').open('wb') as err:
            proc=subprocess.Popen(cmd,cwd=work,stdin=inp,stdout=out,stderr=err,start_new_session=True)
            try:proc.wait(timeout=600)
            except subprocess.TimeoutExpired:status='timed_out';Workbench.terminate(proc)
            exitcode=proc.returncode
    finally:shutil.rmtree(OUT/'.runtime'/m['id'],ignore_errors=True)
    usage=None;completed=False
    for line in (d/'events.jsonl').read_text().splitlines():
        event=json.loads(line)
        if event.get('type')=='turn.completed':completed=True;usage=event.get('usage')
    path=d/'cli-output/answer.md';text=path.read_text() if path.exists() else ''
    valid=candidate_check(text)
    expected=read(d/'packet-hashes.json')
    mutated=[name for name,h in expected.items() if not (work/name).is_file() or sha((work/name).read_bytes())!=h]
    if mutated:
        valid['valid']=False;valid['violations'].append('optimizer mutated supplied input packet')
    if 'failed to spawn code-mode host' in (d/'events.jsonl').read_text():
        valid['valid']=False;valid['violations'].append('optimizer tool runtime unavailable')
    valid['packet_mutated_paths']=mutated
    if status!='completed' or exitcode!=0 or not completed:valid.update(valid=False,process_error=True)
    valid.update(sha256=sha(text),generated_at=archive.now(),base=current)
    (OUT/(variant+'.md')).write_text(text);save(d/'validation.json',valid)
    receipt=dict(variant=variant,current=current,started_at=start,completed_at=archive.now(),status=status,exit_code=exitcode,turn_completed=completed,usage=usage,validation=valid,command=cmd)
    save(d/'result.json',receipt)
    print(json.dumps(dict(event='optimizer_done',variant=variant,valid=valid['valid'],violations=valid['violations'])),flush=True)
    return valid


def execute():
    p=check_frozen();assert read(OUT/'preflight.json')['status']=='PASS'
    assert not (OUT/'invocations.json').exists(),'no retries or silent resume'
    save(OUT/'invocations.json',[]);save(OUT/'results.json',[])
    current='P0';current_rows=[]
    for case in p['dev_order']['P0']:current_rows.append(repair(case,'P0','development'))
    if any(r['category']!='behavior' for r in current_rows):
        save(OUT/'completion.json',dict(status='STOPPED_DEVELOPMENT_BASELINE_UNVERIFIED',invocations=len(read(OUT/'invocations.json'))));return
    selections=[]
    for round_id in [1,2]:
        variant='P'+str(round_id);validation=optimize(round_id,current)
        candidate=[]
        if validation['valid']:
            for case in p['dev_order'][variant]:candidate.append(repair(case,variant,'development'))
            decision=decide(current_rows,candidate)
        else:decision=dict(accept=False,reason='invalid generated workflow; development slots skipped')
        selections.append(dict(round=round_id,candidate=variant,incumbent_before=current,decision=decision,at=archive.now()))
        save(OUT/'selection.json',selections)
        if decision['accept']:current=variant;current_rows=candidate
        if any(r['category'].startswith('execution') for r in candidate):
            save(OUT/'completion.json',dict(status='STOPPED_RUNTIME_FAILURE',invocations=len(read(OUT/'invocations.json'))));return
    shutil.copyfile(OUT/(current+'.md'),OUT/'Pstar.md')
    save(OUT/'selected.freeze.json',dict(selected=current,sha256=sha((OUT/'Pstar.md').read_bytes()),at=archive.now(),basis='development only',selection=selections))
    for slot in p['holdout_schedule']:
        assert sha((OUT/'Pstar.md').read_bytes())==read(OUT/'selected.freeze.json')['sha256']
        variant='P0' if slot['arm']=='P0' else current
        repair(slot['case'],variant,'holdout',slot['replicate'],slot['arm'])
    save(OUT/'completion.json',dict(status='COMPLETE',invocations=len(read(OUT/'invocations.json')),selected=current,at=archive.now()))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','preflight','execute']);args=parser.parse_args();globals()[args.action]()
