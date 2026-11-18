"""Export fixed denominators and paired evidence; never invokes a model or grader."""
import argparse
from collections import defaultdict
import csv
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
POINTS=list(range(0,71,10))
TOKENS=('input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens','total_tokens')


def read(path):return json.loads(Path(path).read_text(encoding='utf8'))
def rows(path):return list(csv.DictReader(Path(path).open(encoding='utf8')))
def save(path,value):Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def csvsave(path,records):
    if not records:return
    fields=list(dict.fromkeys(k for row in records for k in row))
    with Path(path).open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fields);writer.writeheader();writer.writerows(records)


def aggregate(records,denominator):
    valid=[r for r in records if r['gold_valid'] is True]
    passed=sum(r['passed'] is True for r in valid)
    completed=sum(r['completed'] for r in records)
    return dict(expected=denominator,completed=completed,valid_gold=len(valid),passed=passed,
        behavioral_failed=len(valid)-passed,execution_invalid=sum(r['execution_invalid'] for r in records),
        unfinished=denominator-completed-sum(r['execution_invalid'] and not r['completed'] for r in records),coverage=len(valid)/denominator,
        pass_over_valid=passed/len(valid) if valid else None,
        observed_pass_over_30_progress=passed/denominator,
        final_accuracy=passed/denominator if len(valid)==denominator else None)


def export(run_id,plots=False):
    root=HERE/'runs'/run_id;manifest=read(root/'manifest.json');ledger=read(root/'balance.json')
    if manifest['pilot']:raise ValueError('Pilot cannot be exported as the formal growth curve')
    out=HERE/'reports'/run_id;out.mkdir(parents=True,exist_ok=True)
    stages=ledger['stages'];jobs=[];train=[];test=[]
    amendment=read(root/'scheduler-amendment.json') if (root/'scheduler-amendment.json').exists() else None
    def one(row,mode,n):
        job='D'+str(row['rank']).zfill(2) if mode=='learning' else 'M'+str(n)+'-T'+str(row['rank']).zfill(2)
        folder=root/'jobs'/job;done=folder/'completion.json'
        receipt=read(done) if done.exists() else {}
        state=read(folder/'trajectory/state.json') if (folder/'trajectory/state.json').exists() else {}
        delivery_path=folder/'trajectory/delivery.json'
        delivery=read(delivery_path) if delivery_path.exists() else None
        delivery_validation=(delivery or {}).get('validation') or {}
        selected=[s for s in stages if s['stage_id'].startswith('jobs/'+job+'/')]
        durations=[(datetime.fromisoformat(s['observed_at'])-datetime.fromisoformat(s['started_at'])).total_seconds()
            if s.get('observed_at') and s.get('started_at') else None for s in selected]
        model_seconds=sum(durations) if durations and all(v is not None for v in durations) else None
        evaluator_seconds=sum(s.get('seconds',0) for s in state.get('stages',[]) if s['kind'] in ('visible','gold'))
        result=dict(job=job,case_id=row['case_id'],rank=int(row['rank']),mode=mode,checkpoint=n,
            configured_workers=(amendment['testing_workers'] if amendment and n>=amendment['from_checkpoint'] else 2) if mode=='testing' else 1,
            core_case=row['core_case'],source_unit=row['source_unit'],runtime=row['runtime'],
            completed=bool(receipt),status=receipt.get('status',state.get('status','not_started')),
            invalid_reason=receipt.get('invalid_reason'),retained_execution_error=state.get('error'),
            review_execution_invalid=receipt.get('review_execution_invalid',False),review_invalid_reason=receipt.get('review_invalid_reason'),
            initial_delivery_recorded=delivery is not None,
            initial_selected_experience_count=len(delivery.get('selected_sha256s') or []) if delivery is not None else None,
            initial_provisional_experience_count=len(delivery.get('provisional_sha256s') or []) if delivery is not None else None,
            initial_experience_delivered=bool(delivery.get('experience_text')) if delivery is not None else None,
            initial_experience_text_characters=len(delivery.get('experience_text') or '') if delivery is not None else None,
            initial_selected_sha256s=';'.join(delivery.get('selected_sha256s') or []) if delivery is not None else None,
            retrieval_validation_partial=delivery_validation.get('partial',False) if delivery is not None else None,
            retrieval_validation_issue_count=len(delivery_validation.get('issues') or []) if delivery is not None else None,
            gold_valid=receipt.get('gold_valid',False),passed=receipt.get('passed'),verdict=receipt.get('verdict'),
            execution_invalid=state.get('status')=='execution_invalid' and not receipt.get('gold_valid',False),attempts=receipt.get('attempts'),
            actions_started=sum(s['kind']=='action' for s in state.get('stages',[])) if state else None,
            valid_attempts=len(state.get('attempts',[])) if state else None,
            training_accepted=receipt.get('training_accepted'),review_decision=(receipt.get('review') or {}).get('decision'),
            observed_training_accepted=state.get('training_accepted') if mode=='learning' else None,
            observed_training_oracle_valid=(state.get('gold_result') or {}).get('valid') if mode=='learning' else None,
            observed_training_oracle_passed=(state.get('gold_result') or {}).get('passed') if mode=='learning' else None,
            review_outcome=(receipt.get('review') or {}).get('outcome'),
            candidate_sha256=(receipt.get('review') or {}).get('candidate_sha256'),
            review_receipt_sha256=(receipt.get('review') or {}).get('receipt_sha256'),
            reviewer_kind=(receipt.get('review') or {}).get('reviewer_kind'),
            human_reviewed=(receipt.get('review') or {}).get('human_reviewed'),
            approved_entries_after=receipt.get('approved_entries_after'),snapshot_sha256=receipt.get('snapshot_sha256'),
            requests=sum(s['requests'] for s in selected) if selected and all(type(s.get('requests')) is int for s in selected) else None,
            usage_incomplete=any(s.get('usage_incomplete') is not False for s in selected) if selected else None,
            elapsed_seconds=model_seconds+evaluator_seconds if receipt and model_seconds is not None else None,
            elapsed_basis='Recorded model-stage intervals plus evaluator durations; includes pre-resume stages and excludes supervisor pauses',
            model_stage_elapsed_seconds=model_seconds,evaluator_elapsed_seconds=evaluator_seconds if state else None,
            last_execution_wall_seconds=receipt.get('elapsed_seconds'),closed_at=receipt.get('closed_at'),
            cost_cny=None,cost_basis='Shared account balance is observed; exact per-case charges are not supplied by provider',
            receipt_path=str(done.resolve()) if done.exists() else None,
            trajectory_path=str((folder/'trajectory').resolve()) if state else None,
            completion_sha256=hashlib.sha256(done.read_bytes()).hexdigest() if done.exists() else None)
        for key in TOKENS:
            values=[(s.get('tokens') or {}).get(key) for s in selected]
            result[key]=sum(values) if values and all(type(v) is int for v in values) else None
        jobs.append(result);return result
    for i,row in enumerate(rows(HERE/'inputs/training-order.csv')):train.append(one(row,'learning',(i//10)*10))
    testing=rows(HERE/'inputs/testing-cases.csv')
    for n in POINTS:
        for row in testing:test.append(one(row,'testing',n))
    summaries=[]
    for n in POINTS:
        selected=[r for r in test if r['checkpoint']==n];snapshot=root/'checkpoints'/('M'+str(n)+'.json')
        snap=read(snapshot) if snapshot.exists() else None
        requests=[r['requests'] for r in selected]
        summaries.append(dict(checkpoint=n,approved_entries=len(snap['entries']) if snap else None,
            configured_testing_workers=amendment['testing_workers'] if amendment and n>=amendment['from_checkpoint'] else 2,
            retrieval_records=sum(r['initial_delivery_recorded'] for r in selected),
            tests_with_experience=sum(r['initial_experience_delivered'] is True for r in selected),
            tests_with_partial_retrieval_validation=sum(r['retrieval_validation_partial'] is True for r in selected),
            snapshot_sha256=snap['sha256'] if snap else None,
            known_requests_subtotal=sum(v for v in requests if v is not None),
            complete_requests=sum(requests) if all(v is not None for v in requests) else None,
            completed_job_elapsed_seconds_sum=sum(r['elapsed_seconds'] or 0 for r in selected),
            **aggregate(selected,30)))
    groups=[]
    for field in ('source_unit','core_case','runtime'):
        for n in POINTS:
            by=defaultdict(list)
            for row in test:
                if row['checkpoint']==n:by[row[field]].append(row)
            for name,selected in sorted(by.items()):groups.append(dict(checkpoint=n,group_type=field,group=name,**aggregate(selected,len(selected))))
    paired=[];pair_summary=[]
    indexed={(r['checkpoint'],r['case_id']):r for r in test}
    for earlier,later in [(0,n) for n in POINTS[1:]]+[(n-10,n) for n in POINTS[2:]]:
        changes=[]
        for row in testing:
            a=indexed[(earlier,row['case_id'])];b=indexed[(later,row['case_id'])]
            valid=a['gold_valid'] and b['gold_valid']
            delta=int(b['passed'])-int(a['passed']) if valid else None
            changes.append(dict(from_checkpoint=earlier,to_checkpoint=later,case_id=row['case_id'],
                source_unit=row['source_unit'],core_case=row['core_case'],both_valid=valid,
                before_passed=a['passed'],after_passed=b['passed'],delta=delta))
        paired+=changes
        pair_summary.append(dict(from_checkpoint=earlier,to_checkpoint=later,both_valid=sum(r['both_valid'] for r in changes),
            improved=sum(r['delta']==1 for r in changes),regressed=sum(r['delta']==-1 for r in changes),
            unchanged=sum(r['delta']==0 for r in changes),unpaired=sum(not r['both_valid'] for r in changes)))
    stage_rows=[]
    for stage in stages:
        row={k:v for k,v in stage.items() if not isinstance(v,(dict,list))}
        row.update({k:(stage.get('tokens') or {}).get(k) for k in TOKENS});stage_rows.append(row)
    finance={k:ledger.get(k) for k in ('baseline_balance_cny','last_balance_cny','observed_decrease_cny','observed_increase_cny',
        'requests','tokens','observed_tokens','incomplete_usage','unknown_request_count','pending_stage_count','status','stop_reason')}
    finance['caveat']='Account balance movements include concurrent activity and delayed billing; they are not per-job invoices. Unknown usage is null.'
    csvsave(out/'training-ledger.csv',train);csvsave(out/'checkpoint-tests.csv',test);csvsave(out/'checkpoint-summary.csv',summaries)
    csvsave(out/'retrieval-exposure.csv',[{k:r[k] for k in ('job','case_id','checkpoint','completed','gold_valid','passed',
        'initial_delivery_recorded','initial_selected_experience_count','initial_provisional_experience_count',
        'initial_experience_delivered','initial_experience_text_characters','initial_selected_sha256s',
        'retrieval_validation_partial','retrieval_validation_issue_count')} for r in test])
    csvsave(out/'source-core-runtime-groups.csv',groups);csvsave(out/'paired-changes.csv',paired);csvsave(out/'paired-summary.csv',pair_summary)
    csvsave(out/'stage-usage.csv',stage_rows);csvsave(out/'balance-observations.csv',ledger['observations'])
    save(out/'finance.json',finance);save(out/'plot-data.json',summaries)
    experience=[];previous=0
    for r in train:
        count=r['approved_entries_after']
        experience.append(dict(training_rank=r['rank'],case_id=r['case_id'],review_decision=r['review_decision'],
            approved_entries=count,approved_delta=count-previous if count is not None else None,
            candidate_sha256=r['candidate_sha256'],review_receipt_sha256=r['review_receipt_sha256']))
        if count is not None:previous=count
    csvsave(out/'experience-growth.csv',experience)
    save(out/'export-manifest.json',dict(run_id=run_id,exported_at=datetime.now(timezone.utc).isoformat(),
        run_manifest_sha256=hashlib.sha256((root/'manifest.json').read_bytes()).hexdigest(),
        counts=dict(training_rows=len(train),test_rows=len(test),summary_rows=len(summaries)),
        evidence_scope='Same-source variant development evaluation with historical exposure; not independent unseen generalization'))
    lines=['# 经验增长实验结果','',f'运行：`{run_id}`。已闭审训练 {sum(r["completed"] for r in train)}/70，已收尾测试 {sum(r["completed"] for r in test)}/240。',
        '',f'这是 {datetime.now(timezone.utc).isoformat()} 导出的结果快照；当前心跳与进度以 [LIVE_PROGRESS.md](LIVE_PROGRESS.md) 为准。',
        '', '本评估是具有历史暴露的同源变体开发评估，不能解释为独立未见来源泛化。八个节点与30例分母固定；未完成节点不显示最终准确率。',
        '', '| 节点 | 收尾 | 有效Gold | PASS | 行为FAIL | 执行无效 | 未完成 | PASS/30 | PASS/有效Gold | 批准经验 |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in summaries:
        pct=lambda value:'—' if value is None else f'{value:.1%}'
        lines.append(f'| M{r["checkpoint"]} | {r["completed"]} | {r["valid_gold"]} | {r["passed"]} | {r["behavioral_failed"]} | {r["execution_invalid"]} | {r["unfinished"]} | {pct(r["final_accuracy"])} | {pct(r["pass_over_valid"])} | {r["approved_entries"] if r["approved_entries"] is not None else "—"} |')
    lines+=['',f'账户余额观测减少：{finance["observed_decrease_cny"]} CNY；最新余额：{finance["last_balance_cny"]} CNY。这不是逐case账单。未知用量保留为null，详见finance.json与stage-usage.csv。',
        '', '批准库数量与实际采用经验分开统计，详见retrieval-exposure.csv。测试没有后续检索修订，initial_experience_delivered即该测试是否实际收到非空指导；训练的initial字段仅指初次检索，不代表后续诊断后的所有检索。未采用经验时的波动不能直接归因为经验，也不把此组视作随机对照。',
        '', '[论文与代码差异](PAPER_CODE_AUDIT.md) · [工程问题记录](ISSUES.md) · [追加事件](EVENTS.jsonl)',
        '',f'导出目录：`reports/{run_id}`。包含70行训练审核、240行测试、8行汇总、来源/core/runtime分组、成对变化、经验增量及完整计费证据。']
    if amendment:
        lines+=['', '调度修订：用户要求提速后，从M20起测试并发由2提高至4，训练仍为1。冻结求解源码、模型、提示、工具、输出约束、单例预算与成员均保持不变；原manifest及改前账本保留，修订另存scheduler-amendment.json。并发可能影响延迟和执行无效率，因此各节点不是完全相同的调度配置，应同时检查超时/资源异常；不得隐去此差异。']
    (HERE/'RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    if plots:plot(out,summaries)
    print(json.dumps(dict(output=str(out),training_closed=sum(r['completed'] for r in train),testing_closed=sum(r['completed'] for r in test))))


def plot(out,summaries):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator
    x=[r['checkpoint'] for r in summaries]
    y=[r['final_accuracy'] if r['final_accuracy'] is not None else float('nan') for r in summaries]
    e=[r['approved_entries'] if r['approved_entries'] is not None else float('nan') for r in summaries]
    fig,axes=plt.subplots(2,1,figsize=(8,7),sharex=True,layout='constrained')
    axes[0].plot(x,y,marker='o',color='#1864ab');axes[0].set(ylim=(0,1),ylabel='PASS / 30 (complete checkpoints only)',title='Fixed same-source development evaluation')
    axes[1].plot(x,e,marker='s',color='#2b8a3e');axes[1].set(xlabel='Processed and review-closed training cases',ylabel='Approved experience entries',xticks=x)
    axes[1].set_ylim(0,max(1,max((r['approved_entries'] or 0 for r in summaries),default=0)+1))
    axes[1].yaxis.set_major_locator(MaxNLocator(integer=True))
    for ax in axes:ax.grid(alpha=.25)
    fig.savefig(out/'growth-curve.png',dpi=200);fig.savefig(out/'growth-curve.pdf');plt.close(fig)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run-id',required=True);parser.add_argument('--plots',action='store_true')
    args=parser.parse_args();export(args.run_id,args.plots)
