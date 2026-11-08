# 两例选择：先盘点，再筛查，最后学习和对照

本轮只做离线盘点和计划；未启动提取、反思、维护、校准或评分。暂选两个案例，不把它们预记为已准入难例。

## 当前建议

| 角色 | 案例 | 为什么考虑 | 当前边界 |
|---|---|---|---|
| 经验开发／训练 | `transfer-progress-composition-v4-vanilla` | 同模型、自动 Contract 条件下已有 0/2 整体通过；可从实际失败中提炼经验 | 人工 Contract 和旧 E1 也都是 0/2，可能涉及实现／验证瓶颈，不能预设换经验就有效 |
| 跨语言验证候选 | `transfer-progress-composition-v4-window-cued-python3-eval-v2` | 同来源的 v4 系列，保留同步启动、延迟完成、帧顺序、重入清理和消费者差异，改为 Python 标准库实现 | 尚未证明当前自动组困难；有额外启动窗口提示，原生 embedding 与 JS 不同；需核对评价／运行器并筛查基线 |

当前训练例保留 v4 JS；验证候选由 v3 改为 v4 系列的 Python eval-v2。v3 文档更直接，不再作为本轮验证候选。此前未发起任何实验，旧配对保存在 previous-v3-selection.json 及原时间戳计划中。

两者的 `independent_unit_id` 均为 `transfer-retry-abort-handoff`，物理目录为 `transfer-retry-handoff`。Python 来源说明它是同源合成派生例，继承父例模型输出影响，且 eval-v2 是已暴露版本的事后评价修订。不能称为独立新案例或未暴露测试。

### 为什么选 Python v4 系列

| 要核对的关系 | Python 候选中的位置 | 当前判断范围 |
|---|---|---|
| 同步启动／监听先后 | `Subscription.attach` 中 start 后 listen；README 允许 start 同步回调 | 入口顺序问题有对应载体，不是仅凭名称匹配 |
| 接纳与完成分开 | listener 调 decode；deliver 调 audit 和 view；Environment 支持稍后调用已绑定闭包 | 能表达相同类别的先后关系；不是原生 JS Promise |
| 留存记录与界面归属 | `Session.enqueue` 的 audit 保留访问闭包，view 检查 current(v) | 可定位两类副作用；正确政策及具体评分仍需逐项核对 |
| 重入清理／请求优先级 | README 允许 unlisten 同步触发导航；Session 使用 serial/request | 具备对应宿主行为前提，不等于已完成可达性或等价性证明 |
| 访问内帧顺序 | README 说明 full frame、arrival 与 decode 顺序可不同；当前 active/order 路径需修复核查 | 机制适用，不能靠 loaded 数值递增猜测帧新旧 |
| 不同消费者 | Telemetry 与面板分别订阅，README 要求保持诊断消费者行为 | 新经验必须说明适用对象，不能把面板补丁应用于所有订阅者 |

Python 版只声明标准库依赖，可先避免前端框架迁移带来的额外组件差异；运行时版本、宿主 embedding 和研究运行器仍需验证。此候选不在当前 96 条诊断任务登记中，不能声称现有 UI 已直接支持，也不在本轮修改生产登记。

**它不只是更换语言。** Python 候选继承 window-cued 的额外提示：start 可同步产生多个包，showProgress 可在清理句柄返回前触发切换／关闭。训练 v4 原版没有这段直接提示。两侧提示差异必须保留并报告，不悄悄删改冻结题面。正式验证两组仍收到完全相同的 Python 输入，因此可比较该候选内的新经验增量；不能据此归因于纯语言变化或宣称严格语义等价。

## 盘点分母

| 范围 | 数量 | 含义 |
|---|---:|---|
| bench 当前案例 catalog | 348 | 依据 cluster 清单与 standalone active manifest；不是 348 个独立事件 |
| analyzer 本地补充 | 2 | listener 同源诊断拆分 |
| 合计案例表示 | 350 | 见 `cases.csv`，均有准确 manifest 路径和 SHA256 |
| 来源单元标签 | 47 | 按 manifest／登记／旧 inventory 回填；标签数不等于经独立审查的样本量 |
| 诊断实验登记 | 96 | bench 94＋本地 2；登记不等于通过语义、工具及运行准入 |
| 登记中明确阻止新运行 | 1 | disposed-request-continuation-react18，保留原排除状态 |
| 旧 AST 盘点 | 242 | 旧静态分析子集，不能当成当前全部案例 |

全量覆盖的是登记、来源、版本、框架及历史线索；没有对 350 例逐个完成源码语义和评分政策审查。只有重点候选做了进一步阅读，不能说“全部 case 都审查通过”。

## 历史证据怎么使用

### bench 旧运行

`bench-history.csv` 收录 bench/results 中深度不超过四层的 128 份去重 run.json 元数据；跳过隐藏归档、候选、依赖及运行时目录，不读取认证文件。去重键含案例、运行 ID、开始时间、模型、effort、prompt 和起点摘要。

其中 49 条 `gpt-5.6-terra/medium` 记录满足完成、Agent 退出成功、run 与同级 score.json verdict 一致。它们的历史 manifest SHA256 均与当前 manifest 不同。因此它们可作为版本核对线索，不能直接计作“当前版本＋自动 Contract”的失败次数。manifest 变化也不自动证明业务代码变化；还需要完整输入和评分版本核对。

这不是全服务器、全历史实验审计。没有同级 score.json 的记录不据此认定为行为失败或评分无效；只标为本次未获得同级佐证。此表的“corroborated”也不代表独立评分复核。

### analyzer 最近归档

单独核对，不混入旧 run.json 分母：

| 归档 | 已核对的事实 | 选例作用 |
|---|---|---|
| `research/contract-repair-small-v1-20261108` | 固定 Terra/medium；传输 v4 的 M=自动 Contract 为 0/2；H=人工 Contract 和 E=自动 Contract＋旧 E1 也为 0/2；审计案例各组均 2/2 | v4 有当前流水线困难证据；审计例本轮不优先 |
| `research/contract-repair-e1-mechanism-v1-20261108` | 固定 Terra/medium；显式 React 下载变体 A/B 均 3/3 | 不继续把它当已证实难例 |
| `research/contract-repair-e1-cluster-hard-v1-20261108` | 固定 Terra/medium；显式 Vue2/Vue3 下载 eval-v2 两例 A/B 均各 3/3 | Qwen 裸任务失败不能替代目标流水线难度证据 |
| `research/terra-auto-contract-single-screen-v1-20261108` | Python 下载例的 loading 政策存在依据缺口；零模型维护结果 | 不能把校准中止当作模型失败，不进入本轮候选 |

v4 的当前 manifest、原任务、11 个候选文件及 6 个 oracle 文件逐项与 small-batch cohort 摘要相同，见 `selection-evidence.json`。该核对支持版本对应，不替代独立人工语义审查，也不证明与将来的完整 prompt／CLI／预算完全一致。

## 为什么暂不选其他搭配

| 方向 | 本轮取舍 |
|---|---|
| low-cue 下载 → 已测显式下载派生例 | 已测自动组全过，尚未观察到提升空间 |
| 下载 → 传输 | 关键生命周期政策不一致，不宜直接检验旧下载经验 E1 的同机制迁移 |
| listener 原例 → 本地 bootstrap/decode 拆分 | 拆分来源明确已暴露；旧失败版本尚需核对，缺当前自动组难度证据 |
| 传输 v4 → window-cued 原生 JS | 来源明确代码／oracle 等相同，主要增加提示；更适合信息提示对照，不能当新代码迁移 |
| 传输 v4 → v3 原生 JS | 撤回暂选：文档更直接，容易再次选到无观察空间的题 |
| 传输 v4 → Vue3 window-cued eval-v2 | 暂作后备；优先检查不额外引入前端框架的 Python v4 派生例 |

## 执行上的唯一下一步

先核对 Python 原生 embedding、研究运行器和评价依据，再对上述两例完成源码、任务与工具版本绑定，再做无经验的自动 Contract 小筛查。验证候选先跑两次：0/2 或 1/2 可继续考虑，2/2 则停止该配对并报告“本次未观察到提升空间”；不能因两次都过就断言永远没有空间。基础设施异常单列。

不应直接开始完整 self-evolving 对照。两例都满足准入和难度条件以后，才从训练例的反馈生成新经验；验证例的轨迹、补丁、标准和分项结果不进入反思器。完整待执行设计见 `EXPERIMENT_PLAN.md`。
