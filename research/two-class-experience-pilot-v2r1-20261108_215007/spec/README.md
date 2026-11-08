# 按机制选择冻结经验的工具流程 v1

入口为 [METHOD.md](METHOD.md)：4类机制、开发时演化、测试时只读冻结经验、未知回退AUTO。

本目录固定的是可评审规范、拟议配置和一份原样E2研究快照。分类器、统一反馈投影和工具端到端接线尚未实现；没有启动任何模型或评分。protocol.json不是可执行运行器配置。

- taxonomy.json：T1同步事件/重入，T2异步副作用归属，T3延迟结算，T4共享工作/取消恢复。
- experience-registry.json：当前只有T4/E2；其余3类为空；管理元数据不得作为分类捷径。
- experiences/EXP-T4-QUERY-E2.md：原始生成文本，未经润色，保留已知歧义。
- EXPERIMENT_PLAN.md / EXPERIMENT_TRACKER.md：最小落地顺序及待办。
- source-manifest.json / validation.json：本轮已有来源摘要及离线一致性结果，不是路由准确率或效果结果。

旧A/D路由、历史实验和生产经验库未修改。
