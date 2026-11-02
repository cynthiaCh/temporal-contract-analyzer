# 六个小型 GitHub 模块：固定名单测试

下面保留的是 **0.6.8 的原始基线**。后续 0.6.9 的规则改进、同输入复测和范围限制见 [IMPROVEMENTS-0.6.9.md](IMPROVEMENTS-0.6.9.md)，不覆盖旧报告。

本轮只新增外部案例和证据，不修改分析器。工具版本为 **0.6.8**，八次分析的工具 SHA-256 均为 `a4c54c40da67fe4dbc8b11b9e7ed88aa9aaf8e40851b017d9144d893bb652e78`。六个模块来自五个仓库；其中部分仓库此前用过，本次模块均不同。名单在分析前固定，全部结果保留。

| 模块 | 原版行数 | 原版默认卡片 / 原始提示 | 原版自编检查 | 观察与解释 |
| --- | ---: | ---: | --- | --- |
| async.onlyOnce | 8 | 0 / 0 | 3/3 | 顺序第二次调用和同步重入均抛错；用户回调抛错后也保持已调用状态 |
| underscore.negate | 6 | 0 / 0 | 3/3 | 每次调用都应计算取反，重复执行是预期行为 |
| just-throttle | 66 | 0 / 0 | 3/3 | 默认 leading 模式同步重入只执行一次；另检查 cancel 和 trailing flush |
| just-memoize-last | 42 | 0 / 0 | 4/4，其中两项为观察 | 常规最近一次缓存正常；同步重入得到 null；抛错后同参重试返回上一组参数的旧结果 |
| nanoevents | 20 | 0 / 0 | 4/4 | 普通监听器允许重入；README 中先 unbind 再调用的 once 配方只执行一次 |
| tiny-emitter | 67 | 0 / 0 | 4/4 | once 在用户回调前退订，同步重入只执行一次；普通监听器可重复执行 |

原版共 21 项检查通过，其中 19 项验证所选行为，2 项仅固定记录缓存实现的现象。它们不是上游完整测试套件，也不能据此断言原版无缺陷。尤其 `just-memoize-last` 的两项观察通过，不代表其行为正确。

## 人工顺序故障

这两项只用于检验现有工具的覆盖边界，**不是上游已有缺陷**。补丁与失败断言均保存在完整结果目录。

| 模块 | 人工修改 | 运行验证 | 工具结果 |
| --- | --- | --- | --- |
| async.onlyOnce | 将 `fn = null` 移到 `callFn.apply` 之后 | 同步重入执行 2 次且未拒绝；用户回调抛错后再调用也没有按原版阻止。3 项检查中 2 项失败 | 原始提示 0、默认卡片 0：漏报 |
| tiny-emitter.once | 将 `self.off(name, listener)` 移到用户回调之后 | 同步重入执行 2 次；4 项检查中 1 项失败 | 原始提示 0、默认卡片 0：漏报 |

第一个模式涉及严格 null 守卫后 **throw**，现有快照识别针对 early return，未覆盖这个形式；第二个模式需要理解 `off` 对监听器注册状态的影响，当前规则未建立这种跨方法语义。这是基于源码和本次结果的范围解释，不是新增能力。

## 缓存现象的最小解释

当前实现先写 `lastThis` 和 `lastArgs`，随后执行 `lastResult = fn.apply(...)`。若计算抛错，参数键已更新，但结果仍保留旧值：

```js
const memo = memoizeLast(x => {
  if (x === 2) throw new Error('failure');
  return 10;
});
memo(1); // 10
memo(2); // throws
memo(2); // 10：没有再次执行用户函数
```

另一个观察是首次计算内部用相同参数同步重入，会命中尚未完成的缓存并返回初始值 `null`，外层最后返回 `42`。README 只概述最近一次求值缓存，未明确约定重入和异常语义；这里保留可复现现象作为待确认候选，不宣称维护者已确认缺陷，也不计作有明确判定依据的漏报。

## 固定来源

- [async.onlyOnce](https://github.com/caolan/async/blob/85fb18f3d319d14d893ec24648929ff0eb908768/lib/internal/onlyOnce.js)
- [underscore.negate](https://github.com/jashkenas/underscore/blob/5c1e5f686f8500af9c9d15614ed60289d6d35d6b/modules/negate.js)
- [just-throttle](https://github.com/angus-c/just/blob/d8c5dd18941062d8db7e9310ecc8f53fd607df54/packages/function-throttle/index.cjs)
- [just-memoize-last](https://github.com/angus-c/just/blob/d8c5dd18941062d8db7e9310ecc8f53fd607df54/packages/function-memoize-last/index.cjs)
- [nanoevents](https://github.com/ai/nanoevents/blob/081aa8995d82321b8d5d4bb64f97d63cb04380d7/index.js)
- [tiny-emitter](https://github.com/scottcorgan/tiny-emitter/blob/4e6b2eb5869fb4ba862accaef7d16a7051349f4f/index.js)

源码、许可证、相关 README 和来源记录均保存在本目录；`SOURCE_HASHES.json` 校验这些输入。源码字节保留，只通过 `.mjs` / `.cjs` 文件扩展名提供运行模块环境。未安装 npm 依赖。

## 结果与复现

- 完整结果：[run-02/summary.json](run-02/summary.json)。每个模块目录内有原始 JSON、默认及探索报告、HTML、运行 TAP、观察 JSON；人工故障另有补丁。
- [PROTOCOL.md](PROTOCOL.md)：分析前固定的测试范围和解释限制。
- `run-01` 为保留的中断尝试：运行脚本原先预期每个人工故障只失败一项，但 onlyOnce 实际失败两项。随后仅修正运行脚本为要求人工故障至少触发一项失败；源码、分析规则和测试断言未改，完整重跑为 run-02。

在工具仓库根目录执行，输出目录必须尚不存在：

```sh
python3 external-tests/six-small-cases-v1/run.py \
  --output external-tests/six-small-cases-v1/run-03
```

默认使用 VS Code 内嵌 Node（本次 v24.21.0），也可用 `--node` 指定兼容的 Node。脚本会检查输入哈希并保留全部结果；人工故障的测试进程预期失败，运行脚本本身在复现这些失败时正常结束。

没有执行上游完整测试套件。节流检查验证 leading/cancel/flush，同步取消所有定时器，不验证真实时间到期后的自动 trailing 交付。nanoevents 的 once 是 README 配方，作为运行检查存在；静态分析输入仅为其原版 index.js。本轮只说明两个具体覆盖缺口和一个缓存候选现象，不能估计通用准确率，也没有验证 LLM 修复收益。
