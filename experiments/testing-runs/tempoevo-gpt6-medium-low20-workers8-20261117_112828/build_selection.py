"""Lowest gpt-6-sol/medium original-L rates among non-trained exact IDs."""
import csv,json,hashlib
from pathlib import Path
OUT=Path(__file__).resolve().parent;REPO=OUT.parents[3];PARENT=REPO.parent
SOURCE=PARENT/'tempoevo-incremental100-workers4-20261117_011424-resume1'
HISTORY=PARENT/'tempoevo-swe-tempoc-history-20261116/swe242-per-case-model.csv'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,x):(OUT/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def main():
 split=json.loads((SOURCE/'split.json').read_text());prior=json.loads((OUT.parent/'composite-hard100-20261117/exposure-inventory.json').read_text());lineage=json.loads((SOURCE/'initial-lineage.json').read_text())
 train=set(split['training_case_ids'])|{r['case_id'] for r in prior['training']}|set(lineage['known_older_record_source_cases'])
 exposed_tests=set(split['testing_case_ids'])|{r['case_id'] for r in prior['testing']}
 roster={r['case_id']:r for r in json.loads((PARENT/'swe-tempoc/benchmark/swe-tempoc.json').read_text())['cases']}
 eligible=[r for r in csv.DictReader(HISTORY.open(encoding='utf-8-sig')) if r['model']=='gpt-6-sol' and r['effort']=='medium' and int(r['latent_valid'])>0 and r['case_id'] not in train]
 eligible.sort(key=lambda r:(int(r['latent_passes'])/int(r['latent_valid']),-int(r['latent_valid']),r['case_id']))
 chosen=eligible[:20];rows=[]
 for i,r in enumerate(chosen,1):
  cid=r['case_id'];meta=roster[cid];rows.append(dict(rank=i,split='testing',case_id=cid,core_case=meta['parent_case_id'],runtime=meta['runtime'],manifest=meta['manifest'],model='gpt-6-sol',effort='medium',latent_passes=int(r['latent_passes']),latent_valid=int(r['latent_valid']),latent_excluded=int(r['latent_excluded']),latent_pass_rate=int(r['latent_passes'])/int(r['latent_valid']),baseline_low_sample=int(r['latent_valid'])<3,prior_development_test=cid in exposed_tests,known_training_or_experience_source=False))
 assert len(rows)==len({r['case_id'] for r in rows})==20 and not {r['case_id'] for r in rows}&train
 with (OUT/'testing_20_cases.csv').open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 p=sum(r['latent_passes'] for r in rows);n=sum(r['latent_valid'] for r in rows)
 summary=dict(cases=20,model='gpt-6-sol',effort='medium',historical_passes=p,historical_valid_trials=n,pooled_pass_rate=p/n,macro_case_pass_rate=sum(r['latent_pass_rate'] for r in rows)/20,zero_pass_cases=sum(r['latent_passes']==0 for r in rows),at_most_half_cases=sum(r['latent_pass_rate']<=.5 for r in rows),low_sample_cases=sum(r['baseline_low_sample'] for r in rows),maximum_case_rate=max(r['latent_pass_rate'] for r in rows),prior_development_test_cases=sum(r['prior_development_test'] for r in rows),known_training_exact_overlap=0,independent_unseen=False,selection_uses_current_test_outcomes=False,tie_break='historical rate ascending, valid trials descending, case_id',exception='Only19 non-trained cases have historical L<=50%;20th is next-lowest2/3. Sixteen zero-pass cases,three1/3,one2/3.',source_files={str(p):sha(p) for p in [HISTORY,SOURCE/'split.json',SOURCE/'initial-lineage.json',Path(__file__)]})
 write('selection.json',summary)
 lines=['# GPT6 medium low-latent20 test','', '20 exact IDs excluding current70 training, bounded earlier training protocols and known historical experience source IDs. Rank only gpt-6-sol/medium original latent-maintenance valid-trial pass rates; do not use latest repair outcomes to select or break ties.','',f"Historical: {p}/{n} valid trials ({p/n:.2%}); per-case macro {summary['macro_case_pass_rate']:.2%}.16 zero-pass cases,3 at1/3,and1 at2/3. Only19 eligible non-trained cases are <=50%, so include the next-lowest2/3 case to reach20.5 cases have only1–2 valid trials. All20 have prior development test exposure; this is diagnostic retesting, not an unseen holdout.",'', 'Current approved memory is frozen; one Action24requests/600seconds,selection12,Contract12,total48; one final-only Gold; no A/B,diagnosis,extraction or test-time learning. Start8 workers,reduce future concurrency6 then4 only on explicit provider capacity errors. Never replay started requests/cases.','', '|#|core|case|Historical L|','|---:|---|---|---:|']
 lines += [f"|{r['rank']}|{r['core_case']}|{r['case_id']}|{r['latent_passes']}/{r['latent_valid']}|" for r in rows]
 (OUT/'README.md').write_text('\n'.join(lines)+'\n');print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
