# 25 条候选的历史 latent / contract 结果（2026-11-16）

仅匹配精确 case ID 与 gpt-6.1-sol / medium；不合并同源变体、其他模型或推理力度。

**找到 1/25 条的历史记录；其余 24 条在可访问归档和本地扫描中未找到对应记录。**

| # | Case | Latent：通过/有效 | Contract：通过/有效 |
| ---: | --- | ---: | ---: |
| 1 | commit-ack-boundary-vanilla | 未找到记录 | 未找到记录 |
| 2 | derived-total-flush-order-vue3 | 未找到记录 | 未找到记录 |
| 3 | download-polling-restoration-explicit-react18 | 11/11（100.0%） | 6/6（100.0%） |
| 4 | handoff-redirect-reentrancy-vanilla | 未找到记录 | 未找到记录 |
| 5 | external-ticket-bootstrap-explicit-vue2 | 未找到记录 | 未找到记录 |
| 6 | feature-flag-readiness-vue3 | 未找到记录 | 未找到记录 |
| 7 | hydration-watcher-order-vue3 | 未找到记录 | 未找到记录 |
| 8 | local-config-readiness-explicit-vue2 | 未找到记录 | 未找到记录 |
| 9 | locale-readiness-snapshot-vue2 | 未找到记录 | 未找到记录 |
| 10 | optimistic-rollback-version-react18 | 未找到记录 | 未找到记录 |
| 11 | protected-navigation-refresh-react18 | 未找到记录 | 未找到记录 |
| 12 | upload-finalize-barrier-vanilla | 未找到记录 | 未找到记录 |
| 13 | form-api-registration-vue3 | 未找到记录 | 未找到记录 |
| 14 | asyncio-shared-timeout-python | 未找到记录 | 未找到记录 |
| 15 | sqlite-commit-notify-python | 未找到记录 | 未找到记录 |
| 16 | asyncio-queue-drain-python | 未找到记录 | 未找到记录 |
| 17 | metrics-coalesced-view-vanilla | 未找到记录 | 未找到记录 |
| 18 | audit-commit-attribution-vanilla | 未找到记录 | 未找到记录 |
| 19 | trace-deferred-parent-vanilla | 未找到记录 | 未找到记录 |
| 20 | error-reporting-retired-request-vanilla | 未找到记录 | 未找到记录 |
| 21 | permission-menu-race-vue2 | 未找到记录 | 未找到记录 |
| 22 | pagination-reset-order-vue3 | 未找到记录 | 未找到记录 |
| 23 | playwright-navigation-context-retry-vanilla | 未找到记录 | 未找到记录 |
| 24 | asyncio-condition-reservation-python | 未找到记录 | 未找到记录 |
| 25 | contextvars-task-snapshot-python | 未找到记录 | 未找到记录 |

口径与限制：

- 通过率 = PASS /（PASS + 有效行为失败）；执行无效和未评分不进入分母，缺记录不记为 0%。
- download-polling-restoration-explicit-react18：latent 11 PASS / 0 FAIL；contract 6 PASS / 0 FAIL；这两条件无排除项。
- 对应历史运行日期为 2026-10-09、18、19（原始 UTC 时间）；跨批次累计结果，不是新执行的一组统一重复。历史每个条件有记录的输入摘要和 manifest 摘要各为一个版本，未认证与当前公开源码完全一致。
- 历史 contract 是给定 Contract，不是当前自动生成 Auto-Contract；不能拿它代替当前消融结果。两条件该 case 通过率相差 0 个百分点。
- 21 份匹配回执（含 Generic）经原始回执内容和执行时间去重后为 18 次运行：latent 11、contract 6、Generic 1。Generic 不计入本次比较。
- 完整归档含 PASS 分母，未使用仅包含非 PASS 的 failure index 计算通过率。匹配证据保留在 matched-trials.jsonl，原始路径和摘要见 audit.json。
- 本地另扫描 12,003 份 run.json，没有发现超出归档匹配集的目标配置回执。6 个工作区临时子目录权限不足；扫描范围有限，不能宣称穷尽所有历史。
- 这条历史暴露未被此前 284 份 TempoEvo 协议扫描发现，因此应修正“没有协议记录就未运行”的推断。原清单本来就是未认证候选；此 case 不应作为从未运行的盲测案例。
- 本次按用户要求回查历史评分，不依据结果换题；未运行模型或重新评分。余下 24 条也仍需来源与暴露核查。
