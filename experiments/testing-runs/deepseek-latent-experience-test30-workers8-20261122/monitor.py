"""Monitor this run and save the four-arm comparison without publishing a paper."""
import csv,datetime,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
def read(p):return json.loads(p.read_text())
def write(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def collect():
    plan=read(ROOT/'plan.json');run=Path(plan['root']);meta=read(run/'lab.json');rows=read(run/'batch/progress.json');result=[]
    recoveries={};finished=meta['status']=='finished'
    for recovery in plan.get('recoveries',[]):
        rr=Path(recovery['root']);finished=finished and read(rr/'lab.json')['status']=='finished'
        for row in read(rr/'batch/progress.json'):recoveries[row['case_id']]=(row,recovery['id'])
    overrides=read(ROOT/'metric-overrides.json') if (ROOT/'metric-overrides.json').exists() else {}
    for row in rows:
        t=Path(row['root'])/'trajectory';s=read(t/'state.json');g=s.get('gold_result') or {};stages=s.get('stages',[])
        source_run=plan['id'];original_error=s.get('error');turns=sum(x.get('requests',0) for x in stages);credits=sum(x.get('credits') or 0 for x in stages)
        if row['case_id'] in recoveries:
            assert g.get('valid') is not True,'Never replace a valid original score'
            recovered,source_run=recoveries[row['case_id']];t=Path(recovered['root'])/'trajectory';s=read(t/'state.json');g=s.get('gold_result') or {};stages=s.get('stages',[])
            turns+=sum(x.get('requests',0) for x in stages);credits+=sum(x.get('credits') or 0 for x in stages)
        assert s.get('contract') is None and all(x['kind'] in ('action','gold') for x in stages),'Unexpected Contract or preparation model stage'
        value=int(g['passed']) if g.get('valid') is True and isinstance(g.get('passed'),bool) else None
        metric_policy=None
        if row['case_id'] in overrides:
            from hashlib import sha256
            override=overrides[row['case_id']]
            assert value is None and source_run==override['source_run']
            assert sha256((t/'stages/final-gold/raw-result.json').read_bytes()).hexdigest()==override['raw_gold_sha256']
            assert sha256((t/'attempts/1/diff.json').read_bytes()).hexdigest()==override['diff_sha256']
            value=override['passed'];metric_policy=override['reason']
        result.append(dict(case_id=row['case_id'],rank=row['rank'],source_run=source_run,status=s['status'],passed=value,error=s.get('error'),original_error=original_error,metric_policy=metric_policy,gold=g,model_turns=turns,credits=credits,stage_kinds=[x['kind'] for x in stages]))
    write(ROOT/'case-results.json',result)
    passed=sum(r['passed']==1 for r in result);failed=sum(r['passed']==0 for r in result);errors=[r for r in result if r['passed'] is None and r['status'] in ('execution_invalid','cancelled')]
    status=dict(at=now(),run=plan['id'],batch_status='finished' if finished else 'running',total=30,scored=passed+failed,passed=passed,failed=failed,execution_errors=len(errors),candidate_crashes_counted_failed=sum(r['metric_policy'] is not None for r in result),completed_model_turns=sum(r['model_turns'] for r in result),credits=sum(r['credits'] for r in result))
    write(ROOT/'monitor-status.json',status)
    if not finished:return False
    write(ROOT/'unresolved-errors.json',errors)
    if passed+failed!=30:
        status['status']='needs_inspection';write(ROOT/'monitor-status.json',status);print(json.dumps(status),flush=True);return True
    import numpy as np
    previous=list(csv.DictReader((REPO/'review-drafts/table1-deepseek-20261122/crash-as-failure/case-results.csv').open(encoding='utf-8-sig')))
    assert [r['case_id'] for r in previous]==[r['case_id'] for r in result]
    vectors={name:np.array([int(r[key]) for r in previous]) for name,key in [('latent','latent_passed'),('auto_contract','auto_contract_passed'),('auto_contract_experience','experience_passed')]}
    vectors['latent_experience']=np.array([r['passed'] for r in result])
    indices=list(csv.DictReader((REPO/'review-drafts/table1-deepseek-20261122/bootstrap_indices/bootstrap_indices_1000x30.csv').open(encoding='utf-8-sig')))
    samples=np.array([[int(r[f'draw_{i:03}']) for i in range(1,31)] for r in indices]);assert samples.shape==(1000,30)
    statistics={}
    for name,values in vectors.items():
        boot=values[samples].mean(axis=1)*100
        statistics[name]=dict(passed=int(values.sum()),total=30,raw_pass_rate=float(values.mean()*100),bootstrap_mean=float(boot.mean()),bootstrap_sd=float(boot.std(ddof=1)))
    candidate=vectors['latent_experience'];paired={}
    for name in ('latent','auto_contract_experience'):
        baseline=vectors[name];paired[name]=dict(newly_passed=int(((candidate==1)&(baseline==0)).sum()),regressed=int(((candidate==0)&(baseline==1)).sum()))
    summary=dict(run=plan['id'],arms=statistics,paired=paired,bootstrap=dict(replicates=1000,seed=20260925,sd_ddof=1),new_model_usage=dict(model_turns=status['completed_model_turns'],credits=status['credits']),historical_retrieval_reused=read(ROOT/'retrieval-provenance.json'),interpretation='Same fixed30, bank58 and exact per-case experience deliveries; no independent Auto-Contract. Historical selection costs are retained separately; only Action costs newly incurred. Single-run comparison, not a general model-level effect.')
    write(ROOT/'summary.json',summary)
    status['status']='complete';write(ROOT/'monitor-status.json',status);print(json.dumps(status),flush=True);return True
if __name__=='__main__':
    try:
        while not collect():time.sleep(15)
    except Exception as e:
        write(ROOT/'monitor-error.json',dict(at=now(),error=repr(e)));raise
