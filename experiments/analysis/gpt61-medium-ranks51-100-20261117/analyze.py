"""Baseline-only ranking and public run-metadata exposure audit; no model calls."""
import csv,json,hashlib
from pathlib import Path
from fractions import Fraction
from collections import Counter,defaultdict
OUT=Path(__file__).resolve().parent
REPO=OUT.parents[2];PARENT=REPO.parent
HISTORY=PARENT/'tempoevo-swe-tempoc-history-20261116/swe242-per-case-model.csv'
ROSTER=PARENT/'swe-tempoc/benchmark/swe-tempoc.json'
TRAIN=REPO/'examples/tempoevo-v4/case-selections/incremental100-20261117/training_70_cases.csv'
def read(p):return json.loads(p.read_text())
def csvread(p):return list(csv.DictReader(p.open(encoding='utf-8-sig')))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    roster={r['case_id']:r for r in read(ROSTER)['cases']}
    train=csvread(TRAIN);trainids={r['case_id'] for r in train};traincores={r['core_case'] for r in train}
    ranks=[r for r in csvread(HISTORY) if r['model']=='gpt-6.1-sol' and r['effort']=='medium' and int(r['latent_valid'])>0]
    ranks.sort(key=lambda r:(Fraction(int(r['latent_passes']),int(r['latent_valid'])),-int(r['latent_valid']),r['case_id']))
    exposures=defaultdict(list);seen=set()
    old=read(REPO/'examples/tempoevo-v4/case-selections/composite-hard100-20261117/exposure-inventory.json')
    protocols={Path(r['protocol']) for kind in ('training','testing') for r in old[kind]}
    for root in PARENT.glob('tempoevo-*'):
        if root.is_dir():
            for pattern in ('*/trajectory/protocol.json','*/*/trajectory/protocol.json','*/*/*/trajectory/protocol.json','trajectory/protocol.json'):
                protocols.update(root.glob(pattern))
    for p in sorted(protocols):
        if not p.exists():continue
        q=read(p);sp=p.parent/'state.json'
        if not sp.exists():continue
        s=read(sp);cid=q.get('task_id') or q.get('public_case_record',{}).get('id')
        if cid not in roster:continue
        started=bool(s.get('stages') or s.get('attempts'))
        if not started:continue
        scored=q.get('mode')=='testing' and s.get('status')=='scored' and s.get('gold_result') is not None
        exposures[cid].append(dict(protocol=str(p),mode=q.get('mode'),status=s.get('status'),scored=scored))
    rows=[]
    for rank,r in enumerate(ranks[50:100],51):
        cid=r['case_id'];meta=roster[cid];runs=exposures[cid]
        rows.append(dict(rank=rank,case_id=cid,core_case=meta['parent_case_id'],source_unit=meta['source_unit'],
            latent_passes=int(r['latent_passes']),latent_failures=int(r['latent_failures']),latent_valid=int(r['latent_valid']),
            latent_failure_rate=int(r['latent_failures'])/int(r['latent_valid']),
            current_train70=cid in trainids,train70_core_covered=meta['parent_case_id'] in traincores,
            testing_started=any(x['mode']=='testing' for x in runs),testing_scored=any(x['scored'] for x in runs),
            training_started=any(x['mode']=='learning' for x in runs)))
    assert len(trainids)==70 and len(rows)==50 and len({r['case_id'] for r in rows})==50
    assert all(r['latent_passes']+r['latent_failures']==r['latent_valid'] for r in rows)
    groups=[]
    for core in sorted({r['core_case'] for r in rows}):
        rr=[r for r in rows if r['core_case']==core]
        groups.append(dict(core_case=core,cases=len(rr),train70_count=sum(r['core_case']==core for r in train),
            tested=sum(r['testing_scored'] for r in rr),untested=sum(not r['testing_scored'] for r in rr),
            already_train70=sum(r['current_train70'] for r in rr)))
    summary=dict(model='gpt-6.1-sol',effort='medium',rank_metric='original latent valid-trial failure rate descending',
        tie_break='valid trials descending, case_id ascending',eligible_cases=len(ranks),cases_with_observed_failure=sum(int(r['latent_failures'])>0 for r in ranks),
        selected_ranks=[51,100],cases=len(rows),pooled_failures=sum(r['latent_failures'] for r in rows),
        pooled_valid=sum(r['latent_valid'] for r in rows),low_sample_cases=sum(r['latent_valid']<3 for r in rows),
        baseline_count_distribution=dict(Counter(str(r['latent_valid']) for r in rows)),
        testing_scored=sum(r['testing_scored'] for r in rows),not_testing_scored=sum(not r['testing_scored'] for r in rows),
        testing_started=sum(r['testing_started'] for r in rows),already_train70=sum(r['current_train70'] for r in rows),
        training_started=sum(r['training_started'] for r in rows),
        never_train_or_test_started=sum(not r['testing_started'] and not r['training_started'] for r in rows),
        cores=len(groups),covered_cores=sum(g['train70_count']>0 for g in groups),covered_cases=sum(r['train70_core_covered'] for r in rows),
        untested_not_train70=sum(not r['testing_scored'] and not r['current_train70'] for r in rows),
        scope='Sibling tempoevo run protocol/state metadata plus prior bounded exposure inventory; baseline evaluation is separate from experience-pipeline testing.',
        ranking_warning='All selected cases tie at zero observed latent failures; positions within this tier are bookkeeping, not evidence of difficulty differences.',
        source_hashes={str(p):sha(p) for p in (HISTORY,ROSTER,TRAIN)})
    for name,data in [('cases.csv',rows),('cores.csv',groups)]:
        with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
    (OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    (OUT/'exposure-evidence.json').write_text(json.dumps({r['case_id']:exposures[r['case_id']] for r in rows},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(summary,ensure_ascii=False,indent=2));print(json.dumps(groups,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
