# 冻结工具后的新实现检查

2026-11-02，固定源码分析器 **0.6.9**，工具 SHA-256 为 `cd20f4910048bfb95bb31a910c3a64017c9ac3b2bc79bda47d9bc7956d6124f1`。本轮没有修改任何分析器规则。候选来自本仓库此前未作为外部案例测试的 **7 个实现**，共 **14 个原始版本快照**：5 组真实历史修复前后版本，另加 4 个行为对照。没有人工故障变体。

**本轮没有验证到一次真实问题的有效默认命中。**能完整解析的三个历史问题版本均无提示；两组旧 Flow 实现解析失败。唯一一张默认卡出现在通过所选异常契约检查的现代 memoize-one 上，目前不能计为有效缺陷提示。

## 五组上游问题

下表每一行是一组相关的前后版本，不是两个独立实现。行数包括注释。运行检查用独立断言复现上游记录中的行为。

| 实现 | 原版行数（前/后） | 运行证据（问题版 → 修复版） | 问题版默认卡片 | 静态分析解释 |
| --- | ---: | --- | ---: | --- |
| [eventemitter3](https://github.com/primus/eventemitter3/commit/144834c15264128113814a5b5d2f8621c326e5af) | 181 / 181 | once 同步嵌套派发执行 2 次 → 1 次；单监听/多监听路径均复现 | 0 | 正常解析；漏掉已复现问题 |
| [mitt](https://github.com/developit/mitt/commit/f38922aa9190c9126c8fdc3306b32bd2c248b77e) | 61 / 61 | 第一个监听移除自身后，第二个被跳过 → 两者都执行；普通/通配监听均复现 | 0 | 两侧原始 Flow 源码均 parse_error，不能当作成功的阴性检测 |
| [memoize-one](https://github.com/alexreardon/memoize-one/commit/0c5743de4455fcdcc45d06a82bbb260dc194d3fe) | 38 / 52 | 失败参数重试返回旧值或 undefined → 按该历史版本约定重复抛出所缓存异常 | 0 | 两侧原始 Flow 源码均 parse_error |
| [p-memoize](https://github.com/sindresorhus/p-memoize/commit/343ac6e71a77031a69f9e52bf03ea40e1cfdcbc8) | 65 / 65 | 连续未等待的同参调用求值 2 次、结果 [1,2] → 求值 1 次、结果 [1,1] | 0 | 正常解析；漏掉已复现问题 |
| [inflight](https://github.com/isaacs/inflight-DEPRECATED-DO-NOT-USE/commit/1365152d6eade38fe1f4568943d772cc1237f1ef) | 44 / 52 | 完成回调抛错后，同键新请求无法开始 → 可以重新开始 | 0 | 正常解析；漏掉已复现问题 |

对应修复版在各自所选检查中通过，默认卡片也均为 0。这只能说明这些特定行为通过，不是证明整份修复版本无缺陷。inflight 已废弃；此处只使用其真实历史代码和修复证据，不推荐生产使用。

## 四个行为对照

| 版本 | 入口行数 | 独立检查 | 默认卡片 | 解释 |
| --- | ---: | --- | ---: | --- |
| isaacs/once，`0fbb41ec58d13f6f222fdccd03429a892606000b` | 42 | 普通/strict 的顺序与重入检查 4/4 | 0 | property 状态守卫的正确行为控制；不据此宣称工具理解了该保护 |
| memoize-one 现代 TS，`d785546cd6ee9a1f52709eba9c5fb3b76e29de96` | 56，另扫描 41 行比较器 | 缓存、异常重试、保留旧成功缓存 3/3 | 1 | 有顺序候选，但未建立需要改动的契约 |
| mitt 现代 TS，`6b41670516ed8e8b738612f60491995470aa63b3` | 123 | 普通/通配移除、普通重入等 4/4 | 0 | 所选行为通过 |
| memoize，`de93da75055d9e3bb1662c5ec17332b202707d61` | 433 | 缓存、异常重试、保留旧成功缓存 3/3 | 0 | 所选行为通过；这里只测试无过期时间的基础使用 |

现代 memoize-one 的卡定位 `src/memoize-one.ts` L31 守卫、L38 用户求值、L39 缓存赋值。其顺序事实本身正确，但源码明确说明先求值是为了让抛错不覆盖已有缓存，独立测试也验证了这个行为。该实现没有承诺同步重入时只求值一次，因此不能把“写入在回调之后”直接当作缺陷。这里标记为 **通过所测契约的版本上的未证实候选/潜在噪声**，不是有效命中，也不声称已证明所有重入都安全。[完整卡片](run-02/memoize-one-control/focused.md)

历史 memoize-one 修复版会缓存异常，现代版本则不缓存异常；测试按各版本文档与修复记录分别确定期望，没有把两种不同的约定混用。

## 执行顺序和证据

1. 先写 [PROTOCOL.json](PROTOCOL.json)，冻结工具版本、候选仓库与纳入标准。源文件小于 600 行；测试和文档另行保存。研究者可见源码，因此不是双盲实验。
2. 检查源码和历史，固定 [CASES.json](CASES.json)。它记录了分析前的扩展：从原候选 inflight 历史补入第五组修复，另保留两个旧 Flow 实现及其现代 TS 行为对照。未根据检测结果替换案例。
3. 冻结源码、依赖、工具快照和输入哈希。写入 [TEST_PLAN.json](run-02/TEST_PLAN.json)，先执行运行检查，得到 [RUNTIME_LABELS.json](run-02/RUNTIME_LABELS.json)。期望失败的测试名称事先列明；不是看到工具提示后才编造缺陷。
4. 标签与测试代码哈希固定后，才执行静态扫描。分析器读取原始源码，未读取测试、上游补丁、标签或类型擦除产物。每份报告保留默认、探索、JSON 和 HTML 版本。
5. 确认工具文件哈希前后一致，逐项校验静态输入、运行计划与类型擦除。见 [integrity.json](run-02/integrity.json)。这是本地确定性校验，不是独立外部审计。

结果共 **50 项运行检查，42 项通过、8 项预期失败**。8 个失败断言对应 5 个真实历史问题，不是 8 个独立 bug。5 个修复版本和 4 个行为对照在所选检查中均通过。静态分析 10 个快照完整解析，4 个 Flow 快照未解析；共 1 张默认候选卡，没有一张命中这些已复现问题。此结论只针对本批。

两组 Flow 的运行验证使用仓库既有 Babel parser 做类型语法擦除，保留行位置，完整保存擦除范围与输出哈希；擦除后的代码仅运行，不提供给静态分析器。现代 TS 用 Node v24.21.0 的原生类型擦除执行；memoize-one 的扩展名省略导入由指向原始 TS 文件的符号链接解析。没有重写时序代码。CJS/ESM 测试容器的 package.json 只指定模块环境，未安装或执行上游构建脚本。

运行依赖是固定版本的真实 npm 发布文件，校验 registry 的 tarball 完整性后复制到隔离临时目录。没有模拟 once、mimic 或 cache API，也没有为工具新增依赖。完整上游测试套件未执行；这里是有来源的行为复现，不等同于全部上游回归。

来源说明：历史 eventemitter3 的 MIT 声明来自 package.json 的 `license` 字段，该提交没有独立 LICENSE 文件，README 也未重复声明。冻结清单备注中的 `package.json/README` 是不准确的简写，应以实际保存的 package.json 为准；未为修正这句话而重写冻结清单。

`run-01` 保留为中断尝试：依赖使用符号链接时，map-age-cleaner 的嵌套 p-defer 导入无法解析。仅把隔离运行目录中的依赖改为完整复制，未修改测试断言、候选源码或工具；完整结果为 run-02。原始提交、修复 diff 和回归测试片段保存在 discovery 与 upstream-evidence 中。

## 复现

所有输入与依赖已保存，无需网络或 npm install。在分析器仓库根目录运行，输出目录必须不存在：

```sh
python3 -B external-tests/unseen-small-implementations-v1/run.py \
  --phase runtime --output external-tests/unseen-small-implementations-v1/run-03
python3 -B external-tests/unseen-small-implementations-v1/run.py \
  --phase analyze --output external-tests/unseen-small-implementations-v1/run-03
```

脚本会拒绝工具或输入已变动的运行。`frozen-tool/source.zip` 与 `FILES.json` 保存本轮代码与哈希，需保留冻结的解析器依赖环境。默认使用 VS Code 内嵌 Node，也可通过 `--node` 指定兼容解释器。

完整汇总：[summary.json](run-02/summary.json)。每个案例目录包含 runtime.tap、observations.json、report.json、focused.md、focused.html 和 exploratory.md。

## 这批结果支持什么

它暴露了当前规则对新实现的覆盖不足，尤其是属性/数组/Map 状态、派发循环与异常清理；也暴露了通用“状态在回调后写入”提示需要区分缓存提交与重入阻断。Flow 是输入语言支持缺口，应与正常解析后的漏报分开。

这些问题与受限规则支持的精确形状不完全相同，因此不能把三次未检测解释为某个已声明支持模式的召回率；但它们确实说明目前工具无法有效覆盖这批实际项目的相关问题。不要把修复版不报警解释为工具识别出了修复，也不要把类型解析失败当作无问题。

这是一批按可获得修复证据选取的便利样本，不是随机基准；前后版本相关，不能据此估计一般准确率或 ICPC 投稿成功概率。案例现已被阅读和使用，后续若据此修改规则，它们应归入开发/回归集，不能继续称为新留出测试。本轮没有证明 LLM 修改收益。
