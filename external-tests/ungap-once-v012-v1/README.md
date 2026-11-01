# @ungap/once 0.1.2：24 行无运行时依赖模块

来源：[`ungap/once` 提交 `18958325cefa455d45cf90aa2907c5a156c0dc7d`](https://github.com/ungap/once/blob/18958325cefa455d45cf90aa2907c5a156c0dc7d/esm/index.js)，2022 年的小型 Function.prototype.once polyfill。完整 ESM 模块 24 行，核心包装函数约 10 行。没有 import 或运行时依赖；头部和 package.json 保留 ISC 声明，固定树没有单独许可证文件。

## 0.6.6 支持后的结果

最新产物为 `run-03/`；`run-02/` 是保留的中间实现检查。同一固定源码、原始运行脚本与测试下：

| 输入 | 普通/构造调用的静态结果 | 默认问题卡 | 原有自写检查 |
|---|---|---:|---|
| 原版 | 2 条调用前写标志事实 | 0 | 7 通过 |
| 人工变体 | 2 条调用后写标志候选 | 1（合并） | 6 通过，1 失败 |

上游 10 个断言仍通过。新卡保留接收者捕获、标志初始化、Reflect 解构来源、入口判断、普通/构造调用和标志写入的源码证据。原始结果分别保存条件表达式的两条臂，未假定两者同时执行。查看 [新报告对照](run-03/comparison.html)、[新汇总](run-03/summary.json) 和 [历史输入/回归校验](run-03/verification.json)。

另添加了独立于原 7 项检查的构造器重入探针：原版构造 1 次，人工变体构造 2 次。结果及脚本哈希见 [constructor_verification.json](run-03/constructor_verification.json)。这是同一个人工时序变体的另一个入口观察，不是第二个独立缺陷。原测试、脚本、候选字节未修改；补充探针可单独重跑到另一批输出。

```sh
python3 external-tests/ungap-once-v012-v1/check_constructor.py \
  --run external-tests/ungap-once-v012-v1/run-new
```

先用下文 run.py 生成 run-new，补充构造检查拒绝覆盖自己的既有输出。Node 来源与原脚本相同，可通过 --node 指定。旧 run-01、run-02 保留。

本例已参与规则开发，不能再作为未见验证项目；人工变体不属于上游真实缺陷。支持范围是稳定 this 捕获、受限正向布尔标志和有明确候选来源的 Reflect 调用，尚非完整反射/原型派发分析。

## 历史实测结果（工具 0.6.5，未改规则）

| 输入 | 原始提示 | 默认问题卡 | 自写运行检查 | 同步重入时执行次数 |
|---|---:|---:|---|---:|
| 原版 | 0 | 0 | 7 通过 | 1 |
| 人工延迟标志变体 | 0 | 0 | 6 通过，1 失败 | 2 |

此外，原版的固定上游 test/index.js 按原文件运行，10 个 console.assert 全部通过。为让断言失败确实产生非零退出码，预加载测试专用 adapter，把 console.assert 换为 assert.ok 并计数；没有改写候选或上游测试。npm test 中的 c8 覆盖率包装未运行、未安装。这项结果不是完整 npm 构建/覆盖率检查。

结论：原版在这些检查中没有重复执行，人工变体产生重复执行，但当前分析器对两者均未报告。没有提示不能解释为工具已识别出保护正确；这里记录的是检测覆盖缺口。

## 关键代码与人工变体

原版通过方法的 this 保存函数，并从 Reflect 取得调用原语：

```js
const {apply, construct} = Reflect;
// Function.prototype.once 的 value 方法内：
let fn = this, execute = true, returned;
return function once() {
  if (execute) {
    execute = false;
    returned = this instanceof once ?
      construct(fn, arguments) : apply(fn, this, arguments);
  }
  return returned;
};
```

人工变体只把 `execute = false` 移到 returned 赋值完成之后，其余代码不变。回调同步重入包装函数一次，原版执行一次、变体执行两次；顺序调用和微任务重入在两侧均只执行一次。精确差异保存在 run-01/synthetic-order.patch。

该变体由研究者构造，**不是上游真实缺陷、历史修复或维护者确认的问题**。这里没有报告新漏洞或向上游发送信息。

## 为什么 0.6.5 没有报告

- 回调来自 `fn = this`，而不是当前主要跟踪的外层参数及其简单局部副本；还涉及 Function.prototype 方法的接收者来源。
- 实际调用经 `Reflect.apply` / `Reflect.construct` 的局部解构绑定发生，不能直接当作 fn() 或 fn.apply()。
- 独立标志使用正向 `if (execute)` 分支，并将其写为 false；调用还位于构造器判别的条件表达式中。这不属于当前已支持的提前返回标志路径或受限清空模式。

这是多种语法/来源的组合边界，不能只放宽 API 名称匹配就称为解决。0.6.5 检查轮仅测试；0.6.6 的受限实现见本文顶部。

## 验证范围与复现

7 项自写 Node 检查覆盖：一次执行与结果缓存、首调用参数、this、包装器状态独立、构造器单例、同步重入、微任务重入。原版上游测试另以 CJS 导出运行。固定 CJS 与 ESM 文件的文本差异仅为开头一行 use strict，脚本会验证这一点。

分析只接收 ESM 实现文本，先于运行检查执行，不向分析器提供测试、补丁、预期或运行结果。原版 ESM 以相同字节复制到临时 .mjs 加载，不 mock 或转译。polyfill 对 Function.prototype 的修改只发生在独立 Node 子进程；不修改工具进程、编辑器或系统环境。

选取时已阅读源码，不是盲测；虽未用于修改当前规则，这仍是同一 once 功能家族的一个小型案例，不能据此估计跨领域精度或 LLM 收益。

```sh
python3 external-tests/ungap-once-v012-v1/run.py \
  --output external-tests/ungap-once-v012-v1/run-02
```

可指定 `--node` 使用既有 Node >=22。输出必须使用新目录；脚本不联网、不安装 npm 包。脚本成功退出意味着原版 7/7、变体 6/7、上游 10 个断言的观测被复现，不表示变体所有检查通过。

- [结果汇总](run-01/summary.json)
- [默认报告对照](run-01/comparison.html)
- [原版原始运行输出](run-01/original/runtime.tap)
- [人工变体原始运行输出](run-01/synthetic_late_flag/runtime.tap)
- [上游断言计数](run-01/upstream-test/assertions.json)
