Repair the transit stop lookup cache: a fresh online-mode query mounted and unmounted entirely offline later calls its signal-consuming query function with a live signal after reconnect. This occurs independently of refetchOnReconnect. Preserve supported query behavior, interfaces, dependencies and build/test configuration. Change product source only.


以下自动Contract为辅助材料，请依据当前任务和源码核查，不盲从无据政策：
修复离线期间创建并移除的全新 online 模式查询：重新联网后，不应以仍有效的 signal 调用会读取该 signal 的 queryFn；该现象与 refetchOnReconnect 无关。保留每个 key 的共享缓存和独立观察者句柄。首次启动按 networkMode 判断；暂停的工作在 Promise 后续轮次恢复，并受当前连接与焦点条件约束。实际读取 signal 时同步记录消费；取消请求与尝试结算分别处理。无观察者时，未消费的活动工作可以继续写入缓存；已消费的工作可以中止，取消时恢复先前状态并结算原尝试。晚到的完成结果不得写成新尝试的数据。仅改产品源码，保留接口、依赖及构建/测试配置。

在 /workspace 内自主定位、修复与验证。只修改产品源码；保留接口、依赖和构建/测试配置。不安装依赖，不访问网络或研究材料。JS使用 /runtime/node，Python使用 /usr/bin/python3 -B。
原始快照、最终源码、补丁差异、日志及评分由外部Python自动保存。请只修业务代码并做必要验证，不创建实验备份、归档补丁或结果汇总文件。最终返回唯一字段report的JSON，简短说明实际修改、验证与未覆盖范围，不超过6000个Unicode字符。

以下为冻结经验，按当前证据核查适用性：
R01【适用条件】
适用于按键共享缓存、多个独立观察者共享同一工作、每次尝试持有独立取消资源，且信号读取会惰性记录消费、暂停工作可异步续行的查询流程。不得把控制器属于某次尝试，推论为消费记录也必然属于该尝试。

R02【事件关系】
区分首次准入、暂停后的资格恢复、实际进入执行、信号实际读取、重试抑制、取消结算、物理中止与晚到完成。首次启动按网络模式判定；暂停续行还受连接和焦点约束并在后续轮次执行；取消后的旧完成不得提交为新尝试结果。

R03【验证动作】
验证新建、未缓存的 online 模式请求在离线期间最后观察者离开后再重连时，若进入执行则 signal 已中止；零次进入与该种进入均可接受。另分别验证已进入未消费工作的后台写缓存、缓存刷新及后续消费、已消费取消后的状态恢复与晚到结果隔离，以及观察者、键和既有时序行为。

R04【保留行为】
保留共享缓存与独立观察者句柄：非最后观察者离开不得取消共享工作，未知移除无效。已实际进入且未消费的工作可在无观察者后完成；已消费的取消才中止资源、恢复该尝试前状态并阻止晚到覆盖。不能仅因“暂停或尚未进入”就退休已有成功缓存的合法刷新。

R05【排除边界】
不将规则扩展为“所有无观察者工作一律取消”，也不以资源归属重写共享消费归属；更不把一次通过的多项检查视为已隔离的修复原因。对于已被接受的续行、重试调度和缓存刷新，须按其各自时序与资格条件处理。
