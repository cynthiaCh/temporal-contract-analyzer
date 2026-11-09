The workspace draft editor currently writes to the store on every keystroke.
Coalesce edits using the existing trailing-task utility: after a 120 ms quiet
interval, write only the latest text in that editing burst. Subsequent bursts
must continue to save. Preserve the editor's other behavior and public interfaces.
The adjacent search preview is outside this maintenance change.


以下自动Contract为辅助材料，请依据当前任务和源码核查，不盲从无据政策：
Coalesce edits to the workspace draft editor with the existing trailing-task utility. After 120 ms without another edit, commit only the latest text in that burst; later bursts must also commit. A pending accepted edit must be in the store before close or open returns, including when navigation selects another document. Keep the edit bound to its document. Retire the departing save badge before its save can notify subscribers. A save integration may navigate synchronously; a navigation request started inside that callback takes precedence over the earlier request. Preserve synchronous public interfaces. Leave the transient search preview outside this change.

在 /workspace 内自主定位、修复与验证。只修改产品源码；保留接口、依赖和构建/测试配置。不安装依赖，不访问网络或研究材料。JS使用 /runtime/node，Python使用 /usr/bin/python3 -B。
原始快照、最终源码、补丁差异、日志及评分由外部Python自动保存。请只修业务代码并做必要验证，不创建实验备份、归档补丁或结果汇总文件。最终返回唯一字段report的JSON，简短说明实际修改、验证与未覆盖范围，不超过6000个Unicode字符。