# 时序源码证据索引

**工具生成的待核查线索，不是 Oracle、缺陷结论或难度分。**

状态：`parsed`；工具版本：`0.6.9`。
输入摘要：`ef9dc4f1aa455b8952b35f2068d5618f3f3c98ee29a485f40beb3c307d649a27`。
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
| index.js | parsed | 476c06a8056fc0d402d6e8bf0c3fc653e1342bbda8637da50e8aa83f3f7e82dd |

## 待核查模式

没有模式命中；不表示安全。请查看解析覆盖与未建模调用。
## 候选直接调用关系

只列可定位的词法/导入绑定，不等于完整调用图。对象方法、动态绑定和回调实参目标可能未解析。


## 保护与边界位置（存在不等于充分）

- `index.js:11` · guard · `Number.isSafeInteger(maxAge)`
- `index.js:13` · guard · `typeof maxAge !== 'undefined'`
- `index.js:21` · guard · `cacheItem`
- `index.js:31` · await · `await Promise.allSettled([promise])`
- `index.js:32` · guard · `!cachePromiseRejection && reason`
- `index.js:34` · guard · `maxAge`
- `index.js:54` · guard · `!cacheStore.has(memoized)`
- `index.js:60` · guard · `typeof cache.clear !== 'function'`

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
