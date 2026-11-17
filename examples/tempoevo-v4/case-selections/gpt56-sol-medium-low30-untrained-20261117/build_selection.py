"""Rank untrained exact IDs by GPT5.6medium original latent performance only."""
import csv,json,hashlib
from fractions import Fraction
from collections import defaultdict
from pathlib import Path
OUT=Path(__file__).resolve().parent;REPO=OUT.parents[3];BASE=REPO.parent

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def csvread(p):return list(csv.DictReader(p.open(encoding='utf-8-sig')))
def main():
    trainfile=OUT.parent/'incremental100-20261117/training_70_cases.csv';trained={r['case_id'] for r in csvread(trainfile)}
    inventory=OUT.parent/'composite-hard100-20261117/exposure-inventory.json';prior=read(inventory);trained|={r['case_id'] for r in prior['training']}
    lineage=BASE/'tempoevo-incremental100-workers4-20261117_011424-resume1/initial-lineage.json';trained|=set(read(lineage)['known_older_record_source_cases'])
    tested=set()
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
    history=BASE/'tempoevo-swe-tempoc-history-20261116/swe242-per-case-model.csv';baseline=csvread(history);profiles=defaultdict(dict)
    for r in baseline:
        if r['effort']=='medium':profiles[r['case_id']][r['model']]=r
    def secondary(cid):
        rows=[profiles[cid].get(m) for m in ('gpt-6-sol','gpt-6.1-sol')]
        if any(r is None or int(r['latent_valid'])==0 for r in rows):return Fraction(2)
        return sum(Fraction(int(r['latent_passes']),int(r['latent_valid'])) for r in rows)/2
    eligible=[r for r in baseline if r['model']=='gpt-5.6-sol' and r['effort']=='medium' and int(r['latent_valid'])>0 and r['case_id'] not in trained]
    eligible.sort(key=lambda r:(Fraction(int(r['latent_passes']),int(r['latent_valid'])),-int(r['latent_valid']),secondary(r['case_id']),r['case_id'] in tested,r['case_id']))
    # Lexical ID, not previous test outcomes, is the final deterministic tie break.
    chosen=eligible[:30];rows=[]
    for rank,r in enumerate(chosen,1):
        cid=r['case_id'];m=roster[cid];n=int(r['latent_valid']);p=int(r['latent_passes'])
        rows.append(dict(rank=rank,split='testing',case_id=cid,core_case=m['parent_case_id'],runtime=m['runtime'],manifest=m['manifest'],
            model='gpt-5.6-sol',effort='medium',latent_passes=p,latent_valid=n,latent_excluded=int(r['latent_excluded']),latent_pass_rate=p/n,
            supplementary_all_pass=p==n,other_models_mean_pass_rate=float(secondary(cid)) if secondary(cid)<=1 else None,
            prior_test_exposure=cid in tested,known_training_or_experience_source=False))
    assert len(rows)==len({r['case_id'] for r in rows})==30 and not set(r['case_id'] for r in rows)&trained
    with (OUT/'testing_30_cases.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
    result=dict(model='gpt-5.6-sol',effort='medium',cases=30,eligible_cases=len(eligible),excluded_training_source_ids=len(trained),exact_known_training_overlap=0,
        historical_passes=sum(r['latent_passes'] for r in rows),historical_valid_trials=sum(r['latent_valid'] for r in rows),
        macro_latent_pass_rate=sum(r['latent_pass_rate'] for r in rows)/30,zero_pass_cases=sum(r['latent_passes']==0 for r in rows),
        all_pass_supplement_cases=sum(r['supplementary_all_pass'] for r in rows),low_sample_cases=sum(r['latent_valid']<3 for r in rows),
        prior_test_exposure=sum(r['prior_test_exposure'] for r in rows),independent_holdout=False,
        primary_rank='Target-model original latent pass fraction ascending; valid trials descending.',
        supplementary_policy='Only25 untrained cases have observed GPT5.6medium failures. Fill5 target-model1/1 ties with lowest mean GPT6medium/GPT6.1medium original latent pass rates, requiring both valid; missing is not failure.',
        tie_break='Secondary two-model mean; prefer not previously tested within exact ties; exact case ID.',
        uses_current_repair_outcomes=False,exposure_scope='Current70 plus known historical sources and bounded sibling run startedness metadata.',
        source_hashes={str(p):sha(p) for p in (trainfile,inventory,lineage,rosterfile,history,Path(__file__))})
    (OUT/'selection.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    (OUT/'excluded-training-and-experience-sources.json').write_text(json.dumps(sorted(trained),indent=2)+'\n')
    lines=['# GPT5.6 sol medium：未训练低通过率30例','', '排除当前70训练和全部已知历史训练/经验来源ID，按目标模型原始Latent有效试次排名。只有25例0/1，其余均1/1；为满足30例，用GPT6/GPT6.1原始基线难度打破全通过候选的并列，补5例并明确标记。全组历史5/30通过（16.7%），全部仅一次有效基线，不能把0/1当作真实失败概率的可靠估计。已有测试暴露只作披露，不以带经验结果选题。','', '|#|case|core|原Latent|补充项|历史测试暴露|','|---:|---|---|---:|---|---|']
    lines += [f"|{r['rank']}|{r['case_id']}|{r['core_case']}|{r['latent_passes']}/{r['latent_valid']}|{r['supplementary_all_pass']}|{r['prior_test_exposure']}|" for r in rows]
    (OUT/'README.md').write_text('\n'.join(lines)+'\n');print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
