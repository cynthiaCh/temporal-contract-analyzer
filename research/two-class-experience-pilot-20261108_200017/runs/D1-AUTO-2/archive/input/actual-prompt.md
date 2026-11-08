Repair the transit stop lookup cache: a fresh online-mode query mounted and unmounted entirely offline later calls its signal-consuming query function with a live signal after reconnect. This occurs independently of refetchOnReconnect. Preserve supported query behavior, interfaces, dependencies and build/test configuration. Change product source only.


以下自动Contract为辅助材料，请依据当前任务和源码核查，不盲从无据政策：
修复公交站点查询缓存：一个全新、online 模式的查询若在全程离线时订阅并取消订阅，重连后仍须以有效的 AbortSignal 调用会读取 signal 的 queryFn；此行为不依赖 refetchOnReconnect。保留现有查询行为、接口及依赖和构建/测试配置，仅修改产品源码。按 key 共享查询缓存，订阅返回独立观察者句柄；观察者离开时，未消费取消信号的活跃工作可继续写入缓存，已消费信号的工作可被中止。每次尝试拥有自己的取消控制器与完成身份；取消须恢复先前状态并结算原尝试，迟到结果不得写成新尝试的数据。首次启动遵循 networkMode；暂停续行还受焦点约束。

在 /workspace 内自主定位、修复与验证。只修改产品源码；保留接口、依赖和构建/测试配置。不安装依赖，不访问网络或研究材料。JS使用 /runtime/node，Python使用 /usr/bin/python3 -B。
原始快照、最终源码、补丁差异、日志及评分由外部Python自动保存。请只修业务代码并做必要验证，不创建实验备份、归档补丁或结果汇总文件。最终返回唯一字段report的JSON，简短说明实际修改、验证与未覆盖范围，不超过6000个Unicode字符。