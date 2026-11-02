# 时序关系核查（低噪声）

仅展示证据链完整的状态发布候选；当前筛选只支持 reentrant-state-publication。其他规则默认隐藏，未展示不表示安全，也不证明提示能改善修改结果。

解析状态：parsed；工具版本：0.6.9
输入 SHA-256：46b6a70c6b95fe36c2cc89af24851adb1d3534d82efffc10f0eb31e7e47ec3c9
工具 SHA-256：cd20f4910048bfb95bb31a910c3a64017c9ac3b2bc79bda47d9bc7956d6124f1
原始提示 2 条；展示 1 张卡；隐藏 1 条；合并 0 条。

## src/memoize-one.ts · 状态 cache
进入用户函数时，入口读取的闭包状态尚未完成后续写入。
条件：Bounded JavaScript evaluation prefix on the selected normal path; direct IIFEs and unique local functions only. Callback reentry, runtime types, state value meaning, exceptions and full control flow are not proven. .call/.apply are invocation candidates; overridden methods remain unresolved.
核查：若该用户函数同步重入当前入口，状态是否已表示工作正在执行？调用前写入不等于保护充分；需核对写入值、清理和异常路径。可用立即重入测试检查执行次数、排队及拒绝结果。

src/memoize-one.ts:31 · guard
```text
cache && cache.lastThis === this && isEqual(newArgs, cache.lastArgs)
```

src/memoize-one.ts:38 · call
```text
resultFn.apply(this, newArgs)
```

src/memoize-one.ts:39 · write
```text
cache = {
      lastResult,
      lastArgs: newArgs,
      lastThis: this,
    }
```

## 解析覆盖与限制
- src/are-inputs-equal.ts：parsed
- src/memoize-one.ts：parsed
- 结果是语法事实、静态候选调用关系与待核查模式，不是已证明的时序契约、缺陷、严重度或难度分。
- 同名 API 只作为线索；不做全程序类型/别名/控制流证明。动态派发、对象工厂、函数参数传递的完整目标保持未知。
- 局部先后表示同一语法块中位置先后；条件、异常、循环、短路及调用是否实际执行仍需核查。
- await 是潜在暂停点，并非必然切换；取消请求不等于工作与清理完成；移除监听不保证既有异步工作取消。
- 语法中的 if/try/finally 不等于已证明保护充分；无模式命中不等于程序安全。
- 未读取隐藏评分器、参考补丁、模型结果或人工 profile；分析根由操作者提供，文件内容的来源仍需核实。

隐藏原因：{'not_established': 1}
使用 --view exploratory 查看完整提示；原始 JSON 和冻结实验层保留完整证据。