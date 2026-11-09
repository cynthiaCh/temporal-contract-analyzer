A warm progress source in the museum image ingestion shows no initial progress until a later packet arrives. Restore the initial update while preserving the existing transfer, retry, navigation, cleanup and audit behavior, ordinary streaming and subsequent uses. The queue-record format is outside this fix.


以下自动Contract为辅助材料，请依据当前任务和源码核查，不盲从无据政策：
Restore the cached initial progress update when a warm source synchronously emits during start. Each selected or retried attempt has a subscription; later packets and later uses of the same source must continue to work. Record every accepted event once after decode completes, even if its visit has closed. Show progress only for the current visit. Preserve transfer cancellation, accepted retry and navigation ownership, cleanup, queued notices, and the existing queue-record format. Starting the source can invoke a callback before start returns; the candidate calls start before listen.

在 /workspace 内自主定位、修复与验证。只修改产品源码；保留接口、依赖和构建/测试配置。不安装依赖，不访问网络或研究材料。JS使用 /runtime/node，Python使用 /usr/bin/python3 -B。
原始快照、最终源码、补丁差异、日志及评分由外部Python自动保存。请只修业务代码并做必要验证，不创建实验备份、归档补丁或结果汇总文件。最终返回唯一字段report的JSON，简短说明实际修改、验证与未覆盖范围，不超过6000个Unicode字符。