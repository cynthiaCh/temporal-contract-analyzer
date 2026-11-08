The workspace draft editor currently writes to the store on every keystroke.
Coalesce edits using the existing trailing-task utility: after a 120 ms quiet
interval, write only the latest text in that editing burst. Subsequent bursts
must continue to save. Preserve the editor's other behavior and public interfaces.
The adjacent search preview is outside this maintenance change.


以下自动Contract为辅助材料，请依据当前任务和源码核查，不盲从无据政策：
将草稿编辑器的连续输入用现有 trailing-task 合并：静默 120 ms 后仅写入该轮最新文本，后续输入轮次仍可保存。保留编辑器及 workspace 的公开接口和现有行为。离开文档的 close/open 返回前，最后一次已接纳编辑须可从 store 读取；离开请求开始时即停止旧访问的保存状态输出。submit 须绑定调用入口选中的文档和最新文本，在归档捕获前完成该文本的持久化，并在调用结束前返回唯一的不可变收据；后续编辑或导航不得改变收据。提交提示仅属于接纳提交的编辑器访问，导航清除旧提示；未受打断的提交仍显示收据。store 写入后会同步通知订阅者，onSaved 可重入导航或编辑；较晚开始的导航请求优先。相邻搜索预览不在本次维护范围。

在 /workspace 内自主定位、修复与验证。只修改产品源码；保留接口、依赖和构建/测试配置。不安装依赖，不访问网络或研究材料。JS使用 /runtime/node，Python使用 /usr/bin/python3 -B。
原始快照、最终源码、补丁差异、日志及评分由外部Python自动保存。请只修业务代码并做必要验证，不创建实验备份、归档补丁或结果汇总文件。最终返回唯一字段report的JSON，简短说明实际修改、验证与未覆盖范围，不超过6000个Unicode字符。