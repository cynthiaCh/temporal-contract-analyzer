# Problem Anchor

- Bottom-line problem：利用现有 temporal-contract-bench 的任务、候选源码、行为对照与来源记录，设计一个更能帮助核查跨边界时序要求的工具，以及能检验其实际价值的实验，服务 ICPC 2027 Tool Track。
- Must-solve bottleneck：现有四问卡片主要重组启发式 finding，尚未明确连接 continuing work、对象/操作身份、不同消费者效果及保护位置；合成单例与实现测试不能回答真实审查价值。
- Non-goals：本轮不修改 benchmark 历史输入、oracle、冻结结果或独立发布版；不把既有开发案例称为未见验证；不启动付费模型或参与者研究；不在设计阶段实现全程序验证器或自动修复。
- Constraints：当前 analyzer 支持 Python、JS/TS 和 Vue 脚本；复用既有解析、归档与接口；来源相关表示不计独立样本；评估者材料与工具/Agent 可见材料分离；ICPC 2027 Tool Track 时间预算约三周。
- Success condition：从实际源码扫描与代表案例中定位可复核缺口；给出小而具体的数据结构和模块修改；实验有固定对象、信息等量对照、逐义务/消费者指标与停止规则；正、负或无效结果均能确定论文可写主张。
