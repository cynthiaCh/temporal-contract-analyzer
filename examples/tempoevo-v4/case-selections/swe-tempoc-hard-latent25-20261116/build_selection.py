"""Select historically difficult diagnostic cases; never executes a model or scorer.

python3 -B build_selection.py --history /path/to/swe242-per-case-model.csv
History identifies cases and difficulty; this is not a blind held-out sample.
"""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
REPO = OUT.parents[3]
BENCH = REPO.parent / 'swe-tempoc'
LABELS = {
    'debounced-submit-flush': '提交屏障、入口身份和持久化',
    'query-paused-initial-fetch-10266': '惰性消费、共享任务与取消',
    'transfer-retry-abort-handoff': '接收窗口、生命周期与已接收效果',
    'listener-registration-order': '同步启动、监听注册与重入',
    'reentrant-lifecycle-handoff': '重入导航与状态归属',
    'download-polling-restoration': '轮询恢复、代次和前后台所有者',
    'rxjs-asyncsubject-reentrant-6520': '终态缓存与同步重入',
    'async-generator-close-python': '异步清理与退出屏障',
}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write(name, x):
    (OUT / name).write_text(json.dumps(x, ensure_ascii=False, indent=2) + '\n')


def csvfile(name, rows):
    with (OUT / name).open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


def rate(p, n):
    return p/n if n else None


def aggregate(rows):
    totals = Counter()
    for r in rows:
        for arm in ['latent','contract']:
            for field in ['passes','failures','valid','excluded']:
                totals[arm+'_'+field] += int(r[arm+'_'+field])
    return {**totals, **{a+'_pass_rate':rate(totals[a+'_passes'],totals[a+'_valid']) for a in ['latent','contract']}}


def display(p, n):
    return f'{p}/{n} ({100*p/n:.1f}%)' if n else '未找到有效记录'


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--history',type=Path,required=True)
    args=parser.parse_args()
    history=list(csv.DictReader(args.history.open(encoding='utf-8-sig')))
    roster_path=BENCH/'benchmark/swe-tempoc.json'
    roster={r['case_id']:r for r in json.loads(roster_path.read_text())['cases']}
    split_path=REPO/'experiments/evaluation-splits.json'
    split=json.loads(split_path.read_text())
    train=set(split['training_case_ids']); oldtest=set(split['testing_case_ids'])
    grouped=defaultdict(list)
    for row in history:grouped[row['case_id']].append(row)
    stats={}
    for cid, meta in sorted(roster.items()):
        rs=grouped[cid]
        allstats=aggregate(rs)
        target=aggregate([r for r in rs if r['model']=='gpt-6.1-sol' and r['effort']=='medium'])
        profiles={(r['model'],r['effort']) for r in rs if int(r['latent_valid'])>0}
        stats[cid]=dict(case_id=cid,source_unit=meta['source_unit'],parent_case_id=meta['parent_case_id'],
            runtime=meta['runtime'],manifest=meta['manifest'],
            all_models=allstats,target_model=target,model_profiles_with_valid_latent=len(profiles),
            old_training_case=cid in train,old_testing_case=cid in oldtest)
    # Freeze every available case statistic so filtering and rejected items remain inspectable.
    write('historical-inputs.json',dict(history_path=str(args.history.resolve()),history_sha256=sha(args.history),
        roster_sha256=sha(roster_path),split_sha256=sha(split_path),cases=stats))
    eligible=[]
    exclusions={}
    for cid,s in stats.items():
        a,t=s['all_models'],s['target_model']; reasons=[]
        if cid in train:reasons.append('existing_training_case')
        if a['latent_valid']<6:reasons.append('fewer_than_6_valid_latent_trials')
        if a['latent_pass_rate'] is None or a['latent_pass_rate']>.7:reasons.append('pooled_latent_above_70_percent_or_missing')
        if t['latent_pass_rate'] is not None and t['latent_pass_rate']>.6:reasons.append('target_latent_above_60_percent')
        if s['model_profiles_with_valid_latent']<3:reasons.append('fewer_than_3_model_effort_profiles')
        if reasons:exclusions[cid]=reasons
        else:eligible.append(cid)
    # Parent and mechanism quotas prevent autosave ports from monopolizing the sample.
    # Prefer unused exact cases where available; within each group rank ONLY on latent data.
    def order(cid):
        s=stats[cid];a,t=s['all_models'],s['target_model']
        return (s['old_testing_case'], t['latent_pass_rate'] is None,
                t['latent_pass_rate'] if t['latent_pass_rate'] is not None else 0,
                a['latent_pass_rate'], -a['latent_valid'],cid)
    selected=[]
    def take(candidates,n):
        candidates=sorted((cid for cid in candidates if cid in eligible and cid not in selected),key=order)
        assert len(candidates)>=n,(n,candidates)
        selected.extend(candidates[:n])
    def byparent(parent):return [cid for cid in eligible if stats[cid]['parent_case_id']==parent]
    def byunit(unit):return [cid for cid in eligible if stats[cid]['source_unit']==unit]
    take(byparent('document-submit-snapshot-vanilla'),2)
    take(byparent('review-confirmation-binding-vanilla'),2)
    take(byparent('draft-autosave-handoff-vue3'),2)
    take(byunit('query-paused-initial-fetch-10266'),6)
    take(byparent('transfer-progress-composition-v4-window-cued'),4)
    take(byparent('transfer-progress-maintenance-v2-vanilla'),1)
    for unit,n in [('listener-registration-order',2),('reentrant-lifecycle-handoff',3),
                   ('download-polling-restoration',1),('rxjs-asyncsubject-reentrant-6520',1),
                   ('async-generator-close-python',1)]:take(byunit(unit),n)
    selected=sorted(selected,key=lambda c:(list(LABELS).index(stats[c]['source_unit']),order(c)))
    fresh=sorted((c for c in eligible if c not in oldtest),key=lambda c:(stats[c]['source_unit'],order(c)))
    def rows(ids):
        result=[]
        for rank,cid in enumerate(ids,1):
            s=stats[cid];a,t=s['all_models'],s['target_model']
            row=dict(rank=rank,case_id=cid,source_unit=s['source_unit'],parent_case_id=s['parent_case_id'],
                mechanism=LABELS.get(s['source_unit'],s['source_unit']),runtime=s['runtime'],manifest=s['manifest'],
                evidence_tier='target_latent_observed_low' if t['latent_valid'] else 'other_models_hard_target_latent_missing',
                old_training_case=s['old_training_case'],old_testing_case=s['old_testing_case'],
                source_family_seen_in_old_training=any(roster.get(i,{}).get('source_unit')==s['source_unit'] for i in train),
                source_independence_verified=False,
                model_profiles_with_valid_latent=s['model_profiles_with_valid_latent'])
            row.update({'all_'+k:v for k,v in a.items()});row.update({'target_'+k:v for k,v in t.items()})
            result.append(row)
        return result
    chosen=rows(selected);freshrows=rows(fresh)
    csvfile('selected_25_cases.csv',chosen)
    csvfile('not_in_old50_candidates.csv',freshrows)
    write('selection.json',dict(schema_version='tempoevo-historical-latent-hard-selection-v1',
        status='historical_outcome_selected_diagnostic_only',
        independent_heldout=False,training_or_testing_execution_authorized=False,
        selection_policy=dict(source='SWE-TempoC frozen242',exclude_training=True,
            min_valid_latent=6,min_model_effort_profiles=3,max_pooled_latent_pass_rate=.7,
            max_observed_target_latent_pass_rate=.6,unknown_target='retain_as_provisional_other_model_evidence',
            contract_results='reported_but_never_used_for_ranking',max_cases_per_declared_unit=6),cases=chosen))
    write('exclusions.json',exclusions)
    unit_counts=Counter(r['source_unit'] for r in chosen)
    assert len(chosen)==25 and len(set(selected))==25 and not set(selected)&train
    assert set(selected)<=set(roster) and len(unit_counts)==8 and max(unit_counts.values())<=6
    assert all(r['all_latent_valid']>=6 and r['all_latent_pass_rate']<=.7 for r in chosen)
    assert all(r['target_latent_pass_rate'] is None or r['target_latent_pass_rate']<=.6 for r in chosen)
    assert not (set(fresh)&(train|oldtest))
    totals={}
    for scope in ['all','target']:
        totals[scope]={}
        for arm in ['latent','contract']:
            p=sum(r[scope+'_'+arm+'_passes'] for r in chosen)
            n=sum(r[scope+'_'+arm+'_valid'] for r in chosen)
            totals[scope][arm]=dict(passes=p,valid=n,pass_rate=rate(p,n))
    report=dict(selected_count=25,declared_source_units=dict(unit_counts),
        distinct_parent_cases=len({r['parent_case_id'] for r in chosen}),
        target_latent_observed=sum(bool(r['target_latent_valid']) for r in chosen),
        target_latent_missing=sum(not r['target_latent_valid'] for r in chosen),
        reuses_old_test_cases=sum(r['old_testing_case'] for r in chosen),
        not_in_old50=len(fresh),totals=totals,model_calls=0,scorer_calls=0,
        validators='25 unique, frozen roster membership, no old training IDs, source cap6, thresholds, fresh pool disjointness')
    write('validation.json',report)
    lines=['# 重选：SWE-TempoC latent 困难诊断集（2026-11-16）','',
        '本清单替代上一份机制候选25条的推荐地位；旧文件、经验、历史结果和split注册不改写。全部选自冻结242条；未启动训练、测试或模型调用。', '',
        '## 选择规则','',
        '- 排除现有训练1–25的精确case；每条历史latent至少6次有效运行，覆盖至少3个模型/推理力度组合。',
        '- 全模型累计latent通过率不高于70%；若gpt-6.1-sol / medium已有latent记录，则不高于60%。其他模型困难但目标模型已高通过的案例剔除。',
        '- 缺少目标模型latent时，标记为其他模型上的困难候选；不能把Generic成绩或缺失值当作目标模型latent失败。',
        '- 固定机制/父案例配额：提交与身份6、共享取消6、进度/接收窗口5、监听启动2、重入导航3、轮询1、RxJS终态1、异步清理1。提交类内部各取文档、确认、编辑器2条；进度类包含1条不同父案例。',
        '- 家族内优先此前未用于旧26–50的精确case，其次按目标latent、全模型latent与样本数排序；Contract结果只展示，不用于筛选，不只挑Contract成功的案例。',
        '- 70%与60%是本次重新选样的明确难度阈值，不是已有评估协议的修改。', '',
        '## 规模、证据和限制','',
        f"25条覆盖8个声明来源、{report['distinct_parent_cases']}个父案例；每个声明来源最多6条，语言变体不算独立来源。",'',
        f"其中{report['target_latent_observed']}条有目标模型低latent的直接记录，{report['target_latent_missing']}条缺目标模型latent，只能作为待补基线的困难候选。",'',
        f"为了保留25条和上述难度约束，复用旧测试集中的{report['reuses_old_test_cases']}条；精确旧训练case重叠为0。若要求完全排除旧50条，当前规则仅有{len(fresh)}条候选，另存not_in_old50_candidates.csv，不以高通过率案例凑满25。",'',
        '**这是依据已知历史结果选择的困难诊断集，不能标为未见盲测集。** 经验可能来自相同家族，精确case不同不能证明隔离；未重新认证来源、AST、运行环境或评分适配。', '',
        '后续如做训练，只能处理允许学习的案例；原split仍保留旧26–50测试预留，本次不修改或绕过它。若做独立测试，另选未暴露来源且不能使用这些历史验收反馈。此处不授权也不启动任一种运行。','',
        '## 历史通过率','',
        '格式为通过/有效运行；异常排除。目标模型gpt-6.1-sol / medium。全模型率是跨批次描述性累计，不是单模型通过率。历史Contract为给定Contract，非当前Auto-Contract。','',
        '| # | Case | 来源 | 全模型latent | 全模型Contract | 目标latent | 旧26–50 |',
        '|---:|---|---|---:|---:|---:|---|']
    for r in chosen:
        cells=[str(r['rank']),r['case_id'],r['source_unit'],
            display(r['all_latent_passes'],r['all_latent_valid']),
            display(r['all_contract_passes'],r['all_contract_valid']),
            display(r['target_latent_passes'],r['target_latent_valid']),
            '是' if r['old_testing_case'] else '否']
        lines.append('|'+ '|'.join(cells)+'|')
    lines += ['', '## 历史运行累计（不是25个case的pass@k）','',
        '| 范围 | Latent | 给定Contract |','|---|---:|---:|']
    for scope,label in [('all','全部模型/力度'),('target','gpt-6.1-sol / medium（仅有记录的case）')]:
        cells=[label]+[display(totals[scope][a]['passes'],totals[scope][a]['valid']) for a in ['latent','contract']]
        lines.append('|'+ '|'.join(cells)+'|')
    lines += ['', '## 复现','',
        '```bash',f'python3 -B {Path(__file__).resolve().relative_to(REPO)} \\',
        f'  --history {args.history.resolve()}', '```','',
        '历史数据源与SHA在historical-inputs.json；其中冻结全部242条的聚合统计与目标统计。原始回执去重和异常分类见相邻tempoevo-swe-tempoc-history-20261116分析目录。只做本地结构、阈值、去重、配额和排除校验，不重新评分。','']
    (OUT/'README.md').write_text('\n'.join(lines))
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
