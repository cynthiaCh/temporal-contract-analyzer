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
适用于共享来源可被多次访问复用、每次尝试独立订阅，且可见反馈可同步重入导航的场景；相同数据对象不等于相同访问身份。

R02【事件关系】
对启动时可能同步发出缓存事件的来源，须先使该尝试具备接纳资格再启动；后续流式事件仍依该尝试资格处理。

R03【保留行为】
访问退休即停止接纳后来事件，即使清理或移除能力尚未返回；此限制不得依赖延后的物理清理。

R04【保留行为】
退休前已接纳的事件在解码结算时仍须恰好保留一次审计；该结算不得授权退休访问接纳新事件或产生可见进度。

R05【保留行为】
同步重入后，新访问保有自己的界面与取消资源；旧访问的后续结算或清理不得夺取新所有者，并保持既有重试、取消和入口绑定记录语义。

R06【验证动作】
验证同步导航后且外层启动尚未返回时，同一来源的后续事件：分别覆盖隐藏、切换和同源重开，并独立核对退休访问拒收、此前接纳事件的延迟审计及当前访问的有效可见进度；仅在返回后的清理测试不足以覆盖该窗口。

R07【排除边界】
本次仅处理进度接纳时序与生命周期边界；不扩展记录或公共接口，也不改变共享来源复用、独立工作区、重试、取消、导航、资源所有权或既接纳审计策略。
