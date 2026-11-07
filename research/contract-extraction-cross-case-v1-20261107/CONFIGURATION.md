# 执行配置来源与覆盖边界

v2历史记录仅能证明全局service_tier在末槽复制配置之后新增；来源仍未知。本轮没有重构不存在的历史配置，也不宣称服务端路由相同。

本轮不读取用户全局config作为会话配置：每槽从冻结research-config.toml复制配置，显式固定gpt-6-sol/low/service_tier=priority，CLI再用同值覆盖；保留原无重试provider配置、code_mode_host/shell_tool后端及关闭其他工具的flags。模型目录使用同一冻结models-cache.snapshot.json；只有认证复制到独立临时目录，结束后移除。不修改全局配置、不安装依赖。

每槽configuration-before.json、configuration-after.json保留实际研究配置文本及摘要、全局配置摘要与非敏感设置快照，receipt.json保留完整argv；input-config-equivalence.json证明八槽配置副本前后字节一致。全局config本轮前后摘要相同。客户端配置可追溯不等于服务器实际service tier或模型部署可独立认证。

相对U2 v2的必要适配：case-aware材料路径与八槽调度；去除反思入口；固定研究配置而非复制全局config；每槽正式前后快照。request_guard仅将候选根目录README.md加入sed只读文件名允许范围，以兼容C3文档；其文件可见范围和其他命令限制不扩大，两个条件使用同一guard。无node/python业务执行、网络读取或写入权限。

上限保持600秒、report6000字符、12底层请求/槽；全局继续采用49请求硬上限。离线检查的直接读取和模拟hook计数不调用模型；首份真实运行门见first-run-gate.json。正式共8会话/25请求，剩余预算不追加调用。
