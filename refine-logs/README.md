# 基于 benchmark 的工具与实验设计

阅读顺序：`REFINEMENT_REPORT.md` → `TOOL_REDESIGN_SPEC.md` → `EXPERIMENT_PLAN.md`。完整合并版为 `FINAL_PROPOSAL.md`。

本轮只完成设计、源码扫描、候选快照准备和匿名分配；尚未实现新版工具或开展效果实验。科研技能两轮方法评审与实验模型调用分开记录。

复现当前源码盘点：

```sh
/usr/bin/python3 -B refine-logs/scripts/inventory_bench.py
```

该脚本会校验既有输入/工具摘要后复用本次报告；较大的原始JSON以无损`.json.gz`保存。跨源码/工具版本不能直接复用目录，应使用新的输出批次或在副本中运行；它不是冻结研究runner。20秒上限仅用于本次探索，不是性能结论。

`prepare_review_design.py` 已运行，拒绝覆盖已有设计目录；再次准备应在新目录/批次中进行。脚本生成中性base+overlay快照、完整文件摘要、源码复用检查与12个匿名槽位分配，不执行候选或模型，不填写gold。

`evidence/baseline-scans/` 和 `evidence/review-design/snapshots/` 为本地较大原始材料，默认不纳入Git；清单、摘要、复现脚本和诊断结论保留。未上传或发布任何新材料。
