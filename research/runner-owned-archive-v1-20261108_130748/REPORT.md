# 维护模型机械归档职责移交：离线实现报告

## Task 1：现状核对及已确认的重复工作

HEAD 为 `40919fb9f33f2336a581c7d013d4d5d888505387`。初始 tracked diff 为空，已存在未跟踪的 `research/transfer-reflection-crosslang-20261108_202000/`，本轮保留其全部内容。未发现适用的祖先、项目或 research 层 AGENTS.md；其他历史目录中的指令不适用。

直接检查本批 runner/native_backend/control、6 份实际维护 prompt、实际事件及 `contract-repair-small-v1-20261108/runner.py`。证据见 [history-audit.json](history-audit.json)，包含原路径、SHA256、事件行号、item ID、完整命令与退出码。

已确认：

1. 原 Python 运行器已经创建独立工作区，保存起点摘要、实际 prompt、事件（含工具输出）、stderr、原始回答、请求 ledger、patch.diff、receipt 及评分 stdout/stderr。它保留的是可变工作区，并没有独立的最终快照；初始源码来自外部冻结材料，槽位内仅保存起点 hash。
2. 6/6 份实际维护 prompt 含“；补丁从独立工作区归档。”。这是归档职责有歧义的句子；没有明确要求 before/after 副本、命名 patch-archive 目录、整理成本或为归档失败写脚本。不能据此把每个额外动作都归因为明确指令。
3. 两次 JS 经验回验中，实际轨迹证实了 patch 制作、复制业务源码用于 patch-check、反向/正向应用、检查 .orig/.rej 及反复修改补丁。归档核查选取了21条命令证据，逐条区分纯归档与混合业务检查，不把混合命令全部折算成归档请求。另保存19项 patch 工件文件变更证据。这是证据清单，不是完整成本归因或“可节省请求数”。
4. 模型创建的 patch 与副本实际留在业务工作区，随后也被外层 diff 捕获，形成重复归档材料。旧 native_backend 将宿主 cli-output 和 meter 目录挂进执行 namespace；prompt 本身没有给出宿主 research 归档路径。应区分宿主命令记录中的路径与模型真正可访问的挂载。
5. 原 diff 代码未检查退出码；异常分支可能在生成最终 diff 前结束；归档错误与模型失败未完整分离。通用搜索找到的 archive_outputs.py 是历史匿名化流程，不是可直接修改的非冻结公共会话归档模块。

## Task 2：Python 自动归档与 prompt 调整

所有新增文件都在本目录，未修改冻结历史文件。主实现：

|文件|实际改动/职责|
|---|---|
|archive.py|冻结完整原始候选/任务/prompt/config；独立工作区；停止后完整最终快照、摘要、差异、日志/输出/用量与额外文件来源；异常结构化记录|
|runner.py|复用原 session 的单会话启动、角色参数、超时与停止、body proof、计量判定与外部评分位置；将归档接入 finally；没有调度器或自动重试|
|native_backend.py|复用原 Codex 自主工具循环/namespace/flags；取消 host output 与 meter 的挂载；从事件流收集最终回答|
|guard_server.py / guard_client.py|把原 request_guard.account 的文件写入放到外层 Python，通过本地 socket 传递 hook 事件及允许/拒绝决定；不是 ReAct 或 LLM 控制器|
|prompts.py / adapted-prompts/|仅移除已确认的旧归档句，插入用户指定的新职责说明；两组共用同一函数，经验原文保持原样|
|test_offline.py / offline-validation.*|临时候选、假事件/进程及实际 namespace 的离线验证|

复用来源和函数在 [provenance.json](provenance.json)。request_guard.py、read_policy.py、schema、研究配置和模型缓存为注明来源的副本；守卫/读取规则未变，未新增 cp/diff/for 等 shell 关键词黑名单。模型与 effort、24/12 请求上限、600秒上限、结构化简短输出与业务自验证要求保留；没有新增请求预算。主会话只启动一次进程，归档只调用固定 Python/现有 diff，不调用 LLM。

新说明为：

> 原始快照、最终源码、补丁差异、日志及实验结果由外部运行器自动保存。请集中完成业务修复与必要验证，不创建用于实验留档的备份副本、补丁归档目录或结果汇总文件。结束时按现有输出格式简要说明修改与验证结果。

[prompt-equivalence.json](prompt-equivalence.json) 验证两个候选的 AUTO 与 AUTO_EXP 共同修改；原任务、Contract、经验及其他说明可逐字逆变换回旧输入。示例使用旧经验只是离线字节一致性检查，不改变该经验此前未接纳的状态。

改造后的生命周期：

1. 开始前，Python 保存完整原始快照、输入摘要、任务、实际 prompt 和配置，然后建立独立可写业务工作区。归档目录为工作区的 sibling，不挂进 namespace。后续原生调用还需新的冻结输入清单与显式开关；默认禁止模型执行。
2. 执行中，Python 持续保存事件/工具输出/stderr，外层账本同步计量。namespace 仅保留合法源码读取、编辑、自验证以及已有 CLI 运行所需的控制设施，不暴露宿主归档目录。
3. 停止后，无论正常、超时、异常退出或无最终回答，都尽可能快照最终候选、生成 diff 和收集已有输出。缺失回答/用量明确标注，不编造成功或补零。归档失败写入独立 archive-status、archive_stop_reason 和必须停止标记，不覆盖模型原 exit/failure_class/stop_reason，也不请求模型修复。
4. diff 的0/1分别记录正常无文本差异/有差异，其他退出码或工具异常记录 ERROR；不将失败当无改动。采用现有 GNU diff 的逐文件 /dev/null 标签解决新增/删除歧义。完整最终快照和 manifest 另外保留二进制、符号链接、空文件/类型/权限信息，文本补丁不是这些元数据的唯一载体。
5. 后续可信外部评分由调用方显式提供，输入始终是同一最终快照；评分前后检查摘要。没有评分 callback 时不运行评分。若归档失败则阻止评分交接。评分异常/修改源码也单列，不静默修复或删除文件。
6. 对额外文件保留原貌；能绑定 file_change 事件的记录事件来源，未知来源保持未分类，不因 .patch 或 backup 名称删除合法文件。它们仍包含在最终快照和评分输入中，影响不会被清理掩盖。

## Task 3：验证、工作量和剩余限制

最终15项离线测试全部通过，详见 [offline-validation.log](offline-validation.log) 与 [offline-validation.json](offline-validation.json)：

|覆盖|结果|
|---|---|
|无修改、完整快照与空diff|PASS|
|修改、新增、删除、原始快照不变、生成补丁实际回放到独立副本|PASS|
|超时、异常退出、CLI不存在、无最终回答，仍保留已有候选/轨迹/差异|PASS|
|diff返回2或工具不存在，如实记录且不覆盖模型原因，不重试、不调用模型|PASS|
|真实bwrap前缀下宿主归档/output/meter不可访问，合法读/编辑/cp/diff/for仍可用|PASS|
|归档前后业务树摘要不变；复制最终候选后再交给可信评分回调|PASS|
|已有假评分复制收集、评分修改最终候选被识别且不静默回滚|PASS|
|AUTO/AUTO_EXP共同职责、原任务/Contract/经验字节不变|PASS|
|额外文件来源、合法.patch与backup保留；符号链接/二进制/模式完整快照|PASS|
|默认不允许真实模型执行，不能增加时间上限；原角色请求预算保持|PASS|

首轮暴露删除补丁回放和新增符号链接的 GNU diff 边界，已修正并保留失败摘要；后续新增来源标注 fixture 曾误用多行 JSON，改为真实 JSONL 后通过。最终日志对应当前实现。只在代码修正后重做相关快速离线验证，没有重跑历史案例或评分。

本轮工作是一次研究运行器改造和离线验证，非新训练/验证批次。**实验模型调用=0，维护模型执行=0，案例评分重跑=0。** 假进程、synthetic ledger、本地 socket 和复制的 FAKE score 均不计入实验请求或评分。没有安装依赖、修改生产业务/案例/评分政策/全局模型配置，也未创建 Git 提交。

历史输入、轨迹、成本、结论和旧经验接纳状态保持原样；不能用新实现追溯重算旧实验收益。未来若验证省请求或修复率，两组必须采用同一版新运行器及职责说明，在另行授权且冻结的新协议中对照。本轮不声称节省任何请求或提高修复率。

限制：验证使用假事件/进程，未用真实模型检查新的归档职责说明是否总被遵守；本地namespace与hook通路已实际测试，但完整模型服务调用本轮未执行。所有候选文件都保存，但没有自动把额外文件语义分类为“垃圾”。文本patch与完整文件系统快照的能力边界分开记录。此实现是单会话归档模块，未替换、恢复或改写任何历史批次调度器。

完整性及无修改检查见 integrity-validation.json；本轮文件清单与摘要见 ARTIFACTS.sha256。推荐提交信息见 COMMIT_MESSAGE.txt，未执行提交。
