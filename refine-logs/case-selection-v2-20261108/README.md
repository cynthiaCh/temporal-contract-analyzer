# 两例选取与新经验开发计划

当前状态：仅离线盘点和计划，0 新模型调用、0 评分调用。训练与验证配对为暂选，尚未整体准入。

先读 [选择理由](SELECTION.md)，再读 [待执行计划](EXPERIMENT_PLAN.md)。训练候选为传输 composition-v4，验证候选已按用户意见改为同来源的 `transfer-progress-composition-v4-window-cued-python3-eval-v2`；撤回 v3 暂选。旧配对未执行，保存于 previous-v3-selection.json。

| 文件 | 用途 |
|---|---|
| cases.csv | 当前 350 个案例表示，来源、路径、运行时、摘要与登记情况 |
| units.csv | 47 个来源单元标签的表示分布；不是独立样本认证 |
| bench-history.csv | 有边界的旧 bench 运行元数据，严格区分模型、effort、条件及版本 |
| summary.json | 盘点分母与扫描限制 |
| selection-evidence.json | 两例输入冻结、训练历史版本对应和验证难度未知 |
| source-manifest.json | 本次使用的原始输入摘要 |
| protocol.json | 文档性计划约束；不是运行器配置，run_enabled=false |
| EXPERIMENT_TRACKER.md | 已完成与尚未执行的阶段 |
| validation.json | 本轮离线关联和完整性检查；不含模型或评分结果 |

`inventory.py` 只读取案例登记、manifest 与历史 JSON 元数据，并将盘点文件写入指定新目录。不导入执行器、不调用模型、不执行候选或 oracle。重新盘点时指定空目录：

```sh
python3 -B refine-logs/case-selection-v2-20261108/inventory.py --out /tmp/temporal-case-inventory-new
```

该脚本重建 cases/units/bench-history/summary 和相应基础 source-manifest；重点案例的额外核对、计划和人工阅读结论单独归档，不由元数据自动推导。

旧 `contract-self-evolution-v1-20261108` 检验的是冻结 E1。这里计划从训练例生成新经验，两套研究问题、预算和分母不能合并。
