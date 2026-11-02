# 时序源码证据索引

**工具生成的待核查线索，不是 Oracle、缺陷结论或难度分。**

状态：`parsed`；工具版本：`0.6.9`。
输入摘要：`0219b720606789e57f546ecd51988d4a227a7b6907004e5d68c48997e628bda6`。
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
| index.js | parsed | 3e3679233f20177d63d253e7c2645024fef51731d05df15621c62a48ba98e0d3 |

## 待核查模式

### hint-1 · reentrant-listener-detach

已在用户回调前退订本次监听。

成立条件/限制：One same-source array-backed registration/removal protocol, one captured receiver, matching event and local listener identity, and a straight synchronous wrapper. No runtime receiver-type, overridden method, array-intrinsic or callback-reentry proof.

待核查：这个包装是否要求只交付一次？请沿注册与移除实现检查：回调立即再次派发同一事件或抛错时，监听是否仍然有效？

`index.js:26` · <module>/once

```text
this.on(name, listener, ctx)
```

`index.js:19` · <module>/once

```text
self = this
```

`index.js:20` · <module>/once/listener

```text
function listener () 
```

`index.js:7` · <module>/on

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

`index.js:42` · <module>/off

```text
function (name, callback) {
    var e = this.e || (this.e = {});
    var evts = e[name];
    var liveEvents = [];

    if (evts && callback) {
      for (var i = 0, len = evts.length; i < len; i++) {
        if (evts[i].fn !== callback && evts[i].fn._ !== callback)
          liveEvents.push(evts[i]);
      }
    }

    // Remove event from queue to prevent memory leak
    // Suggested by https://github.com/lazd
    // Ref: https://github.com/scottcorgan/tiny-emitter/commit/c6ebfaa9bc973b33d110a84a307742b7cf94c953#commitcomment-5024910

    (liveEvents.length)
      ? e[name] = liveEvents
      : delete e[name];

    return this;
  }
```

`index.js:22` · <module>/once/listener

```text
callback.apply(ctx, arguments)
```

`index.js:21` · <module>/once/listener

```text
self.off(name, listener)
```

## 候选直接调用关系

只列可定位的词法/导入绑定，不等于完整调用图。对象方法、动态绑定和回调实参目标可能未解析。


## 保护与边界位置（存在不等于充分）

- `index.js:47` · guard · `evts && callback`
- `index.js:49` · guard · `evts[i].fn !== callback && evts[i].fn._ !== callback`

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
