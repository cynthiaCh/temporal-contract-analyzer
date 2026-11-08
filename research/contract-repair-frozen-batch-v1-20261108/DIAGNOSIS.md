# 已有失败定位（2026-11-08）

AI 离线调查；不是独立盲审。没有运行新维护模型。历史目录的200份非运行时归档文件已完整读取／解析并记录摘要，见 evidence/historical-inventory.json；未把 REPORT.md 当唯一证据。原任务、五份候选文件、完整提取输出、实际prompt、六槽完整工具输出、最终补丁及原始评分的核查见 evidence/historical-run-review.json。历史协议全部文件摘要匹配（evidence/historical-freeze-check.json）。没有发现适用的祖先或所选目录 AGENTS.md；归档 GEPA 内部 AGENTS.md 不适用本研究。

## Task 1：可以定位什么

唯一有效模型Contract维护是 u02/M-r1。u06/M-r2 请求上限中断，不能用作行为失败。u02 正常轮询通过，关闭／重开五项失败。**可以确认的是修复实现和可见验证没有覆盖这些事件；不能确认它主要由Contract提取失败造成。**原维护任务只明示 pending 继续、ready 后交付，没有规定关闭后丢弃结果等全部政策；原评分将历史额外规格作为必答。提取报告已正确辨认生命周期风险并保留政策未知。输入—评分适用性是因果归因前最靠前的有效性问题，必须先隔离，不能靠经验补造政策。

本次选择的单一候选经验仅针对独立可证的 D（验证事件替代），不是声称解决五项评分失败。原低线索U2暂缓进入正式批量；保留其诊断和来源身份。用政策可从候选直接恢复的显式同源任务作开发变体；其他来源单独报告。经验未经批准不能称专家经验或执行增强组。

分类：A Contract遗漏；B 错误或过宽；C 正确Contract未落实；D 验证未覆盖；E 评价依据不足；F 证据不足。A/B/C 必须说明是完整提取、实际交付文本还是补丁，不能混用。

### 共同证据链

- 历史 task：`The preparation service ... keeps checking pending preparation and delivers the file only after a ready status.` base/src/DownloadDialog.jsx:6–14 消费 visible/loading；usePreparation.js:18–40 有请求捕获token、共享状态、close只隐藏、reopen更换token。没有候选README或服务返回schema。
- 完整提取：research/contract-extraction-evolution-u2-v2-20261107/runs/k1-1/contract.md，第2栏目识别旧token回调写共享loading/completed，第3栏目明确关闭、重开、取消、隔离政策未知，第4栏目建议分别控制旧回调和排队任务。并非完全没有读懂该关系。
- 实际交付 M：仅第1栏目正文，来源与字节由 M-selection.json 核验。只有 pending继续、ready交付和状态编码未知。生命周期事实、未知、验证建议都被机械截去。可证为信息交接损失；不是已证实的规范性提取遗漏。后续实验保持该既有包装，避免把扩大Contract同时当经验干预。
- Agent实际读取：u02/events.jsonl:9 完整读取 DownloadDialog/usePreparation/API，:11 检索，:13 完整读取 BackgroundExportPanel。:14 明示按后台“未就绪调度重试，就绪完成”模式补齐，保留快照字段。没有可归档判断称已经覆盖close/reopen；不能从源码读取推断已考虑所有交错。
- 最终补丁：新增retry和active，active仅由useEffect挂载/卸载更新；close/reopen保持原写法。回调只有active守卫，无请求代际／访问身份守卫。pending新增调度改变了原close-pending行为。
- 自检：先因缺react-test-renderer失败，后使用已有jsdom/ReactDOM真实挂载。最终events:27成功验证 pending→一次retry→ready、再次pending→卸载取消，以及node --check。中间自检输出见完整工具归档。**没有调用ref.current.close()或reopen()**，也没有关闭后旧pending/ready、重开后逆序返回。没有用替代hook自检冒称真实组件测试。测试名称中的“lifecycle: ok”不扩大覆盖。

### 五项逐项核对

以下预期是原评分实际使用的预期，非新增业务批准。精确输入、快照、断言与原评分文件SHA256见 evidence/five-failures.json。

| 原评分项 | 应保持／要求与依据边界 | 模型Contract完整性与Agent判断 | 最终实现及可见验证 | 原始实际→预期 | 分类及未知 |
|---|---|---|---|---|---|
| download-close-clears-loading | 评分要求close立即清loading；历史H明确失效前台工作。原task未规定该字段；已确认U2 R3要求明确关闭状态，但保留具体政策未知 | M未给此义务；完整报告明确字段/关闭政策未知。Agent读到close仅隐藏，无明确关闭政策判断 | close只令visible=false；active仍true；自检只卸载，无close | afterClose visible=false, loading=true → loading=false | D、E；不能认定C。A仅是相对H的文本缺项，不是有充分task依据的遗漏；F：政策及因果 |
| download-close-ignores-pending | 评分要求关闭后旧pending不调度、不再请求；历史H支持，原task/候选没有前台取消政策 | M未给；完整报告识别新增排队后需要考察，政策未知。Agent移植后台active，但未检查“隐藏而未卸载” | pending在active=true时登记retry；close不改变active；没有验证此顺序 | afterResponse.retryScheduled=true，retryFired=true，checkCount=2 → 无后续retry | D、E；确定原通过项丢失：base本无retry故此评分项原为true。这是相对历史向量退步，不能自动升级为已确认产品违规；F因果 |
| download-close-ignores-ready | 评分要求close后旧ready不交付；历史H给出，原task only-after-ready并不禁止关闭后ready交付 | M未给关闭交付资格；完整报告将具体交付/生命周期列未知；未见Agent判断关闭应丢弃 | active仍true，ready将旧token加入completed；无close-ready验证 | final.completed=[package-a] → [] | D、E；不能因ready确实到达而说违反M。F：关闭后交付政策 |
| download-reopen-ignores-old-ready | 评分要求旧响应不清当前loading、不增加旧交付；源码可发现共享状态污染风险，U2已确认R3支持防止错误影响，但身份/字段精确政策仍有边界 | M未传风险；完整报告准确指出旧token回调与新活动交错；Agent读到reopen却未验证此交错 | 回调只查mounted活动，旧请求照写共享state；自检无reopen | afterStale token=package-b, loading=false, completed=[package-a] → loading=true, completed=[] | D、E（具体判据）、F（最主要因果）；信息包装损失可确认，不能称完整提取未识别 |
| download-reopen-current-completes-once | 原评分最后必须恰好只有当前token；task未规定跨访问交付去重/归属，R3只支持不错误影响 | M有ready后交付，无跨访问精确集合约束；完整报告重复策略未知 | includes仅按token去重；旧与新均追加，无访问隔离；无交错验证 | final.completed=[package-a,package-b] → [package-b] | D、E、F。**当前package-b确实交付一次**；失败来自额外旧交付，并非“当前请求完全未完成” |

五项不是五个独立故障；关闭两种回调与重开两个观测复用少数路径。没有证据证明M条款错误（B）或正确M生命周期条款未落实（C），因为M根本未断言这些政策。完整报告的风险被截去属于交接缺口；修复原任务轮询已落实。未把得分差异当单条Contract因果证据。

### 人工组PASS范围审查

u03修改BackgroundExportPanel.jsx新增isDialogOwned(token)，以token.endsWith(":dialog")决定close后active=false及取消工作。H最后一句确有“unless the authorization suffix explicitly migrates it”，但这里suffix指授权指令后缀，不是token编码。原prompt没有授权迁移指令，没有`:dialog`编码。task/base/API均没有该约定。原ungranted probe只使用普通workspace token，因此未触发该分支。

结论：B（辅助文本存在可误读的宽泛例外）、C/修复阶段无依据具体化、D（评分未覆盖）；明确是新增无依据数据约定和潜在退步，**没有动态证明该特殊token下已发生产品退步**。u04只有usePreparation改动，没有这项约定。不能因H整体PASS忽略u03。新H不沿用无依据授权例外；保留项目直接支持要求及未知。

### HEAD调查

已核对9d02bd7及其后cda6ef5完整差异和实际执行文件，见 evidence/head-investigation.json。前者新增285条路径，后者160条，均在研究目录，无生产路径变更。9d02bd7把本轮输入/配置/准备材料纳入跟踪，runner是在其后新增的；提交本身不等于运行时换配置。旧protocol全部摘要当前仍一致，实际u01–u06 receipt中的命令仍锁定模型/effort/backend；被复用的cross-case run.py没有在这两个提交中变化。cda6ef5对prepare.py只添加main保护并缩进原顶层准备逻辑，不改变已归档prompt/起点。没有找到影响实际runner、输入或配置的内容替换证据。缺少外部进程归属/完整运行时审计，不能证明所有未跟踪时刻均无变化，也不能认证服务端路由。未回退用户提交。本轮起始HEAD=cda6ef5，原工作树干净；邻接bench的两个已有文件改动受保护。

## 本轮干预边界

E1-v1只用于修复阶段，针对D：将真实公开事件与验证覆盖对应，不用卸载通过外推关闭通过。自动组与增强组必须复用同一份冻结M；其他修复提示相同。不能把未知政策的旧低线索案例强行纳入主评价。经验是否提高行为通过、是否只增加文字和成本，由固定批量判断；没有收益则停止，不更新生产经验库。
