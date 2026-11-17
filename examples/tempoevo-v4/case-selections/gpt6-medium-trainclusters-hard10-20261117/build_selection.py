"""Baseline-ranked same-core transfer selection; no use of current repair outcomes."""
import csv,json,hashlib
from pathlib import Path
from fractions import Fraction
OUT=Path(__file__).resolve().parent;REPO=OUT.parents[3];BASE=REPO.parent

def read(p):return json.loads(p.read_text())
def csvread(p):return list(csv.DictReader(p.open(encoding='utf-8-sig')))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    trainfile=OUT.parent/'incremental100-20261117/training_70_cases.csv';trainrows=csvread(trainfile)
    cores={r['core_case'] for r in trainrows};trained={r['case_id'] for r in trainrows}
    inventory=OUT.parent/'composite-hard100-20261117/exposure-inventory.json';prior=read(inventory)
    trained|={r['case_id'] for r in prior['training']}
    lineage=BASE/'tempoevo-incremental100-workers4-20261117_011424-resume1/initial-lineage.json'
    trained|=set(read(lineage)['known_older_record_source_cases']);tested={r['case_id'] for r in prior['testing'] if r.get('started')}
    # Examine only public run metadata/startedness, not prior test verdicts.
    for root in BASE.glob('tempoevo-*'):
        if not root.is_dir():continue
        for pattern in ('*/trajectory/protocol.json','*/*/trajectory/protocol.json','*/*/*/trajectory/protocol.json'):
            for p in root.glob(pattern):
                sp=p.parent/'state.json'
                if not sp.exists():continue
                q=read(p);s=read(sp)
                if not s.get('stages') and not s.get('attempts'):continue
                cid=q.get('task_id') or q.get('public_case_record',{}).get('id')
                if not cid:continue
                if q.get('mode')=='learning':trained.add(cid)
                if q.get('mode')=='testing':tested.add(cid)
    rosterfile=BASE/'swe-tempoc/benchmark/swe-tempoc.json';roster={r['case_id']:r for r in read(rosterfile)['cases']}
    history=BASE/'tempoevo-swe-tempoc-history-20261116/swe242-per-case-model.csv'
    eligible=[r for r in csvread(history) if r['model']=='gpt-6-sol' and r['effort']=='medium' and int(r['latent_valid'])>0 and r['case_id'] not in trained and roster[r['case_id']]['parent_case_id'] in cores]
    eligible.sort(key=lambda r:(Fraction(int(r['latent_passes']),int(r['latent_valid'])),-int(r['latent_valid']),r['case_id'] in tested,r['case_id']))
    rows=[]
    for rank,r in enumerate(eligible[:10],1):
        cid=r['case_id'];m=roster[cid]
        rows.append(dict(rank=rank,split='testing',case_id=cid,core_case=m['parent_case_id'],runtime=m['runtime'],manifest=m['manifest'],
            model='gpt-6-sol',effort='medium',latent_passes=int(r['latent_passes']),latent_valid=int(r['latent_valid']),latent_excluded=int(r['latent_excluded']),
            historical_failure_rate=1-int(r['latent_passes'])/int(r['latent_valid']),training_core_examples=sum(x['core_case']==m['parent_case_id'] for x in trainrows),
            known_training_or_experience_source=False,prior_test_exposure=cid in tested))
    assert len(rows)==10 and len({r['case_id'] for r in rows})==10
    assert all(r['training_core_examples']>0 and r['case_id'] not in trained for r in rows)
    with (OUT/'testing_10_cases.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
    summary=dict(cases=10,cores=len({r['core_case'] for r in rows}),model='gpt-6-sol',effort='medium',eligible_cases=len(eligible),
        historical_passes=sum(r['latent_passes'] for r in rows),historical_valid_trials=sum(r['latent_valid'] for r in rows),
        macro_failure_rate=sum(r['historical_failure_rate'] for r in rows)/10,prior_test_exposure=sum(r['prior_test_exposure'] for r in rows),
        exact_training_overlap=0,training_core_coverage=10,independent_holdout=False,
        tie_break='Latent pass fraction ascending; valid sample count descending; untested first within exact ties; case_id.',
        outcome_selection='Only frozen original baseline. Current experience-assisted repair success/failure never used.',
        exposure_scope='Current70, known historical experience sources, bounded sibling run protocol/state metadata; not a globally exhaustive exposure proof.',
        source_hashes={str(p):sha(p) for p in (trainfile,inventory,lineage,rosterfile,history,Path(__file__))})
    (OUT/'selection.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    (OUT/'excluded-training-and-experience-sources.json').write_text(json.dumps(sorted(trained),indent=2)+'\n')
    lines=['# GPT6 medium：训练同cluster最难10例','', '按训练70的parent_case_id/core匹配；排除已知训练及经验来源的精确ID，再按GPT6 medium原始Latent失败率排名。未知/无效基线不算失败。所有10例均0/3通过，分布在6个训练core；均有历史开发测试暴露。本轮使用最新61条经验，是历史复测，非独立holdout。','', '|#|case|core|训练同core数量|原Latent通过|','|---:|---|---|---:|---:|']
    lines += [f"|{r['rank']}|{r['case_id']}|{r['core_case']}|{r['training_core_examples']}|{r['latent_passes']}/{r['latent_valid']}|" for r in rows]
    (OUT/'README.md').write_text('\n'.join(lines)+'\n');print(json.dumps(summary,ensure_ascii=False))
if __name__=='__main__':main()
