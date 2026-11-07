1. 可确认的 Contract
- `submit` 接受异步提交结果：`service.commit(snapshot)` 返回 receipt 的 Promise，或拒绝；`submit` 返回在处理提交结果后才完成的 Promise。依据：原任务背景。
- 每次有效提交在调用入口捕获 doc、actor、text。提交成功后，使用该快照和返回的 revision 恰好创建一条成功审计记录；提交失败不创建成功审计。依据：README.md:3。
- 已接受的提交在 `close` 或再次 `open` 后仍须完成其结果处理。保存成功或错误的 UI 只属于当前访问及其最新一次提交；旧访问或较早提交的结果不得更新该 UI。依据：README.md:3。
- 保留编辑器行为、公开方法及其他消费者；搜索预览不属于本次变更。依据：原任务背景；README.md:5。

2. 每条的条件、效果、来源及依据
- 有当前访问并调用 `submit` 时：捕获当时的 doc、actor、text，交给 `commit`；异步成功后才记录审计，并在符合 UI 所有权条件时显示 saved。README.md:3 明确快照和成功审计义务；src/controller.js:7-13 展示当前快照、UI 守卫和提交流程，但同步调用方式只是当前实现事实，不能作为异步规范。
- `commit` 拒绝时：不产生成功审计；仅当该提交仍属当前访问的最新提交时显示 error；`submit` 的 Promise 须在失败处理完成后结算。README.md:3、原任务背景；src/controller.js:12-13 是现有错误 UI 形态，未确定 Promise 最终应兑现还是拒绝。
- 成功提交跨越关闭或重新打开时：审计仍按原提交快照生成；旧提交不得改变新访问 UI。README.md:3；src/controller.js:5、11、15 的 visit 身份检查是当前实现事实，支持理解现有访问边界。
- 审计数据形态：当前实现将快照字段与 `receipt.revision` 合并后交给 `audit.record`。src/observations.js:1；README.md:3 明确 revision 与快照的行为要求，具体对象结构仅有实现证据。
- 无当前访问调用 `submit`：当前实现返回 `null`。src/controller.js:7-8；原任务要求 `submit` 返回 Promise，二者在此情形是否冲突尚无明确说明，不能将 `null` 当作新合同。
- 当前公开接口为 `open(doc,actor)`、`edit(text)`、`submit()`、`close()`。src/controller.js:2-16；原任务要求保留公开方法，但这些签名是候选源码所见，并无独立接口文档。搜索预览当前为 40 ms、隐藏时丢弃待处理查询、可复用，README.md:5；src/search-preview.js:3-9。此项仅作范围约束。

3. 不能确认的候选要求
- `commit` 拒绝后，`submit` 返回的 Promise 应拒绝、兑现为特定值，还是沿用当前 `failed` 的 `undefined` 返回：原任务仅说“settles after handling the outcome”，未规定结算状态或值；src/controller.js:12-13 只是同步实现。
- 无当前访问时 `submit` 是否也必须返回 Promise，以及应如何结算：原任务措辞与 src/controller.js:8 的当前 `null` 行为存在待澄清边界。
- `audit.record` 或 `render` 自身抛错时的 Promise 结果、`service.commit` 同步抛错的处理方式：候选材料没有相应协议。不能据现有 `try/catch` 推定新要求。
- 提交顺序与完成顺序不同或关闭期间重新编辑时，审计记录的全局排序、取消机制及额外 UI 状态：材料只规定每次成功的审计和当前访问最新提交的 UI 所有权。

4. 建议验证范围
- 分别以兑现和拒绝的可控 Promise 检查：`submit` 结算前完成对应审计或错误 UI 处理；成功审计恰好一次且含调用入口快照与返回 revision，失败没有成功审计。
- 交错完成多次提交，并穿插 `edit`、`close`、`open`：检查各自快照与审计仍对应原提交，只有当前访问最新提交能显示 saved/error。
- 核对现有公开方法、编辑行为及搜索预览消费路径没有受影响。以上只是建议验证；不能由此确定拒绝后的结算形式、无当前访问的返回合同或依赖自身抛错的处理协议。