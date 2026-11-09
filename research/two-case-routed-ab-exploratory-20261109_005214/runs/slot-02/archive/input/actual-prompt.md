Repair the museum exhibit lookup cache: a fresh online-mode query mounted and unmounted entirely offline later calls its signal-consuming query function with a live signal after reconnect. This occurs independently of refetchOnReconnect. Preserve supported query behavior, interfaces, dependencies and build/test configuration. Change product source only.


以下自动Contract为辅助材料，请依据当前任务和源码核查，不盲从无据政策：
候选自动 Contract：对同一 key 的在线模式查询，若首次订阅时离线，首次执行应暂停；若该观察者在重连前退订，且该次执行尚未实际开始，重连不应让已离开的观察者触发 queryFn，也不应向该次执行交付可用 signal。此要求独立于 refetchOnReconnect。保留共享缓存、观察者接口及受当前条件约束的暂停、重试和取消语义。当前源码中，离线首次订阅创建未结算的 attempt；退订仅设置 retry_cancelled；online 事件仍可将该 attempt 排入续行并调用 request。

在 /workspace 内自主定位、修复与验证。只修改产品源码；保留接口、依赖和构建/测试配置。不安装依赖，不访问网络或研究材料。JS使用 /runtime/node，Python使用 /usr/bin/python3 -B。
原始快照、最终源码、补丁差异、日志及评分由外部Python自动保存。请只修业务代码并做必要验证，不创建实验备份、归档补丁或结果汇总文件。最终返回唯一字段report的JSON，简短说明实际修改、验证与未覆盖范围，不超过6000个Unicode字符。