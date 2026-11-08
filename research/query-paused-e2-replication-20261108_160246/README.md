# Frozen E2 same-case independent replication

唯一来源query-paused-e2-low-20261108_151511。E2、两组实际prompt、候选、任务、自动Contract、原评分和运行器原样复用；不恢复旧批次，不训练/反思或生成新经验。先读PLAN.md，结果见REPORT.md/summary.json。

prepare.py核验来源并复制冻结输入；preflight.py只用临时小候选、假事件/假评分回调及原隔离命名空间做本地检查；freeze.py在任何模型调用前写入protocol.json/sha256。control.py逐字节复用源控制器，六槽新会话，不支持恢复或补跑。analyze.py/report.py只在六槽结束或协议异常停止后统一分析，不调用模型或评分器。

调度种子2026110803只控制块内顺序，顺序A,B,A,B,A,B。六槽最多144底层请求、每槽600秒、并发1，最多6次原外部评分。归档由原Python运行器保存，模型只访问独立业务目录和合法工具。

宿主全局默认tier在本次之前变化；该文件不被实验actor加载。host-config-isolation.json记录独立profile/完整CLI尾部与源一致、宿主配置不可见的离线证明；保护当前宿主文件，不修改它，也不把其默认值当作本次CLI显式priority配置。第一次离线准备假设过严的失败及未运行的preflight导入错误见offline-preparation-notes.json，没有模型或评分重试。

source-evidence/只有外层来源核验材料，不交付维护模型。runs/<slot>/workspace为独立业务候选，兄弟archive/保存输入/实际prompt、事件/工具/stderr、模型回答、计量、最终候选、自动补丁、原评分与SHA清单。所有模型新增文件原样保存，不按名字/后缀清理。

behavior-vectors.json、behavior-counts.csv保存全部29项；scope-review.json逐份复核所有补丁；tool-diagnostics.json保留非零工具诊断；integrity-validation.json记录输入/归档/计量及评分交接摘要核验。源E2批0/3和1/3仅列历史，不混入新分母。

完成后不要重新执行准备或控制器。最终ARTIFACTS.sha256覆盖所有交付普通文件（自身除外）。没有自动E3、其他case或生产经验更新，也不创建Git提交。
