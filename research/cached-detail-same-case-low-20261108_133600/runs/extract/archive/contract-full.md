## 1. 可确认的 Contract
详情面板打开已有缓存的记录时，应在 `open(id)` 返回前交付缓存快照，并继续接收该次订阅的网络更新；无缓存时，仍按正常网络订阅流程工作。每次 `open(id)` 都是新活动，包括重复打开同一 ID。选择状态代表最新请求的目的地，详情记录只在所属活动仍被选中时才有用；离开后不得保留该活动的传输订阅。合规审查继续要求新鲜网络观察，最近预览的呈现行为保持不变。

## 2. 每条的条件、效果、来源及依据
- **缓存命中与后续更新。** 条件：详情 `open(id)` 时共享仓库已有该 ID。效果：开启动作内交付 `source: "cache"` 的记录，随后保留实时订阅并交付 `source: "network"` 的更新。[原任务]明确要求缓存优先且持续收取网络更新；[仓库源码](/workspace/src/record-repository.js:1)明确说明 `watch(id, "prefer-cache", receive)` 可在返回释放句柄前同步回调，并继续订阅。[详情源码](/workspace/src/detail-panel.js:10)当前调用 `watchFresh`，只是待改变的实现事实，不能据此把等待网络当作义务。
- **冷记录。** 条件：仓库没有该 ID 缓存。效果：开启动作仍建立网络订阅，待传输更新后交付；不能要求立即出现记录。[原任务]要求冷记录正常工作；[仓库源码](/workspace/src/record-repository.js:8)显示仅缓存命中才同步交付，订阅仍会建立。[README](/workspace/README.md:6)说明传输在 `subscribe` 返回后提供更新。
- **活动与身份。** 条件：每次 `open(id)`，包括同 ID 重开，以及 `close()` 或打开另一 ID。效果：新打开是新活动；`selection()` 和选择渲染表示最新请求的目的地；记录只在其活动被选中时有用。选中活动持续接收网络更新，直到关闭或再次打开；离开后不保留传输订阅。[README](/workspace/README.md:8)直接规定这些行为。[详情源码](/workspace/src/detail-panel.js:2)显示当前 `current`、`release` 的写入和消费位置，但其具体赋值顺序并非业务规范。
- **同步交付与重入。** 缓存回调可能在仓库返回释放句柄之前执行；工作区先调用 `renderDetail`，再同步调用可请求 `open` 或 `close` 的 `onDetail`。[仓库源码](/workspace/src/record-repository.js:3)、[工作区源码](/workspace/src/workspace.js:7)、[README](/workspace/README.md:14)足以支持该时序。因此，在缓存交付触发导航的条件下，详情活动及释放句柄的归属须仍满足上一条的最新选择和离开释放要求。仓库还说明每个返回的句柄恰好拥有该次 watch，即使交付期间发生导航；这支持追踪句柄归属，不指定唯一实现方式。[仓库源码](/workspace/src/record-repository.js:5)
- **跨请求时间线。** 当前实现中，一次 `open` 先 `close`：旧句柄被调用、`current` 清空、选择渲染为 `null`；再创建 watch，最后写入 `current` 并渲染 ID。[详情源码](/workspace/src/detail-panel.js:3) 缓存优先模式使交付可能落在“watch 已开始、`current` 尚未写入”的间隙；网络交付则由订阅回调在后续发生。[仓库源码](/workspace/src/record-repository.js:8) 网络回调先写仓库共享缓存，再在该 watch 仍 `live` 时交付；释放将 `live` 置假并调用 `stop`。[仓库源码](/workspace/src/record-repository.js:13) 后续 `open` 会消费旧 `current.release`。旧网络回调若与新活动交错，其捕获的 ID 决定缓存写入位置，而详情交付受该旧 watch 的 `live` 状态控制；现有资料未给出传输取消与已排队回调的完整保证，故只能作条件性判断。
- **相邻组件边界。** 合规审查当前以 `watchFresh` 取得新鲜观察，关闭时释放；其注释明确缓存不能支持合规决定。[合规源码](/workspace/src/compliance-review.js:1) [README](/workspace/README.md:17)及原任务支持将此列为应保留行为。最近预览当前只呈现网络观察并在隐藏时释放；其缓存呈现属单独迁移。[预览源码](/workspace/src/recent-preview.js:1) [README](/workspace/README.md:17)及原任务支持保持现状。这些组件的实现不自动成为详情面板的设计模板。

## 3. 不能确认的候选要求
- 缓存命中时 `renderSelection(id)` 与缓存 `renderDetail` 的精确先后顺序：已确认最新目的地与记录所属活动的可观察要求，但资料未规定两个渲染调用的唯一顺序。
- 关闭后已排队传输回调是否仍会执行、`stop()` 是否取消排队工作，以及关闭后缓存是否仍可能被该回调写入：仓库代码显示即使 `live` 为假，回调入口若被调用仍先写缓存；缺少传输接口对排队与取消的保证，不能断定实际发生或规定额外隔离策略。
- 宿主卸载行为：README 说明没有前端框架生命周期；公开入口只有 `open`、`close`、`selection`，没有卸载契约。[README](/workspace/README.md:21) [工作区源码](/workspace/src/workspace.js:13)
- 详情交付后其他业务字段、缓存新鲜度或缓存保留时长的含义：源码给出 `id`、`value`、`source` 和订阅机制，未给出额外产品政策。不能要求某单一字段独自表达完整活动状态。

## 4. 建议验证范围
- 分别检查缓存命中与未命中：同步交付时点、正确 ID 和 `source`、后续网络更新，以及冷记录的订阅和交付。
- 检查同 ID 重开、切换 ID、关闭，以及缓存交付期间 `onDetail` 同步触发打开或关闭：最新选择、记录所属活动、各次 watch 句柄的释放和存活订阅。
- 用可控传输分别检查请求进行中、请求结束后的等待间隙、后续请求，以及回调已排队时的交错；同时观察仓库缓存写入与详情交付。此类验证只能确认所用传输调度下的行为，不能替代未提供的传输取消保证。
- 确认合规审查仍等待网络观察、最近预览仍只呈现网络观察。以上是建议范围，尚未执行验证；本次仅只读检查了候选文档与源码。