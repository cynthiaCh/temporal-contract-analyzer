# 时序源码证据索引

**工具生成的待核查线索，不是 Oracle、缺陷结论或难度分。**

状态：`parsed`；工具版本：`0.6.9`。
输入摘要：`1739d690bbfe55d57cf99f8b55bcdf547bd966b2cf3e3f6feea765f8115aa968`。
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
| index.ts | parsed | b1054f14ee68c5786bbb2d9a32661786321bf703c0a233e6fd0e2961e03ddad1 |

## 待核查模式

没有模式命中；不表示安全。请查看解析覆盖与未建模调用。
## 候选直接调用关系

只列可定位的词法/导入绑定，不等于完整调用图。对象方法、动态绑定和回调实参目标可能未解析。

- `index.ts:172` validateMaxAge → `index.ts::<module>/validateMaxAge`
- `index.ts:181` getValidCacheItem → `index.ts::<module>/getValidCacheItem`
- `index.ts:190` validateMaxAge → `index.ts::<module>/validateMaxAge`
- `index.ts:289` memoize → `index.ts::<module>/memoize`
- `index.ts:344` getPropertyDescriptor → `index.ts::<module>/getPropertyDescriptor`
- `index.ts:361` memoize → `index.ts::<module>/memoize`
- `index.ts:431` getValidCacheItem → `index.ts::<module>/getValidCacheItem`

## 保护与边界位置（存在不等于充分）

- `index.ts:82` · guard · `!item`
- `index.ts:86` · guard · `item.maxAge <= Date.now()`
- `index.ts:95` · guard · `value === Number.POSITIVE_INFINITY`
- `index.ts:99` · guard · `!Number.isFinite(value)`
- `index.ts:100` · guard · `source === '′maxAge′ option'`
- `index.ts:107` · guard · `value > maxTimeoutValue`
- `index.ts:108` · guard · `source === '′maxAge′ option'`
- `index.ts:121` · guard · `descriptor`
- `index.ts:171` · guard · `typeof maxAge === 'number'`
- `index.ts:173` · guard · `maxAge <= 0`
- `index.ts:182` · guard · `cacheItem`
- `index.ts:189` · guard · `computedMaxAge !== undefined && computedMaxAge !== Number.POSITIVE_INFINITY`
- `index.ts:192` · guard · `computedMaxAge <= 0`
- `index.ts:204` · guard · `computedMaxAge !== undefined && computedMaxAge !== Number.POSITIVE_INFINITY`
- `index.ts:279` · guard · `context.kind === 'method'`
- `index.ts:280` · guard · `context.private`
- `index.ts:288` · guard · `!memoizedMethod`
- `index.ts:313` · guard · `currentReceiver !== receiver`
- `index.ts:316` · guard · `currentPrototype === receiver`
- `index.ts:336` · guard · `context.static`
- `index.ts:345` · guard · `descriptor?.value !== decoratedMethod`
- `index.ts:360` · guard · `!memoizedGetter`
- `index.ts:379` · guard · `!cache`
- `index.ts:383` · guard · `typeof cache.clear !== 'function'`
- `index.ts:390` · call · `clearTimeout(timer)`
- `index.ts:424` · guard · `!cacheKey`

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
