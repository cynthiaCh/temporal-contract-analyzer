"""Summarize the disjoint70 training IDs and GPT5.6medium30 testing IDs."""
import csv,json,hashlib
from pathlib import Path
OUT=Path(__file__).resolve().parent;REPO=OUT.parents[2];BASE=REPO.parent
TRAIN=REPO/'examples/tempoevo-v4/case-selections/incremental100-20261117/training_70_cases.csv'
RATES=REPO/'experiments/incremental-runs/tempoevo-incremental100-workers4-20261117_011424-resume1/rates/per-case.csv'
TEST=REPO/'experiments/testing-runs/tempoevo-gpt56-sol-medium-low30-untrained-workers8-20261117_180752'
OVERLAP=REPO/'experiments/analysis/gpt56-low30-content-overlap-20261117/audit.json'
def read(p):return json.loads(p.read_text())
def csvread(p):return list(csv.DictReader(p.open(encoding='utf-8-sig')))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    train=csvread(TRAIN);train_scores={r['case_id']:r for r in csvread(RATES) if r['cohort']=='train70'}
    test=csvread(TEST/'testing_30_cases.csv');completion=read(TEST/'completion.json');scores={r['case_id']:r for r in completion['cases']}
    assert len(train)==70 and len(test)==30 and not {r['case_id'] for r in train}&{r['case_id'] for r in test}
    assert len({r['case_id'] for r in train+test})==100
    groups=[]
    for core in sorted({r['core_case'] for r in train}):
        tr=[r for r in train if r['core_case']==core];te=[r for r in test if r['core_case']==core]
        groups.append(dict(core_case=core,training_cases=len(tr),training_passed=sum(train_scores[r['case_id']]['current_passed']=='True' for r in tr),
            testing_cases=len(te),testing_passed=sum(scores[r['case_id']]['gold_passed'] is True for r in te),
            testing_failed=sum(scores[r['case_id']]['gold_passed'] is False for r in te),testing_invalid=sum(scores[r['case_id']]['gold_passed'] is None for r in te)))
    assert sum(g['testing_cases'] for g in groups)==30
    overlap=read(OVERLAP)
    summary=dict(total_unique_cases=100,training_cases=70,testing_cases=30,exact_id_overlap=[],training_cores=24,testing_cores=14,
        training_model='gpt-6.1-sol/medium',testing_model='gpt-5.6-sol/medium',training_first_passed=61,training_final_passed=65,training_max_actions=3,
        testing_passed=completion['passed'],testing_failed=completion['failed'],testing_invalid=completion['execution_invalid'],testing_valid=28,
        testing_pass_rate=23/28,all_selected_cases_with_pass=23/30,testing_latent_passes=5,testing_latent_valid=30,
        testing_provided_contract_passes=28,testing_provided_contract_valid=29,testing_provided_contract_excluded=1,
        prior_testing_exposure=sum(r['prior_test_exposure']=='True' for r in test),target_baseline_trials_per_case=1,
        exact_task_text_overlap_cases=len({r['test_case'] for r in overlap['actual_training_matches']['task']}),
        exact_task_and_source_overlap_cases=len({r['test_case'] for r in overlap['actual_training_matches']['task_and_source']}),
        frozen_experiences=61,testing_experience_updates=False,independent_holdout=False,
        input_sha256s={str(p):sha(p) for p in (TRAIN,RATES,TEST/'testing_30_cases.csv',TEST/'completion.json',OVERLAP)})
    (OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    with (OUT/'per-core.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(groups[0]),lineterminator='\n');w.writeheader();w.writerows(groups)
    cases=[]
    for r in train:
        x=train_scores[r['case_id']];cases.append(dict(group='training70',case_id=r['case_id'],core_case=r['core_case'],runtime=r['runtime'],model='gpt-6.1-sol/medium',passed=x['current_passed'],status='passed' if x['current_passed']=='True' else 'repair_exhausted'))
    for r in test:
        x=scores[r['case_id']];cases.append(dict(group='testing30',case_id=r['case_id'],core_case=r['core_case'],runtime=r['runtime'],model='gpt-5.6-sol/medium',passed=x['gold_passed'],status=x['status']))
    with (OUT/'cases100.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(cases[0]),lineterminator='\n');w.writeheader();w.writerows(cases)
    lines=['# 训练70例＋GPT5.6-sol medium测试30例总结','',
      '这是一套由70个训练ID与30个测试ID组成的100例记录，两组精确ID不重合。模型训练权重没有更新；训练是修复任务、反思并积累可检索经验。训练侧执行模型和测试侧模型不同，预算也不同，不应合算单一通过率。','',
      '|集合|模型|case数 / core数|原Latent|带经验首轮|带经验最终|','|---|---|---:|---:|---:|---:|',
      '|训练集|GPT-6.1-sol medium|70 / 24|51.2%，覆盖70/70|87.1%（61/70）|92.9%（65/70），最多3轮|',
      '|测试集|GPT-5.6-sol medium|30 / 14|16.7%（5/30）||82.1%（23/28有效评分）；2例执行异常|','',
      '训练70：26条历史成功记录复用，44例实际补跑。最终65通过、5修复耗尽；原Latent为case等权平均，试次加权另为175/226=77.4%。已有历史经验先于本次训练存在，因此不能宣称当前61条经验全部仅来自这70例。','',
      '测试30：排除当前70及74个已知训练/经验来源ID，按目标模型原Latent排序。只有25例0/1，补充5例1/1；补充的并列按GPT6/GPT6.1原基线难度选，不使用最近带经验测试成败。30例各只有一次有效目标模型基线。25例零通过组当前18通过、5行为失败、2执行异常；补充5例全部通过。','',
      '测试使用冻结61条已接受当前经验，8并发，单次Action24requests/600seconds，总请求上限48，一次最终Gold；无AB、诊断、提炼、经验更新或Gold反馈。30例的队列已经结束，尚有2例未获得有效评分；23/30=76.7%是全部入选样本中已通过的比例，不把两例执行异常计为行为失败。','',
      '测试历史给定Contract基线为28/29=96.6%，另1例无效；这是预先给定Contract，不是仅Auto-Contract生成。该列不能替换为自动Contract消融，也不能宣称当前带经验结果优于给定Contract。','',
      '## 重合与泛化边界','',
      '- 精确训练case ID：0/30重合；与74个已知训练/来源ID同样无重合。',
      '- 当前30例全部来自训练覆盖的14个core；24/30已有历史测试暴露。',
      '- 对197份实际训练original快照核对，完整任务＋公开源码的精确副本0/30，但17/30的任务描述逐字相同。未认证改名/结构/语义近重复不存在。',
      '- 正确定位为同cluster任务变体、跨模型经验迁移的开发复测，不是独立新题泛化或严格零泄露实验。','',
      '## 两例执行异常','',
      '- transfer-progress-maintenance-v2-vue2：selection阶段，包含sort的只读命令被工具策略拦截；没有Gold评分。',
      '- transfer-progress-composition-v4-window-cued-python3-eval-v2：Action请求返回Bad Request；没有合法最终提交/Gold评分。','',
      '## 逐core分布','',
      '|core|训练数量|训练通过|测试数量|测试通过|测试失败|测试异常|','|---|---:|---:|---:|---:|---:|---:|']
    lines += [f"|{g['core_case']}|{g['training_cases']}|{g['training_passed']}|{g['testing_cases']}|{g['testing_passed']}|{g['testing_failed']}|{g['testing_invalid']}|" for g in groups]
    lines += ['', '完整100个精确ID见cases100.csv，逐core数字见per-core.csv，原始输入哈希见summary.json。测试原始运行目录：'+str(BASE/TEST.name)+'。本总结不调用模型、评分器，不改变历史结果或经验。']
    (OUT/'REPORT.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({k:summary[k] for k in ('total_unique_cases','training_cases','testing_cases','exact_id_overlap','training_cores','testing_cores','testing_passed','testing_failed','testing_invalid')}))
if __name__=='__main__':main()
