"""Frozen one-case diagnostic; nine serial independent trials, no retries."""
import argparse, base64, hashlib, importlib.util, json, os, random, shutil, subprocess, sys, threading, time, urllib.request
from pathlib import Path
OUT=Path(__file__).resolve().parent
REPO=OUT.parents[1]
PRIOR=REPO/'research/prompt-evolution-experiment-v1-20261106'
sys.path[:0]=[str(PRIOR),str(REPO)]
spec=importlib.util.spec_from_file_location('trusted_previous',PRIOR/'run.py')
prev=importlib.util.module_from_spec(spec);spec.loader.exec_module(prev)
prev.rtmod.OUT=OUT
CASE='transfer-progress-composition-v4-vanilla'
SEED=2026110602
sha=prev.sha;read=prev.read;save=prev.save

def wb():return prev.IsolatedWorkbench(OUT/'trials/reports',node=str(prev.NODE))

def token_count(text):
    # Existing regex package; static rank data is archived, no pip dependencies.
    import regex
    ranks={base64.b64decode(a):int(b) for a,b in (l.split() for l in (OUT/'o200k_base.tiktoken').read_bytes().splitlines())}
    pat=regex.compile(r"[^\r\n\p{L}\p{N}]?[\p{Lu}\p{Lt}\p{Lm}\p{Lo}\p{M}]*[\p{Ll}\p{Lm}\p{Lo}\p{M}]+(?i:'s|'t|'re|'ve|'m|'ll|'d)?|[^\r\n\p{L}\p{N}]?[\p{Lu}\p{Lt}\p{Lm}\p{Lo}\p{M}]+[\p{Ll}\p{Lm}\p{Lo}\p{M}]*(?i:'s|'t|'re|'ve|'m|'ll|'d)?|\p{N}{1,3}| ?[^\s\p{L}\p{N}]+[\r\n/]*|\s*[\r\n]+|\s+(?!\S)|\s+")
    total=0
    for match in pat.finditer(text):
        piece=match.group().encode()
        if piece in ranks:total+=1;continue
        parts=[bytes([b]) for b in piece]
        while len(parts)>1:
            pairs=[ranks.get(parts[i]+parts[i+1],float('inf')) for i in range(len(parts)-1)]
            best=min(pairs)
            if best==float('inf'):break
            i=pairs.index(best);parts[i:i+2]=[parts[i]+parts[i+1]]
        total+=len(parts)
    return total

def freeze():
    p=read(OUT/'protocol.json')
    assert sha((OUT/'protocol.json').read_bytes())==(OUT/'protocol.sha256').read_text().strip()
    for f,h in p['frozen_files'].items():assert sha(Path(f).read_bytes())==h,f
    return p

def prepare():
    assert not (OUT/'protocol.json').exists()
    historical=[r for r in read(PRIOR/'results.json') if r['case']==CASE and r['variant']=='P0'][0]
    old=Path(historical['path'])/'jobs/j-001'
    meta=read(PRIOR/'protocol.json')['cases'][CASE]
    mat=OUT/'materials';mat.mkdir()
    shutil.copytree(PRIOR/'cases'/CASE/'input',mat/'input')
    for n in ['task.md','common.md','source-retrieval.json']:shutil.copyfile(PRIOR/'cases'/CASE/n,mat/n)
    for n in ['P0.md','RECORD_GUARD.md']:shutil.copyfile(PRIOR/n,mat/n)
    a=(old/'prompt.md').read_text()
    assert a==(mat/'common.md').read_text()+'\n<execution-workflow>\n'+(mat/'P0.md').read_text()+'\n'+(mat/'RECORD_GUARD.md').read_text()+'\n</execution-workflow>\n'
    chunks=[('README.md',8,26,'visible visit/attempt/feed and consumer definitions'),('src/progress-source.js',8,32,'start evaluation precedes dispatch; host removal callback'),('src/transfer.js',1,17,'transport/watch/abort/late cleanup handoff; not included in common RAG'),('src/panel.js',4,34,'navigation retirement and cleanup ordering'),('src/retry.js',4,15,'retry replaces physical attempt within visit'),('src/queue.js',8,20,'separate history and display callbacks'),('src/progress.js',1,12,'current receipt/decode/delivery implementation')]
    evidence='\n<candidate-context>\n'
    sources=[]
    for path,lo,hi,why in chunks:
        f=mat/'input'/path;lines=f.read_text().splitlines(keepends=True)
        snippet=''.join(lines[lo-1:hi]);assert len(lines)>=hi
        evidence+=f'\n## {path}:{lo}-{hi}\n```\n'+''.join(f'{i}: {lines[i-1]}' for i in range(lo,hi+1))+'```\n'
        sources.append(dict(path=path,start=lo,end=hi,source_sha256=sha(f.read_bytes()),snippet_sha256=sha(snippet),research_selection_reason=why,original_visibility='original frozen candidate input file; present in historical manifest input_files',original_manifest_sha256=meta['input_files'][path],already_in_common=path!='src/transfer.js'))
        assert sha(f.read_bytes())==meta['input_files'][path]
    evidence+='\n</candidate-context>\n'
    question='\n根据 README.md:8-26、src/progress-source.js:24-28、src/transfer.js:3-16、src/panel.js:10-34、src/retry.js:4-15 和 src/queue.js:8-20，核对 start 内 initialPacket 函数先触发导航、随后派发 progress，与 progress 已进入解码后才导航或重试这两种顺序：事件接纳、历史记录和当前显示各依赖什么归属及有效性条件？请依据原任务与可见实现判断，并区分已有事实和仍需验证的假设。\n'
    # Question grounded in task preservation + source code; no oracle names/required expected outcome.
    (mat/'evidence.md').write_text(evidence);(mat/'question.md').write_text(question)
    save(mat/'visibility.json',dict(manual_targeted_diagnosis=True,automatic_retrieval_claim=False,sources=sources,question_basis=['original task preservation of navigation/retry/audit behavior','README.md:8-26','src/progress-source.js:24-28','src/transfer.js:3-16','src/panel.js:10-34','src/retry.js:4-15','src/queue.js:8-20'],historical_baseline=historical))
    # Static, public tokenizer data only; not a model/search request.
    urllib.request.urlretrieve('https://openaipublic.blob.core.windows.net/encodings/o200k_base.tiktoken',OUT/'o200k_base.tiktoken')
    lengths={}
    for label,s in [('B',evidence),('C',evidence+question)]:
        lengths[label]=dict(characters=len(s),utf8_bytes=len(s.encode()),tokens=token_count(s),tokenizer='o200k_base public proxy; not asserted to equal gpt-6-sol internal tokenizer',max_characters=6500,max_tokens=2200)
        assert len(s)<=6500 and lengths[label]['tokens']<=2200,lengths[label]
    save(mat/'lengths.json',lengths)
    prompts={'A':a,'B':a+evidence,'C':a+evidence+question}
    for arm,text in prompts.items():(mat/(arm+'.prompt.md')).write_text(text)
    assert prompts['C']==prompts['B']+question and prompts['B']==a+evidence
    initial=dict(head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),status=subprocess.check_output(['git','status','--short'],text=True),diff=subprocess.check_output(['git','diff'],text=True))
    save(OUT/'initial-git.json',initial)
    rng=random.Random(SEED);runs=[];w=wb()
    for rep in [1,2,3]:
        arms=list('ABC');rng.shuffle(arms)
        for arm in arms:
            m=w.prepare_case(dict(case_id=CASE,model='gpt-6-sol',effort='low',timeout=600,repeats=1,conditions=['none'],use_local_config=True))
            assert m['input_files']==meta['input_files']
            d=w.folder(m['id'])/'jobs/j-001'
            (d/'prompt.md').write_text(prompts[arm]);(d/'report.md').write_text((mat/'common.md').read_text())
            m['jobs'][0].update(prompt_sha256=sha(prompts[arm]),report_sha256=sha((mat/'common.md').read_bytes()),report_characters=len((mat/'common.md').read_text()))
            save(w.folder(m['id'])/'manifest.json',m)
            runs.append(dict(id=m['id'],arm=arm,replicate=rep,sequence=len(runs)+1,path=str(w.folder(m['id'])),prompt_sha256=sha(prompts[arm]),input_files=m['input_files']))
    save(OUT/'runs.json',runs)
    # Protect ALL existing tracked and untracked source/history files, excluding this new directory.
    protected=[REPO/p for p in subprocess.check_output(['git','ls-files'],cwd=REPO,text=True).splitlines() if (REPO/p).is_file()]
    for root in [PRIOR, REPO/'research/staged-react-experiment-v1-20261105', REPO/'research/question-selection-experiment-v1-20261105',Path(meta['manifest']).parent]:
        protected += [f for f in root.rglob('*') if f.is_file() and '__pycache__' not in f.parts]
    protected += [f for f in mat.rglob('*') if f.is_file()]+[OUT/'PLAN.md',OUT/'run.py',OUT/'runs.json',OUT/'initial-git.json',OUT/'o200k_base.tiktoken']
    protected += [Path(r['path'])/'jobs/j-001/prompt.md' for r in runs]+[f for r in runs for f in (Path(r['path'])/'input').rglob('*') if f.is_file()]
    p=dict(created_at=prev.archive.now(),case=CASE,case_meta=meta,baseline_history=historical,maximum_calls=9,model='gpt-6-sol',effort='low',timeout=600,seed=SEED,model_sampling_seed=None,output_limit='inherited CLI limits; no explicit output token cap',schedule=runs,lengths=lengths,evidence_sha256=sha(evidence),question_sha256=sha(question),frozen_files={str(f):sha(f.read_bytes()) for f in sorted(set(protected))})
    save(OUT/'protocol.json',p);(OUT/'protocol.sha256').write_text(sha((OUT/'protocol.json').read_bytes())+'\n')
    print('FROZEN',lengths,flush=True)

def preflight():
    p=freeze();w=wb();s=OUT/'offline'
    for n in ['workspace','output','stage','profile']:(s/n).mkdir(parents=True)
    cmd=prev.rtmod.isolation(s/'workspace',s/'output',s/'stage',s/'profile',w.codex)
    script='''set -eu
test ! -e /home/sribd
test ! -e /proc/1/root/home/sribd
test ! -e /workspace/../materials
test -x /opt/codex-code-mode-host
/opt/codex --version
/opt/codex-code-mode-host --help
printf 'const x = 1;' > /workspace/example.js
node --check /workspace/example.js
/runtime/node16 --version
printf '{}' > /stage/records.jsonl
test ! -e /workspace/records.jsonl
'''
    result=subprocess.run(cmd+['/bin/bash','-c',script],capture_output=True,text=True,timeout=30)
    save(OUT/'offline-isolation.json',dict(exit_code=result.returncode,stdout=result.stdout,stderr=result.stderr));assert result.returncode==0
    cp=Path(p['case_meta']['manifest']);cm=read(cp);rt=prev.runtime(cm,'legacy-js',str(prev.NODE));cal=[]
    for label in ['unchanged','reference']:
        files,_=prev.capture(cp.parent/'base');modes=prev.file_modes(cp.parent/'base',files)
        if label=='reference':
            ref=cp.parent/cm['references']['bounded'];overlay,_=prev.capture(ref);files.update(overlay);modes.update(prev.file_modes(ref,overlay))
        dest=OUT/'calibration'/label/'candidate';prev.write_files(dest,files,modes)
        raw=prev.invoke([rt['path'],str(cp.parent/cm['oracle']['probe']),str(dest),'ungranted'],dest.parent/'oracle',threading.Event(),prev.Workbench.terminate,CASE)
        assert raw['verdict']==('PASS' if label=='reference' else 'UNDERREACH')
        cal.append(dict(label=label,verdict=raw['verdict'],runtime=rt))
    mat=OUT/'materials';a=(mat/'A.prompt.md').read_bytes();b=(mat/'B.prompt.md').read_bytes();c=(mat/'C.prompt.md').read_bytes();e=(mat/'evidence.md').read_bytes();q=(mat/'question.md').read_bytes()
    assert a==(Path(p['baseline_history']['path'])/'jobs/j-001/prompt.md').read_bytes()
    assert b==a+e and c==b+q
    for text in [e,q]:
        for banned in [b'oracle',b'reference',b'start-switch-admission',b'retry-preserved',b'UNDERREACH',b'P0',b'condition',b'expected better']:assert banned not in text,banned
    save(OUT/'preflight.json',dict(status='PASS',at=prev.archive.now(),no_model_calls=True,calibration=cal,baseline_byte_identical=True,evidence_byte_identical=True,c_only_question=True,manual_semantic_boundary_review='Source only excerpts; question asks relation/order without prescribing outcome or repair; no hidden/reference content',archiving='existing Workbench full events, tool output, prompt, usage, changes, answer, post-run oracle',runtime_helper_checked=True))
    print('PREFLIGHT_PASS',flush=True)

def execute():
    freeze();assert read(OUT/'preflight.json')['status']=='PASS';assert not (OUT/'invocations.json').exists()
    ledger=[];rows=[];w=wb()
    for r in read(OUT/'runs.json'):
        freeze();ledger.append(dict(id=r['id'],sequence=r['sequence'],at=prev.archive.now()));save(OUT/'invocations.json',ledger)
        start=time.monotonic();d=Path(r['path'])/'jobs/j-001';row=dict(r)
        try:
            w.start(r['id']);w.thread.join();m=w.read(r['id']);j=m['jobs'][0];ep=w.latest_evaluation(r['id']);ev=read(ep) if ep else {};score=ev.get('jobs',{}).get('j-001',{})
            category='execution-failure' if j['status']!='completed' else 'behavior' if ev.get('calibration_verdict')=='PASS' and score.get('status') in ['passed','failed'] else 'validation-unverified'
            events=(d/'events.jsonl').read_text()
            if 'failed to spawn code-mode host' in events:category='execution-tool-unavailable'
            row.update(category=category,process=j['status'],evaluation=str(ep) if ep else None,usage=j.get('usage'),started_at=j.get('started_at'),completed_at=j.get('completed_at'),raw_oracle=str(Path(r['path'])/score['result_path']) if 'result_path' in score else None)
        except Exception as error:row.update(category='execution-error',error=repr(error))
        finally:shutil.rmtree(OUT/'.runtime'/r['id'],ignore_errors=True)
        row['including_score_seconds']=time.monotonic()-start;rows.append(row);save(OUT/'results.json',rows)
        print(json.dumps(dict(event='done',n=len(rows),arm=r['arm'],rep=r['replicate'],category=row['category'])),flush=True)
    save(OUT/'completion.json',dict(status='COMPLETE',calls=len(ledger),at=prev.archive.now()))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','preflight','execute']);args=parser.parse_args();globals()[args.action]()
