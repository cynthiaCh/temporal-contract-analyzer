"""Frozen 24-call development pilot. Prepare/calibrate before any model calls."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import math
import os
from pathlib import Path
import random
import sys
import threading
import time

OUT=Path(__file__).resolve().parent
REPO=OUT.parents[1]
sys.path[:0]=[str(OUT),str(REPO)]
os.environ['TCA_BENCH_ROOT']=str(REPO.parent/'temporal-contract-bench-git')
os.environ['TCA_PYTHON_BIN']='/home/sribd/anaconda3/bin/python3.11'
from temporal_contract_analyzer import archive
from temporal_contract_analyzer.workbench import Workbench,capture,inventory,file_modes,write_files
from temporal_contract_analyzer.case_catalog import case_input
from temporal_contract_analyzer.case_evaluation import invoke,runtime
from source_retrieval import retrieve
from retriever import retrieve as retrieve_questions, render, CONFIG, load
BANK=REPO/'research/temporal-contract-question-bank-v1/questions.jsonl'
NODE=REPO/'results/ad-model-effort-20261104/runtime/node-v16.20.2-linux-x64/bin/node'
CASES=['listener-registration-order-vanilla','document-submit-snapshot-vanilla','handoff-redirect-reentrancy-vanilla','feature-flag-readiness-vue3']
ARMS=['S','F','R']
MODEL='gpt-6-sol';EFFORT='low';TIMEOUT=600
sha=lambda v:hashlib.sha256(v if isinstance(v,bytes) else v.encode()).hexdigest()
read=lambda p:json.loads(Path(p).read_text())
save=archive.atomic_json

def question_retrieve(task,source_packet):
    packet=retrieve_questions(task,source_packet['snippets'],BANK)
    return packet,render(packet['selected_ids'],BANK)

def check_frozen():
    p=read(OUT/'protocol.json')
    assert sha((OUT/'protocol.json').read_bytes())==(OUT/'protocol.freeze.sha256').read_text().strip()
    for name,h in p['frozen_files'].items():assert sha(Path(name).read_bytes())==h,name
    return p


def selection_review(runs):
    # Researcher applicability review of visible task/code BEFORE launches/outcomes.
    judgments={
      'listener-registration-order-vanilla':dict(applicable=['TCQ-001','TCQ-002','TCQ-003'],uncertain=[],evidence='subscription.js connects before addEventListener; decode.then(receive) survives detach; workspace-navigation.js permits synchronous select/hide from publish.'),
      'document-submit-snapshot-vanilla':dict(applicable=['TCQ-003','TCQ-004','TCQ-005'],uncertain=[],evidence='README requires close/open settlement, accepted submit receipt and visit-bound notice; store notifications run inline and may navigate/edit.'),
      'handoff-redirect-reentrancy-vanilla':dict(applicable=['TCQ-003'],uncertain=[],evidence='README permits synchronous navigation during handoff; later-started navigation wins. Synchronous store writes, no deferred work or async result.'),
      'feature-flag-readiness-vue3':dict(applicable=[],uncertain=[],evidence='runTarget waits for loadedFlag; runAdjacent is emergency fail-open. No listener registration, visit retirement, callback reentry, persistent history/display split or deferred writes.')}
    for c,v in judgments.items():
      selected=next(r['question_ids'] for r in runs if r['case']==c and r['arm']=='R')
      v.update(selected=selected,missed=sorted(set(v['applicable'])-set(selected)),irrelevant=sorted(set(selected)-set(v['applicable'])-set(v['uncertain'])))
    return dict(reviewed_at=archive.now(),stage='before any formal call or behavior score; main-agent researcher review, not independent human/blind review',cases=judgments)

def prepare():
    assert not (OUT/'protocol.json').exists(),'refuse overwrite'
    exposure=read(REPO/'research/temporal-contract-question-bank-v1/provenance.json')['split_policy']
    # Unknown/shared authored lineage is conservatively exploratory, never independent.
    save(OUT/'split-policy-snapshot.json',exposure)
    calibration=[];case_meta={}
    # Run only trusted unchanged/reference calibration, not model self-tests.
    for case in CASES:
        ci=case_input(case);record=ci['case_record'];cp=REPO.parent/'temporal-contract-bench-git'/record['manifest'];cm=read(cp);base=cp.parent
        rt=runtime(cm,'legacy-js',str(NODE));vrows=[]
        for label in ['unchanged','reference']:
            files,_=capture(base/'base');modes=file_modes(base/'base',files)
            if label=='reference':
                reference=base/cm['references']['bounded'];overlay,_=capture(reference);files.update(overlay);modes.update(file_modes(reference,overlay))
            target=OUT/'calibration'/case/label/'candidate';write_files(target,files,modes)
            result=invoke([rt['path'],str(base/cm['oracle']['probe']),str(target),'ungranted'],target.parent/'oracle',threading.Event(),Workbench.terminate,case)
            assert result['verdict']==('PASS' if label=='reference' else 'UNDERREACH'),(case,label,result)
            vrows.append(dict(label=label,verdict=result['verdict'],raw=str(target.parent/'oracle/stdout.json')))
        calibration.append(dict(case=case,runtime=rt,variants=vrows))
        case_meta[case]=dict(independent_unit_id=cm.get('independent_unit_id'),provenance=cm.get('provenance'),validation=cm.get('validation'),source_classification=('development-source' if case in exposure['affected_cases'] else 'related-author-template / independent lineage unverified'),case_manifest=str(cp),case_manifest_sha256=sha(cp.read_bytes()),oracle_files={str(f):sha(f.read_bytes()) for f in sorted((base/'oracle').rglob('*')) if f.is_file()},exposure='development-source',independent_generalization_test_allowed=False)
    save(OUT/'calibration.json',calibration)
    wbs=[Workbench(OUT/'trials'/('lane'+str(i))/'reports',node=str(NODE)) for i in range(3)]
    runs=[];blocks=[];rng=random.Random(2026110502)
    for rep in [1,2]:
        order=list(CASES);rng.shuffle(order)
        for case in order:
            arms=list(ARMS);rng.shuffle(arms);block='b-%02d'%(len(blocks)+1);blocks.append(dict(id=block,case=case,replicate=rep,arms=arms))
            packets=OUT/'packets'/case
            for lane,arm in enumerate(arms):
                wb=wbs[lane];m=wb.prepare_case(dict(case_id=case,model=MODEL,effort=EFFORT,timeout=TIMEOUT,repeats=1,conditions=['none'],use_local_config=True))
                folder=wb.folder(m['id']);job=m['jobs'][0];d=folder/'jobs/j-001';files,_=capture(folder/'input');base_prompt=(d/'prompt.md').read_text()
                source_packet,source=retrieve(m['task'],files);question_packet,qtext=question_retrieve(m['task'],source_packet)
                materials=dict(S=source,F=source+'\n'+render([q['id'] for q in load(BANK)],BANK),R=source+'\n'+qtext)
                material=materials[arm];prompt=base_prompt+('\n<candidate-assistance>\n'+material+'\n</candidate-assistance>\n' if material else '')
                (d/'prompt.md').write_text(prompt);(d/'report.md').write_text(material)
                job.update(prompt_sha256=sha(prompt),report_sha256=sha(material),report_characters=len(material))
                m['question_bank_study']=dict(arm=arm,replicate=rep,block=block,exposure='development-source',engine_condition='none is transport only; study arm determines appended intervention',feedback_delivered=False)
                save(folder/'manifest.json',m);save(folder/'source-retrieval.json',source_packet);save(folder/'question-retrieval.json',question_packet)
                packets.mkdir(parents=True,exist_ok=True)
                for name,text in materials.items():
                    fp=packets/(name+'.md')
                    if fp.exists():assert fp.read_text()==text
                    else:fp.write_text(text)
                fp=packets/'retrieval.json'
                if fp.exists():assert {k:v for k,v in read(fp).items() if k!='elapsed_seconds'}=={k:v for k,v in question_packet.items() if k!='elapsed_seconds'}
                else:save(fp,question_packet)
                prior=next((r for r in runs if r['case']==case),None)
                if prior:assert prior['input_files']==m['input_files']
                runs.append(dict(case=case,arm=arm,replicate=rep,block=block,lane=lane,id=m['id'],path=str(folder),input_files=m['input_files'],prompt_sha256=sha(prompt),material_sha256=sha(material),material_chars=len(material),question_ids=question_packet['selected_ids'] if arm=='R' else [q['id'] for q in load(BANK)] if arm=='F' else []))
    save(OUT/'runs.json',runs)
    save(OUT/'selection-review.json',selection_review(runs))
    tracked=list((REPO/'temporal_contract_analyzer').glob('*.py'))+list((REPO/'tools/temporal-contract-analyzer').glob('*.cjs'))+[OUT/'run.py',OUT/'source_retrieval.py',OUT/'retriever.py',OUT/'offline-validation.json',OUT/'PLAN.md',OUT/'prior-audit.json',OUT/'selection-review.json',BANK,OUT/'runs.json',OUT/'calibration.json']+list((OUT/'packets').rglob('*md'))+list((OUT/'packets').rglob('*json'))
    tracked += [Path(r['path'])/'jobs/j-001/prompt.md' for r in runs]+[f for r in runs for f in (Path(r['path'])/'input').rglob('*') if f.is_file()]
    protocol=dict(random_seed=2026110502,retrieval_config=CONFIG,output_limit='Same Workbench command and inherited local config as prior round; no explicit output token cap in prior script',selection_review_at=archive.now(),schema_version='question-selection-v1',created_at=archive.now(),client_date='2026-11-05',model=MODEL,effort=EFFORT,timeout=TIMEOUT,max_invocations=24,max_parallel=3,arms=ARMS,cases=case_meta,blocks=blocks,question_selection='Frozen weighted lexical BM25 with score >=5 and >=3 English matches; task + SAME retrieved code snippets only; top2, may abstain',hypothesis='R reduces irrelevant questions and costs relative to F; compare whole behavior and losses against S without presupposing benefit.',primary='Whole-task PASS, loss of originally passed checks, unnecessary behavior changes on negative case. Descriptive only, four cases, two repeats per condition.',secondary='Required and forbidden effect vectors, stable check losses across fresh repairs, observed token/time cost; no continuation regression rate.',stopping='Exactly24 scheduled calls. No outcome-selected retry/replacement/additional calls. Process failures and unverified evaluations reported separately.',exposure='Exploratory only: 2 direct development cases, 1 related authored extension, 1 shared-template negative; no independently certified generalization case.',confounds=['Two calls per case/arm are too few for reliable effect estimates.','Question and generic appendices differ in length/content; no equal-token claim.','Small candidate repositories; source packing may cover most files.','Local workspace-write is not hermetic filesystem read isolation.','Both bank and generic checklist are author exposed.'],frozen_files={str(f):sha(f.read_bytes()) for f in tracked})
    save(OUT/'protocol.json',protocol);(OUT/'protocol.freeze.sha256').write_text(sha((OUT/'protocol.json').read_bytes())+'\n')
    print(json.dumps(dict(event='ALL24_FROZEN',retrieval={c:read(OUT/'packets'/c/'retrieval.json')['selected_ids'] for c in CASES})),flush=True)

def execute():
    protocol=check_frozen();assert not (OUT/'invocations.json').exists(),'refuse relaunch or overwrite'
    runs=read(OUT/'runs.json');results=[];ledger=[];lock=threading.Lock()
    wbs=[Workbench(OUT/'trials'/('lane'+str(i))/'reports',node=str(NODE)) for i in range(3)]
    save(OUT/'invocations.json',ledger);save(OUT/'results.json',results)
    def worker(rec):
        check_frozen();wb=wbs[rec['lane']]
        with lock:
            assert len(ledger)<24
            ledger.append(dict(id=rec['id'],block=rec['block'],launched_at=archive.now()));save(OUT/'invocations.json',ledger)
        try:
            wb.start(rec['id']);wb.thread.join();m=wb.read(rec['id']);j=m['jobs'][0];ep=wb.latest_evaluation(m['id']);ev=read(ep) if ep else {};row=ev.get('jobs',{}).get(j['id'],{})
            category='execution-failure' if j['status']!='completed' else ('behavior-'+('pass' if row['status']=='passed' else 'failure') if ev.get('calibration_verdict')=='PASS' and row.get('status') in ['passed','failed'] else 'validation-unverified')
            out=dict(rec,job=j['id'],process=j['status'],category=category,outcome=row.get('status','unverified'),calibration=ev.get('calibration_verdict'),evaluation=str(ep) if ep else None,usage=j.get('usage'),started_at=j.get('started_at'),completed_at=j.get('completed_at'))
        except Exception as e:
            out=dict(rec,category='execution-error',error=type(e).__name__+': '+str(e))
        with lock:
            results.append(out);save(OUT/'results.json',results)
            print(json.dumps(dict(event='done',n=len(results),case=rec['case'],arm=rec['arm'],replicate=rec['replicate'],category=out['category'])),flush=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        for block in protocol['blocks']:
            print('BLOCK_START '+block['id'],flush=True)
            for future in as_completed([pool.submit(worker,r) for r in runs if r['block']==block['id']]):future.result()
    save(OUT/'completion.json',dict(status='COMPLETE',invocations=len(ledger),results=len(results),completed_at=archive.now()))
    print('COMPLETE',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--execute',action='store_true');args=parser.parse_args()
    if args.execute:execute()
    else:prepare()
