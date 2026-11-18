"""Read-only receipt and protocol audit; no solver, scorer or balance API calls."""
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
def read(path):return json.loads(path.read_text(encoding='utf8'))
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def rows(name):return list(csv.DictReader((HERE/'inputs'/name).open(encoding='utf8')))


def audit(run_id):
    root=HERE/'runs'/run_id;manifest=read(root/'manifest.json');budget=read(root/'balance.json')
    events=[json.loads(line) for line in (root/'events.jsonl').read_text(encoding='utf8').splitlines() if line]
    errors=[];checks=Counter()
    def check(ok,label,detail):
        checks[label]+=1
        if not ok:errors.append(dict(check=label,detail=detail))
    for path,sha in manifest['bindings'].items():check(digest(REPO/path)==sha,'frozen_file',path)
    amendment_path=root/'scheduler-amendment.json'
    if amendment_path.exists():
        amendment=read(amendment_path)
        check(amendment['original_manifest_sha256']==digest(root/'manifest.json'),'scheduler_original_manifest','manifest.json')
        for name,sha in amendment['scheduler_bindings'].items():check(digest(HERE/name)==sha,'scheduler_binding',name)
        check(budget['policy']==amendment['policy'],'scheduler_budget_policy','balance.json')
        check(digest(root/'engineering-observations/scheduler-2-to-4/balance-before.json')==amendment['previous_ledger_sha256'],'scheduler_prior_ledger','balance-before.json')
        check(amendment['from_checkpoint']==20 and amendment['testing_workers']==4 and amendment['training_workers']==1,'scheduler_scope','scheduler-amendment.json')
    check(not manifest['initial_snapshot']['entries'],'empty_initial_bank','manifest')
    expected={}
    for row in rows('training-order.csv'):expected['D'+row['rank'].zfill(2)]=(row,'learning',((int(row['rank'])-1)//10)*10)
    for point in range(0,71,10):
        for row in rows('testing-cases.csv'):expected[f'M{point}-T'+row['rank'].zfill(2)]=(row,'testing',point)
    completed={};evaluations=Counter(e.get('job') for e in events if e['event']=='evaluation_finished' and e.get('kind')=='gold')
    for path in sorted((root/'jobs').glob('*/completion.json')):
        receipt=read(path);job=path.parent.name;completed[job]=receipt
        check(job in expected,'fixed_membership',job)
        if job not in expected:continue
        row,mode,point=expected[job];trajectory=path.parent/'trajectory';protocol=read(trajectory/'protocol.json');state=read(trajectory/'state.json')
        check(receipt['case_id']==row['case_id'] and receipt['mode']==mode and receipt['checkpoint']==point,'job_identity',job)
        check(digest(trajectory/'state.json')==receipt['state_sha256'],'sealed_state',job)
        check(protocol['model']==dict(model='deepseek-flash',reasoning_effort='high'),'model_identity',job)
        check(protocol['total_request_cap']==(132 if mode=='learning' else 48),'job_cap',job)
        check(protocol['max_attempts']==(3 if mode=='learning' else 1),'action_cap',job)
        check(sum(s['kind']=='action' for s in state['stages'])<=protocol['max_attempts'],'action_count',job)
        check(protocol['retrieval_profile']==('source-bound-v8' if mode=='learning' else 'business-source-v1'),'retrieval_profile',job)
        grouped=Counter()
        for stage in state['stages']:
            if stage['kind'] in ('visible','gold'):continue
            grouped[stage.get('budget_group',stage['key'])]+=stage.get('requests',0)
            check(digest(trajectory/'stages'/stage['key']/'result.json')==stage['result_sha256'],'stage_result',job+'/'+stage['key'])
        for group,requests in grouped.items():check(requests<=(24 if group.startswith('action') else 12),'stage_budget',job+'/'+group)
        own=[s for s in budget['stages'] if s['stage_id'].startswith('jobs/'+job+'/')]
        check(all(s['state']=='settled' and s.get('usage_incomplete') is False for s in own),'completed_usage',job)
        check(sum(s['requests'] for s in own)==receipt['requests'],'receipt_request_total',job)
        if mode=='testing':
            snapshot=read(root/'checkpoints'/f'M{point}.json')
            check(receipt['snapshot_sha256']==snapshot['sha256']==protocol['memory_snapshot_sha256'],'checkpoint_snapshot',job)
            check(evaluations[job]==(1 if receipt['gold_valid'] or receipt.get('gold_attempted') else 0),'single_final_gold',job)
            check(not any(s['kind'] in ('diagnosis','extract','routing','contract_review') for s in state['stages']),'testing_roles',job)
            check(receipt['review'] is None,'no_test_learning',job)
        else:
            closure=path.parent/'review/closure.json'
            check(closure.exists() and digest(closure)==receipt['review_closure_sha256'],'training_review_closed',job)
    prepared={e['job']:e['at'] for e in events if e['event']=='job_prepared'}
    for rank in range(2,71):
        job=f'D{rank:02}';previous=f'D{rank-1:02}'
        if job in prepared:check(previous in completed and completed[previous]['closed_at']<=prepared[job],'sequential_training_barrier',job)
    for point in range(0,71,10):
        frozen=[e for e in events if e['event']=='checkpoint_frozen' and e['checkpoint']==point]
        if point and frozen:check(f'D{point:02}' in completed and completed[f'D{point:02}']['closed_at']<=frozen[0]['at'],'checkpoint_training_barrier',str(point))
    for event in events:
        if event['event']=='stage_intent':check(event['model']==dict(model='deepseek-flash',reasoning_effort='high'),'actual_stage_model',event['stage'])
    ids=[s['stage_id'] for s in budget['stages']]
    check(len(ids)==len(set(ids)),'unique_billing_stage','balance.json')
    final=(root/'completion.json').exists()
    if final:
        check(set(completed)==set(expected),'all_310_closed',str(len(completed)))
        check(budget['pending_stage_count']==0 and not budget['incomplete_usage'],'final_accounting','balance.json')
    result=dict(run_id=run_id,audited_at=datetime.now(timezone.utc).isoformat(),final=final,
        status='passed' if not errors else 'failed',closed_jobs=len(completed),expected_jobs=310,
        checks=dict(checks),errors=errors,manifest_sha256=digest(root/'manifest.json'),
        limitation='Provisional while active. Verifies saved receipts and protocol evidence, not provider internals or independent invoice attribution.')
    out=HERE/'reports'/run_id;out.mkdir(parents=True,exist_ok=True)
    (out/'integrity-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result,ensure_ascii=False))
    return not errors


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run-id',required=True)
    raise SystemExit(0 if audit(parser.parse_args().run_id) else 1)
