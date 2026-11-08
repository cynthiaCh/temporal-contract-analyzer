# Frozen-experience same-case follow-up

本目录是独立新批次；不是恢复旧批次，也不重新训练。研究问题、候选准入变化、固定分析规则见 PLAN.md；完成后的结论见 REPORT.md 和 summary.json。

- prepare.py：核对旧来源与模型配置，逐字节复制输入、经验、运行器；保留来源和既有文件摘要。
- preflight.py：只执行本地命名空间读写与验证检查；不执行模型或案例评分。旧15项归档测试和10份评分校准按版本对应复用。
- freeze.py：正式调用前一次性冻结。protocol.sha256 核对 protocol.json，后者包含实际输入、配置、评分版本、prompt、六槽调度、运行适配和分析规则摘要。
- control.py：唯一正式执行入口，只接受新批次，不支持恢复、重试、补跑、提取或反思。按冻结六槽顺序调用原 runner.session，并复用原 score 函数。正常行为失败不停止后续槽位。
- runner.py / archive.py / native_backend.py / guard_*.py / request_guard.py / read_policy.py 等：旧批次逐字节复用。运行器职责与两组公共 prompt 不变。
- analyze.py / report.py：全部结束（或协议异常停止）后才分析实际已启动槽位；不调用模型或评分器。
- source-evidence/：原开发结果、准入失败、版本与校准记录，只供外层核验，不挂载给维护模型。
- runs/<slot>/workspace：独立业务候选。兄弟 archive/ 保存输入、实际 prompt、事件、stderr、计量、最终快照、自动补丁、原始回答和原评分结果；归档目录不挂载给模型。

协议冻结后新增的分析/报告/完整性材料是交付产物，不回写冻结协议。主控会话只读原始结果做分析，不启动额外评委或经验更新。所有模型新增业务文件原样保存；不以文件名或后缀做静默清理。

ARTIFACTS.sha256 是交付时目录内全部普通文件的最终摘要（清单自身除外）；每槽另有归档摘要清单。不要重新执行已完成的控制器或准备脚本。
