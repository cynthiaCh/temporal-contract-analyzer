A transfer with a warm progress source shows no initial progress until a later
packet arrives. Restore the initial progress update without changing the public
transfer, retry, navigation, cleanup, or audit behavior. Preserve the ordinary
streaming path and subsequent uses. The queue-record format is outside this fix.


以下自动Contract为辅助材料，请依据当前任务和源码核查，不盲从无据政策：
Restore the initial progress update from a warm progress source. The source may emit cached progress synchronously when a subscription starts, but the current watcher starts it before attaching the listener. Accepted events must be decoded and audited once, even if decoding completes after the visit closes; visible progress belongs only to the current visit. Preserve later streaming events, reuse of the source across visits, retry and cancellation behavior, navigation ownership, cleanup, and the existing queue-record format.

在 /workspace 内自主定位、修复与验证。只修改产品源码；保留接口、依赖和构建/测试配置。不安装依赖，不访问网络或研究材料。JS使用 /runtime/node，Python使用 /usr/bin/python3 -B。
原始快照、最终源码、补丁差异、日志及评分由外部Python自动保存。请只修业务代码并做必要验证，不创建实验备份、归档补丁或结果汇总文件。最终返回唯一字段report的JSON，简短说明实际修改、验证与未覆盖范围，不超过6000个Unicode字符。

以下为冻结经验，按当前证据核查适用性：
R01【适用条件】
适用于可复用来源、每次尝试独立订阅且进度回调可同步重入导航的场景；不得以文件相同推断访问身份相同。

R02【事件关系】
对可能在启动期间同步发出缓存状态的来源，应先使该尝试的接收资格生效，再触发启动；后续流式事件仍按该尝试处理。

R03【保留行为】
事件一经当前访问接纳，解码完成后必须保留一次审计；访问退休后不再接纳新事件，且已退休尝试不得产生可见进度。

R04【保留行为】
同步重入后，新的访问保有自己的界面与取消资源；旧尝试的后续清理不得夺取新所有者，既有重试和取消语义保持不变。

R05【验证动作】
验证缓存首帧、后续流式帧、延迟解码、隐藏及切换/重开都分别满足接纳、审计与可见性义务；特别检查重入后退休订阅不再接纳新帧。

R06【排除边界】
本次范围不扩展队列记录或公共接口，也不以进度维护改变共享来源复用、独立工作区、重试、取消或导航策略。
