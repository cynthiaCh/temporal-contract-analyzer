# 时序关系核查（低噪声）

仅展示证据链完整的状态发布候选；当前筛选只支持 reentrant-state-publication。其他规则默认隐藏，未展示不表示安全，也不证明提示能改善修改结果。

解析状态：parsed；工具版本：0.6.6
输入 SHA-256：6253ece0a514887e2d4ae8c7b3d7f4b05c30db4d4195e3b5381b9ba11c4c637c
工具 SHA-256：e57d41514a9cab0b66c1547352ac09998ca502047295f67c7926ddbfc1d5bbdf
原始提示 2 条；展示 1 张卡；隐藏 0 条；合并 1 条。

## index.js · 状态 execute
先反射调用捕获的接收者函数，随后才写入阻止重复执行的标志；同步重入可能再次调用。
条件：Bounded JavaScript evaluation prefix on the selected normal path; direct IIFEs and unique local functions only. Callback reentry, runtime types, state value meaning, exceptions and full control flow are not proven. Positive shared-boolean branch, a stable receiver value capture, and candidate Reflect.apply/construct provenance. Conditional arms are alternatives; receiver callable type, native built-in identity and indirect mutation are not proven.
核查：普通调用或构造调用若同步重入同一包装入口，是否会重复执行？请分别核查分支、异常和缓存结果；调用前写入不等于所有路径安全。

index.js:14 · guard
```text
execute
```

index.js:16 · call
```text
construct(fn, arguments)
```

index.js:18 · write
```text
execute = false
```

index.js:12 · write
```text
fn = this
```

index.js:12 · write
```text
execute = true
```

index.js:3 · write
```text
{apply, construct} = Reflect
```

index.js:17 · call
```text
apply(fn, this, arguments)
```

## 解析覆盖与限制
- index.js：parsed
- 结果是语法事实、静态候选调用关系与待核查模式，不是已证明的时序契约、缺陷、严重度或难度分。
- 同名 API 只作为线索；不做全程序类型/别名/控制流证明。动态派发、对象工厂、函数参数传递的完整目标保持未知。
- 局部先后表示同一语法块中位置先后；条件、异常、循环、短路及调用是否实际执行仍需核查。
- await 是潜在暂停点，并非必然切换；取消请求不等于工作与清理完成；移除监听不保证既有异步工作取消。
- 语法中的 if/try/finally 不等于已证明保护充分；无模式命中不等于程序安全。
- 未读取隐藏评分器、参考补丁、模型结果或人工 profile；分析根由操作者提供，文件内容的来源仍需核实。

隐藏原因：{}
使用 --view exploratory 查看完整提示；原始 JSON 和冻结实验层保留完整证据。