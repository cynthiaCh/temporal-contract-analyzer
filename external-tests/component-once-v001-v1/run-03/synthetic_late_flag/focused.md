# 时序关系核查（低噪声）

仅展示证据链完整的状态发布候选；当前筛选只支持 reentrant-state-publication。其他规则默认隐藏，未展示不表示安全，也不证明提示能改善修改结果。

解析状态：parsed；工具版本：0.6.4
输入 SHA-256：3cd2422eb263d82e0a2da30b59c6566ece0a851fed1e6917a09c02749102b039
工具 SHA-256：61aa00af07abc47e0264ce32963d3a5a0bd22bac2d65bfafa679818d118f4c77
原始提示 2 条；展示 1 张卡；隐藏 1 条；合并 0 条。

## index.js · 状态 called
选定嵌套分支中，外部调用发生后才写入入口防重复标志；同步重入可能再次通过检查。
条件：Bounded JavaScript evaluation prefix on the selected normal path; direct IIFEs and unique local functions only. Callback reentry, runtime types, state value meaning, exceptions and full control flow are not proven. Selected nested if/else path and fallthrough of a bare-identifier early-return guard; one true flag publication in this linear block. Receiver property state, indirect mutations and other paths remain unresolved.
核查：在相同接收者和分支条件下，用户函数同步重入是否会重复执行？请核对异常路径与标志含义；调用前写入不等于所有路径安全。

index.js:29 · guard
```text
called
```

index.js:30 · call
```text
fn.apply(this, arguments)
```

index.js:31 · write
```text
called = true
```

index.js:28 · guard
```text
this == global
```

## 解析覆盖与限制
- index.js：parsed
- 结果是语法事实、静态候选调用关系与待核查模式，不是已证明的时序契约、缺陷、严重度或难度分。
- 同名 API 只作为线索；不做全程序类型/别名/控制流证明。动态派发、对象工厂、函数参数传递的完整目标保持未知。
- 局部先后表示同一语法块中位置先后；条件、异常、循环、短路及调用是否实际执行仍需核查。
- await 是潜在暂停点，并非必然切换；取消请求不等于工作与清理完成；移除监听不保证既有异步工作取消。
- 语法中的 if/try/finally 不等于已证明保护充分；无模式命中不等于程序安全。
- 未读取隐藏评分器、参考补丁、模型结果或人工 profile；分析根由操作者提供，文件内容的来源仍需核实。

隐藏原因：{'not_established': 1}
使用 --view exploratory 查看完整提示；原始 JSON 和冻结实验层保留完整证据。