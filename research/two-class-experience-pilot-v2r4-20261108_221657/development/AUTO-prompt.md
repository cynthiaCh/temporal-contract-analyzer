Repair the transit stop lookup cache: a fresh online-mode query mounted and unmounted entirely offline later calls its signal-consuming query function with a live signal after reconnect. This occurs independently of refetchOnReconnect. Preserve supported query behavior, interfaces, dependencies and build/test configuration. Change product source only.


以下自动Contract为辅助材料，请依据当前任务和源码核查，不盲从无据政策：
修复离线期间创建并移除的全新 online 模式查询：重新联网后，不应以仍有效的 signal 调用会读取该 signal 的 queryFn；该现象与 refetchOnReconnect 无关。保留每个 key 的共享缓存和独立观察者句柄。首次启动按 networkMode 判断；暂停的工作在 Promise 后续轮次恢复，并受当前连接与焦点条件约束。实际读取 signal 时同步记录消费；取消请求与尝试结算分别处理。无观察者时，未消费的活动工作可以继续写入缓存；已消费的工作可以中止，取消时恢复先前状态并结算原尝试。晚到的完成结果不得写成新尝试的数据。仅改产品源码，保留接口、依赖及构建/测试配置。

在 /workspace 内自主定位、修复与验证。只修改产品源码；保留接口、依赖和构建/测试配置。不安装依赖，不访问网络或研究材料。JS使用 /runtime/node，Python使用 /usr/bin/python3 -B。
原始快照、最终源码、补丁差异、日志及评分由外部Python自动保存。请只修业务代码并做必要验证，不创建实验备份、归档补丁或结果汇总文件。最终返回唯一字段report的JSON，简短说明实际修改、验证与未覆盖范围，不超过6000个Unicode字符。