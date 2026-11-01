# 时序源码证据索引

**工具生成的待核查线索，不是 Oracle、缺陷结论或难度分。**

状态：`parsed`；工具版本：`0.6.4`。
输入摘要：`3cd2422eb263d82e0a2da30b59c6566ece0a851fed1e6917a09c02749102b039`。
工具摘要：`61aa00af07abc47e0264ce32963d3a5a0bd22bac2d65bfafa679818d118f4c77`。

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
| index.js | parsed | 3e22fd741f6fb05ef012d9c1180f1a336671ec455057e153bfe625439fdbc36e |

## 待核查模式

### hint-1 · reentrant-state-publication

选定嵌套分支中，外部调用发生后才写入入口防重复标志；同步重入可能再次通过检查。

成立条件/限制：Bounded JavaScript evaluation prefix on the selected normal path; direct IIFEs and unique local functions only. Callback reentry, runtime types, state value meaning, exceptions and full control flow are not proven. Selected nested if/else path and fallthrough of a bare-identifier early-return guard; one true flag publication in this linear block. Receiver property state, indirect mutations and other paths remain unresolved.

待核查：在相同接收者和分支条件下，用户函数同步重入是否会重复执行？请核对异常路径与标志含义；调用前写入不等于所有路径安全。

`index.js:28` · <module>/<callback>#2/once

```text
this == global
```

`index.js:29` · <module>/<callback>#2/once

```text
called
```

`index.js:30` · <module>/<callback>#2/once

```text
fn.apply(this, arguments)
```

`index.js:31` · <module>/<callback>#2/once

```text
called = true
```

### hint-2 · reentrant-state-publication

已定位入口状态读取和用户函数调用，当前同步前缀未建立对应写入关系。

成立条件/限制：Bounded JavaScript evaluation prefix on the selected normal path; direct IIFEs and unique local functions only. Callback reentry, runtime types, state value meaning, exceptions and full control flow are not proven. .call/.apply are invocation candidates; overridden methods remain unresolved.

待核查：若该用户函数同步重入当前入口，状态是否已表示工作正在执行？调用前写入不等于保护充分；需核对写入值、清理和异常路径。可用立即重入测试检查执行次数、排队及拒绝结果。

`index.js:28` · <module>/<callback>#2/once

```text
this == global
```

`index.js:39` · <module>/<callback>#2/once

```text
fn.apply(this, arguments)
```

## 候选直接调用关系

只列可定位的词法/导入绑定，不等于完整调用图。对象方法、动态绑定和回调实参目标可能未解析。


## 保护与边界位置（存在不等于充分）

- `index.js:28` · guard · `this == global`
- `index.js:29` · guard · `called`
- `index.js:37` · guard · `this[key]`

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
