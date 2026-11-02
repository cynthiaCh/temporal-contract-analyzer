# 时序源码证据索引

**工具生成的待核查线索，不是 Oracle、缺陷结论或难度分。**

状态：`parsed`；工具版本：`0.6.9`。
输入摘要：`46b6a70c6b95fe36c2cc89af24851adb1d3534d82efffc10f0eb31e7e47ec3c9`。
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
| src/are-inputs-equal.ts | parsed | 2e6f3b85a8c8dd07c5f900d48d0ce3ed577e864f9ea088931b5ee2223812865c |
| src/memoize-one.ts | parsed | 5d4b84a3f500aa604f1ed2bf7887b603e6f09e603117b43201e0d5f101f55e78 |

## 待核查模式

### hint-1 · reentrant-state-publication

进入用户函数时，入口读取的闭包状态尚未完成后续写入。

成立条件/限制：Bounded JavaScript evaluation prefix on the selected normal path; direct IIFEs and unique local functions only. Callback reentry, runtime types, state value meaning, exceptions and full control flow are not proven. .call/.apply are invocation candidates; overridden methods remain unresolved.

待核查：若该用户函数同步重入当前入口，状态是否已表示工作正在执行？调用前写入不等于保护充分；需核对写入值、清理和异常路径。可用立即重入测试检查执行次数、排队及拒绝结果。

`src/memoize-one.ts:31` · <module>/memoizeOne/memoized

```text
cache && cache.lastThis === this && isEqual(newArgs, cache.lastArgs)
```

`src/memoize-one.ts:38` · <module>/memoizeOne/memoized

```text
resultFn.apply(this, newArgs)
```

`src/memoize-one.ts:39` · <module>/memoizeOne/memoized

```text
cache = {
      lastResult,
      lastArgs: newArgs,
      lastThis: this,
    }
```

### hint-2 · reentrant-state-publication

已定位入口状态读取和用户函数调用，当前同步前缀未建立对应写入关系。

成立条件/限制：Bounded JavaScript evaluation prefix on the selected normal path; direct IIFEs and unique local functions only. Callback reentry, runtime types, state value meaning, exceptions and full control flow are not proven. .call/.apply are invocation candidates; overridden methods remain unresolved.

待核查：若该用户函数同步重入当前入口，状态是否已表示工作正在执行？调用前写入不等于保护充分；需核对写入值、清理和异常路径。可用立即重入测试检查执行次数、排队及拒绝结果。

`src/memoize-one.ts:31` · <module>/memoizeOne/memoized

```text
cache && cache.lastThis === this && isEqual(newArgs, cache.lastArgs)
```

`src/memoize-one.ts:38` · <module>/memoizeOne/memoized

```text
resultFn.apply(this, newArgs)
```

## 候选直接调用关系

只列可定位的词法/导入绑定，不等于完整调用图。对象方法、动态绑定和回调实参目标可能未解析。

- `src/are-inputs-equal.ts:36` isEqual → `src/are-inputs-equal.ts::<module>/isEqual`

## 保护与边界位置（存在不等于充分）

- `src/are-inputs-equal.ts:13` · guard · `first === second`
- `src/are-inputs-equal.ts:18` · guard · `safeIsNaN(first) && safeIsNaN(second)`
- `src/are-inputs-equal.ts:30` · guard · `newInputs.length !== lastInputs.length`
- `src/are-inputs-equal.ts:36` · guard · `!isEqual(newInputs[i], lastInputs[i])`
- `src/memoize-one.ts:31` · guard · `cache && cache.lastThis === this && isEqual(newArgs, cache.lastArgs)`

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
