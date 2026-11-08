# 单案例 Terra/medium 自动Contract难度筛选

2026-11-08 Asia/Shanghai。AI辅助研究，不冒称独立人工复核。本轮不是E1效果实验，禁止追加E1/人工Contract、新验证提醒、经验、GEPA、反思、候选替换、补跑或第二例；不创建提交，不修改原有代码/评分/经验/全局配置/历史。

Task 1：调用前唯一选定 `download-polling-restoration-python3-eval-v2`。它是登记在download-polling-restoration cluster中的非explicit Python派生及eval-v2修订，原parent=canonical react18，不是low-cue核心。E1来源是low-cue arm的u02，不是canonical；这里只匹配关闭/重开/已排队retry/旧响应机制，绝不交付E1。此case未参加近期explicit/Vue2/Vue3或transfer对照，未找到匹配固定K1的Terra/medium自动Contract记录。现有Terra/medium裸任务与人工Contract各1次PASS，不能冒充自动Contract通过或失败；其他模型失败仅背景，不能用作本轮难度证据。来源、版本、登记和历史分层见selection/source-relationship/historical-context及source/。原low-cue不可见关闭政策未移入。本例为已暴露同源开发任务、不是独立泛化或预先证实难例。

政策：原任务pending持续检查、ready才交付；README明确异步false/true、外部调度及前后台分属owner。候选可见DialogResource.close→invalidate（generation++、cancel retry、清loading），reopen新generation，check/retry均有disposed/generation guard；dispose按自身现有快照语义清资源。WorkspaceJob.close只隐藏并继续，start保留其现有行为，不统一套前台规则。评分不要求猜无文档身份编码或取消绝对保证。原始起点UNDERREACH、bounded reference PASS、六个既有mutants全部检出，8次零模型校准不计模型难度。评分使用原ungranted，oracle文件版本与冻结摘要逐项关联，不改断言。没有因作者旧确认栏空白机械阻断可见源码支持政策。

Task 2：无有效完全匹配自动Contract，新增提取最多1次。固定K1原文/gpt-6-sol/low，只提供原任务+候选可见材料，提取只读；无E1、人工标准、评分、参考或历史输出。严格四栏，机械交付第1栏正文，完整报告保留，既有规则不改；不人工补齐。全文、正文、摘要、来源、交付范围及实际prompt在首次维护评分前冻结。提取无效/工具失败即停，不重生成。提取作为准备，不能并入维护成功率。

两个维护会话均仅同一原任务+同一候选+上一批同一公共指令+同一自动Contract。公共指令原样保留（含既有Node路径说明，不新增Python专用提示/自检脚本）。修复gpt-5.6-terra/medium、priority显式配置；模型目录与实际命令/请求hook核对，不静默替换。提取gpt-6-sol/low。服务器tier路由不独立认证。原生Codex自主exec、已修复读取后端，不用ReAct外层。source-body证据只将后缀从JS扩为本例Python，模型权限/读取门不变，正式前冻结。每槽独立可写候选，从相同3文件摘要起点复制，不接续补丁、不共享报告。执行模型不挂研究/评分/reference/历史/其他槽位；认证、临时运行、工作区均Git外，profile不归档。源码正文与隔离零模型检查通过才开跑；首个正式提取真实读取证据计正式预算。

准确顺序x01提取→r1自动Contract→r2自动Contract，串行。最多3顶层会话、60底层请求；提取12请求/600秒，维护各24请求/600秒。最终report6000 Unicode字符、CLI stdout16MiB；无核验推理token原生硬上限。反思/GEPA/预跑/重试/补跑/候选替换均0。配置/工具/服务/计量/评分关联异常立即停后续槽位、单列异常、不算模型行为失败。正常模型格式/资源交付失败也标无效，不替换。两槽原计划完成即停，无论成功率。

Task 3：事前筛选规则（不得按结果修改）：

- 任一维护槽无效或未启动（包括提取无效导致未启动）：证据不足，最终“证据不足”。
- 两次有效均FAIL，且至少一次存在评分依据充分且真正驱动了E1相关关闭/重开/排队后retirement/旧响应/前后台政策关系的错误效果：重复失败候选，最终“可作为重复失败候选”。
- 一次PASS一次FAIL：表现不稳定；若失败确有上述E1相关关系，最终“可作为不稳定候选”；若仅其他机制失败，单列不稳定但最终“暂不适合”E1。
- 两次有效均PASS：本批未发现提升空间，最终“暂不适合”。
- 两次均FAIL但仅其他机制/前置轮询失败、未证E1相关错误效果：不按整体FAIL冒充E1适用难例，最终“暂不适合”。

E1关系集合依据原oracle的close-before-response、foreground-close-scheduled、same-token/multiple-reopen、current-ready-before-old-pending、dispose、background-close/start/ownership等，逐assertion与实际schedule核查。若close-scheduled只因“没有安排retry”前置断言失败，不能冒充已经验证到错误的关闭后效果；纯polling/readiness单列。无需与E1失败根因完全一致，但必须写明机制证据与未知，不能从模型自述或总分推断。

评价保存整体、所有effect、schedule中间状态、原通过项丢失/新增forbidden、实际prompt、配置、源正文证据、完整事件、源码补丁/附带文件、原始score与全部请求/工具/缓存/推理/耗时。自检不替代原评分；错误自检、预算、服务与行为失败区分。不新增隐藏要求。无核验价格不估货币，主聊天准备/分析token无法取得单列排除。筛选结果仅供选例；未来E1对照必须另立批次、独立基线，不能拼接本轮失败与未来增强组。

产物：PLAN、选择/来源/历史、配置/准入、Contract全文和正文/摘要/范围、两份维护记录、summary.json、REPORT.md和建议Git subject/body。旧文件/结果保持原样，本批结束即停止。
