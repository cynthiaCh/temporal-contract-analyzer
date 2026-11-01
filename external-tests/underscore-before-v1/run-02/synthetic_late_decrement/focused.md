# 时序关系核查（低噪声）

仅展示证据链完整的状态发布候选；当前筛选只支持 reentrant-state-publication。其他规则默认隐藏，未展示不表示安全，也不证明提示能改善修改结果。

解析状态：parsed；工具版本：0.6.8
输入 SHA-256：1eec54d0872e11862460aeeb461e6388e170f3cd901b376ff5fc685787a9390f
工具 SHA-256：a4c54c40da67fe4dbc8b11b9e7ed88aa9aaf8e40851b017d9144d893bb652e78
原始提示 1 条；展示 1 张卡；隐藏 0 条；合并 0 条。

## before.js · 状态 times
先调用用户函数，随后才递减本次次数预算；同步重入可能复用尚未消耗的旧预算。
条件：Bounded JavaScript evaluation prefix on the selected normal path; direct IIFEs and unique local functions only. Callback reentry, runtime types, state value meaning, exceptions and full control flow are not proven. A single -- update, safe-integer literal comparison, and one callback on the positive budget branch. Assumes a finite safe-integer budget and the documented numeric quota meaning; coercion, exceptions, invocation-method overrides and indirect mutation are not proven.
核查：按有限安全整数的调用预算解释时，若用户函数同步重入，是否会超出允许次数？请核对输入数值范围、异常后的预算与缓存；不据此判定后续清理有错。
说明：调用后的清空绑定仅作来源与顺序证据；本卡核查入口状态写入与调用的先后，不判定清理语句本身有错。
说明：清空仅在条件 times <= 1 成立时发生，不能当作每条路径都会执行的动作。

before.js:6 · guard
```text
times > 1
```

before.js:7 · call
```text
func.apply(this, arguments)
```

before.js:9 · write
```text
--times
```

before.js:10 · guard
```text
times <= 1
```

before.js:10 · write · 条件成立时在调用后清空绑定（顺序事实）
```text
func = null
```

## 解析覆盖与限制
- before.js：parsed
- 结果是语法事实、静态候选调用关系与待核查模式，不是已证明的时序契约、缺陷、严重度或难度分。
- 同名 API 只作为线索；不做全程序类型/别名/控制流证明。动态派发、对象工厂、函数参数传递的完整目标保持未知。
- 局部先后表示同一语法块中位置先后；条件、异常、循环、短路及调用是否实际执行仍需核查。
- await 是潜在暂停点，并非必然切换；取消请求不等于工作与清理完成；移除监听不保证既有异步工作取消。
- 语法中的 if/try/finally 不等于已证明保护充分；无模式命中不等于程序安全。
- 未读取隐藏评分器、参考补丁、模型结果或人工 profile；分析根由操作者提供，文件内容的来源仍需核实。

隐藏原因：{}
使用 --view exploratory 查看完整提示；原始 JSON 和冻结实验层保留完整证据。