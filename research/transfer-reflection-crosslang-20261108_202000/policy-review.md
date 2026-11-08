# AI 辅助政策核查（非人工批准）

两例原任务一致，README 要求恢复 warm 初始帧并保留 public transfer/retry/navigation/cleanup/audit/queue/telemetry；full frame 不得因解码乱序倒退。候选正文已阅读并归档，来源摘要见 cohort/version-correspondence。

|关系|明确要求与源码依据|边界|
|---|---|---|
|同步启动|两README明确 start 可同步发缓存；任务要求恢复初始帧；JS progress.js 与 Python Subscription.attach 当前先start后注册|Python额外提示多包及sink切换，不能删除|
|接纳与完成|README要求保留取消/历史；JS transfer.js abort signal 与停止监听，Python Attempt.aborted、cancel 和 listener；开始时过期的工作不应新解码；已接纳闭包当前继续完成|“仅当前非取消attempt可接纳”是维护保留要求结合源码归属推导，不仅靠参考答案|
|记录与显示|README 明确 history vs open panel；JS queue.js record 无当前性guard，receive守 current===visit；Python Session.enqueue audit闭包无guard，view current(v)|已接受工作的history保留、旧visit不显示，有可见依据|
|帧顺序|full frame、decode可异序；retry仍同visit，两例README；JS queue/retry 和Python Session/Visit|visit范围freshness为目标义务推导，不要求具体token实现；值非时钟，Python明示可下降|
|重入清理|JS progress-source.js removal先提交可同步导航，panel.js清空owner/自增request并回验；Python README及select/hide/dispose 同构|保留既有request优先级；不推导任意外部异步政策|
|retry|JS retry.js注释一次接受命令、cancel先enqueue，notice.js归属；Python Session.retry取消→捕获原visit enqueue，条件notice；README要求保留retry与queue|不能因已过时删除已接受队列命令；只能约束物理/显示归属|
|telemetry|两README明确独立消费者保持原行为；JS telemetry注释 live-only、先start后listen；Python Telemetry相同先start后listen|不能全局改成register-first；已接纳delta完成保留|
|schema|README明确四字段、仅另授权byteCount；本批ungranted|expanded正控制应OVERREACH|

未知与范围：不要求拒绝解码/Promise rejection、物理完成后行为、任意恶意宿主；Python README明确排除部分情况。JS具体宿主的多同步帧可由外部host实现，实际reachability需观测，不声称与Python纯语言等价。参考通过只是工具校准，不替代上述政策依据。

评分边界：登记mutants覆盖admission/freshness/effect split/cleanup/telemetry，Python另有attempt-local freshness。非每个断言独立mutant校准，计数不等于独立义务；assertion-obligation-map 与 mutation-map 原样留评价侧。实际Python为宿主python3（frozen-config记录版本），与声明3.8.10分别记录，不伪造相同版本。
