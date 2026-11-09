The museum accession notes currently writes on every edit. Coalesce edits using the existing trailing utility: after a 120 ms quiet interval, write only the latest text in that burst. Subsequent bursts must continue to save. Preserve other behavior and public interfaces. The adjacent preview is outside this change.


以下自动Contract为辅助材料，请依据当前任务和源码核查，不盲从无据政策：
馆藏登记笔记的 edit(text) 应使用现有 Trailing 工具合并连续编辑：静默 120 ms 后只将该批次最新文本写入对应记录；后续批次仍须保存。已接纳的编辑在离开或提交边界返回前须完成持久化，不能因取消定时任务而丢失。提交应绑定入口时选中的记录及文本：capture 调用前存储须已有该文本，并返回一份不可变收据；后续导航不得撤销已接纳的提交。保存事件的可见呈现归属当前挂载的订阅，离开时立即结束；提交通知归属原访问，导航清除通知，访问未中断时显示通知。保留 open、edit、close、submit、dispose 的同步接口及其他既有行为。相邻预览不在本次修改范围。

在 /workspace 内自主定位、修复与验证。只修改产品源码；保留接口、依赖和构建/测试配置。不安装依赖，不访问网络或研究材料。JS使用 /runtime/node，Python使用 /usr/bin/python3 -B。
原始快照、最终源码、补丁差异、日志及评分由外部Python自动保存。请只修业务代码并做必要验证，不创建实验备份、归档补丁或结果汇总文件。最终返回唯一字段report的JSON，简短说明实际修改、验证与未覆盖范围，不超过6000个Unicode字符。