# 时序源码证据索引

**工具生成的待核查线索，不是 Oracle、缺陷结论或难度分。**

状态：`parsed`；工具版本：`0.6.9`。
输入摘要：`18821f86f879b9cd11b8aff12f8d62fb02f8284342d5d7d59db90f7c7ba38250`。
工具摘要：`24aa49247e46c8c1bc9b219388413954410ba8219f58adb0a59d735e4ae0271b`。

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
| packages/function-memoize-last/index.cjs | parsed | 97985c20f94b5a1fba4a6baa2e20331c5caf46baacad683ff220f8d46a1a802f |

## 待核查模式

### hint-1 · argument-cache-publication

缓存参数与接收者先更新，随后才执行用户函数并写入结果；若求值抛错，同参重试可能命中旧结果，同步重入也可能读到尚未完成的结果。

成立条件/限制：Recognized last-arguments/receiver cache-miss predicate with three null-initialized closure bindings and one flat update branch. A thrown RHS skips result assignment after key writes. Assumes a stable, reflexive argument comparator for a same-argument retry; exception/reentry contracts and indirect mutation are not proven. No automatic rollback or repair is prescribed.

待核查：计算抛错后应重试、重复抛错还是返回旧值？请用不同参数的成功调用、失败调用和同参重试核查，另检查同步重入；不能只提前设置键就认定缓存有效。

`packages/function-memoize-last/index.cjs:34` · <module>/memoizeLast/<callback>

```text
!lastArgs || this !== lastThis || !_isEqual(lastArgs, args)
```

`packages/function-memoize-last/index.cjs:27` · <module>/memoizeLast

```text
lastArgs = null
```

`packages/function-memoize-last/index.cjs:26` · <module>/memoizeLast

```text
lastThis = null
```

`packages/function-memoize-last/index.cjs:28` · <module>/memoizeLast

```text
lastResult = null
```

`packages/function-memoize-last/index.cjs:36` · <module>/memoizeLast/<callback>

```text
lastArgs = args
```

`packages/function-memoize-last/index.cjs:35` · <module>/memoizeLast/<callback>

```text
lastThis = this
```

`packages/function-memoize-last/index.cjs:37` · <module>/memoizeLast/<callback>

```text
fn.apply(this, args)
```

`packages/function-memoize-last/index.cjs:37` · <module>/memoizeLast/<callback>

```text
lastResult = fn.apply(this, args)
```

`packages/function-memoize-last/index.cjs:40` · <module>/memoizeLast/<callback>

```text
return lastResult;
```

## 候选直接调用关系

只列可定位的词法/导入绑定，不等于完整调用图。对象方法、动态绑定和回调实参目标可能未解析。


## 保护与边界位置（存在不等于充分）

- `packages/function-memoize-last/index.cjs:4` · guard · `arr1.length !== arr2.length`
- `packages/function-memoize-last/index.cjs:9` · guard · `arr1[i] !== arr2[i]`
- `packages/function-memoize-last/index.cjs:18` · guard · `typeof fn !== 'function'`
- `packages/function-memoize-last/index.cjs:22` · guard · `isEqual !== undefined && typeof isEqual !== 'function'`
- `packages/function-memoize-last/index.cjs:34` · guard · `!lastArgs || this !== lastThis || !_isEqual(lastArgs, args)`

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
