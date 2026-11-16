"""Zero-model draft selection from frozen baseline summaries; never changes active split."""
import csv, hashlib, json
from collections import defaultdict
from fractions import Fraction
from pathlib import Path

OUT=Path(__file__).resolve().parent
REPO=OUT.parents[3]
HISTORY=REPO.parent/'tempoevo-swe-tempoc-history-20261116/swe242-per-case-model.csv'
ROSTER=REPO.parent/'swe-tempoc/benchmark/swe-tempoc.json'
MODELS=('gpt-6-sol','gpt-6.1-sol')
SEED='composite-hard100-v1-20261117'

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,value):(OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def csvout(name,rows):
    with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    roster={r['case_id']:r for r in json.loads(ROSTER.read_text())['cases']}
    history=defaultdict(dict)
    for row in csv.DictReader(HISTORY.open(encoding='utf-8-sig')):
        if row['model'] in MODELS and row['effort']=='medium':history[row['case_id']][row['model']]=row
    # Compare the same two profiles; missing/invalid trials never count as failures.
    eligible={c:v for c,v in history.items() if set(v)==set(MODELS) and all(int(v[m]['latent_valid'])>0 for m in MODELS)}
    score=lambda c:sum((Fraction(int(eligible[c][m]['latent_passes']),int(eligible[c][m]['latent_valid'])) for m in MODELS),Fraction())/2
    ordered=sorted(eligible,key=lambda c:(score(c),-min(int(eligible[c][m]['latent_valid']) for m in MODELS),c))
    selected=ordered[:100];assert len(selected)==100
    exposure=json.loads((OUT/'exposure-inventory.json').read_text())
    train={r['case_id'] for r in exposure['training']};tested={r['case_id'] for r in exposure['testing']}
    prior=json.loads((REPO/'examples/tempoevo-v4/case-selections/training-conditioned-provisional25-20261115/provenance-audit.json').read_text())
    sources=set(prior['known_experience_source_cases']);exposed=train|tested|sources
    old=json.loads((REPO/'experiments/evaluation-splits.json').read_text())
    groups=defaultdict(list)
    for c in selected:groups[roster[c]['parent_case_id']].append(c)
    # Approximate each group's30% quota, preserve at least one training item.
    # Singleton groups cannot be in both sets. Largest remainder gives exactly30.
    quotas={g:min(len(v)-1,int(Fraction(3*len(v),10))) for g,v in groups.items()}
    while sum(quotas.values())<30:
        available=[g for g,v in groups.items() if quotas[g]<len(v)-1]
        g=min(available,key=lambda g:(-(Fraction(3*len(groups[g]),10)-quotas[g]),g));quotas[g]+=1
    test=set()
    for g,items in groups.items():
        # Prefer no detected prior exposure; this does not certify independence.
        items=sorted(items,key=lambda c:(c in exposed,hashlib.sha256((SEED+'|'+c).encode()).hexdigest()))
        test.update(items[:quotas[g]])
    rows=[]
    for rank,c in enumerate(selected,1):
        r=dict(rank=rank,split='testing' if c in test else 'training',case_id=c,core_case=roster[c]['parent_case_id'],source_unit=roster[c]['source_unit'],role=roster[c]['role'],runtime=roster[c]['runtime'],manifest=roster[c]['manifest'],composite_pass_rate=float(score(c)),baseline_min_valid=min(int(eligible[c][m]['latent_valid']) for m in MODELS),prior_learning_started=c in train,prior_testing_started=c in tested,known_historical_experience_source=c in sources,old_reserved_test=c in old['testing_case_ids'],detected_prior_exposure=c in exposed)
        for m,key in zip(MODELS,['gpt6','gpt61']):
            for field in ['latent_passes','latent_valid','latent_excluded']:r[key+'_'+field]=int(eligible[c][m][field])
        rows.append(r)
    assert len(test)==30 and len(set(selected)-test)==70 and not (test & (set(selected)-test))
    stats=[dict(core_case=g,total=len(v),train=len(v)-quotas[g],test=quotas[g],test_fraction=quotas[g]/len(v),test_detected_exposure=sum(c in exposed for c in v if c in test)) for g,v in sorted(groups.items())]
    csvout('selected_100_cases.csv',rows);csvout('training_70_cases.csv',[r for r in rows if r['split']=='training']);csvout('testing_30_cases.csv',[r for r in rows if r['split']=='testing']);csvout('core-groups.csv',stats)
    audit=dict(status='draft_not_launched',models=list(MODELS),effort='medium',difficulty='equal-model-weight mean of original latent-maintenance valid-trial pass rates; ascending',tie_break='larger minimum valid sample count, then exact case ID',eligible_cases=len(eligible),missing_valid_profile_cases=sorted(set(history)-set(eligible)),selected=100,train=70,test=30,core_groups=len(groups),singleton_groups=sum(len(v)==1 for v in groups.values()),selected_both_models_100_percent=sum(score(c)==1 for c in selected),max_composite_pass_rate=float(score(selected[-1])),selected_min_profile_trials_lt3=sum(r['baseline_min_valid']<3 for r in rows),test_detected_prior_exposure=sum(c in exposed for c in test),test_prior_learning_or_experience_source=sorted(test & (train|sources)),train_old_reserved_test=sorted((set(selected)-test)&set(old['testing_case_ids'])),independent_unseen_test=False,current_library_reusable_for_clean_test=False,active_split_changed=False,model_calls=0,allocation='largest remainder to30 test total; singleton classes train-only; prefer test IDs without detected prior exposure',fresh_run_requirement='choose a new split policy and provenance scope before launch; fresh empty memory if claiming learning from only these70; old exposed test cases remain development cases',groups=stats)
    write('selection.json',audit)
    write('provenance.json',dict(inputs={str(p):digest(p) for p in [HISTORY,ROSTER,OUT/'exposure-inventory.json',REPO/'experiments/evaluation-splits.json',REPO/'examples/tempoevo-v4/case-selections/training-conditioned-provisional25-20261115/provenance-audit.json',Path(__file__)]},historical_source_version_equivalence='not_recertified_for_new_execution',ranking_uses_only_existing_baseline_summaries=True,oracle_or_reference_inputs=False))
    train25=set(old['training_case_ids']);recent={r['case_id'] for r in csv.DictReader((REPO/'examples/tempoevo-v4/case-selections/swe-tempoc-paired10-sol6-20261116/training_10_cases.csv').open(encoding='utf-8-sig'))}
    write('history-audit.json',dict(old_training25=len(train25),recent_training10=len(recent),overlap=sorted(train25&recent),union=len(train25|recent),observed_learning_protocols=len(exposure['training']),observed_learning_unique_cases=len(train),observed_testing_unique_cases=len(tested),observed_scored_testing_unique_cases=len({r['case_id'] for r in exposure['testing'] if r['status']=='scored'}),historical_source_records=prior['record_count'],historical_records_known_source_cases=len(sources),historical_records_unresolved=len(prior['unresolved_historical_records']),observed_learning_or_known_source_unique=len(train|sources),current_approved_experiences=39,consolidated_older_experiences=37,new_approved_content_experiences=2,per_current_entry_training_lineage='not preserved for older37; cannot certify exact source-case count',inventory_scope='bounded sibling experiment protocol/state metadata plus historical71-record source audit; absence does not prove no exposure'))
    lines=['# 综合最难100：分层划分草案','', '状态：只生成清单，未改动现行split，未启动训练或测试。','', '难度按gpt-6-sol/medium与gpt-6.1-sol/medium原始L通过率等权平均，要求两组均至少1次有效记录；排除缺失/无效记录，不计作失败。按难度、最小样本数降序、case ID排序取100。','', f"共{len(groups)}个真正core类（parent_case_id），{audit['singleton_groups']}个单例类；因此不能每类严格70/30。草案用最大余数法取70训练/30测试，单例只给训练。",'',f"其中{audit['selected_both_models_100_percent']}例在两组历史基线均为100%；{audit['selected_min_profile_trials_lt3']}例至少一组不足3次有效记录。这是相对难度排序，不是100个均经充分重复验证的难题。",'',f"测试草案中{audit['test_detected_prior_exposure']}例有已知开发/训练/测试/经验来源暴露，不能作为新鲜holdout。所有测试均优先选择无已知暴露的ID，但部分类不存在这样的候选。",'', '现有39条经验包含历史归并来源，不能宣称仅来自本次70例。若评价从70例学习的效果，应新建空经验库重新训练并审核后冻结；历史开发测试的暴露仍需单独报告。当前划分只是可审查草案，执行前须解决历史role冲突并重新做全部环境/评分对照校准。','', '|core case|总数|train|test|test已知暴露|','|---|---:|---:|---:|---:|']
    lines += [f"|{g['core_case']}|{g['total']}|{g['train']}|{g['test']}|{g['test_detected_exposure']}|" for g in stats]
    # Alternative: protect test IDs from all detected historical exposure while
    # retaining the SAME hardest100 and one training example in each core class.
    capacities={g:min(len(v)-1,sum(c not in exposed for c in v)) for g,v in groups.items()}
    assert sum(capacities.values())>=30
    protected_quotas={g:min(capacities[g],int(Fraction(3*len(v),10))) for g,v in groups.items()}
    while sum(protected_quotas.values())<30:
        available=[g for g in groups if protected_quotas[g]<capacities[g]]
        g=min(available,key=lambda g:(-(Fraction(3*len(groups[g]),10)-protected_quotas[g]),g))
        protected_quotas[g]+=1
    protected_test=set()
    for g,items in groups.items():
        candidates=sorted((c for c in items if c not in exposed),key=lambda c:hashlib.sha256((SEED+'|'+c).encode()).hexdigest())
        protected_test.update(candidates[:protected_quotas[g]])
    protected_rows=[dict(r,split='testing' if r['case_id'] in protected_test else 'training') for r in rows]
    assert len(protected_test)==30 and not protected_test&exposed
    assert all(any(c not in protected_test for c in v) for v in groups.values())
    csvout('exposure-protected-training70.csv',[r for r in protected_rows if r['split']=='training'])
    csvout('exposure-protected-testing30.csv',[r for r in protected_rows if r['split']=='testing'])
    protected_stats=[dict(core_case=g,total=len(v),train=len(v)-protected_quotas[g],test=protected_quotas[g],test_fraction=protected_quotas[g]/len(v)) for g,v in sorted(groups.items())]
    csvout('exposure-protected-core-groups.csv',protected_stats)
    write('exposure-protected-plan.json',dict(status='recommended_draft_not_launched',same_selected100=True,train=70,test=30,test_detected_prior_exposure=0,core_groups=24,groups_without_test=sum(protected_quotas[g]==0 for g in groups),groups=protected_stats,independent_unseen_test='not certified: bounded historical audit and baseline-outcome-selected cohort',within_core_transfer=True,active_split_changed=False,initial_memory='fresh empty approved store and fresh provisional pool recommended; do not silently reuse39',training_history='old exposed cases may occur on training side; this remains a development design',current_approved_experiences_activated=False,baseline_trial_history_allowed=True,allocation='largest remainder subject to zero detected test exposure and at least one training item per core',model_calls=0))
    lines += ['', '## 建议采用的历史暴露优先划分', '', '同一100例另生成 exposure-protected-training70.csv / exposure-protected-testing30.csv。测试30例均不在本次扫描发现的训练、开发测试及旧经验来源清单中，且每个测试core都有训练case。为此部分core没有测试，其他core测试比例会高于30%。这仍不等于已认证从未见过：扫描有边界、旧经验逐条来源不完整，且本样本按已有baseline结果选取。', '', '运行建议：使用全新经验库，从这70例重新训练、审核并冻结；测试30例一次提交、Gold仅最终评分，不用测试结果改经验后重新算正式成绩。若继续使用现有39条经验，则应明确报告历史经验迁移设定，不能写成仅用这70例得到的经验。', '', '当前工具对部分非Python/JS源码的结构分析仍为unsupported；清单保留这些case，但新100例执行前必须逐例确认工具/语言覆盖、原始/参考/负例控制和镜像依赖，不能把不支持或基础设施失败当作难题失败。']
    (OUT/'README.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({k:v for k,v in audit.items() if k not in ['groups','missing_valid_profile_cases','test_prior_learning_or_experience_source','train_old_reserved_test']},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
