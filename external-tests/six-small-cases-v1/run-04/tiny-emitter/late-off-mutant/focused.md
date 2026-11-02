# 时序关系核查（低噪声）

仅展示证据链完整的状态发布、监听退订顺序及参数缓存候选。其他规则默认隐藏；提示需结合接口约定与运行验证，未展示不表示安全，也不证明修改收益。

解析状态：parsed；工具版本：0.6.9
输入 SHA-256：aab7158d850ae9682db3ec356b9f36089a026b14dfa5952d8fe876beeb78e6a9
工具 SHA-256：cd20f4910048bfb95bb31a910c3a64017c9ac3b2bc79bda47d9bc7956d6124f1
原始提示 1 条；展示 1 张卡；隐藏 0 条；合并 0 条。

## index.js · 状态 listener
用户回调执行后才退订同一个已注册监听；同步重入派发可能再次调用它。
条件：One same-source array-backed registration/removal protocol, one captured receiver, matching event and local listener identity, and a straight synchronous wrapper. No runtime receiver-type, overridden method, array-intrinsic or callback-reentry proof.
核查：这个包装是否要求只交付一次？请沿注册与移除实现检查：回调立即再次派发同一事件或抛错时，监听是否仍然有效？

index.js:26 · call
```text
this.on(name, listener, ctx)
```

index.js:19 · write
```text
self = this
```

index.js:20 · function_definition
```text
function listener () 
```

index.js:7 · function_definition
```text
function (name, callback, ctx) {
    var e = this.e || (this.e = {});

    (e[name] || (e[name] = [])).push({
      fn: callback,
      ctx: ctx
    });

    return this;
  }
```

index.js:42 · function_definition
```text
function (name, callback) {
    var e = this.e || (this.e = {});
    var evts = e[name];
    var liveEvents = [];

    if (evts && callback) {
      for (var i = 0, len = evts.length; i < len; i++) {
        if (evts[i].fn !== callback && e… [截短；请查看源码]
```

index.js:21 · call
```text
callback.apply(ctx, arguments)
```

index.js:22 · call
```text
self.off(name, listener)
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