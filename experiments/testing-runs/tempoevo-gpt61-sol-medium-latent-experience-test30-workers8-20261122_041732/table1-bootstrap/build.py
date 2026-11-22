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
assert completion['passed']==23 and completion['failed']==7 and completion['unscored']==0
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
summary=dict(model='gpt-6.1-sol',reasoning_effort='medium',arms=arms,bootstrap=dict(generator='tools/generate_bootstrap_indices.py',generator_sha256=digest(REPO/'tools/generate_bootstrap_indices.py'),seed=20260925,n_bootstrap=1000,n_source_cases=30,draws_per_replicate=30,index_base=0,sd_ddof=1,index_file_sha256=digest(index_file),reference_sha256=digest(reference),missing_policy='Use the same 30-case index draw for both arms. Exclude unscored outcomes from each replicate denominator; never impute failures. scored_flag is a coverage indicator, not an outcome or ground-truth label.'),raw_inputs={name:digest(RUN/name) for name in ['completion.json','parent-results.json']},memory=dict(entries=61,frozen_delivery_replay=True),overleaf_project='https://www.overleaf.com/project/6aeb6a27e6c2f33263179d63',overleaf_status='not_synced_authentication_required')
a=arms['latent_experience']
summary['overleaf_display_cell']='%.1f ± %.1f'%(a['bootstrap_mean'],a['bootstrap_sd'])
summary['overleaf_status']='updated_and_source_readback_verified' if (HERE/'overleaf-sync/readback-verification.json').exists() else 'pending_upload'
write(HERE/'summary.json',summary)
(HERE/'cell.tex').write_text('%% GPT-6.1-sol medium; 23/30 valid; 1000 paired bootstrap draws, seed20260925, sample SD.\n$%.1f \\pm %.1f$\n'%(a['bootstrap_mean'],a['bootstrap_sd']))
readme=f"""# Table 1: GPT-6.1-sol medium, Latent + Experience only

Raw:23/30=76.7%, no unscored cases. Bootstrap mean ± sample SD: {a['bootstrap_mean']:.4f} ± {a['bootstrap_sd']:.4f}%; displayed cell: {a['bootstrap_mean']:.1f} ± {a['bootstrap_sd']:.1f}%.

Generated with tools/generate_bootstrap_indices.py, 1000 paired draws of30 fixed cases, seed20260925, sample SD(ddof=1). The index matrix exactly matches the preceding GPT-5.6 Latent+Experience bootstrap. The coverage column is not ground truth. Historical Auto-Contract+Experience is recomputed for reference only; its existing Table1 cell is preserved. Frozen61 bank, no new selector/Contract calls or experience updates. Runtime differences from historical parent are disclosed in the experiment README.

Overleaf verification and exact one-cell patch are in overleaf-sync/. Reproduce with python3 -B {HERE.relative_to(REPO)/'build.py'}
"""
(HERE/'README.md').write_text(readme)
print(json.dumps(arms,indent=2))
