# 待核查清单（研究侧，禁止进入 Agent 检索）

这些内容没有作为独立正式机制入库。条目与 jobs/scope 的关联均见 provenance.json。

1. **配置可用不等于表单 API 就绪。** jobs.config-readiness-pending：A 补丁用 Promise.resolve 替代网络等待；候选 SchemaForm 的 mounted 用 setTimeout 发出 API。原始评分缺 personnel-form-ready/personnel-parent-values-preserved；CASE_NOTES 也核查了四份失败补丁。微任务先于 API 回调是可行机制，但本次未独立核对表单调度测试建模与原任务要求的完整一致性，也未找到同条件成功样本。下一步应使用候选公开组件挂载顺序重现，并对照显式 API-ready 屏障；不能仅凭失败名或 R 材料漏文件断言唯一原因。A 已读过组件仍失败，检索缺失不是唯一已证实原因。

2. **下载续修两项退步的具体原因。** jobs.download-regression-pending：hypothesis_review 的 e-f4634cdd9ae34866/j-001，参考校准 PASS，父子比较确实丢失 download-reopen-current-completes-once 与 download-retries-until-ready-once。补丁同时增加自动 start、扩大 status 判定和卸载失效逻辑；无法从一次组合修改分离哪个变化导致哪项退步。需要核对 preparation-api 的真实状态协议、当前任务与共享后台消费者，然后用受控公开驱动逐项消融；本次不运行。不得因模型自行猜测 true/ready 字符串就把它当服务协议。

3. **异常缓存有效性、重试以及逆序帧。** 本次最近六批精读证据没有闭合“异常发生→缓存键值不一致→后续访问错误→保留行为对照”的链。README 的规则说明和更早单元测试不能替代本范围实际失败证据。transfer 任务确实要求解码逆序不得回退，已读样本也有帧序号与通过记录，但本次未精读对应失败候选，因此没有单独拆为一道已支持的问题。若扩围，应另列批次并核对实际输入、补丁和行为。

4. **身份、权限与状态快照的泛化。** 草稿可见 README 明示提交在入口接纳文档和值；成功补丁保持入口快照，通知只属于原访问。这支持 TCQ-004 的有界核查前提；未观察到本批精读失败候选将身份/权限快照错误改变的完整证据，不能据此发明“所有异步操作固定入口权限”的题目。权限撤销、事务回滚及提交时授权需新证据。

5. **transfer 接纳窗口与完成窗口。** jobs.transfer-unified-guard-regression 的父输入本来就缺 start-switch-admission；续修 active 守卫既未补此项，又丢失已接纳历史。jobs.transfer-success 同时修改 handle 早发布、onSubscribe、retry 等多处后全部通过。源码/trace 支持重入窗口存在，但不能证明某一个新增回调或守卫是唯一必要修复。正式题库只保留 TCQ-003/004 的通用核查，不生成具体 transfer 修复模板。

6. **执行失败与验证异常要分开。** information-gap 批次 e-9eb71728c3644d1c（S*）与 e-1239a9e54f024482（C）原始 result.json 中 turn_completed=false、exit_code=1，事件报 Selected model is at capacity，未评分：归 execution-failure，不是行为失败，也不是验证器发现缺陷。验证基础设施异常应归 validation-unverified（参考校准失败、oracle 进程失败、缺少可信输出或版本比较 unverified）；本次所选本地已评分档案未发现此类，脚本逐项复核，不能将“本次为零”解释成基础设施永远可靠。

7. **未交付与逐场景未知。** assistance-applicability 的 16 个 S/D 槽位未交付、未调用，不计入 48 次调用，也不算修复失败。旧 AD listener 的逐场景状态全未知，但 raw observed_effects/整体 verdict 有效；TCQ-001/002 主要用后续 checklist 原始具体输出交叉核查，不把 unknown 当 false。全仓分支只有 12 次 A 筛选，没有 treatment；不能从其停止或零报告推断静态辅助有效/无效。

8. **提示增益的解释与来源独立性。** 已有 CASE_NOTES、MECHANISM_NOTES 与 DIAGNOSTIC_NOTES 说明不少失败 Agent 已读 README；不能说 R 或 D 提供了其他条件从未获得的契约。上下文呈现、注意分配、采样与组合干预仍未分离。checklist 比较不支持 D* 超过通用清单，单个机制正确不等于题库有收益。document authored extension、同源 listener 与 transfer 家族都属于开发来源；split_policy 中的全批排除集合必须在后续研究执行。新增候选若来源不明，先核查谱系再划分。
