# 固定 E1 机制匹配开发实验

2026-11-08 Asia/Shanghai。仅 download-polling-restoration-explicit-react18；U2 显式同源变体，适用范围内开发验证，非独立泛化测试。不改经验、技能、评分、历史或全局配置；不提交。

Task 1：前台 invalidateOnClose=true，关闭保留挂载但使 generation 失效、清理 retry/loading；后台关闭仅隐藏，工作继续；卸载另行清理；重开新 generation。候选、原任务、case manifest、oracle 全部匹配历史可信校准，原始 UNDERREACH、reference PASS、两错误变体检出。评分不直接覆盖 retry 已排队后关闭、卸载等项目，单列未知，不能靠总分抵消退步。完整绑定见 admission/cohort/calibration。

Task 2：无有效匹配自动 Contract；只新增一次 K1 提取 gpt-6-sol/low，只见原任务和候选，提取失败即停止。按固定四栏机械取第1栏正文，完整报告保留，不编辑；任何维护评分前冻结正文、摘要和来源及 A/B 实际提示。A=原任务+上一批同一公共提示+自动 Contract；B 仅逐字追加 E1-v1。E1 SHA 57527138a98bfa0d34a432ca82e7b863694b33818aa5a9a3c032ad69f4aaed1e，有既有批准及本次明确授权。

维护 gpt-5.6-terra/medium，priority；准确命令和 profile 配置摘要逐槽归档，不替换型号。A/B各3次，同一起点独立副本，重复内随机排序，种子2026110803只控制调度，不称模型种子。串行并发1；顺序见schedule.json。7顶层会话上限，提取12请求/600秒、维护每槽24请求/600秒，全局156请求/4200秒预留。report 6000 Unicode字符、CLI stdout 16777216 bytes；无已验证推理token硬上限，不声称有。无额外模型预跑、反思、补跑、自动重试、其他案例或GEPA。所有正式调用计预算，资源/交付失败保留；服务、工具、配置、计量或评分异常停止新槽，不替换槽位。

使用上一批修复且零模型验证通过的原生读取后端及策略，复用其session实现，移除旧dispatcher；提取只读、维护独立可写。运行、认证profile、工作副本、临时文件全部在仓库外 /tmp 私有目录，归档排除.runtime/auth及凭证。namespace不挂研究标准、oracle、参考、其他槽位或历史。首个正式槽位真实读取证据计入正式预算。运行前零模型重放当前源码正文及隔离/配置/归档检查。CLI全局配置始末摘要保护。

Task 3：沿用原ungranted评分，逐effect及schedule保留；报告整体、pending到ready、等待、关闭后pending/ready、重开旧/当前响应、后台及原行为。已排队retry后关闭仅能按真实维护轨迹说明自检覆盖，不伪称原评分覆盖。机制清单仅研究事后使用，绝不追加给B提示。检查真实close仍挂载、retry/重开交错、是否用unmount替代、是否改变补丁/行为或仅说明/工具/成本。三配对完整报告，天花板不换题，不宣称稳定/因果/泛化；token、缓存、推理子项、请求、工具、耗时完整计量，无费率不估货币，主聊天准备成本无法取得单列排除。

产物包含全部提示、冻结Contract/E1、来源、配置、轨迹、补丁、原评分、成本、summary和REPORT，提供commit subject/body而不创建提交。
