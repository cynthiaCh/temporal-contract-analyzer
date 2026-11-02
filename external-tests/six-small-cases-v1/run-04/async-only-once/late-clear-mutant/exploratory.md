# 时序源码证据索引

**工具生成的待核查线索，不是 Oracle、缺陷结论或难度分。**

状态：`parsed`；工具版本：`0.6.9`。
输入摘要：`faa54dfd74fdffb60670f6d63868cfb613de4c896d54a3f998e688d906373586`。
工具摘要：`cd20f4910048bfb95bb31a910c3a64017c9ac3b2bc79bda47d9bc7956d6124f1`。

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
| lib/internal/onlyOnce.js | parsed | ce9f6f6522b3bc22deaecccfeea25615ed7040d656cfb571560ad8d388179be8 |

## 待核查模式

### hint-1 · reentrant-state-publication

先调用本地回调快照，随后才清空入口读取的原始绑定；同步重入可能再次取得同一函数。

成立条件/限制：Bounded JavaScript evaluation prefix on the selected normal path; direct IIFEs and unique local functions only. Callback reentry, runtime types, state value meaning, exceptions and full control flow are not proven. One simple local declaration snapshots an outer parameter after a strict null early-throw guard and before its only visible null clear. The alias has no other visible writes; runtime callable types and method replacement remain unresolved.

待核查：回调经局部副本调用时，原绑定是否已使重入入口拒绝再次调用？请核对同步重入和首次抛错后的行为；清空原变量不等于清空先前副本。

`lib/internal/onlyOnce.js:3` · <module>/onlyOnce/<callback>

```text
fn === null
```

`lib/internal/onlyOnce.js:4` · <module>/onlyOnce/<callback>

```text
callFn = fn
```

`lib/internal/onlyOnce.js:5` · <module>/onlyOnce/<callback>

```text
callFn.apply(this, args)
```

`lib/internal/onlyOnce.js:6` · <module>/onlyOnce/<callback>

```text
fn = null
```

## 候选直接调用关系

只列可定位的词法/导入绑定，不等于完整调用图。对象方法、动态绑定和回调实参目标可能未解析。


## 保护与边界位置（存在不等于充分）

- `lib/internal/onlyOnce.js:3` · guard · `fn === null`

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
