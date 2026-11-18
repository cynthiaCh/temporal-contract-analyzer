# V12 经验增长实验：当前 v4 审查快照

本目录对应 `growth-v12-ds-adapter-v4-20261118-01`。采用本轮冻结时的 master V12 流程，论文仅作方法对照；不新增效果复现门槛。v4 从空经验库的 M0 重新开始，旧运行不续跑、不拼接。

## 核心配置

| 项目 | 当前配置 |
|---|---|
| 模型 | `deepseek-flash`，reasoning effort `high` |
| 接口 | DeepSeek Responses API；现有 Codex CLI `0.169.0` |
| 数据 | 固定训练70、测试30；成员与顺序在 `inputs/` |
| 节点 | M0、M10、M20、M30、M40、M50、M60、M70 |
| 训练 | 顺序执行；最多3次Action；公开检查加训练Oracle；成功反思或三次有效失败后的专家总结；独立AI内容审核后入库 |
| 测试 | 固定快照；每例1次Action、唯一最终Gold；不学习、不按Gold择优重试 |
| 检索 | 训练 `source-bound-v8`；测试 `business-source-v1` |
| 请求上限 | 普通分析/检索/Contract/诊断/提炼阶段12；Action24；AI审核12；各阶段600秒，原阶段内修正仍共用预算 |
| 并发 | M0/M10测试2；M20起测试4；训练始终1 |
| 计量 | 请求级拦截/回执、共享锁账本；未知保留unknown；现金余量10 CNY，每个在途阶段预留10 CNY；最大在途由2调整为4，未增加单例预算 |
| 运行隔离 | 模型solver与可信controller/grader分离；solver不挂载Docker socket或Gold实现；工具仍受白名单与路径限制 |

真实请求中的 Flash/high 和结构化输出参数已在前期独立接入小试验证；参数传入不意味着模型所有输出必然满足schema，最终仍严格校验。官方配置参考：[Codex接入](https://api-docs.deepseek.com/quick_start/agent_integrations/codex/)、[Responses API](https://api-docs.deepseek.com/guides/responses_api/)。不执行官方安装脚本来扩大隔离环境权限。

## 审查顺序与文件职责

1. `review-provenance/frozen-manifest.json`：真实运行最初的不可变manifest、模型、镜像/CLI身份和102项绑定；不是新生成的示意配置。
2. `run_growth.py`、`controller.py`：冻结的正式编排入口与可信Docker控制器。`temporal_contract_analyzer/tempoevo_v4.py` 是实际阶段流程，`delegated_review.py` 是AI总结/审核/入库。
3. `temporal_contract_analyzer/_session_runtime/model-profiles.json`、`deepseek-model-catalog.json`、`native_backend.py`、`runner.py`：本轮实际DeepSeek能力配置、基础指令及CLI适配；任务提示仍来自V12流程。
4. `_session_runtime/read_policy.py`、`guard_server.py`、`request_guard.py`：工具语法/路径守卫、请求预算与停止结算。`balance_budget.py` 是共享计量控制。
5. `admission/runtime.json`、`controller-runtime.json`、`zero100-v1.json`：实际镜像ID和100例零模型准入证据。构建工具在 `tools/tempoevo-docker/prepare_*.py`，配套Dockerfile在 `containers/tempoevo/`。
6. `supervise_growth.py`：当前监督器v6。`close_bounded_invalid.py`、`close_review_invalid.py`、`recover_unlaunched.py`：只对有充分证据的执行无效/未派发阶段处理，不自动补模型请求。
7. `close_evaluator_invalid.py`、`close_reflection_invalid.py`：经个案调查后使用的严格闭审工具，保留原始结果和真实训练评分；不是通用忽略异常开关。
8. `run_growth_parallel.py`、`amend_scheduler.py`：M20起2→4的调度修订。继承冻结Run，只调整独立测试的并发，不更改训练流程。原manifest未改写；明确差异见 `review-provenance/scheduler-amendment.json`。
9. `export_results.py`、`audit_results.py`、`render_evidence.py`：只读导出与审计。`ANALYSIS_PLAN.md` 是结果解释口径，`ISSUES.md` 是工程问题与处置记录。

`supervisor-history/` 中v4/v5/v6是审计历史，不是三个可任选的实验流程。`review-provenance/prompt-source-inventory.json`包含审计时不同版本的提示对照，不能当成当前配置；当前实际源码及manifest绑定才是依据。`official-capability-summary.json`是官方配置对照，也不代表所有官方工具在本实验中开放。

## 相对master的主要工程差异

- 固定70/30编排、八节点冻结快照、共享余额/用量账本和可审计的AI委托审核。
- DeepSeek官方兼容catalog/base instructions与最小JSON转义、原始来源引用说明；Flash/high档位保持不变。
- 修正Docker内重复namespace隔离导致公开文件不可读的适配问题；保留外层容器隔离、只读挂载与工具守卫。
- 对受限工具的必要语法适配、请求级停止与在途结算、CLI身份校验；没有开放任意Shell或绕过证据/schema约束。
- 本地100例grader准入和案例目录解析适配；测试仍只做最终一次Gold。
- 当前监督器识别严格外层schema拒绝，并独立保留经验阶段失败与训练分数；原始答案不修补。

## 已知限制与建议重点检查

- 原生 `structured.py.validate` 的 `anyOf` 校验不完整；外层严格 `schema_validator.py` 已拒绝相关无效候选。为保持运行版本，本轮未热改原生解析器。不能把 native valid=true 等同于最终合法入库。
- 精确引用校验会拒绝近似改写，例如把源码单引号改成双引号。M10库有4个经验包，但只有3/30测试交付了非空指导；需区分库规模与实际采用经验。
- D12通过训练但反思选择 `revise` 同时标注 `implementation_gap`，被原有语义规则拒绝；按经验阶段无效闭审，训练PASS保留。这不是漏掉反思，也不是已批准却写错库。
- CLI的 `write_stdin` 不产生与普通Shell相同的PreToolUse钩子，前期审计未证明能够通过功能开关消除该差异；不要宣称已完全修复。已有命令语法限制和外层隔离保留。
- 候选运行错误在当前冻结grader分类为执行无效。M10 PHP case还暴露公开文档`aclose`与native桥接`close`映射不够明确的限制；本轮不据Gold改公开任务或补跑。
- 70/30属于存在历史暴露的同源变体开发评估，不是独立未见来源泛化；GPT带61条经验不是M0对照。单次曲线上升也不能单独证明经验的因果收益。
- M20起并发变化可能影响延迟/超时，必须披露并检查执行有效率，不能说所有节点调度完全相同。

## 如何查看与验证

只读校验，不调用模型、Docker或网络：

```sh
python -B tools/verify_v4_review.py
```

离线回归的推荐范围：`tests/test_deepseek_audit.py`、`test_balance_budget.py`、`test_delegated_review.py`、`test_research_read_policy.py`、`test_model_profiles_and_retries.py`，以及本目录`test_parallel_scheduler.py`。Linux fcntl测试应在兼容Linux运行环境执行；跳过不能算通过。

`review-provenance/M10-experience-snapshot.json`是前10例的4条已批准经验包（31条规则），附AI审核。`checkpoint-summary.csv`和`paired-summary.csv`是M10收尾时的结果快照：M0为7PASS/22FAIL/1无效，M10为10PASS/19FAIL/1无效；双方均有效28例中4改善、1退步。后续实验仍在运行，这些文件不是最终成绩。两个节点都有1个无效，主准确率按原规则留缺口，另报告有效分母和缺失范围。

## 运行与复现边界

这是一份可核对真实运行的审查副本，不是把本机在途任务复制给第二个控制器。当前源文件保留真实本机路径、镜像ID、owner和volume；不要直接用同一个run_id/volume启动另一份。原始runs、完整账本、凭据、Docker镜像、Codex二进制、benchmark-source.tar均未上传。

新环境复现需要合法取得外部benchmark与CLI，按构建工具重建镜像、完成动态准入，并使用独立run_id/store/volume和对应新冻结配置。不能把本分支的本机准入报告当成另一环境已准入，也不能修改现有绑定后继续拼接本轮曲线。当前v6监督入口要求已记录的调度修订；新实验应显式制定并冻结自己的调度配置。

审查副本离线验证：82项测试通过、0失败、0跳过；额外四并发调度/账本验证通过。容器无网络、无凭据、无Docker socket，模型和Gold调用均为0。详情见 `review-provenance/review-validation.json`。完整46,214项构建文件清单未上传，使用 `grader-build-summary.json` 保留原清单哈希、100例范围和条目数量。

发布后补充：D14训练首次PASS，但独立AI审核的原始来源引用校验失败。新增 `close_citation_invalid.py` 仅扩展独立无新增闭审工具，调用冻结来源校验复现拒绝，保留原始审核及训练PASS，不激活候选、不追加模型请求；运行中的102项冻结源码/输入及3项调度绑定仍未改变。详见ISSUES.md第16项。
`export_results.py`另输出TRAINING_RESULTS.md与training-summary.json：按已闭审且评分有效的同一训练队列，报告最多1/2/3次Action后的累计通过率；提前通过计入累计，经验阶段失败保留真实训练评分，求解无效单列。
