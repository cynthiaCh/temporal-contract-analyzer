# 自动 once 配置入口：窄范围验证

**已经实现“两个源码路径 + 一次显式行为要求确认 → 自动配置 → 前后重入观察 → 重放命令”。**它减少了手写绑定材料；本轮没有测量开发者时间，也没有证明检测能力优于 fast-check。

入口是 `tools/temporal-behavior-probe/auto_once.py`。先仅解析源码提出 wrapper 候选，不执行目标模块；只有 `--confirm-at-most-once` 才运行已有 probe 的单次同步重入场景。使用者确认的是这个有限场景的至多一次要求，不是从函数名推断的语义。支持范围、API/契约假设和延后能力在工具 README 与 `implement-stage/auto-once-v1/ASSUMPTIONS.md`。

## 新源码结果

开发使用合成早/晚 guard 及拒绝样例，通过后冻结引擎，再查找未出现在既有本地实验记录中的 `3rd-Eden/one-time`。原始源码、说明和 MIT 许可证保存于 `UPSTREAM.json`。另一个候选 `jonschlinkert/one-time` 返回 404，没有测试。选择及停止规则见 [PROTOCOL.md](PROTOCOL.md)。

| 固定案例 | 自动候选配置 | 独立运行观察 | 工具结论与重放 |
| --- | --- | --- | --- |
| 1.0.0 release→同一 release | 成功 | 缺少 fn.name，加载失败 | inconclusive，重放同样无法下结论 |
| 真实历史重构 8e075514→646e3445 | 成功 | 回调 1→1 次 | 当前场景未违约，重放一致 |
| 较早源码→同一较早源码 | 成功 | 回调 1→1 次 | 当前场景未违约，重放一致 |
| 较早源码→人工 late-guard 回归 | 成功 | 回调 1→2 次 | 当前场景引入违约，重放一致 |

人工修改只把 `called = true` 从 callback 调用前移到后，补丁保存于 `ARTIFICIAL.patch`。**它不是上游历史缺陷，不能作为发现真实新 bug 的数量。**这里的真实上游修改是行为保持的函数命名重构。较早无依赖源码是读到新版本依赖后主动选择的兼容输入，不是随机盲抽；较新版本失败没有丢弃、安装依赖或替换实现。

每个候选生成的 plan 都直接交给既有独立 fast-check 通用模型。它也正确获得对应观察；缺依赖时也无法完成执行。为公平核对同一域，对两侧都配对执行 mode=reenter/times=2；baseline 原有属性搜索还包含异常和重叠场景，这些额外覆盖不计入这个单场景比较。`oracle.cjs` 另外独立执行普通断言，确认观察不以工具自己的判定为真值。

## 实际减少了什么

既有 wrapper JSON 最少需要 6 个叶字段：api.kind、行为要求，以及两侧 root/entry。显式填写 commonjs 时为 8 个。新入口接收两个完整文件路径，加一个确认标志；root、entry、module 和结构候选自动得到。输出位置和运行时选项两侧都需要，均排除在这个输入清单之外。

这是 **6 个配置叶字段（显式格式 8 个）→ 3 个领域输入值**，不是“效率提高一倍”。选用 once 专用命令本身已表达领域选择；路径拆分和默认模块格式也是机械推导。我们没有测到阅读需求、选择入口、配置理解或确认语义需要多少时间，也没有与一个同样简化了 CLI 的 baseline 做用户实验。

最重要的结论是：**这层自动配置可以同时帮助我们的执行器和 fast-check。**没有为新项目编写专用场景函数，但之前的通用 fast-check 模型同样无需新增场景代码；新增价值只能主张减少显式绑定材料、提供保守候选与可审查证据，不能主张更强生成、推理或一般生产率收益。仅少写 JSON 是较薄的便利功能，尚不足以单独支撑强研究贡献。

## 核查、原始材料和复现

- `run-02/SUMMARY.json`：最初冻结版在四种情况上的完整结论；`run-03/SUMMARY.json`：补上构造期回调有效性检查后的同输入开发复验，结果相同，不是新的留出实验。
- 每个情况的 `proposal.json`：未确认、不执行目标的静态候选；`report.json` 和 `report-replay.json`：确认后的完整行为/重放。
- `execution-command.json`：实际执行入口；`ORACLE.json`：独立检查；`fast-check-{before,after}/`：原生模型观测和附加配对重放。
- `FROZEN-pre-sweep.json`：选择外部源码前的冻结版，适用于 run-01/02；`FROZEN.json`：审查后版本，适用于 run-03。不能把审查后版本说成在选择源码前已冻结。
- `run-01/INTERRUPTION.json`：首次测量误将缺依赖错误里的临时路径差异当成不一致。原始报告保留；run-02 仅修正实验脚本，按观察值或 inconclusive 分类比较，没有修改引擎或输入。

可从仓库根目录复制运行（输出路径需不存在）：

```sh
python3 tools/temporal-behavior-probe/auto_once.py \
  external-tests/auto-once-adaptation-v1/snapshots/old/index.js \
  external-tests/auto-once-adaptation-v1/snapshots/artificial-regression/index.js \
  --confirm-at-most-once --output once-example.json
```

报告中的 `replay_command` 是可直接执行的 argv 数组，为输出文件生成新的名字。去掉确认标志可只检查候选绑定。输出包含一个场景的证据，不是项目安全认证。ESM、emitters、reexports 和复杂别名尚未支持。

重跑完整迁移流程：

```sh
python3 -B external-tests/auto-once-adaptation-v1/run.py \
  --output external-tests/auto-once-adaptation-v1/run-04
```

本轮新增作用域测试 8/8 通过，原有 probe 测试 9/9 通过。技能要求的一轮新上下文假设审查发现：构造 factory 时也可能调用 callback，提前消耗重入触发。前端现在将这种情况标为 inconclusive，并明确零回调时没有测试到重入；新增针对性检查通过。其余关于候选识别强度、复制运行环境、退出码及可变路径重放的假设已补入说明。该审查来自同模型家族，不能视为独立正确性认证。

第二轮审查确认前述假设已对齐，另提出 1 项输入约定：外层输入为 0，内层输入跟随 callback 实际收到的第一个参数。此项已写入 A12 和工具说明，由实施者对照现有 runner 核查；两轮预算用尽，未再复审。保留最后的 gaps 结果，不宣称 clean 或独立通过。这里的三个正常运行案例均未变换该参数。

已有 pinned Babel 用于静态候选解析；没有新增或安装产品依赖。新入口独立于冻结静态分析器。没有 Git 提交。

来源：[原始较早源码](https://github.com/3rd-Eden/one-time/blob/8e07551446ea4a06ce524e8d0ea237f63324e4b5/index.js)、[真实重构](https://github.com/3rd-Eden/one-time/commit/646e3445b2f3bdc60888e15f5a1434efdbe5c8b0)、[1.0.0 源码](https://github.com/3rd-Eden/one-time/blob/aa7ced4ad6c65b1f5433b4c9fefb3b809adee5fc/index.js)。以上是一个新实现上的功能核查，非独立用户研究或通用效果证明。
