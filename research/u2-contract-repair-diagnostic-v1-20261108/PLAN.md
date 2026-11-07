# U2 historical-pair N/H/M repair development diagnostic

AI辅助分析，已暴露开发案例，非独立人工复核或泛化测试。只新增本目录，不改原业务、技能、标准、评分或历史，不创建提交。六槽结束即停止，不生成新Contract、技能、反思，不运行GEPA。

历史来源：contract-standard-mapping-v1-20261107准确关联的 recovered-06-node18/j0001 (N UNDERREACH) 与 j0002 (H PASS)。实际prompt、run、score、最终candidate逐字核对；起点、模型gpt-5.6-terra、medium、600秒、CLI0.159.2、ungranted、空overlay一致；非空prompt仅差精确Contract。单次顺序配对和状态协议补丁差异不能确立某条Contract因果。当前oracle六文件匹配历史plan input_sha256；三项无模型校准复现起点及历史N/H向量。没有改评分器。

N=精确原任务+历史公共维护指令+本轮共同workspace/依赖/JSON交付说明；H仅增加历史成功组Contract原文，不扩写。M仅增加U2 v2首份实际有效K1 k1-1第1栏目正文，按冻结4栏目标题边界原样截取；不带分析轨迹、K0/K1技能或标准。三组外围指令相同，没有仅给H/M的提醒或角色。完整prompt和来源文件在prompts/、contracts/和M-selection.json。

H范围：pending继续检查、ready后交付来自原任务；具体loading保持、前台关闭使timer与所有响应失效、重开代际、后台workspace所有权及授权例外是不同程度的历史显式额外规格，不能要求M/N从不足输入中猜中。争议与未知保留在H-source-applicability.json；既有历史benchmark规范照用，只作该历史对照，不自动批准当前产品政策。

评分覆盖：pending→pending→ready、等待区间loading与retryScheduled、ready completed一次、请求中close后pending/ready旧回调、异token重开旧ready、后台正常轮询及关闭后继续。不覆盖retry已排队后close、同token重开、多个并发响应、授权迁移及真实文件下载接口。未覆盖项不得由整体PASS外推；不添加新断言或综合评分。以冻结ungranted原始verdict报告整体，各effect单列；目标为原任务pending继续与ready交付的原effect，不用总分抵消关键退步。

执行恢复：gpt-5.6-terra/medium（当前模型目录列出，但无额外模型预跑），原生Codex exec自主路径，code_mode_host与shell_tool开启，不加ReAct。Node保持历史v18.17.0同一二进制，React18依赖只读提供。旧CLI不存在，改用当前0.164.0-alpha.11.1；显式priority，历史tier未知；这些差异和共同指令、隔离、预算差异见configuration-differences.json，非严格历史复刻。

冻结预算：沿用此前已核验研究配置，每槽600秒、12底层请求、report最多6000字符，全局49请求，总计最多6个正式会话，N/H/M各2次。历史未存请求与输出硬上限，不冒称与历史相同。无自动重试、补跑、反思、模型预跑、扩大规模；每槽失败保留不替换。原生hook硬门及独立研究profile，模型不能挂载评分器、参考、标准、历史和其他运行；全局配置不改。priority为客户端设置，服务端路由不独立认证。

调度种子2026110812，仅控制顺序：两轮各对N/H/M排列一次（不按结果排序），准确顺序冻结于schedule.json。所有独立工作区从同一精确历史base复制，逐槽在启动前保存摘要。首个正式槽位必须有真实成功工具输出匹配原始源码正文且执行有效，否则停止，保留原轨迹；该门不看质量或得分。若预算耗尽或计量失效停止，不换槽位。工具、服务和评分异常与行为失败分开，后续不改变输入或评分。

每槽会话退出后研究侧隔离评分，归档实际prompt、事件、原始交付、补丁、score与用量；后续模型看不到。比较整体、目标、每个effect，相对起点与同repeat的N新增/丢失；禁止效果按反向成功语义判断。H好于N/M接近H只作初步信号；H好于N而M未改善只定位候选缺口，不断言因果；N/H都通过则报告天花板，不换题；H失败核查历史与环境差异；波动完整保留。六槽之后完成summary.json与REPORT.md即停止。
