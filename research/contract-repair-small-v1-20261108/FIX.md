# Task 1：读取工具门修复

旧批已停止，无存活runner/native CLI/bwrap；全部旧文件摘要记录在protected-previous-batch.json。旧失败槽与费用不覆盖、不混算；旧未执行计划已被用户最新指令替代，本目录代码不导入旧调度器。

直接原因：旧read_command对命令文本中的任意`$`一律拒绝，且只允许简单读取命令；两条普通`for f ...; do echo ...; nl ...; done`因此被PreToolUse误拒并kill CLI。不是服务故障或源码缺失。

修复仅位于本目录的read_policy.py和request_guard.py：保留原Pre/PostModelRequest计量、无重试、硬停止；把只读语法门替换为封闭语法解析，支持限定候选文件列表的普通for循环、已绑定循环变量、echo/printf文件标记以及pwd/ls/rg/cat/nl/sed -n/head/tail/wc。循环体仍只允许读取命令，路径解析/通配符结果限制在/workspace，拒绝越界/符号链接逃逸、命令替换、重定向、写入命令、sed原地修改及rg执行钩子。没有开放任意脚本来修复读取，没有关闭工具或隔离。

实际命令仍由原Bash工具执行，候选提取只读挂载，修复仅提供独立可写候选；宿主研究目录、标准/隐藏评分器/参考补丁及其他槽位均未挂载。CLI自身所需profile/output/meter是每槽独立的管理路径，不能看到别槽。此为合作式任务隔离，不夸称防御任意恶意程序的安全证明。

零模型验证见offline-validation.json和offline-v3/：

- 两条历史被拒命令逐字重放，分别对应原版本候选fixture；每份源文件摘要一致，并验证所有长度至少20字符的原正文行均出现于真实成功输出。不是仅检查文件列表或自述。历史fixture重放不是第三个正式实验案例。
- 正常循环/简单读取允许；越界、管理员路径、参考/评分/其他槽位、符号链接逃逸、写入及命令替换受限；实际提取工作区写入失败，维护工作区独立写入成功；Node16与工具后端可用。
- 24次合成Pre/Post后第25次dispatch前硬终止；已知token用量准确保留。失败Post后下一请求被阻断，禁止自动重试。真实本地进程组超时fixture已终止。合成事件不计实验调用或成本。
- 准备阶段两次零模型失败也保留：移除旧调度器时遗漏global_snapshot辅助函数，及现有Python不支持Path.is_relative_to；已修正，原始记录在offline-attempt1/2-error.json及offline*/。未在离线最终PASS前启动模型。

旧经验、提取技能、人工标准、评分器、生产代码和全局配置未改。旧guard原文、修复后的guard及策略文件均归档；正式前冻结其哈希，正式中不再改工具门。
