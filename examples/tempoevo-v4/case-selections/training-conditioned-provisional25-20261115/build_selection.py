"""Build a public-input-only shortlist. Never executes a model or evaluator.

Usage: TCA_BENCH_ROOT=/path/to/bench python3 build_selection.py
The resulting shortlist is deliberately NOT an executable held-out registration.
"""
import csv
import hashlib
import json
from pathlib import Path
import sys

OUT = Path(__file__).resolve().parent
REPO = OUT.parents[3]
sys.path.insert(0, str(REPO))
from temporal_contract_analyzer.case_catalog import registered_cases, catalog, case_input
from temporal_contract_analyzer import experience_approval

# Public obligations determine selection; no observed repair outcomes are inputs.
# IDs below denote hypotheses for transfer, NOT actual retrieval or causal proof.
SPECS = [
    ('commit-ack-boundary-vanilla', 'transfer', 'B', ['boundary-settlement'], '区分持久提交完成与 outbox 接收确认'),
    ('derived-total-flush-order-vue3', 'transfer', 'B', ['boundary-settlement', 'accepted-entry-binding'], '保存前刷新派生值；审计保留事件时快照'),
    ('download-polling-restoration-explicit-react18', 'transfer', 'L', ['cache-attempt-isolation', 'persistent-owner'], '前台代次与后台任务所有者分别处理'),
    ('handoff-redirect-reentrancy-vanilla', 'transfer', 'O', ['reentrant-ownership', 'consume-before-callback'], '同步重入可替换外层跳转；离开移交仅一次'),
    ('external-ticket-bootstrap-explicit-vue2', 'transfer', 'R', ['startup-reception', 'result-freshness'], '先建立身份，再允许受保护消费者启动'),
    ('feature-flag-readiness-vue3', 'transfer', 'R', ['startup-reception'], '就绪后执行一次；保留应急通道的 fail-open'),
    ('hydration-watcher-order-vue3', 'transfer', 'O', ['startup-reception'], '报告与编辑器对 hydration 的订阅顺序相反'),
    ('local-config-readiness-explicit-vue2', 'transfer', 'R', ['startup-reception', 'progress-bootstrap'], '同步配置不能替代子表单 API 的真实就绪事件'),
    ('locale-readiness-snapshot-vue2', 'transfer', 'I', ['accepted-entry-binding'], '新收据等待当前 locale；旧审计保留原快照'),
    ('optimistic-rollback-version-react18', 'transfer', 'F', ['result-freshness'], '旧失败不能覆盖新成功；原子批次保持整组回滚'),
    ('protected-navigation-refresh-react18', 'transfer', 'R', ['startup-reception'], '受保护导航等待刷新；公共路由仍可直接访问'),
    ('upload-finalize-barrier-vanilla', 'transfer', 'B', ['boundary-settlement', 'retained-effects'], '提交等待上传；遥测保留不同完成政策'),
    ('form-api-registration-vue3', 'transfer', 'R', ['startup-reception', 'logical-admission'], '真实 API 发布后写入一次，不以微任务代替就绪'),
    ('asyncio-shared-timeout-python', 'transfer', 'L', ['lazy-shared-cancellation', 'independent-consumers', 'persistent-owner'], '调用者超时不取消服务拥有的共享查询'),
    ('sqlite-commit-notify-python', 'transfer', 'B', ['boundary-settlement', 'retained-effects', 'consume-before-callback'], '事务提交后通知；回滚和通知失败分开归属'),
    ('asyncio-queue-drain-python', 'transfer', 'A', ['logical-admission', 'retained-effects', 'boundary-settlement'], 'drain 等持久化完成；close 拒绝新工作并保留已接收工作'),
    ('metrics-coalesced-view-vanilla', 'transfer', 'A', ['logical-admission', 'trailing-coalescing', 'independent-consumers'], '合并 UI 不能丢失已接收的指标增量'),
    ('audit-commit-attribution-vanilla', 'transfer', 'I', ['accepted-entry-binding', 'retained-effects'], '提交入口绑定身份；成功持久化后记录审计'),
    ('trace-deferred-parent-vanilla', 'transfer', 'I', ['accepted-entry-binding', 'retained-effects'], '延后执行仍绑定 enqueue 时 trace；UI 受访问生命周期约束'),
    ('error-reporting-retired-request-vanilla', 'transfer', 'L', ['retained-effects', 'accepted-entry-binding'], '已接收重试和终态错误上报不随 UI 退出丢失'),
    ('permission-menu-race-vue2', 'boundary', 'I', ['startup-reception', 'accepted-entry-binding'], '不能将最新权限覆盖已签署审计快照'),
    ('pagination-reset-order-vue3', 'boundary', 'O', ['boundary-settlement'], '订单分页需重置，但游标流必须保留 continuation；相似名称不足以迁移'),
    ('playwright-navigation-context-retry-vanilla', 'boundary', 'L', ['cache-attempt-isolation'], '仅导航上下文失效允许重试，其他定位错误仍须传播'),
    ('asyncio-condition-reservation-python', 'boundary', 'A', ['logical-admission'], '通知不是库存满足；不能用就绪经验替代锁内条件循环'),
    ('contextvars-task-snapshot-python', 'boundary', 'I', ['accepted-entry-binding'], '每任务快照与父上下文隔离；不能把最新值策略套到所有上下文'),
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    entries = {row['id']: (source, root, row) for source, root, row in registered_cases()}
    availability = {row['id']: row for row in catalog()['cases']}
    split = json.loads((REPO / 'experiments/evaluation-splits.json').read_text())
    old_ids = set(split['training_case_ids'] + split['testing_case_ids'])
    # Inventory public provenance only; never follow oracle/reference/mutant paths.
    unit_by_id = {}
    for cid, (_, root, row) in entries.items():
        m = json.loads((root / row['manifest']).read_text())
        unit_by_id[cid] = row.get('independent_unit_id') or m.get('independent_unit_id')
    # Include known aliases of the autosave family even if registries name them differently.
    def family(unit):
        return 'debounced-submit-flush' if unit == 'draft-autosave-handoff-v2' else unit
    old_units = {family(unit_by_id[cid]) for cid in old_ids if cid in unit_by_id}
    source_refs = {}
    unresolved = []
    record_files = sorted((REPO / 'experience-memory/records').glob('*.json'))
    for path in record_files:
        record = json.loads(path.read_text())
        found = set()
        for ref in record.get('audit', {}).get('sources', []):
            parts = set(Path(ref.get('path', '')).parts)
            for cid in parts.intersection(entries):
                source_refs.setdefault(cid, []).append(str(path.relative_to(REPO)))
                found.add(cid)
        if not found:
            unresolved.append(record.get('id', path.name))
    source_units = {family(unit_by_id[cid]) for cid in source_refs if unit_by_id[cid]}
    # Bounded search of local experiment protocol metadata; no state/results/events.
    protocol_exposure = {}
    protocols = set()
    for parent in REPO.parent.iterdir():
        if parent.is_dir() and parent != REPO and ('tempoevo' in parent.name or 'training' in parent.name):
            for pattern in ('protocol.json', '*/protocol.json', '*/trajectory/protocol.json', 'trajectory/protocol.json'):
                protocols.update(parent.glob(pattern))
    for path in sorted(protocols):
        try:
            p = json.loads(path.read_text())
        except (OSError, ValueError):
            continue
        cid = p.get('task_id')
        if cid in entries:
            protocol_exposure.setdefault(cid, []).append(dict(path=str(path), mode=p.get('mode'), sha256=digest(path)))
    exposed_units = {family(unit_by_id[cid]) for cid in protocol_exposure if unit_by_id[cid]}
    bank = experience_approval.freeze(REPO / 'experience-memory/library')
    library_ids = {item['id'] for path in (REPO / 'experience-memory/library').glob('*.json')
                   for item in json.loads(path.read_text()).get('experiences', [])}
    selected = []
    inventories = {}
    def tree_identity(base):
        inventory = {str(f.relative_to(base)): digest(f) for f in sorted(base.rglob('*'))
                     if f.is_file() and not f.is_symlink()}
        return hashlib.sha256(json.dumps(inventory, sort_keys=True).encode()).hexdigest()
    old_source_hashes = set()
    for cid in old_ids | set(source_refs):
        if cid in entries:
            _, root, row = entries[cid]
            base = (root / row['manifest']).parent / 'base'
            if base.is_dir():
                old_source_hashes.add(tree_identity(base))
    selected_source_hashes = set()
    for rank, (cid, role, label, rules, rationale) in enumerate(SPECS, 1):
        assert availability[cid]['supported'], (cid, availability[cid])
        assert cid not in old_ids
        unit = family(unit_by_id[cid])
        assert unit and unit not in old_units | source_units, (cid, unit)
        assert set(rules) <= library_ids, (cid, rules)
        public = case_input(cid)
        _, root, row = entries[cid]
        mp = root / row['manifest']
        m = json.loads(mp.read_text())
        # Hash only candidate-visible source/documents, never benchmark internals.
        base = Path(public['candidate'])
        inventory = {str(f.relative_to(base)): digest(f) for f in sorted(base.rglob('*'))
                     if f.is_file() and not f.is_symlink()}
        source_sha = tree_identity(base)
        assert source_sha not in old_source_hashes | selected_source_hashes, cid
        selected_source_hashes.add(source_sha)
        inventories[cid] = dict(manifest=str(mp), manifest_sha256=digest(mp),
                                prompt_sha256=public['case_record']['prompt_sha256'],
                                public_tree_sha256=source_sha,
                                public_candidate_files=inventory)
        selected.append(dict(rank=rank, case_id=cid, group=role, primary_label=label,
            declared_unit_id=unit, runtime=row.get('language'),
            mechanism=row.get('mechanism'), experience_hypotheses=rules,
            rationale=rationale, public_obligation=m.get('construct', {}).get('focal_obligation'),
            manifest=str(mp), source_kind=row.get('source_kind'), provenance=m.get('provenance'),
            declared_prior_exposure=row.get('prior_exposure', 'unspecified'),
            historical_protocols=protocol_exposure.get(cid, []),
            same_declared_unit_protocol_cases=sorted(i for i in protocol_exposure if family(unit_by_id[i]) == unit),
            known_experience_source_overlap=False, old50_declared_unit_overlap=False,
            lineage_verified=False, holdout_eligibility_verified=False,
            ast_coverage='not_verified', grader_integration='not_executed',
            status='provisional_do_not_run_as_independent_test'))
    assert len(selected) == 25 and len({r['declared_unit_id'] for r in selected}) == 25
    assert sum(r['group'] == 'transfer' for r in selected) == 20
    assert sum(r['group'] == 'boundary' for r in selected) == 5
    write('selection.json', dict(schema_version='tempoevo-provisional-mechanism-selection-v1',
        status='blocked_pending_provenance_review', cases=selected))
    fields = ['rank', 'case_id', 'group', 'primary_label', 'declared_unit_id', 'mechanism',
              'experience_hypotheses', 'rationale', 'holdout_eligibility_verified', 'status']
    with (OUT / 'selected_25_cases.csv').open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fields, extrasaction='ignore'); w.writeheader()
        for r in selected:
            w.writerow({**r, 'experience_hypotheses': ';'.join(r['experience_hypotheses'])})
    write('public-input-sha256.json', inventories)
    write('memory-snapshot.json', bank)
    write('provenance-audit.json', dict(
        scope='Bounded local protocol inventory and historical experience source-path metadata only; absence is not proof of no exposure.',
        record_count=len(record_files), unresolved_historical_records=unresolved,
        known_experience_source_cases=source_refs,
        known_experience_source_units=sorted(source_units), old50_units=sorted(old_units),
        discovered_protocol_count=len(protocols), observed_protocol_units=sorted(exposed_units),
        selected_with_protocol_exposure=sum(bool(r['same_declared_unit_protocol_cases']) for r in selected),
        merged_library_per_entry_origin='not_preserved; topic matching is not source attribution',
        historical_record_sha256={str(p.relative_to(REPO)): digest(p) for p in record_files},
        selection_input_sha256=digest(REPO / 'experiments/evaluation-splits.json')))
    write('study-design.json', dict(status='blocked_pending_provenance_review', executable=False,
        purpose='Test hypotheses derived from frozen existing training; do not modify training.',
        conditions=['Auto-Contract', 'Auto-Contract + structured experience'],
        paired_inputs=['original_source', 'AST', 'model_profile', 'action_budget', 'grader'],
        memory_snapshot_sha256=bank['sha256'], model='gpt-6.1-sol', reasoning_effort='medium',
        mode='testing', max_actions=1, gold_policy='once_after_final_submission_no_feedback',
        learning=False, pooled_primary_denominator=20, boundary_denominator=5,
        qualification=['Trace merged experience origins or retain unverified status',
                       'Audit source/ancestor similarity beyond declared unit IDs',
                       'Audit prior model/development exposure beyond bounded local inventory',
                       'Check public source/AST and runtime compatibility without selecting on Gold outcomes'],
        note='Design metadata only. Existing preparer hardcodes old50 and split registry is fixed at25+25. Do not use it to launch this shortlist.'))
    result = dict(selected=25, transfer=20, boundary=5, unique_declared_units=25,
        frozen_approved_experiences=len(bank['entries']),
        certified_independent_cases=0, old50_overlap=0, known_experience_source_unit_overlap=0,
        duplicate_public_trees=0,
        selected_with_historical_protocol_exposure=sum(bool(r['same_declared_unit_protocol_cases']) for r in selected),
        model_calls=0, evaluator_calls=0, source_and_prompt_hashes_present=True)
    write('validation.json', result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
