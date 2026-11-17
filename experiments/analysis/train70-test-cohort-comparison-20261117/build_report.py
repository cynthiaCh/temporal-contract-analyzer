"""Historical descriptive comparison; no models, scorers, or memory writes."""
import csv,json,hashlib
from pathlib import Path
from collections import Counter
OUT=Path(__file__).resolve().parent;REPO=OUT.parents[2];BASE=REPO.parent
RATES=REPO/'experiments/incremental-runs/tempoevo-incremental100-workers4-20261117_011424-resume1/rates/per-case.csv'
HISTORY=BASE/'tempoevo-swe-tempoc-history-20261116/swe242-per-case-model.csv'
LATEST=REPO/'experiments/testing-runs/tempoevo-sol61-medium-ranks26-46-workers8-20261117_155257/completion.json'
AUTO_TEST=BASE/'tempoevo-v11-noexperience-autocontract-test26-50-20261115'
AUTO_TRAIN=BASE/'tempoevo-v7-autocontract-noexperience-top25-20261113_232348'
def read(p):return json.loads(p.read_text())
def csvread(p):return list(csv.DictReader(p.open(encoding='utf-8-sig')))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def trajectory(root,cid):
    for p in (root,root/'batch'/cid/'trajectory',root/cid/'trajectory'):
        if (p/'protocol.json').is_file() and (p/'state.json').is_file():return p
    raise ValueError('Missing trajectory: '+str(root)+' '+cid)
def auto(root,cid,mode):
    path=root/cid/'trajectory'
    if not path.exists():return None
    q=read(path/'protocol.json');s=read(path/'state.json')
    assert q['condition']=='contract' and not q['memory_snapshot']['entries'] and q['mode']==mode
    assert q['model']==dict(model='gpt-6.1-sol',reasoning_effort='medium')
    if mode=='testing':
        assert q['max_attempts']==1 and q['limits']['action']['requests']==24
        gold=s.get('gold_result') or {};valid=s['status']=='scored' and gold.get('valid') is True
        return dict(path=str(path),valid=valid,passed=gold.get('passed') if valid else None,first_passed=gold.get('passed') if valid else None,status=s['status'])
    gold=s.get('final_acceptance') or {};valid=gold.get('valid') is True
    return dict(path=str(path),valid=valid,passed=gold.get('passed') if valid else None,
        first_passed=s['attempts'][0].get('acceptance_passed') if s['attempts'] else None,status=s['status'])
def aggregate(rows):
    x={}
    for field in ('latent','provided_contract'):
        valid=[r for r in rows if r[field+'_valid']>0];n=sum(r[field+'_valid'] for r in rows);p=sum(r[field+'_passes'] for r in rows)
        x[field]=dict(covered=len(valid),total=len(rows),passes=p,valid_trials=n,
            excluded=sum(r[field+'_excluded'] for r in rows),macro_rate=sum(r[field+'_passes']/r[field+'_valid'] for r in valid)/len(valid) if valid else None,
            pooled_rate=p/n if n else None)
    for key in ('auto_test','auto_train'):
        valid=[r[key] for r in rows if r[key] and r[key]['valid']]
        x[key]=dict(recorded=sum(bool(r[key]) for r in rows),valid_cases=len(valid),passed=sum(r['passed'] is True for r in valid),
            first_passed=sum(r['first_passed'] is True for r in valid),rate=sum(r['passed'] is True for r in valid)/len(valid) if valid else None)
    x['with_experience']=dict(cases=len(rows),passed=sum(r['with_experience_passed'] for r in rows),
        first_passed=sum(r['with_experience_first_passed'] for r in rows),rate=sum(r['with_experience_passed'] for r in rows)/len(rows),
        max_actions=max(r['max_actions'] for r in rows))
    return x

def main():
    raw=csvread(RATES);hist={r['case_id']:r for r in csvread(HISTORY) if r['model']=='gpt-6.1-sol' and r['effort']=='medium'}
    inputs={str(p):sha(p) for p in (RATES,HISTORY,LATEST)}
    cohorts={key:[] for key in ('train70','new_test20','retained_regression10','latest_retest21')}
    specs=[(r['cohort'],r['case_id'],Path(r['score_root']),r) for r in raw]
    latest=read(LATEST)
    specs += [('latest_retest21',r['case_id'],Path('../tempoevo-sol61-medium-ranks26-46-workers8-20261117_155257').resolve(),None) for r in latest['cases']]
    evidence=[]
    for cohort,cid,root,prior in specs:
        p=trajectory(root,cid);q=read(p/'protocol.json');s=read(p/'state.json')
        assert q['model']==dict(model='gpt-6.1-sol',reasoning_effort='medium')
        if cohort=='train70':
            accepted=s.get('training_accepted') is True
            # Some retained V8 summaries predate training_accepted but carry exact final PASS.
            if prior:assert accepted==(prior['current_passed']=='True')
            first=s['attempts'][0].get('acceptance_passed') is True
        else:
            gold=s.get('gold_result') or {};assert s['status']=='scored' and gold.get('valid') is True
            accepted=gold['passed'];first=accepted;assert q['max_attempts']==1
        if prior:
            assert accepted==(prior['current_passed']=='True')
            assert first==(prior['first_action_passed']=='True')
        row=dict(cohort=cohort,case_id=cid,with_experience_passed=accepted,with_experience_first_passed=first,max_actions=q['max_attempts'],
            experience_bank_entries=len(q['memory_snapshot']['entries']),score_root=str(p),auto_test=auto(AUTO_TEST,cid,'testing'),auto_train=auto(AUTO_TRAIN,cid,'learning'))
        h=hist.get(cid,{})
        for field,key in [('latent','latent'),('provided_contract','contract')]:
            for suffix in ('passes','valid','excluded'):row[field+'_'+suffix]=int(h.get(key+'_'+suffix) or 0)
        cohorts[cohort].append(row)
        evidence.append(dict(cohort=cohort,case_id=cid,protocol_sha256=sha(p/'protocol.json'),state_sha256=sha(p/'state.json')))
    assert [len(cohorts[k]) for k in cohorts]==[70,20,10,21]
    summary={k:aggregate(v) for k,v in cohorts.items()}
    tests30=cohorts['new_test20']+cohorts['retained_regression10']
    assert len(tests30)==len({r['case_id'] for r in tests30})==30
    summary['test30']=aggregate(tests30)
    for key in ('new_test20','retained_regression10','latest_retest21','test30'):
        summary[key]['with_experience']['first_passed']=None
    latestids={r['case_id'] for r in cohorts['latest_retest21']}
    overlap={k:sorted(latestids&{r['case_id'] for r in v}) for k,v in cohorts.items() if k!='latest_retest21'}
    (OUT/'summary.json').write_text(json.dumps(dict(model='gpt-6.1-sol',effort='medium',groups=summary,latest_overlap=overlap,
        input_hashes=inputs,metric='latent is case-equal macro over available valid trials; auto is real no-memory generation, not provided Contract',
        limitations=['Historical protocols and bank sizes differ; not contemporaneous controlled ablation.','Auto-only training source includes public-feedback-assisted up-to3Actions; latest/retained tests use1Action.','Unavailable/invalid baselines remain missing, never failure.']),ensure_ascii=False,indent=2)+'\n')
    flat=[]
    for group in cohorts.values():
        for row in group:
            r={k:v for k,v in row.items() if k not in ('auto_test','auto_train')}
            for key in ('auto_test','auto_train'):
                for field in ('path','valid','passed','first_passed','status'):r[key+'_'+field]=row[key].get(field) if row[key] else None
            r['display_group']='test30' if r['cohort'] in ('new_test20','retained_regression10') else r['cohort']
            if r['cohort']!='train70':r['with_experience_first_passed']=None
            flat.append(r)
    with (OUT/'per-case.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(flat[0]),lineterminator='\n');w.writeheader();w.writerows(flat)
    (OUT/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps(summary,ensure_ascii=False,indent=2));print('overlaps',{k:len(v) for k,v in overlap.items()})
if __name__=='__main__':main()
