# 开发集内反馈机制实验归档

入口：[REPORT.md](REPORT.md)、[summary.json](summary.json)。这是已暴露开发材料的反思机制诊断，不是GEPA搜索或维护评测。

- 生成前冻结：PLAN.md、protocol.json、units.freeze.json、evidence-key.json、schedule.json、inputs/。
- 请求与用量：request-meter/events.jsonl、requests.json、runs/。原监测状态异常的纠正见receipt-reconciliation.json，原记录不改。
- 审查：anonymous-review/保留独立人类复核用的空表；review.csv是当前执行Agent的未盲化代理审查。review.freeze.json在读取private-label-mapping.json之前冻结；unblinded-results.csv为此后的标签合并。
- 工具/代码：prepare.py、preflight.py、request_guard.py、run.py仅用于本轮已结束的协议，不应为复现分析再次运行模型。anonymize.py拒绝覆盖既有映射。匿名证据中的common-observations.json是在审查冻结前补入的同一common-record副本，摘要绑定，不是模型新增输入。
- 安全离线复核：在仓库根目录运行 `python3 -B research/development-feedback-mechanism-v1-20261106/finalize.py`。它不调用模型、评分器或优化器，只核验冻结记录并更新派生统计/保护检查。首次运行解盲已发生；再次运行不构成新的盲评。

匿名包中原始证据与内容可能揭示来源，隐藏标签不等于完全盲化。独立人工复核尚未完成。标签映射应与提供给独立审查者的包分开交付。

NEXT_EXPERIMENT.md只是建议，未执行。未创建提交、未安装依赖、未修改历史档案。
