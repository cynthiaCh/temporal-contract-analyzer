Repair the museum exhibit lookup cache: a fresh online-mode query mounted and unmounted entirely offline later calls its signal-consuming query function with a live signal after reconnect. This occurs independently of refetchOnReconnect. Preserve supported query behavior, interfaces, dependencies and build/test configuration. Change product source only.


以下自动Contract为辅助材料，请依据当前任务和源码核查，不盲从无据政策：
修复展品查询缓存中离线挂载后卸载的情形：新建的 online 模式查询在全程离线且尚未实际读取 signal 时，重连后仍可恢复请求；请求函数随后读取 signal 时，应获得有效的 signal，并将消费归属记录到该次执行。此行为不依赖 refetchOnReconnect。保留按键共享缓存、独立观察者句柄、现有订阅与状态接口，以及网络模式、聚焦、重试、取消和恢复语义。最后一个观察者离开后，已消费的活动请求可取消并回退原状态；未消费的工作可在观察者离开后完成并写入缓存。异步完成只影响其所属执行尝试，不能将旧尝试结果写入新尝试。仅修改产品源码，保持依赖及构建、测试配置。

在 /workspace 内自主定位、修复与验证。只修改产品源码；保留接口、依赖和构建/测试配置。不安装依赖，不访问网络或研究材料。JS使用 /runtime/node，Python使用 /usr/bin/python3 -B。
原始快照、最终源码、补丁差异、日志及评分由外部Python自动保存。请只修业务代码并做必要验证，不创建实验备份、归档补丁或结果汇总文件。最终返回唯一字段report的JSON，简短说明实际修改、验证与未覆盖范围，不超过6000个Unicode字符。