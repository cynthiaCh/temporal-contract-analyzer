# 时序关系核查（低噪声）

仅展示证据链完整的状态发布候选；当前筛选只支持 reentrant-state-publication。其他规则默认隐藏，未展示不表示安全，也不证明提示能改善修改结果。

解析状态：parsed；工具版本：0.6.9
输入 SHA-256：06065f9ccbc985f367949420d072ac0131cc9795386be18d0b938e733273619d
工具 SHA-256：cd20f4910048bfb95bb31a910c3a64017c9ac3b2bc79bda47d9bc7956d6124f1
原始提示 3 条；展示 0 张卡；隐藏 3 条；合并 0 条。

当前筛选未展示候选，不表示没有时序问题。

## 解析覆盖与限制
- src/draft-store.js：parsed
- src/editor.js：parsed
- src/receipt-archive.js：parsed
- src/save-status.js：parsed
- src/search-preview.js：parsed
- src/timers.js：parsed
- src/trailing-task.js：parsed
- src/workspace.js：parsed
- 结果是语法事实、静态候选调用关系与待核查模式，不是已证明的时序契约、缺陷、严重度或难度分。
- 同名 API 只作为线索；不做全程序类型/别名/控制流证明。动态派发、对象工厂、函数参数传递的完整目标保持未知。
- 局部先后表示同一语法块中位置先后；条件、异常、循环、短路及调用是否实际执行仍需核查。
- await 是潜在暂停点，并非必然切换；取消请求不等于工作与清理完成；移除监听不保证既有异步工作取消。
- 语法中的 if/try/finally 不等于已证明保护充分；无模式命中不等于程序安全。
- 未读取隐藏评分器、参考补丁、模型结果或人工 profile；分析根由操作者提供，文件内容的来源仍需核实。

隐藏原因：{'exploratory_rule': 3}
使用 --view exploratory 查看完整提示；原始 JSON 和冻结实验层保留完整证据。