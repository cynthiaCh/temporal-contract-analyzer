# 时序源码证据索引

**工具生成的待核查线索，不是 Oracle、缺陷结论或难度分。**

状态：`parsed`；工具版本：`0.6.3`。
输入摘要：`6e4916e3244918ee7c2c6f7c29231bcaf8b3e8912859f3ca0efa6a872e71873a`。
工具摘要：`e58fe872aa7a31bc179d6f1930b92e02d78ac1e53690aa9c85d36a1bb7624a48`。

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
| index.js | parsed | 6b711efb524045d3c768b5303cd6f4f15d3cb0f7c860017d9fb2cd7bf455be7a |

## 待核查模式

### hint-1 · reentrant-state-publication

入口条件仍持有用户函数时调用该函数，随后才清空同一闭包绑定；同步重入可能再次进入该分支。

成立条件/限制：Bounded JavaScript evaluation prefix on the selected normal path; direct IIFEs and unique local functions only. Callback reentry, runtime types, state value meaning, exceptions and full control flow are not proven. Selected positive identifier guard branch only; the only visible write to this parameter is a later null/undefined clear. Other branches, indirect mutation and overridden .call/.apply remain unresolved.

待核查：用户函数若立即重入包装入口，是否会再次执行？请检查同步重入、throw 选项与首次抛错后的重试语义；不能直接提前清空而忽略重试行为。

`index.js:17` · <module>/onetime/onetime

```text
function_
```

`index.js:18` · <module>/onetime/onetime

```text
function_.apply(this, arguments_)
```

`index.js:19` · <module>/onetime/onetime

```text
function_ = undefined
```

## 候选直接调用关系

只列可定位的词法/导入绑定，不等于完整调用图。对象方法、动态绑定和回调实参目标可能未解析。


## 保护与边界位置（存在不等于充分）

- `index.js:6` · guard · `typeof function_ !== 'function'`
- `index.js:17` · guard · `function_`
- `index.js:20` · guard · `options.throw === true`
- `index.js:34` · guard · `!calledFunctions.has(function_)`

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
