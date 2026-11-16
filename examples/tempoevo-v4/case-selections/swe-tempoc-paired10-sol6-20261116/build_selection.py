"""Freeze a diagnostic 10+10 selection; no model calls or scoring."""
import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parent
REPO = OUT.parents[3]
MODEL = 'gpt-6-sol'
# Fixed mechanism quotas, with public-source pairing reviewed before export.
PAIRS = [
    ('提交前刷新、退出屏障', 'draft-autosave-handoff-vanilla-port-react',
     'draft-autosave-handoff-vanilla-port-python3'),
    ('提交前刷新、退出屏障', 'draft-autosave-handoff-vue3-port-jquery',
     'draft-autosave-handoff-vue3-port-react'),
    ('提交前刷新、退出屏障', 'draft-autosave-handoff-order-example-python3',
     'draft-autosave-handoff-vue3-port-vue2'),
    ('确认入口身份与快照绑定', 'review-confirmation-binding-python3',
     'review-confirmation-binding-react'),
    ('确认入口身份与快照绑定', 'review-confirmation-binding-vue3',
     'review-confirmation-binding-jquery'),
    ('共享请求、惰性消费与取消', 'query-paused-initial-fetch-10266-python3',
     'query-paused-initial-fetch-10266-vue3'),
    ('同步首帧、接收窗口与乱序防回退', 'transfer-progress-composition-v4-window-cued-vue3-eval-v2',
     'transfer-progress-composition-v4-window-cued-vue2-eval-v2'),
    ('进度订阅、生命周期与清理', 'transfer-progress-maintenance-v2-python3',
     'transfer-progress-maintenance-v2-react'),
    ('导航重入、草稿归属与状态发布', 'workspace-draft-projection-latent-vanilla-port-python3',
     'workspace-draft-projection-latent-vanilla-port-vue3'),
    ('pending轮询、恢复与前后台所有权', 'download-polling-restoration-python3-eval-v2',
     'download-polling-restoration-jquery-eval-v2'),
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def write_csv(name, rows):
    with (OUT / name).open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--history', type=Path, required=True)
    parser.add_argument('--trials', type=Path, required=True)
    parser.add_argument('--bench', type=Path, required=True)
    args = parser.parse_args()
    roster_path = args.bench / 'benchmark/swe-tempoc.json'
    roster = {r['case_id']: r for r in json.loads(roster_path.read_text())['cases']}
    split_path = REPO / 'experiments/evaluation-splits.json'
    old = json.loads(split_path.read_text())
    history = list(csv.DictReader(args.history.open(encoding='utf-8-sig')))
    target = {r['case_id']: r for r in history if r['model'] == MODEL and r['effort'] == 'medium'}
    ids = {cid for _, a, b in PAIRS for cid in (a, b)}
    assert len(ids) == 20
    trials = [json.loads(line) for line in args.trials.read_text().splitlines()]
    trials = [r for r in trials if r['case_id'] in ids and r['model'] == MODEL
              and r['effort'] == 'medium' and r['condition'] == 'latent-maintenance']
    receipt_checks = 0
    for trial in trials:
        # Verify the source receipts, including invalid executions kept outside denominators.
        for name, digest in trial['receipt_file_sha256'].items():
            assert sha(Path(name)) == digest, name
            receipt_checks += 1
    rows = []
    inputs = {}
    for role, pos in [('training', 1), ('testing', 2)]:
        for pair_id, pair in enumerate(PAIRS, 1):
            cid = pair[pos]
            meta, stat = roster[cid], target[cid]
            n, p = int(stat['latent_valid']), int(stat['latent_passes'])
            assert n > 0 and p / n <= .5, cid
            assert cid not in old['testing_case_ids'] if role == 'training' else cid not in old['training_case_ids']
            actual = Counter(r['category'] for r in trials if r['case_id'] == cid)
            assert actual['pass'] == p and actual['behavioral_failure'] == n - p, cid
            assert sum(actual.values()) - n == int(stat['latent_excluded']), cid
            assert meta['runtime'] in ('python3', 'jquery', 'react18', 'vue2', 'vue3')
            manifest_path = args.bench / meta['manifest']
            manifest = json.loads(manifest_path.read_text())
            assert manifest['id'] == cid
            prompt = manifest_path.parent / manifest['diagnostic_tasks']['maintenance']['core_prompt']
            base = manifest_path.parent / 'base'
            assert prompt.is_file() and base.is_dir()
            inputs[cid] = dict(manifest=meta['manifest'], manifest_sha256=sha(manifest_path),
                prompt_sha256=sha(prompt), public_files={str(p.relative_to(base)): sha(p)
                    for p in sorted(base.rglob('*')) if p.is_file()})
            peer = roster[pair[3 - pos]]
            assert peer['source_unit'] == meta['source_unit']
            rows.append(dict(rank=len(rows)+1, split=role, pair_id=pair_id, case_id=cid,
                paired_case_id=pair[3-pos], mechanism=pair[0], runtime=meta['runtime'],
                source_unit=meta['source_unit'], parent_case_id=meta['parent_case_id'],
                pair_relation='same_parent' if peer['parent_case_id'] == meta['parent_case_id'] else 'similar_mechanism_different_parent',
                manifest=meta['manifest'], model=MODEL, effort='medium',
                latent_passes=p, latent_valid=n, latent_excluded=int(stat['latent_excluded']),
                latent_pass_rate=p/n, contract_passes=int(stat['contract_passes']),
                contract_valid=int(stat['contract_valid']),
                old_training_case=cid in old['training_case_ids'],
                old_testing_case=cid in old['testing_case_ids']))
    summary = {}
    for role in ('training', 'testing'):
        selected = [r for r in rows if r['split'] == role]
        p, n = sum(r['latent_passes'] for r in selected), sum(r['latent_valid'] for r in selected)
        summary[role] = dict(cases=len(selected), historical_passes=p, historical_valid=n,
            pooled_trial_pass_rate=p/n, macro_case_pass_rate=sum(r['latent_pass_rate'] for r in selected)/10,
            excluded=sum(r['latent_excluded'] for r in selected),
            cases_below_three_valid_trials=[r['case_id'] for r in selected if r['latent_valid'] < 3])
    write_csv('selected_20_cases.csv', rows)
    for role in ('training', 'testing'):
        subset = [dict(r, rank=i) for i, r in enumerate([x for x in rows if x['split'] == role], 1)]
        write_csv(role + '_10_cases.csv', subset)
    dump('selection.json', dict(schema_version='tempoevo-paired-diagnostic-selection-v1',
        selected_at='2026-11-16', tool='temporal-contract-analyzer', model=MODEL, effort='medium',
        rules=dict(condition='latent-maintenance', maximum_target_pass_rate=.5,
            minimum_target_valid_trials=1, train_test_exact_overlap=0,
            train_excludes_old_reserved_tests=True, test_excludes_old_training=True,
            selection_uses_contract_outcomes=False, historical_outcome_selected=True,
            independent_unseen_test=False), summary=summary, cases=rows))
    dump('public-input-sha256.json', inputs)
    dump('provenance.json', dict(inputs={str(p.resolve()): sha(p) for p in
        (args.history, args.trials, roster_path, split_path, Path(__file__))},
        model_docs='https://developers.openai.com/api/docs/guides/latest-model',
        baseline_receipt_copies_verified=receipt_checks,
        historical_input_version_equivalence='not_recertified_for_new_runs'))
    (OUT / 'baseline-trials.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in trials))
    dump('model-profiles.json', dict(schema_version='tempoevo-model-profiles-v1',
        default_profile='sol6-medium', retry_policy=dict(max_retries=2, backoff_seconds=2),
        profiles={'sol6-medium': dict(model=MODEL, reasoning_effort='medium', service_tier='priority',
            provider=dict(name='OpenAI', wire_api='responses', requires_openai_auth=True))}))
    dump('validation.json', dict(status='PASS', checks=['20 unique roster cases',
        '10 training and 10 testing', 'all target L pass rates <= 50%',
        'no missing target baseline', 'all pairs share declared source unit',
        'raw receipt digests and trial totals verified', 'public input files present and hashed',
        'all runtimes in analyzer language scope', 'old split role restrictions respected'],
        model_calls=0, scorer_executions=0, production_split_changed=False))
    lines = [
        '# SWE-TempoC：训练10 + 同机制测试10（2026-11-16）', '',
        '本目录保留 **`gpt-6-sol / medium`** 的历史选例依据；当前执行模型为 `gpt-6.1-sol / medium`，流程见 [WORKFLOW.md](../../../../docs/WORKFLOW.md)。经验构建不更新模型权重。', '',
        '## 选择依据', '',
        '- 全部来自冻结242条 roster；每条都有精确 case、精确模型与力度的历史 L（latent-maintenance）有效记录，原始通过率均 ≤50%。',
        '- 只以 L 成绩判定难度；给定 Contract 和 Generic 成绩不参与筛选。异常、污染和未评分排除，不能计作失败。',
        '- 10组一一配对：9组同父case跨语言/框架，1组为同源 autosave 不同父case的相似机制。双方精确ID不重叠。',
        '- 全部是分析器覆盖的 Python、JS/React/jQuery/Vue；保留确认身份、共享取消、进度窗口、导航重入和轮询等机制。',
        '- 训练最多使用旧训练case，不把旧预留测试case挪入训练；测试排除全部旧训练case。此目录不改写原25+25注册或全局模型默认值。', '',
        '## 配对清单', '',
        '下表通过率均为 gpt-6-sol / medium 原始 L 的通过数/有效次数。', '',
        '|组|机制|训练case|原始L|测试case|原始L|',
        '|---:|---|---|---:|---|---:|',
    ]
    for i, (mechanism, train, test) in enumerate(PAIRS, 1):
        a, b = target[train], target[test]
        lines.append(f"|{i}|{mechanism}|`{train}`|{a['latent_passes']}/{a['latent_valid']}|`{test}`|{b['latent_passes']}/{b['latent_valid']}|")
    lines += ['', '第3组为不同父case：Python order-example 的尾沿合并、退出flush与草稿归属，迁移到 Vue2 编辑器；不能记为独立来源。其余9组父case相同。', '',
        '## 历史基线规模', '', '|集合|case数|有效运行累计|逐case通过率均值|', '|---|---:|---:|---:|']
    for role, label in [('training', '训练'), ('testing', '测试')]:
        s = summary[role]
        lines.append(f"|{label}|10|{s['historical_passes']}/{s['historical_valid']} ({s['pooled_trial_pass_rate']:.1%})|{s['macro_case_pass_rate']:.1%}|")
    lines += ['',
        '累计是历史有效运行次数，不是新流程的成功率或pass@k。17条有3次有效记录，训练2条只有2次、测试1条只有1次，0/1不代表稳定0%。训练/测试各排除2次异常执行。', '',
        '## 历史模型选择依据', '',
        '选例时使用 gpt-6-sol / medium 是基于历史记录匹配：它在这20条上有完整的低L基线；gpt-6.1-sol / medium 在部分候选上缺L记录，另一些已高通过，不适合直接继承本清单的难度判断。',
        '历史模型用于解释选例难度，不代表当前执行配置或模型优劣结论。当前模型设置以 [WORKFLOW.md](../../../../docs/WORKFLOW.md) 和实际冻结协议为准。',
        '`model-profiles.json` 保留历史 sol6-medium 配置，仅用于重现选例依据；当前执行使用仓库 sol61-medium 配置。', '',
        '## 用于训练和测试', '',
        '使用本目录 training_10_cases.csv 和 testing_10_cases.csv；两份rank各为1–10，selected_20_cases.csv 中训练为1–10、测试为11–20。学习和测试都使用公开L任务与源码；当前系统生成自己的Auto-Contract，不能把历史给定Contract作为工具的输入或收益。',
        '当前测试只使用完整已审核经验单组：业务适用性检索、Auto-Contract、一次 Action、最终独立 Gold；不执行 A/B 或无经验对照，不执行 Contract Review。固定流程见 [WORKFLOW.md](../../../../docs/WORKFLOW.md)。',
        '选例依据已知历史结果，且同源变体有意跨集合配对，所以只能报告同机制/跨表示迁移，不能报告未见来源泛化或独立盲测。训练流程最多3次Action，测试按当前实现1次Action/最终Gold；不要把二者的重试成功率直接相减。', '',
        '## 就绪程度与限制', '',
        '本次完成的是选例、原始回执核对、输入指纹冻结与模型配置，未启动训练或测试。额外的当前全库完整性检查和旧catalog接入检查见 benchmark-acceptance-check.json 与 catalog-readiness.json；这些是选例之外的运行前状态，不包含在 selection validation 的PASS内。',
        '当前 SWE-TempoC 全库不匹配 MANIFEST.json，因此不能继承已发布242/242验收结论；新执行前需核对源码差异并重新校准环境。部分新case尚未接入当前训练catalog，且 --swe-tempoc-root 适配器目前仅支持testing；本清单不能直接宣称为已校准、可执行的训练批次。测试case也不能因catalog缺项被改作训练。', '',
        '## 文件与复现', '',
        '- `selection.json`：20条精确case、10组关系、规则和历史统计。',
        '- `baseline-trials.jsonl`：仅选中模型在这20条的原始L回执索引，包含异常记录；逐份源回执SHA已核对。',
        '- `provenance.json`、`public-input-sha256.json`：历史表、roster、旧split、公开任务和源码指纹。',
        '- `validation.json`：计数、阈值、角色限制、回执与公开输入检查。', '',
        '```bash',
        'python3 -B examples/tempoevo-v4/case-selections/swe-tempoc-paired10-sol6-20261116/build_selection.py \\',
        f'  --history {args.history.resolve()} \\',
        f'  --trials {args.trials.resolve()} \\',
        f'  --bench {args.bench.resolve()}',
        '```', '',
    ]
    (OUT / 'README.md').write_text('\n'.join(lines))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
