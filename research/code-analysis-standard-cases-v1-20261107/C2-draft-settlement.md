# C2 草稿：延迟写入与离开／提交结算

**AI 辅助编写，全部待用户确认，非独立人工审查。**评价冻结原始源码；原始版本尚未把 trailing-task 接入 editor，不把未来延迟场景当已经观察的缺陷。

## 1. 一句话说明

把逐键保存改成延迟保存时，要区分“可以等待安静间隔的写入”和“离开／提交返回前必须完成的结算”，同时保留不同界面效果的资格。

## 2. 原任务与保留范围

[原任务](cases/C2/task.md:1)要求使用已有工具合并编辑，120 ms 安静期后仅写该批最后文本，后续批次仍保存，保留接口，预览不在变更范围。[README](cases/C2/candidate/README.md:3)另有候选可见约定：离开返回前可读最后编辑，提交入口固定文档／文本、归档前持久化，通知仅归属原访问，onSaved 可同步导航，后发导航请求优先。**这些是项目文档要求，不是已证明原始实现全部满足。**

来源单元 `debounced-submit-flush`，已用于官方 GEPA val，属于已暴露、人工编写开发来源。与 C3 共享辅助模板，不能据名称视为独立真实项目样本。来源见 [manifest](source-manifest.json)。

## 3. 源码事实表

| ID | 原始源码的有限事实 | 依据 |
|---|---|---|
| C2-S1 | edit 更新 current.text 后立即 store.write；无 current 则返回。editor 接收 timers，但没有调用 trailing-task。 | [editor.js](cases/C2/candidate/src/editor.js:3)，3–20 行 |
| C2-S2 | store 先写 records，再同步通知仍在集合内的订阅者；onSaved 经工作区订阅收到 navigation，可产生重入。 | [draft-store.js](cases/C2/candidate/src/draft-store.js:10)，10–20 行；[workspace.js](cases/C2/candidate/src/workspace.js:3)，3–6 行 |
| C2-S3 | close 先清 current，再退订旧 save badge；open 先 close，再读 store 建新 visit；selection 返回当前 id/text/visit。 | [editor.js](cases/C2/candidate/src/editor.js:5)，5–15、22–23 行 |
| C2-S4 | submit 先取 selection；无选择返回 null，否则 capture 后发可见通知、返回 receipt。该函数没有新增写入／等待。open/close 先清提交提示。 | [workspace.js](cases/C2/candidate/src/workspace.js:8)，8–16 行 |
| C2-S5 | helper 的 push 替换 pending 并重新安排计时；flush 在调用 work 前清旧批次；cancel 丢弃待办。 | [trailing-task.js](cases/C2/candidate/src/trailing-task.js:3)，3–25 行 |
| C2-S6 | 预览使用 40 ms 且 hide 调 cancel；归档 capture 冻结新对象、存储并返回，list 返回副本。 | [search-preview.js](cases/C2/candidate/src/search-preview.js:3)，3–8 行；[receipt-archive.js](cases/C2/candidate/src/receipt-archive.js:3)，3–11 行 |

## 4. 两种关键顺序

- **原始源码顺序，未新运行：**有效 edit → 更新文本 → 写 store → inline onSaved／其他订阅者 → 正常返回，再由调用方 close 或 submit。原始实现没有待触发的编辑计时器；回调可能重入，不能省略此条件（S1/S2）。
- **任务与文档支持的待核查顺序，并非原始运行观察：**编辑进入待保存批次 → 120 ms 前 close/open 或 submit；与“先等安静期写完，再离开／提交”区分。前者要结合 README:5–6、15–24 的返回／归档边界判断，而不能因未到 120 ms 就一概丢弃。helper 的 flush 与 cancel 后果不同（S5），预览的丢弃政策也不能照搬给持久草稿（S6）。

若写入 inline 通知触发新导航，README:9–13 要求按请求开始顺序决定归属；这是文档支持的查证方向，**不声称某段尚不存在的延迟实现已经触发了故障**。

## 5. 行为要求及依据

| ID | 要求／待核查关系 | 来源与边界 |
|---|---|---|
| C2-R1 | 120 ms 合并该批最后文本，后续批次可继续；保留同步公开接口及预览政策。 | task:1–5；[README](cases/C2/candidate/README.md:3):3–4、26–33 |
| C2-R2 | close/open 返回前离开文档可读最后接纳编辑，旧 badge 立即退役；持久化和界面显示资格分别核查。 | [README](cases/C2/candidate/README.md:5):5–7；[save-status.js](cases/C2/candidate/src/save-status.js:1):1–6 |
| C2-R3 | submit 的入口身份／文本、持久化先于 capture、恰好一个归档，与原 visit 的可见通知分别核查；不要假定同步回调无导航。 | [README](cases/C2/candidate/README.md:9):9–24；属于可见文档要求，待人工确认 |

未使用历史测试／评分当业务事实；不规定唯一实现，不要求全局串行化。

## 6. 未知项

- C2-U1：onSaved 的具体调用方和异常政策未提供；文档允许重入，但不能据此断言每条重入路径都实际发生。
- C2-U2：真实 timers 精度、注入 timers 的完整保证和宿主渲染未验证；只能分析 helper 接口与给定 browserTimers（[timers.js](cases/C2/candidate/src/timers.js:1):1–4）。
- C2-U3：文档定义目标保留行为，不等于原实现天然满足所有组合；没有本轮执行证据或历史补丁事实参与评价。

## 7. 模型报告评价清单

“满足／部分满足／不满足／证据不足”；接受等价、分散表述，合理未知不扣成确定错误，不用总分抵消关键关系错误。

| ID | 只评价候选可见材料支持的内容 |
|---|---|
| C2-A1 | 识别原始同步写入、尚未接入延迟工具，引用入口／存储。 |
| C2-A2 | 说明 push、flush、cancel 和后续批次的不同作用，不把预览策略推广到草稿。 |
| C2-A3 | 区分安静期写入与 close/open 返回前结算，标明后者延迟场景为任务推导。 |
| C2-A4 | 区分持久化／归档义务与 badge／通知资格，以及同文档的不同 visit。 |
| C2-A5 | 将 inline 回调、导航请求先后与接口文档对应；不捏造可达故障或忽略未知。 |
| C2-A6 | 验证建议对应批次、离开、提交和回调重入，保留预览与无选择行为；无需给唯一修复。 |

## 8. 用户确认表

| ID | 关键问题 | 状态 | 用户选择 | 备注 |
|---|---|---|---|---|
| C2-Q1 | 是否确认 README 的“离开返回前可读、提交归档前已持久化”应保留，即使不足 120 ms？ | 待确认 | 确认／需要修改／无法判断 | |
| C2-Q2 | 是否确认同步 onSaved 可导航、后发请求优先，以及持久记录与 visit 通知资格应分别评价？ | 待确认 | 确认／需要修改／无法判断 | |
