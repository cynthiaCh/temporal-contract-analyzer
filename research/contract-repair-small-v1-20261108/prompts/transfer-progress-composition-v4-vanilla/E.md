A transfer with a warm progress source shows no initial progress until a later
packet arrives. Restore the initial progress update without changing the public
transfer, retry, navigation, cleanup, audit, or queue-record behavior. Full
progress frames may decode out of order; do not allow an older frame to roll the
current display backward. Preserve ordinary streaming, diagnostic telemetry,
and subsequent uses.


以下为辅助材料。依据原任务和项目证据核查其适用性；存在冲突或证据不足时不要盲目执行。

1. 对有进度源的传输，若 `start()` 同步发出缓存的初始包，面板应收到解码后的初始进度；随后到达的进度包仍应正常处理。
2. 完整进度帧的解码可能乱序完成；较旧的帧不得使当前面板显示倒退。
3. 修复须保留公开传输、重试、导航、清理、审计、队列记录及诊断遥测的既有行为。`recordProgress` 的历史记录与 `showProgress` 的面板显示是不同输出。

## 

完成原维护任务，实际修改候选代码并做相关验证。仅在 /workspace 内工作，不查看研究材料、历史、评分器、其他槽位或网络。Node自检使用 /runtime/node，并记录 --version；不安装依赖。最终返回JSON，唯一字段report，最多6000个Unicode字符，报告实际交付、验证与未覆盖范围；补丁从独立工作区归档。

<experience>
# E1 v1 — 公开事件与验证覆盖逐项对应

状态：AI 提炼，待专家确认。仅用于修复阶段；不更改提取技能、Contract、控制器或测试工具。未写入生产经验库。

适用条件：维护涉及异步回调、排队工作，且公开入口能够改变显示、访问身份或活动生命周期。

已观察失败关系：一个历史修复读取了关闭与重开入口，却仅验证正常完成和卸载；卸载自检通过时，关闭／重开仍无相应失效处理。测试一个事件不能证明另一个公开事件的行为。此观察不证明所有关闭都应取消工作。

需要查证的源码位置类型：公开事件入口、宿主调用点、回调登记与完成位置、队列调度和取消位置、共享状态写入及消费者、相邻消费者、任务及项目文档。

应检查的事件顺序：先列出本次修改触及且有依据的公开事件，再分别检查事件发生在请求完成前、排队后、下一活动开始前后的路径。实际驱动文档支持的事件；不能用卸载代替仍挂载的关闭，也不能用正常完成代替身份变更后的旧回调。记录真正执行的顺序、观察和未覆盖项。

应保留的行为：按各自任务／文档或可恢复的既有约定保留已接纳工作、可见结果及相邻消费者的行为。分别核查它们的适用边界。禁止仅从相邻实现或命名推导统一取消政策，禁止补造接口、状态编码或身份约定。

不适用与未知：未涉及异步或生命周期的任务不强加此清单；无明确政策的路径只报告未知，不增造断言。取消保证、同身份重开、嵌套可变数据及错误传播按案例来源核查，不在此经验中规定答案。

来源：u2-contract-repair-diagnostic-v1-20261108/runs/u02/events.jsonl（成功源码读取及两次真实自检）、workspace/src/usePreparation.js、原始score.stdout.json。评分要求是否适用另见 DIAGNOSIS.md，经验不携带其断言、输入值或修复方案。

版本：E1-v1，2026-11-08，单一固定增量；不生成其他版本，不进行搜索或按结果选择。

</experience>
