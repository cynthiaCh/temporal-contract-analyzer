1. 原任务目标与需要保留的行为
原任务要求适配异步保存：`service.commit(snapshot)` 返回收据 Promise，也可能拒绝；`submit` 应返回在结果处理完成后才敲定的 Promise。需保留编辑器行为、公开方法及其他消费者。README 要求提交时捕获 doc、actor、text；成功后用该快照和返回的 revision 生成一条审计记录，失败不生成成功审计；已接受的提交不因关闭或重开而丢失；saved/error 只属于当前访问及其最新提交（README.md:3）。搜索预览明确不在本次变更范围内。

2. 关键源码事实及路径、行号
`open` 建立访问对象，`edit` 更新其 text，`close` 清空 current（src/controller.js:5-6,15）。`submit` 在无当前访问时返回 null；否则设置 latest 身份标记并复制快照（src/controller.js:7-10）。成功回调先调用 `observe`，再按当前访问和 latest 标记决定是否渲染 saved，最后返回收据；失败回调用同一条件决定是否渲染 error，未显式返回值（src/controller.js:11-12）。`observe` 读取 `receipt.revision` 并调用 `audit.record`（src/observations.js:1）。当前 `submit` 将 `service.commit(snapshot)` 的返回值立即交给成功回调，`try/catch` 只覆盖这段同步执行（src/controller.js:13）。工作区检索未找到 controller 的实际外部调用者或 service、audit、render 的具体实现。

3. 相关事件顺序及其依据
现有代码中，快照和 latest 标记先于 commit 调用；同步路径上，commit 返回后立即执行审计，再判断并渲染 saved（src/controller.js:9-13）。若 commit 返回 Promise，现有代码会把 Promise 当作收据传给 `observe`，无法等待兑现或捕获异步拒绝。异步适配所需的顺序是：提交时固定快照与访问身份；成功兑现后处理收据并完成审计，再决定 UI；拒绝后处理失败及 UI；随后 `submit` 的 Promise 才敲定。不同提交的兑现先后未知，不能假定与发起顺序一致。关闭、重开或后续提交可能发生在兑现前；身份条件决定旧结果是否仍可影响 UI（src/controller.js:5,9,11-12,15）。

4. 不同消费者、阶段或效果是否采用不同条件
审计成功记录不受 current/latest 条件限制；saved/error 渲染受该条件限制（src/controller.js:11-12）。因此旧访问或较早提交的成功结果仍应进入历史，但不应覆盖当前界面；失败不写成功审计（README.md:3）。搜索预览使用独立的 40 ms 延后任务，hide 会取消待发布查询（src/search-preview.js:3-8；src/trailing-task.js:16-26），不是保存结果的消费者。

5. 能确认的要求、仅有线索的判断及未知项
任务和 README 明确要求异步结果处理、成功审计、失败无成功审计，以及 UI 归属规则。源码确认当前同步调用形态不满足 Promise 收据与异步拒绝。`failed` 没有显式返回值，提示当前同步失败可能返回 undefined；但新 Promise 应在拒绝后兑现还是继续拒绝、同步抛错如何映射，任务未具体规定。`audit.record`、`render` 是否异步或会抛错，以及公开方法的外部调用约定，候选源码未给出；不据此推断业务政策。

6. 建议验证的行为范围
后续可验证成功、拒绝及同步抛错时 `submit` 的返回类型、敲定时机、收据或错误的可观察结果，以及审计和 UI 的先后顺序；验证连续提交逆序完成、关闭后完成、重开后完成时的审计内容与 UI 归属；验证快照不随之后的编辑改变。这些观察可确认实现是否符合已知顺序和归属要求，但不能单靠测试确定文档未规定的拒绝传播或外部依赖契约。本轮未运行测试或修改文件。