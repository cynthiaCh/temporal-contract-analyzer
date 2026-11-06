import random,subprocess,shutil,re
from runtime import *

def prepare():
    assert not (OUT/'protocol.json').exists()
    save(OUT/'initial-git.json',dict(head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),status=subprocess.check_output(['git','status','--short'],text=True),diff=subprocess.check_output(['git','diff'],text=True)))
    shutil.copyfile(BANK,OUT/'questions.snapshot.jsonl');meta={};private=[];bans=[]
    for split,cases in [('train',TRAIN),('val',VAL),('test',TEST)]:
        for c in cases:
            ci=case_input(c);cp=case_root(ci['case_record'])/ci['case_record']['manifest'];cm=read(cp);files,_=capture(Path(ci['candidate']));modes=file_modes(Path(ci['candidate']),files);folder=OUT/'materials'/c
            write_files(folder/'input',files,modes);packet,source=retrieve(ci['task'],files);questions=render([q['id'] for q in load(BANK)],BANK)
            common='Work only on the candidate-visible files in this workspace. Do not inspect sibling experiment jobs, original repositories or report stores.\n\n'+ci['task'].strip()+'\n\n<candidate-assistance>\n'+source+'\n'+questions+'\n</candidate-assistance>\n'
            for n,t in [('task.md',ci['task']),('source.md',source),('questions.md',questions),('common.md',common)]: (folder/n).write_text(t)
            save(folder/'source-retrieval.json',packet)
            meta[c]=dict(split=split,case_record=ci['case_record'],manifest=str(cp),manifest_sha256=sha(cp.read_bytes()),independent_unit_id=cm.get('independent_unit_id'),source_cluster=str(cp.parent.relative_to(REPO.parent/'temporal-contract-bench-git')).split('/arms/')[0],provenance=cm.get('provenance'),exposure='historically research exposed; exploratory, not independent generalization',input_files={k:sha(v) for k,v in files.items()},file_modes=modes,common_sha256=sha(common),oracle_files={str(f):sha(f.read_bytes()) for f in (cp.parent/'oracle').rglob('*') if f.is_file()})
            (folder/'K0.prompt.md').write_text(full_prompt(c,(OUT/'K0.md').read_text()))
            effects=read(cp.parent/cm['oracle']['effects'])['variants']['ungranted'];private+=list(effects['required'])+list(effects['forbidden']);bans.append(c)
            for text in files.values():bans+=re.findall(r'\b[a-z]+(?:[A-Z][a-z0-9]+){2,}\b',text.decode('utf-8',errors='replace'))
    for a,b in [('train','val'),('train','test'),('val','test')]:
        for key in ['independent_unit_id','source_cluster']:assert not {m[key] for m in meta.values() if m['split']==a}&{m[key] for m in meta.values() if m['split']==b}
    save(OUT/'private-score-identifiers.json',sorted(set(private)));save(OUT/'skill-banned-identifiers.json',sorted(set(private+bans)))
    save(OUT/'split.json',dict(cases=meta,selection_basis='PLAN.md fixed prior to formal results; credible historical failures plus easier preservation tasks',sources=['research/failure-mechanism-diagnosis-v1-20261106/REPORT.md','research/react-skill-evolution-v1-20261106/REPORT.md','research/prompt-evolution-experiment-v1-20261106/REPORT.md','results/assistance-applicability-v1-20261105/pilot/results.csv','results/ad-model-effort-20261104/results.csv'],independent_generalization_cases=0))
    for name in ['task-ledger','task-results','reflection-calls','adapter-evaluations','reflection-datasets','budget-checks']:save(OUT/(name+'.json'),[])
    save(OUT/'reflection-meter/config.json',dict(max_requests=6));env=OUT/'environment';env.mkdir(exist_ok=True)
    (env/'pip-freeze.txt').write_text(subprocess.check_output([str(OUT/'.venv/bin/python'),'-m','pip','freeze','--all'],text=True))
    import importlib.metadata,gepa
    save(env/'official.json',dict(version=importlib.metadata.version('gepa'),commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=OUT/'official-src',text=True).strip(),source_diff=subprocess.check_output(['git','diff'],cwd=OUT/'official-src',text=True),installed=str(Path(gepa.__file__).parent),api='gepa.optimize / GEPAAdapter / EvaluationBatch / GEPAResult',installation='isolated venv, pip install full pinned official source checkout',production_dependencies_modified=False))
    rng=random.Random(SEED);first={c:rng.sample(['A','B'],2) for c in TEST};schedule=[]
    for rep in [1,2]:
        order=list(TEST);rng.shuffle(order)
        for c in order:
            for arm in first[c] if rep==1 else first[c][::-1]:schedule.append(dict(case=c,arm=arm,replicate=rep))
    protected=[REPO/s for s in subprocess.check_output(['git','ls-files'],cwd=REPO,text=True).splitlines() if (REPO/s).is_file()]
    for root in [r for r in (REPO/'research').iterdir() if r.is_dir() and r!=OUT and r.name.endswith(('20261105','20261106'))]+[Path(m['manifest']).parent for m in meta.values()]:protected += [f for f in root.rglob('*') if f.is_file() and '__pycache__' not in f.parts and '.git' not in f.parts]
    protected += [f for f in (OUT/'materials').rglob('*') if f.is_file()]+list(OUT.glob('*.py'))+list(OUT.glob('*.md'))+list(env.glob('*'))+[OUT/'split.json',OUT/'questions.snapshot.jsonl',OUT/'private-score-identifiers.json',OUT/'skill-banned-identifiers.json']
    protected += list(Path(gepa.__file__).parent.rglob('*.py'))
    p=dict(created_at=archive.now(),model=MODEL,effort='low',timeout=600,output_limit='unchanged original CLI defaults',gepa_config=dict(seed=SEED,commit=read(env/'official.json')['commit'],max_metric_calls=24,reflection_bottom_request_cap=6,cache_evaluation=False,use_merge=False),cases=meta,test_schedule=schedule,independent_generalization_cases=0,frozen_files={str(f):sha(f.read_bytes()) for f in sorted(set(protected))})
    save(OUT/'protocol.json',p);(OUT/'protocol.sha256').write_text(sha((OUT/'protocol.json').read_bytes())+'\n');print('FROZEN',len(protected))
if __name__=='__main__':prepare()
