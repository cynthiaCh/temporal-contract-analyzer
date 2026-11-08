# 2+2 分类经验工具试验：前置停止报告

Task 1：实现复用、离线预检与四例来源

起始 HEAD 为 a2a9daf39295caf9098d91ba2405681bf9e0ac09，初始 status/diff 为空。
只在本带时间戳目录新增文件；未修改原案例、旧实验、评分规则、生产行为或全局配置。
未安装依赖，未创建提交，未启动旧调度器，也未导入其顶层执行代码。

指定 refine-logs/experience-toolflow-v1-20261108/ 不存在，METHOD.md、taxonomy.json、
protocol.json、experience-registry.json 四份文件均缺失。扩大检索同级 wangshu 工作区，
未找到指定 METHOD/taxonomy/registry。没有将外部预期方向改写成分类器输入，
没有自行定义 T1—T4，也没有按案例名映射类别。这是付费调用前的关键规范阻断。

四例均取自相邻 temporal-contract-bench-git/case-clusters 的实际 arms manifest，
使用原 maintenance core task、base、oracle。inputs 下分别快照候选、编号源码正文、
任务、manifest 和评价材料；管理/评价材料未发送给任何 Agent。

| 案例 | 来源单元 | 原始 | bounded | expanded | 退化变体数 |
|---|---|---|---|---|---|
| query-paused-initial-fetch-10266-vanilla | query-paused-initial-fetch-10266 | UNDERREACH | PASS | PASS | 7 |
| document-submit-snapshot-vanilla | debounced-submit-flush | UNDERREACH | PASS | OVERREACH | 8 |
| query-paused-initial-fetch-10266-python3 | query-paused-initial-fetch-10266 | UNDERREACH | PASS | PASS | 7 |
| document-submit-snapshot-python3-eval-v2 | debounced-submit-flush | UNDERREACH | PASS | OVERREACH | 6 |

两对是同源跨语言样本，不是四个独立新来源。原 manifest 的 provenance 和来源摘要
已原样保存。尤其 T2 明确披露旧求解暴露、事后评分修订 v2、独立准入尚待完成。
query 训练案例亦已有指定旧实验暴露；不声称其他样本未见。
本轮来源文档已被当前执行 Agent 读取；这些访问也不算盲测。

评分适配直接调用各实际 manifest 指定 probe.cjs，采用 ungranted 原规则。
校准覆盖原始、bounded/expanded/noop 参考与 manifest 列出的全部退化变体。
全部校准检查 case_id、退出码、runtimeError、完整 observed_effects、原规则下 verdict
一致性和候选未变。全部 bounded 通过、原始不通过、全部退化变体不通过。
校准原始 stdout 包含完整行为向量、断言、实际/预期值和轨迹；receipt 保留命令、耗时、
候选摘要和版本。校准是评分检查，不能算维护成功或训练反馈。

候选可见依据：四例 README 给出共享工作/取消/恢复或提交快照/通知/离开结算政策；
T2 另有 docs/host-api.md 说明同步订阅、入口接纳和访问归属。原文和行号保存在
inputs/<case>/visible-source-lines.json。这里的政策解释来自当前执行 Agent 的文档核查，
不是通用分析器推断。未以缺人工批准标记为由阻断，也未伪造批准。

实际校准环境为 Node v18.17.0、Python 3.8.10、bubblewrap 0.4.0。
JS manifest 标示 v16.20.2；沿用既有校准使用的 Node18，版本差异如实记录，
不声称 Node16 原环境复现。Python 正文已读取和快照，实际原评分器运行 Python 案例。

实现 interfaces.py 的保守路由与通用行为差异提取：主类过滤、前提/排除事实检查、
0或1条选择、冲突回退、正文与适用描述摘要绑定、管理元数据拒绝。
反馈区分原有成功、改善、退步、实际与标准差异和未知项；解释必须显式传入，
未包装旧 prepare.py 的 query 专用诊断。13 项合成检查全部通过，覆盖未知类、
空库、缺前提、矛盾、冲突、正文/前提篡改、错误源码证据和不可见元数据。
字面证据绑定不能证明语义正确；这只是可复用原语，不是完整分类器。

已核对旧 runner.session、control.score、Python 自动归档和底层请求计量代码及既有
离线证据，摘要见 reuse-provenance.json。control.score 为单例接口，且其 verdict
重建未覆盖同时欠修与越界；新校准适配已覆盖该原评分值，没有修改旧接口。
新批次 AST/分类/runner 联调、真实工具隔离与请求计量联调尚未完成，不能以旧 PASS
替代新批次检查。完整模型流程保持不可执行，避免在缺失规范时启动付费调用。

Task 2：两例开发、经验冻结和两例测试

触发零模型前置停止。D1/D2 的两次 AUTO、反思、开发回验均未启动。
没有新经验候选，没有经验入库决定，也没有冻结经验库。
这不是“两类训练后为空”，而是训练尚未进行。
T1/T2 未预分析、未分类、未路由，A/B 各两次均未启动。
无命中、回退或提示相同的实际结果，测试分母为0。
actual-schedule.json 为空；route-records.json 明确标注 not_started。
schedule.json 只保存固定种子 2026110804 的块内 A/B 计划，未声称控制模型采样。
protocol.json 保存用户要求和预算；其状态明确为未完成 campaign freeze。
没有实际 prompt、结构化训练反馈、反思输出、最终维护候选或维护补丁；
artifact-status.json 明确解释这些缺失，没有用空内容冒充已完成成果。

Task 3：完整得失、成本、限制与下一步

本轮只得到评分可信性和通用接口的离线证据，没有经验效果、分类器准确率或泛化结果。
不能报告整题通过率、经验命中率、A/B 成本差、改善或退步，也不把校准混入测试分母。
预分析/维护/反思会话和底层请求均为0，无实验模型过程启动。
工程准备的当前助手 token 和货币成本未知，保持 null，不补零。
summary.json 记录离线脚本墙钟耗时，此耗时不包含全部人工/助手工程准备。

下一步是恢复原指定目录的四份 v1 文件并核对版本，然后在新的授权阶段补齐 AST、
预分析 schema/prompt、标准适配说明和 runner 隔离/计量的联调，完成全部冻结后才可
启动训练。不得把本轮原语检查称作完整工具实现，也不得复用任何旧经验作训练种子。
本次到此结束，不自动扩大案例，不自动启动后续阶段。

可复现检查：python3 -B -m unittest discover -s research/two-class-experience-pilot-20261108_171554 -p test_interfaces.py
preflight.py 已完成一次；防重跑检查会拒绝覆盖本轮 summary。
closeout.py 只更新报告和摘要，不启动模型。
