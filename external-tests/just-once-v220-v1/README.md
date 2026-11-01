# just-once 2.2.0：26 行零依赖模块检查

固定来源：[`angus-c/just` 提交 `d8c5dd18941062d8db7e9310ecc8f53fd607df54`](https://github.com/angus-c/just/blob/d8c5dd18941062d8db7e9310ecc8f53fd607df54/packages/function-once/index.cjs)。包版本 just-once 2.2.0，CommonJS 文件含示例注释共 26 行，无导入和运行时依赖。MIT 许可、ESM 导出、README、package 与上游测试一并保存。

## 0.6.7 改进后的结果

最新结果为 `run-02/`；与旧 run-01 的候选、测试和运行器字节一致：

| 输入 | 新分析 | 默认问题卡 | 原有运行检查 |
|---|---|---:|---|
| 原版，保留 fn = undefined | called 在调用前写入 | 0 | 7 通过 |
| 人工延迟标志变体，保留 fn = undefined | called 在调用后写入 | 1 | 6 通过、1 失败 |

工具现在确认调用点在唯一简单清空之前，而不因后续清空放弃参数来源。新卡同时标注 L23 的 fn = undefined 是“调用后清空绑定（顺序事实）”，并明确本提示核查入口状态的写入先后，不判定清理本身有错。原版不需要修改或删除这句清理。

查看 [新对照报告](run-02/comparison.html)、[新汇总](run-02/summary.json)、[输入及旧案例校验](run-02/verification.json)。新批次的静态删除清理诊断与保留清理的源码得到相同前后顺序；删除清理不再是识别的前提。run.py 与 witness.test.mjs 未改；run-01 漏报材料保留。

本例现已用于规则开发，不再作为未见验证项目。人工变体不属于真实上游缺陷；修复的是工具的识别漏报，而不是原版程序的清理行为。受限支持条件见工具文档 STATE_PUBLICATION_REVIEW.md 的 0.6.7 小节。

## 历史实测结果（0.6.6 未修改）

| 输入 | 原始提示 | 默认问题卡 | 自写运行检查 | 同步重入时回调次数 |
|---|---:|---:|---|---:|
| 原版 | 0 | 0 | 7 通过 | 1 |
| 人工延迟标志变体 | 0 | 0 | 6 通过、1 失败 | 2 |

两份实现均成功解析。变体的失败只出现在同步重入检查；普通顺序调用、返回值缓存、参数/this 转交、独立包装器和微任务重入均保持通过。

这表明当前分析没有区分本次人工时序退化；默认无卡片不能解释为安全。变体由研究者构造，**不是上游真实缺陷、维护者确认问题或历史修复**。原版在已运行检查中没有重复执行，不代表覆盖了所有行为。

## 代码中的区别

原版 L21–23：

```js
called = true;
value = fn.apply(this, arguments);
fn = undefined;
```

人工变体仅交换前两句，保留释放回调引用的清理语句：

```js
value = fn.apply(this, arguments);
called = true;
fn = undefined;
```

回调立即重入其包装入口一次，变体中 called 尚未写入，因此重复执行。见证限制为只重入一次，避免无限递归。

## 为什么 0.6.6 漏报：调用后的清理也阻断了函数来源关联

当前 publication.py 的 parameter_call() 会因参数存在任何可见写入而放弃关联，只有先前少数受限场景另行放行。此处 fn = undefined 在调用之后，是正常的释放引用操作，却使 fn.apply 的参数来源整体被排除；独立的 called 标志关系因此也没有建立。不是低噪声筛选隐藏了提示：原始 findings 同样为空。

静态诊断见 run-01/cleanup-diagnostic.json：仅在诊断字符串中删除末尾 fn = undefined，原版得到 write_before_call（0 张问题卡），延迟标志变体得到 write_after_call（1 张卡）。这两个诊断输入只用于定位分析原因，没有运行，也不作为候选修复建议；删除清理会改变引用保留行为，不应作为工具外部的“修复”。

下一步需要在调用点核对可见改写的先后关系，同时保留对兄弟函数、方法覆写、解构和不确定分支的防误关联检查。0.6.6 检查轮只测试；0.6.7 的改进见本文顶部。

## 检查范围

- 按模块体量和零依赖特征选择，先读源码再扫描，不是盲测；同属一直测试的 once 家族，不能据此估计跨领域准确率或 LLM 收益。
- 7 项自写 Node 检查分别覆盖：非法参数、顺序调用/缓存、首调用参数、this、独立包装器、同步重入、微任务重入。
- 保留上游 test/function-once/index.cjs 的 4 个用例，但没有安装仓库的测试框架或运行上游完整套件；7 项结果不冒充上游套件结果。
- 分析仅接收 CJS 实现，不输入测试、文档、补丁、预期或运行结果；扫描先于运行验证。
- 使用既有 Node v24.21.0，在临时目录按原始 CommonJS 加载，不 mock、转译或安装 npm 包。原版字节与下载文件一致；变体只有标志与调用顺序的交换。
- 候选、出处与许可证有 SOURCE_HASHES.json，运行器和见证摘要另存。两侧使用与此前 Ramda/@ungap 检查相同的工具摘要，工具核心 git diff 为空。

## 查看与复现

- [结果汇总](run-01/summary.json)
- [默认报告对照](run-01/comparison.html)
- [原版原始运行输出](run-01/original/runtime.tap)
- [人工变体原始运行输出](run-01/synthetic_late_flag/runtime.tap)
- [精确人工差异](run-01/synthetic-order.patch)
- [只删除清理的静态诊断](run-01/cleanup-diagnostic.json)

```sh
python3 external-tests/just-once-v220-v1/run.py \
  --output external-tests/just-once-v220-v1/run-02
```

可通过 --node 指定既有 Node >=22，输出必须使用新目录。脚本成功退出代表原版 7/7、变体 6/7 的观测被复现，不表示变体所有检查通过。
