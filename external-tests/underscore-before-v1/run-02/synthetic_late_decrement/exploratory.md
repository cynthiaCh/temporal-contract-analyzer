# 时序源码证据索引

**工具生成的待核查线索，不是 Oracle、缺陷结论或难度分。**

状态：`parsed`；工具版本：`0.6.8`。
输入摘要：`1eec54d0872e11862460aeeb461e6388e170f3cd901b376ff5fc685787a9390f`。
工具摘要：`a4c54c40da67fe4dbc8b11b9e7ed88aa9aaf8e40851b017d9144d893bb652e78`。

## 范围与限制

- 结果是语法事实、静态候选调用关系与待核查模式，不是已证明的时序契约、缺陷、严重度或难度分。
- 同名 API 只作为线索；不做全程序类型/别名/控制流证明。动态派发、对象工厂、函数参数传递的完整目标保持未知。
- 局部先后表示同一语法块中位置先后；条件、异常、循环、短路及调用是否实际执行仍需核查。
- await 是潜在暂停点，并非必然切换；取消请求不等于工作与清理完成；移除监听不保证既有异步工作取消。
- 语法中的 if/try/finally 不等于已证明保护充分；无模式命中不等于程序安全。
- 未读取隐藏评分器、参考补丁、模型结果或人工 profile；分析根由操作者提供，文件内容的来源仍需核实。

## 文件与解析覆盖

| 文件 | 状态 | SHA-256 |
|---|---|---|
| before.js | parsed | 35c83ad186c4f9b13cd382c1defe9349045e72e0aa6b26c08edeb686c06d6ede |

## 待核查模式

### hint-1 · reentrant-state-publication

先调用用户函数，随后才递减本次次数预算；同步重入可能复用尚未消耗的旧预算。

成立条件/限制：Bounded JavaScript evaluation prefix on the selected normal path; direct IIFEs and unique local functions only. Callback reentry, runtime types, state value meaning, exceptions and full control flow are not proven. A single -- update, safe-integer literal comparison, and one callback on the positive budget branch. Assumes a finite safe-integer budget and the documented numeric quota meaning; coercion, exceptions, invocation-method overrides and indirect mutation are not proven.

待核查：按有限安全整数的调用预算解释时，若用户函数同步重入，是否会超出允许次数？请核对输入数值范围、异常后的预算与缓存；不据此判定后续清理有错。

`before.js:6` · <module>/before/<callback>

```text
times > 1
```

`before.js:7` · <module>/before/<callback>

```text
func.apply(this, arguments)
```

`before.js:9` · <module>/before/<callback>

```text
--times
```

`before.js:10` · <module>/before/<callback>

```text
times <= 1
```

`before.js:10` · <module>/before/<callback>

```text
func = null
```

## 候选直接调用关系

只列可定位的词法/导入绑定，不等于完整调用图。对象方法、动态绑定和回调实参目标可能未解析。


## 保护与边界位置（存在不等于充分）

- `before.js:6` · guard · `times > 1`
- `before.js:10` · guard · `times <= 1`

## 解析器

```json
{
  "python": {
    "parser": "stdlib.ast",
    "version": "3.9.6"
  },
  "javascript_typescript": {
    "status": "available",
    "parser": "@babel/parser",
    "version": "7.29.8",
    "library_sha256": "6969920ae0610df927b6b3e675d1309372c268e36d391652af8e3e0183cbe8f8",
    "node": "v24.21.0"
  }
}
```
