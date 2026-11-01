# 时序关系核查（低噪声）

仅展示证据链完整的状态发布候选；当前筛选只支持 reentrant-state-publication。其他规则默认隐藏，未展示不表示安全，也不证明提示能改善修改结果。

解析状态：parsed；工具版本：0.6.3
输入 SHA-256：6e4916e3244918ee7c2c6f7c29231bcaf8b3e8912859f3ca0efa6a872e71873a
工具 SHA-256：e58fe872aa7a31bc179d6f1930b92e02d78ac1e53690aa9c85d36a1bb7624a48
原始提示 1 条；展示 1 张卡；隐藏 0 条；合并 0 条。

## index.js · 状态 function_
入口条件仍持有用户函数时调用该函数，随后才清空同一闭包绑定；同步重入可能再次进入该分支。
条件：Bounded JavaScript evaluation prefix on the selected normal path; direct IIFEs and unique local functions only. Callback reentry, runtime types, state value meaning, exceptions and full control flow are not proven. Selected positive identifier guard branch only; the only visible write to this parameter is a later null/undefined clear. Other branches, indirect mutation and overridden .call/.apply remain unresolved.
核查：用户函数若立即重入包装入口，是否会再次执行？请检查同步重入、throw 选项与首次抛错后的重试语义；不能直接提前清空而忽略重试行为。

index.js:17 · guard
```text
function_
```

index.js:18 · call
```text
function_.apply(this, arguments_)
```

index.js:19 · write
```text
function_ = undefined
```

## 解析覆盖与限制
- index.js：parsed
- 结果是语法事实、静态候选调用关系与待核查模式，不是已证明的时序契约、缺陷、严重度或难度分。
- 同名 API 只作为线索；不做全程序类型/别名/控制流证明。动态派发、对象工厂、函数参数传递的完整目标保持未知。
- 局部先后表示同一语法块中位置先后；条件、异常、循环、短路及调用是否实际执行仍需核查。
- await 是潜在暂停点，并非必然切换；取消请求不等于工作与清理完成；移除监听不保证既有异步工作取消。
- 语法中的 if/try/finally 不等于已证明保护充分；无模式命中不等于程序安全。
- 未读取隐藏评分器、参考补丁、模型结果或人工 profile；分析根由操作者提供，文件内容的来源仍需核实。

隐藏原因：{}
使用 --view exploratory 查看完整提示；原始 JSON 和冻结实验层保留完整证据。