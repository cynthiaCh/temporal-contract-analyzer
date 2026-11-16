"""Freeze authorized incremental70 + new20 + retained regression10, no model calls."""
import csv,hashlib,json,datetime,shutil
from pathlib import Path
from collections import defaultdict
OUT=Path(__file__).resolve().parent;REPO=OUT.parents[3];PARENT=REPO.parent
BASE=OUT.parent/'composite-hard100-20261117'
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def csvwrite(p,rows):
 with p.open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
 roster={x['case_id']:x for x in json.loads((PARENT/'swe-tempoc/benchmark/swe-tempoc.json').read_text())['cases']}
 historical=json.loads((BASE/'exposure-inventory.json').read_text());known=json.loads((OUT.parent/'training-conditioned-provisional25-20261115/provenance-audit.json').read_text())['known_experience_source_cases']
 exposed={r['case_id'] for kind in ['training','testing'] for r in historical[kind]}|set(known)
 oldroot=PARENT/'tempoevo-business-full39-test10-workers4-20261117_001331';previous=json.loads((oldroot/'completion.json').read_text());old10={r['case_id'] for r in previous['cases']};assert len(old10)==10 and previous['passed']==8
 selected=list(csv.DictReader((BASE/'selected_100_cases.csv').open(encoding='utf-8-sig')));missing=old10-{x['case_id'] for x in selected}
 for cid in sorted(missing):
  meta=roster[cid];selected.append(dict(selected[0],case_id=cid,core_case=meta['parent_case_id'],source_unit=meta['source_unit'],role=meta['role'],runtime=meta['runtime'],manifest=meta['manifest'],composite_pass_rate='unavailable_in_both_profile_ranking'))
 removed=[]
 while len(selected)>100:
  victim=next(x for x in reversed(selected[:100]) if x['case_id'] not in old10);selected.remove(victim);removed.append(victim['case_id'])
 groups=defaultdict(list)
 for x in selected:groups[x['core_case']].append(x['case_id'])
 fresh=[x for x in selected if x['case_id'] not in exposed];assert len(fresh)>=20
 # Fill same-core test quotas while retaining a training counterpart for every test.
 tests=set(old10)
 for _ in range(20):
  allowed=[x for x in fresh if x['case_id'] not in tests and len(set(groups[x['core_case']])-tests)>1]
  chosen=min(allowed,key=lambda x:(-(.3*len(groups[x['core_case']])-len(set(groups[x['core_case']])&tests)),hashlib.sha256(('incremental100-v1|'+x['case_id']).encode()).hexdigest()));tests.add(chosen['case_id'])
 assert len(tests)==30 and not (tests-old10)&exposed
 rows=[]
 for i,x in enumerate(selected,1):
  cid=x['case_id'];meta=roster[cid]
  rows.append(dict(rank=i,case_id=cid,split='testing' if cid in tests else 'training',core_case=meta['parent_case_id'],source_unit=meta['source_unit'],runtime=meta['runtime'],manifest=meta['manifest'],cohort='retained_regression10' if cid in old10 else 'new_test20' if cid in tests else 'train70',composite_pass_rate=x['composite_pass_rate'],historical_exposure=cid in exposed))
 csvwrite(OUT/'selected_100_cases.csv',rows)
 for name,subset in [('training_70_cases.csv',[x for x in rows if x['split']=='training']),('testing_new20_cases.csv',[x for x in rows if x['cohort']=='new_test20']),('testing_retained10_cases.csv',[x for x in rows if x['cohort']=='retained_regression10'])]:csvwrite(OUT/name,[dict(x,rank=i) for i,x in enumerate(subset,1)])
 train={r['case_id'] for r in rows if r['split']=='training'}
 assert len(train)==70 and not train&tests and all(set(groups[roster[c]['parent_case_id']])&train for c in tests)
 split=dict(schema_version='tempoevo-incremental-split-v1',selection_file=str((OUT/'selected_100_cases.csv').relative_to(REPO)),selection_sha256=sha(OUT/'selected_100_cases.csv'),training_case_ids=sorted(train),testing_case_ids=sorted(tests),independence=dict(unseen=False,new20='no detected prior development exposure in bounded audit',retained10='previously exposed regression cohort'),testing_policy=dict(actions=1,gold='final_only',learning=False))
 dump(OUT/'split.json',split)
 # Accepted V8-semantic runs may be reused as historical training, not rescored.
 matches={};rejected={}
 for base in [PARENT/'tempoevo-v8-online-top25-20261114_202942',PARENT/'tempoevo-v8-compatible-train10-20261116_172034/batch-v2']:
  for p in base.glob('*/trajectory/protocol.json'):
   protocol=json.loads(p.read_text());cid=protocol.get('task_id')
   if cid not in train:continue
   state=json.loads((p.parent/'state.json').read_text());model=protocol.get('model')
   if model!=dict(model='gpt-6.1-sol',reasoning_effort='medium') or protocol.get('max_attempts')!=3 or protocol.get('acceptance_policy')!='training_gold_and_required_visible' or state.get('training_accepted') is not True:
    rejected[cid]='not accepted under equivalent V8 model/three-action/dual-evaluator semantics';continue
   from temporal_contract_analyzer.swe_tempoc_inputs import case_input
   from temporal_contract_analyzer.tempoevo_v4 import capture,inventory
   current=case_input(cid,PARENT/'swe-tempoc');a,_=capture(current['candidate']);b,_=capture(p.parent/'original');b.pop('VISIBLE_CHECKS.md',None)
   if a!=b or current['task']!=protocol['task']:rejected[cid]='original public source or task changed';continue
   attempts=state['attempts']
   if not attempts:continue
   stages=state['stages']
   if any(z.get('status')!='complete' for z in stages) or any(type(z.get('requests')) is not int for z in stages):rejected[cid]='incomplete stages/usage';continue
   binding=json.loads((p.parent/'binding.json').read_text())
   if sha(p)!=binding['protocol']:raise ValueError('Historical protocol drift')
   for attempt in attempts:
    candidate=p.parent/'attempts'/str(attempt['number'])/'candidate'
    assert inventory(capture(candidate)[0])==attempt['candidate_inventory']
   matches[cid]=dict(case_id=cid,root=str(p.parent),protocol_sha256=sha(p),state_sha256=sha(p.parent/'state.json'),status=state['status'],accepted=True,attempts=len(attempts),semantics='historical V8-equivalent accepted run; original public task/source exact match; current39 seed differs',training_recipe=protocol.get('training_recipe'))
 pending=[r for r in rows if r['split']=='training' and r['case_id'] not in matches]
 csvwrite(OUT/'training_to_run.csv',[dict(r,rank=i) for i,r in enumerate(pending,1)])
 dump(OUT/'reuse.json',dict(reused=list(matches.values()),reuse_count=len(matches),to_run=len(pending),non_reused_reasons=rejected,policy='reuse accepted V8-semantic model+source-matched training; historical scores/roots unchanged; exclude unfinished and exhausted cases'))
 dump(OUT/'plan.json',dict(status='frozen_not_started',train=70,reuse=len(matches),train_to_run=len(pending),new_test=20,retained_test=10,retained_passed=8,retained_root=str(oldroot),workers=4,model='gpt-6.1-sol',reasoning_effort='medium',training_recipe='v8-compatible-v1',training_seed='current39 approved historical guidance',review_authority='user explicitly authorizes automatic acceptance of subsequent new experiences as Silas',review_type='user_authorized_automatic_acceptance_not_independent_human_review',test_policy='train then approve/freeze then new20; retain original8/10 unchanged; aggregate is mixed-time/mixed-bank diagnostic result',strict_global_hardest100=False,forced_retained10_added=sorted(missing),replaced_rank100_cases=removed,initial_approved39_lineage=str(BASE/'history-audit.json')))
 print(json.dumps(dict(train=70,reused=len(matches),to_run=len(pending),new20=20,retained10=10,mandatory_added=len(missing))))
if __name__=='__main__':
 import sys;sys.path.insert(0,str(REPO));main()
