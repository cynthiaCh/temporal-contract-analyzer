# One E2 revision, then frozen same-case A/B

本目录贯穿一次E2修订与六槽对照。先读 DIAGNOSIS.md 和 PLAN.md，结果见 REPORT.md/summary.json。不要重新执行已完成的阶段；反思和控制器均有新批次/不恢复检查，不支持第二候选、补跑或E3。

- prepare.py、DIAGNOSIS.md、diagnosis.json、evidence/：零模型、零评分重跑的原经验→公开选择→实际补丁→原标准→行为结果定位；没有修改或运行人工修复补丁。
- training-feedback.json、reflection-input.md：三项目标成功与两项保留行为失败同时反馈，包含原始源码、实际变化和原标准。没有提供reference答案或历史整题成功补丁。
- E1.md：旧经验原样副本。
- reflection.py、reflection-protocol.json/sha256：唯一一次原配置反思，gpt-5.6-terra/medium，12请求/600秒上限、无工具。实际调用归档于 training-runs/reflection/archive/。
- NEW_EXPERIENCE.md：E2等于唯一反思的原始report，未经人工编辑。experience-review.json明确记录文本剩余歧义，不事后润色。
- experience-freeze.json、protocol.json/sha256：所有维护前冻结E2、两组实际prompt、反思归档、调度和分析规则。A原样复用；B只追加E2。
- control.py：复用上一批的六槽控制器和原score回调，gpt-5.6-terra/low，每槽24请求/600秒，独立会话/工作区，并发1。
- runner.py/archive.py/native_backend.py/guard_*.py/request_guard.py/read_policy.py及原配置/schema：逐字节复用，机械归档不调用模型。业务工作区与宿主归档隔离。
- analyze.py/report.py：只在六槽结束或协议停止后统一分析，不调用模型或评分器。原开发和E1正式结果单列，不池化分母。
- scope-review.json、tool-diagnostics.json、behavior-vectors.json、behavior-counts.csv、integrity-validation.json：逐槽补丁、非零工具诊断、全部29项行为、成本与完整性。

离线检查的第一次本地脚本错误和修正记录见 offline-preflight-correction.json，原失败夹具保留；没有改实际模型计量逻辑。无隐藏模型预跑、额外评委或自动重试。最终ARTIFACTS.sha256覆盖交付的全部普通文件（清单自身除外），每槽另有归档清单。

若E2无整题收益，按预先约定停止继续打磨本经验，保留负结果，不自动生成E3或改变模型/case/Contract/预算。即使观察到增量，也只限本次同题小样本，不自动扩展或更新生产经验库。
