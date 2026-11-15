"""Read historical receipts only; no model calls or rescoring."""
import csv
import hashlib
import json
from pathlib import Path
import subprocess
from collections import Counter

OUT = Path(__file__).resolve().parent
SELECTION = OUT.parent / 'selection.json'
REPO = OUT.parents[4]
ARCHIVE = REPO.parent / 'gpt61-sol-medium-hardest50-20261113_002929'
SOURCE = ARCHIVE / 'deduplicated_target_trials.jsonl'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    cases = json.loads(SELECTION.read_text())['cases']
    ids = {r['case_id'] for r in cases}
    trials = [json.loads(line) for line in SOURCE.read_text().splitlines()]
    matching = [r for r in trials if r['case_id'] in ids]
    assert all(r['model'] == 'gpt-6.1-sol' and r['resolved_effort'] == 'medium' for r in matching)
    roots = [REPO.parent / d / 'results' for d in ['temporal-contract-bench-git', 'swe-tempoc']]
    proc = subprocess.run(['rg', '--files', '--hidden', '--no-ignore', *map(str, roots), '-g', 'run.json'],
                          capture_output=True, text=True)
    archive_paths = {p for r in matching for p in r['receipt_paths']}
    local_hits, unreadable = [], []
    for name in proc.stdout.splitlines():
        p = Path(name)
        try:
            x = json.loads(p.read_text())
        except (OSError, ValueError):
            unreadable.append(name)
            continue
        if not isinstance(x, dict) or x.get('case_id') not in ids:
            continue
        if (x.get('model') or x.get('system_identity')) != 'gpt-6.1-sol':
            continue
        effort = x.get('reasoning_effort') or x.get('effort')
        if effort == 'medium':
            local_hits.append(dict(path=name, sha256=sha(p), case_id=x['case_id'], condition=x.get('condition')))
    additional = [r for r in local_hits if r['path'] not in archive_paths]
    assert not additional, 'New historical receipts need normalization before publishing totals'
    rows = []
    for case in cases:
        row = dict(rank=case['rank'], case_id=case['case_id'], group=case['group'])
        for short, condition in [('latent', 'latent-maintenance'), ('contract', 'contract-provided-maintenance')]:
            v = [r for r in matching if r['case_id'] == case['case_id'] and r['condition'] == condition]
            counts = Counter(r['category'] for r in v)
            passed, failed = counts['pass'], counts['behavioral_failure']
            valid = passed + failed
            row.update({short + '_pass': passed, short + '_fail': failed, short + '_valid': valid,
                        short + '_excluded': len(v) - valid,
                        short + '_pass_rate': passed / valid if valid else None})
        rows.append(row)
    (OUT / 'per-case.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
    with (OUT / 'per-case.csv').open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    (OUT / 'matched-trials.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in matching))
    audit = dict(model='gpt-6.1-sol', reasoning_effort='medium', exact_case_id_match=True,
        source=str(SOURCE), source_sha256=sha(SOURCE), selection_sha256=sha(SELECTION),
        source_archive=str(REPO.parent / 'failure-review-export-20261029.zip'),
        archive_receipt_copies=sum(r['receipt_copies'] for r in matching),
        deduplicated_matching_trials=len(matching), local_receipt_files_scanned=len(proc.stdout.splitlines()),
        local_matched_receipts=local_hits, additional_receipts=additional,
        unreadable_json=unreadable, filesystem_scan_errors=proc.stderr.splitlines(),
        scan_is_exhaustive=False, model_calls=0, scorer_calls=0,
        historical_contract='contract-provided-maintenance; not Auto-Contract',
        missing_result='Not found in the accessible archive and scanned local roots; not a failure or proof of never run')
    (OUT / 'audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2) + '\n')
    lines = ['# 25 条候选的历史 latent / contract 结果（2026-11-16）', '',
        '仅匹配精确 case ID 与 gpt-6.1-sol / medium；不合并同源变体、其他模型或推理力度。', '',
        '**找到 1/25 条的历史记录；其余 24 条在可访问归档和本地扫描中未找到对应记录。**', '',
        '| # | Case | Latent：通过/有效 | Contract：通过/有效 |',
        '| ---: | --- | ---: | ---: |']
    for r in rows:
        cells = []
        for c in ['latent', 'contract']:
            n = r[c + '_valid']; k = r[c + '_pass']
            cells.append(f'{k}/{n}（{100*k/n:.1f}%）' if n else '未找到记录')
        lines.append(f"| {r['rank']} | {r['case_id']} | {cells[0]} | {cells[1]} |")
    lines += ['', '口径与限制：', '',
        '- 通过率 = PASS /（PASS + 有效行为失败）；执行无效和未评分不进入分母，缺记录不记为 0%。',
        '- download-polling-restoration-explicit-react18：latent 11 PASS / 0 FAIL；contract 6 PASS / 0 FAIL；这两条件无排除项。',
        '- 对应历史运行日期为 2026-10-09、18、19（原始 UTC 时间）；跨批次累计结果，不是新执行的一组统一重复。历史每个条件有记录的输入摘要和 manifest 摘要各为一个版本，未认证与当前公开源码完全一致。',
        '- 历史 contract 是给定 Contract，不是当前自动生成 Auto-Contract；不能拿它代替当前消融结果。两条件该 case 通过率相差 0 个百分点。',
        '- 21 份匹配回执（含 Generic）经原始回执内容和执行时间去重后为 18 次运行：latent 11、contract 6、Generic 1。Generic 不计入本次比较。',
        '- 完整归档含 PASS 分母，未使用仅包含非 PASS 的 failure index 计算通过率。匹配证据保留在 matched-trials.jsonl，原始路径和摘要见 audit.json。',
        '- 本地另扫描 12,003 份 run.json，没有发现超出归档匹配集的目标配置回执。6 个工作区临时子目录权限不足；扫描范围有限，不能宣称穷尽所有历史。',
        '- 这条历史暴露未被此前 284 份 TempoEvo 协议扫描发现，因此应修正“没有协议记录就未运行”的推断。原清单本来就是未认证候选；此 case 不应作为从未运行的盲测案例。',
        '- 本次按用户要求回查历史评分，不依据结果换题；未运行模型或重新评分。余下 24 条也仍需来源与暴露核查。', '']
    (OUT / 'REPORT.md').write_text('\n'.join(lines))
    print(json.dumps(dict(found_cases=sum(bool(r['latent_valid'] or r['contract_valid']) for r in rows),
                          latent_pass=sum(r['latent_pass'] for r in rows),
                          latent_valid=sum(r['latent_valid'] for r in rows),
                          contract_pass=sum(r['contract_pass'] for r in rows),
                          contract_valid=sum(r['contract_valid'] for r in rows),
                          local_scanned=audit['local_receipt_files_scanned']), indent=2))


if __name__ == '__main__':
    main()
