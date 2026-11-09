A transfer with a warm progress source shows no initial progress until a later
packet arrives. Restore the initial progress update without changing the public
transfer, retry, navigation, cleanup, or audit behavior. Preserve the ordinary
streaming path and subsequent uses. The queue-record format is outside this fix.


以下自动Contract为辅助材料，请依据当前任务和源码核查，不盲从无据政策：
Restore the initial progress update from a warm progress source. The source may emit cached progress synchronously when a subscription starts, but the current watcher starts it before attaching the listener. Accepted events must be decoded and audited once, even if decoding completes after the visit closes; visible progress belongs only to the current visit. Preserve later streaming events, reuse of the source across visits, retry and cancellation behavior, navigation ownership, cleanup, and the existing queue-record format.

在 /workspace 内自主定位、修复与验证。只修改产品源码；保留接口、依赖和构建/测试配置。不安装依赖，不访问网络或研究材料。JS使用 /runtime/node，Python使用 /usr/bin/python3 -B。
原始快照、最终源码、补丁差异、日志及评分由外部Python自动保存。请只修业务代码并做必要验证，不创建实验备份、归档补丁或结果汇总文件。最终返回唯一字段report的JSON，简短说明实际修改、验证与未覆盖范围，不超过6000个Unicode字符。