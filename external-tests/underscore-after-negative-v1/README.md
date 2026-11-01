# Underscore.after：8 行的负对照

固定来源：[`jashkenas/underscore` 提交 `5c1e5f686f8500af9c9d15614ed60289d6d35d6b`](https://github.com/jashkenas/underscore/blob/5c1e5f686f8500af9c9d15614ed60289d6d35d6b/modules/after.js)，package 版本 1.13.8。这里选的是与 before 同一项目中的另一个独立模块，原版只有 8 行，无 import/运行时依赖。许可证、package 和出处保留并绑定哈希。

## 本例的约定

源码注释明确：从第 N 次调用起，每次入口调用都会执行回调。after(3, fn) 的前两次不执行，从第三次开始持续执行。它不是单次执行保护器，不应将激活后的额外调用或同步重入自动判作重复执行缺陷。

## 结果（工具 0.6.8 未修改）

| 输入 | 原始提示 | 默认问题卡 | 自写运行检查 | 激活后的同步重入回调次数 |
|---|---:|---:|---|---:|
| 原版 | 0 | 0 | 6 通过 | 2，符合本例约定 |
| 人工重排对照 | 0 | 0 | 6 通过 | 2，符合本例约定 |

两份源码均成功解析，测试观察相同。当前没有发出不必要的重复执行提示；但规则尚未建模此处的 < 激活谓词，因此不能把零提示当成已识别完整安全语义、没有其他风险或总体精度提高的证明。也不声称发现上游缺陷。

## 重排对照是什么

原版核心：

```js
if (--times < 1) {
  return func.apply(this, arguments);
}
```

对照只用于本轮有限整数输入的行为比较：

```js
var result;
if (times < 2) {
  result = func.apply(this, arguments);
}
--times;
return result;
```

比较阈值相应调整，并保存返回值，以便把更新推迟到调用之后。它被标记为有效重排控制，**没有被标记为注入故障**。本轮测试表明激活次数、后续持续执行、返回值/参数/this 和重入行为一致；不声称对任意 JavaScript 类型、强制转换副作用、极端数值或异常路径都已证明等价。

在次数预算的 before 中，消耗预算可以让入口条件从真变假；在 after 的激活阶段，进一步递减不会阻止已经满足条件的新调用。未来扩展规则时应保留此类负例，避免把“调用后更新计数器”一概报成问题。

## 检查与范围

6 项自写 Node 检查覆盖：第 3 次激活并持续执行、0/1 次立即激活、每次合格调用的新 this/参数与结果、独立计数器、激活后的同步重入、微任务重入。同步和微任务见证各执行两次，预期如此；未将之前 once 的“只能执行一次”断言套用到本例。

先阅读约定再固定检查，不是盲测；此例与前一轮同库且同一计数包装器家族，不代表独立跨领域验证。分析器只接收 after.js，不读取测试、文档、预期或运行结果。原版以相同字节复制成临时 ESM 模块直接执行，不 mock、转译或安装 npm 包。既有 Node v24.21.0，工具代码和摘要保持与前一轮 before 0.6.8 相同。

未运行 Underscore 完整测试套件；本例没有恶意/故障变体，不能估计检出率。所有文件摘要保留，原始报告、运行输出、重排精确差异均可复查。

## 复现

```sh
python3 external-tests/underscore-after-negative-v1/run.py \
  --output external-tests/underscore-after-negative-v1/run-02
```

可用 --node 指定既有 Node >=22。输出必须使用新目录，脚本不联网或安装软件；成功退出表示两侧各 6 项检查通过、观察一致。

- [汇总](run-01/summary.json)
- [默认报告对照](run-01/comparison.html)
- [原版原始运行输出](run-01/original/runtime.tap)
- [重排对照原始运行输出](run-01/reordered_valid_control/runtime.tap)
- [精确重排差异](run-01/reordered-control.patch)
