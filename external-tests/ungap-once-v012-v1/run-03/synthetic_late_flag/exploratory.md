# 时序源码证据索引

**工具生成的待核查线索，不是 Oracle、缺陷结论或难度分。**

状态：`parsed`；工具版本：`0.6.6`。
输入摘要：`6253ece0a514887e2d4ae8c7b3d7f4b05c30db4d4195e3b5381b9ba11c4c637c`。
工具摘要：`f2bc2dd739e56b8bde0d2044c28a92e8fa89dda30916c8bdb6cf677e332160bc`。

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
| index.js | parsed | 9f0f206530c04fee140b4e71bfe83aad4329efb9782cec56af9ddcbcf73f09bc |

## 待核查模式

### hint-1 · reentrant-state-publication

先反射调用捕获的接收者函数，随后才写入阻止重复执行的标志；同步重入可能再次调用。

成立条件/限制：Bounded JavaScript evaluation prefix on the selected normal path; direct IIFEs and unique local functions only. Callback reentry, runtime types, state value meaning, exceptions and full control flow are not proven. Positive shared-boolean branch, a stable receiver value capture, and candidate Reflect.apply/construct provenance. Conditional arms are alternatives; receiver callable type, native built-in identity and indirect mutation are not proven.

待核查：普通调用或构造调用若同步重入同一包装入口，是否会重复执行？请分别核查分支、异常和缓存结果；调用前写入不等于所有路径安全。

`index.js:14` · <module>/value/once

```text
execute
```

`index.js:12` · <module>/value

```text
fn = this
```

`index.js:12` · <module>/value

```text
execute = true
```

`index.js:3` · <module>

```text
{apply, construct} = Reflect
```

`index.js:16` · <module>/value/once

```text
construct(fn, arguments)
```

`index.js:18` · <module>/value/once

```text
execute = false
```

### hint-2 · reentrant-state-publication

先反射调用捕获的接收者函数，随后才写入阻止重复执行的标志；同步重入可能再次调用。

成立条件/限制：Bounded JavaScript evaluation prefix on the selected normal path; direct IIFEs and unique local functions only. Callback reentry, runtime types, state value meaning, exceptions and full control flow are not proven. Positive shared-boolean branch, a stable receiver value capture, and candidate Reflect.apply/construct provenance. Conditional arms are alternatives; receiver callable type, native built-in identity and indirect mutation are not proven.

待核查：普通调用或构造调用若同步重入同一包装入口，是否会重复执行？请分别核查分支、异常和缓存结果；调用前写入不等于所有路径安全。

`index.js:14` · <module>/value/once

```text
execute
```

`index.js:12` · <module>/value

```text
fn = this
```

`index.js:12` · <module>/value

```text
execute = true
```

`index.js:3` · <module>

```text
{apply, construct} = Reflect
```

`index.js:17` · <module>/value/once

```text
apply(fn, this, arguments)
```

`index.js:18` · <module>/value/once

```text
execute = false
```

## 候选直接调用关系

只列可定位的词法/导入绑定，不等于完整调用图。对象方法、动态绑定和回调实参目标可能未解析。


## 保护与边界位置（存在不等于充分）

- `index.js:14` · guard · `execute`

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
