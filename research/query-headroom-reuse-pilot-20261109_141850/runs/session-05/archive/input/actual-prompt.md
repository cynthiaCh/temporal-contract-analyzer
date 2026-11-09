Repair the transit stop lookup cache: a fresh online-mode query mounted and unmounted entirely offline later calls its signal-consuming query function with a live signal after reconnect. This occurs independently of refetchOnReconnect. Preserve supported query behavior, interfaces, dependencies and build/test configuration. Change product source only.


以下自动Contract为辅助材料，请依据当前任务和源码核查，不盲从无据政策：
修复离线期间创建并移除的全新 online 模式查询：重新联网后，不应以仍有效的 signal 调用会读取该 signal 的 queryFn；该现象与 refetchOnReconnect 无关。保留每个 key 的共享缓存和独立观察者句柄。首次启动按 networkMode 判断；暂停的工作在 Promise 后续轮次恢复，并受当前连接与焦点条件约束。实际读取 signal 时同步记录消费；取消请求与尝试结算分别处理。无观察者时，未消费的活动工作可以继续写入缓存；已消费的工作可以中止，取消时恢复先前状态并结算原尝试。晚到的完成结果不得写成新尝试的数据。仅改产品源码，保留接口、依赖及构建/测试配置。

在 /workspace 内自主定位、修复与验证。只修改产品源码；保留接口、依赖和构建/测试配置。不安装依赖，不访问网络或研究材料。JS使用 /runtime/node，Python使用 /usr/bin/python3 -B。
原始快照、最终源码、补丁差异、日志及评分由外部Python自动保存。请只修业务代码并做必要验证，不创建实验备份、归档补丁或结果汇总文件。最终返回唯一字段report的JSON，简短说明实际修改、验证与未覆盖范围，不超过6000个Unicode字符。

以下为冻结经验，按当前证据核查适用性：
R01【适用条件】
适用于共享缓存跨观察者存活、每次尝试各有取消资源、取消能力按实际读取惰性记录，且暂停续行异步恢复的场景。

R02【事件关系】
全新在线模式工作在离线时尚未实际进入、最后一个观察者离开后，应使该尝试不再能在重连续行中以仍有效的取消信号进入；其结算、状态恢复与资源终止须按既有取消语义协调。

R03【排除边界】
不得仅因工作处于暂停、未进入或暂时无观察者，就一概退休：已有成功缓存支撑的后台刷新，以及已实际进入但未读取取消能力的工作，仍可按既有规则继续并写回缓存。

R04【保留行为】
共享的消费记录与某次尝试的取消资源必须保持分别归属；不得因资源是尝试局部的，便迁移、重置或改为尝试局部的共享消费记录。

R05【保留行为】
保留多观察者共享、未知离开无副作用、已消费工作可物理中止并恢复先前状态、未消费已进入工作可后台完成，以及旧尝试晚到完成不得覆盖当前数据。

R06【验证动作】
验证时分别覆盖：目标离线离开后重连时零次进入或以已终止信号进入；合法缓存后台续行与随后读取；以及续行资格、异步时序、状态恢复、观察者复用和晚到完成隔离。
