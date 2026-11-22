"""Reproduce Table 1 cells using the requested paired bootstrap index generator."""
import csv,hashlib,json,statistics,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
REPO=next(p for p in HERE.parents if (p/'tools/generate_bootstrap_indices.py').exists())
RUN=HERE.parent

def read(p):return json.loads(p.read_text())
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,value):p.write_text(json.dumps(value,indent=2)+'\n')
completion=read(RUN/'completion.json');parents=read(RUN/'parent-results.json')
order=list(csv.DictReader((REPO/'cases/test30.csv').open(encoding='utf-8-sig')))
new={r['case_id']:r for r in completion['cases']};old={r['case_id']:r for r in parents}
assert len(order)==30 and set(new)==set(old)=={r['case_id'] for r in order}
assert completion['passed']==22 and completion['failed']==7 and completion['unscored']==1
rows=[]
for row in order:
    cid=row['case_id'];r=new[cid]
    passed=r['gold_passed'] if r['status']=='scored' and type(r['gold_passed']) is bool else None
    rows.append(dict(rank=row['rank'],case_id=cid,scored_flag=int(passed is not None),latent_experience_passed='' if passed is None else int(passed),auto_contract_experience_passed=int(old[cid]['gold_passed']),status=r['status']))
reference=HERE/'case-results.csv'
with reference.open('w',encoding='utf-8-sig',newline='') as out:
    writer=csv.DictWriter(out,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
command=[sys.executable,'-B',str(REPO/'tools/generate_bootstrap_indices.py'),'--reference',str(reference),'--label-column','scored_flag','--output-dir',str(HERE/'bootstrap_indices'),'--n-bootstrap','1000','--seed','20260925']
subprocess.run(command,cwd=REPO,check=True)
index_file=HERE/'bootstrap_indices/bootstrap_indices_1000x30.csv'
with index_file.open(encoding='utf-8-sig',newline='') as handle:
    indexes=[[int(row['draw_%03d'%i]) for i in range(1,31)] for row in csv.DictReader(handle)]
assert len(indexes)==1000 and all(len(r)==30 for r in indexes)
arms={};replicates=[]
for name,column in [('latent_experience','latent_experience_passed'),('auto_contract_experience','auto_contract_experience_passed')]:
    outcomes=[None if r[column]=='' else int(r[column]) for r in rows]
    valid=[v for v in outcomes if v is not None];values=[];sizes=[]
    for draw in indexes:
        sampled=[outcomes[i] for i in draw if outcomes[i] is not None]
        assert sampled,'Empty valid bootstrap replicate; cannot impute a score'
        values.append(100*sum(sampled)/len(sampled));sizes.append(len(sampled))
    arms[name]=dict(passed=sum(valid),valid_cases=len(valid),total_cases=30,unscored_cases=30-len(valid),raw_pass_rate=100*sum(valid)/len(valid),bootstrap_mean=statistics.mean(values),bootstrap_sd=statistics.stdev(values),minimum_valid_draws=min(sizes),maximum_valid_draws=max(sizes),table_cell='%.2f $\\pm$ %.2f'%(statistics.mean(values),statistics.stdev(values)))
    for i,(value,n) in enumerate(zip(values,sizes)):
        if len(replicates)<=i:replicates.append(dict(replicate=i+1))
        replicates[i][name+'_accuracy']=value;replicates[i][name+'_valid_draws']=n
with (HERE/'replicates.csv').open('w',encoding='utf-8-sig',newline='') as out:
    writer=csv.DictWriter(out,fieldnames=list(replicates[0]));writer.writeheader();writer.writerows(replicates)
summary=dict(model='gpt-5.6-sol',reasoning_effort='medium',arms=arms,bootstrap=dict(generator='tools/generate_bootstrap_indices.py',generator_sha256=digest(REPO/'tools/generate_bootstrap_indices.py'),seed=20260925,n_bootstrap=1000,n_source_cases=30,draws_per_replicate=30,index_base=0,sd_ddof=1,index_file_sha256=digest(index_file),reference_sha256=digest(reference),missing_policy='Use the same 30-case index draw for both arms. Exclude unscored outcomes from each replicate denominator; never impute failures. scored_flag is a coverage indicator, not an outcome or ground-truth label.'),raw_inputs={name:digest(RUN/name) for name in ['completion.json','parent-results.json']},memory=dict(entries=61,frozen_delivery_replay=True),overleaf_project='https://www.overleaf.com/project/6aeb6a27e6c2f33263179d63',overleaf_status='not_synced_authentication_required')
write(HERE/'summary.json',summary)
a=arms['latent_experience'];(HERE/'cell.tex').write_text('%% GPT-5.6-sol medium, Latent + Experience only; 22/29 valid, one unscored.\n%% Bootstrap: 1,000 draws over the fixed30, seed20260925, sample SD (ddof=1).\n%% Unscored outcomes excluded within each draw; not counted as failures.\n$%.2f \\pm %.2f$\n'%(a['bootstrap_mean'],a['bootstrap_sd']))
lines=['# Table 1 update: GPT-5.6-sol medium','', '| Condition | Raw valid pass rate | Bootstrap mean ± SD (%) | Coverage |','|---|---:|---:|---:|']
for name,label in [('auto_contract_experience','Auto-Contract + Experience (historical)'),('latent_experience','Latent + Experience only (new)')]:
    a=arms[name];lines.append('| '+label+' | %.1f%% (%d/%d) | %.2f ± %.2f | %d/30 |'%(a['raw_pass_rate'],a['passed'],a['valid_cases'],a['bootstrap_mean'],a['bootstrap_sd'],a['valid_cases']))
lines+=['','Use `cell.tex` for the new Table 1 cell. These values are the mean and sample SD of bootstrap accuracy, not raw accuracy plus a confidence interval.','', 'Method: the requested tools/generate_bootstrap_indices.py, 1,000 paired draws of 30 case indices with replacement, random.Random seed20260925. Both conditions use identical draws. Unscored outcomes are excluded from each replicate denominator; the scored_flag input column records coverage and is not a ground-truth label. One case is unscored for the new arm, so effective bootstrap denominators vary.','', 'Required table note: "Execution-invalid cases are excluded from the accuracy denominator, including within bootstrap resamples; the GPT-5.6 Latent + Experience arm has 29/30 valid cases. Entries report bootstrap mean ± sample SD over 1,000 shared case resamples (seed 20260925)."','', 'The 61-entry library and historical per-case experience deliveries were frozen. The source/runtime differences from the historical parent are disclosed in the run README.','', 'Overleaf has not been modified: Git authentication is unavailable and there is no connected document session. The exact existing Table 1 source is still required to preserve its structure and notes.','', 'Reproduce from any checkout containing this archive:','', '```sh','python3 -B '+str(HERE.relative_to(REPO)/'build.py'),'```','']
(HERE/'README.md').write_text('\n'.join(lines))
print(json.dumps(arms,indent=2))
