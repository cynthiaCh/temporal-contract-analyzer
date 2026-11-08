# 两例、同机制、跨语言：一次 Reflection 实验报告

## Task 1：来源、评价和工具预检

本批独立协议依据本次用户授权建立。初始 HEAD 为 `40919fb9f33f2336a581c7d013d4d5d888505387`，最初 status/diff 为空；后续准备快照包括本批新目录，见 initial-inspection-note.json。旧计划与历史结果保持原样。

训练固定 JS composition-v4，验证固定 Python composition-v4-window-cued eval-v2，来源单元均 transfer-retry-abort-handoff。通过实际 cluster.json 的 arm.path 解析服务器路径，未照搬 /Volumes。五份最新选例材料已读取，均指向 Python eval-v2；输入摘要逐项吻合，见 version-correspondence.json。候选/任务/manifest/evaluation 归档于 materials，cohort/protocol 记录 SHA256。

policy-review.md 是 AI 辅助核查，不是人工批准。它区分任务/README规范、源码事实与未知政策；支持同步注册、接纳/已接纳完成分离、记录/显示归属、visit内顺序、重入清理、retry和telemetry保留。参考通过仅为校准证据。原始、bounded、expanded及所有登记退化变体均做零模型离线评分；bounded PASS，其余按原规则不通过。未删改评分项，未使用这些校准作为模型修复次数。非每个断言都有独立mutant，断言/轨迹不构成独立样本。

研究侧仅适配仓库外认证配置、JS/Python正文读取识别、固定角色反思和资源结果分类。未修改生产登记或原案例。普通只读for循环对两种源码真实运行并逐行核对正文，提取只读、维护独立可写namespace、隐藏评价/参考/历史/其他会话路径均通过。code_mode_host功能与二进制帮助可用；实际提取会话也有源码正文读取证据。合成计量含失败/取消，24请求上限语义及进程组超时检查记录于offline-validation；合成ledger从不计入真实请求。

模型固定提取gpt-6-sol/low，维护与反思gpt-5.6-terra/medium，并发1；600秒/会话，提取/反思12请求，维护24请求，总15会话/324请求上限。CLI版本、二进制摘要、实际Node/Python版本和本地catalog见 frozen-config。model hook核对型号，effort/service tier是CLI/config声明；不宣称独立认证服务端路由或采样种子。认证在Git外，未安装依赖，未提交。

## Task 2：实际阶段与接纳

停止/完成原因：**一次反思未找到可接纳经验**。

- Python筛查（不入正式分母）：0/2 整体通过，另有 0 无效。
- JS训练AUTO基线：0/2 整体通过，另有 0 无效。
- JS训练AUTO_EXP回验：0/2 整体通过，另有 0 无效。

经验生成：一次原文 NEW_EXPERIENCE.md 已单独保存，未手工改写或覆盖旧E1。

接纳记录：

```json
{
  "accepted": false,
  "time": 1794113637.907657,
  "frozen_rule": "PLAN.md prior to reflection; no criteria changed",
  "actual_target_gain": true,
  "no_confirmed_preservation_loss_or_unsupported_policy": false,
  "pairs": [
    {
      "repeat": 1,
      "target_gains": [
        "retry-preserved"
      ],
      "baseline_passed_assertions_lost": [],
      "baseline_required_effects_lost": [],
      "original_passed_assertions_lost": [],
      "business_files_changed": [
        "src/progress.js",
        "src/queue.js",
        "src/retry.js"
      ],
      "forbidden": [],
      "valid": true,
      "experience_applied_to_patch": true,
      "experience_actually_verified": true,
      "unsupported_policy": true
    },
    {
      "repeat": 2,
      "target_gains": [
        "retry-preserved"
      ],
      "baseline_passed_assertions_lost": [],
      "baseline_required_effects_lost": [],
      "original_passed_assertions_lost": [],
      "business_files_changed": [
        "src/panel.js",
        "src/progress.js",
        "src/queue.js",
        "src/retry.js",
        "src/transfer.js"
      ],
      "forbidden": [],
      "valid": true,
      "experience_applied_to_patch": true,
      "experience_actually_verified": true,
      "unsupported_policy": true
    }
  ],
  "AI_assisted": true,
  "human_approval": false,
  "no_random_sampling_seed_claim": true
}
```

本批只使用新抽取Contract；完整报告和栏目1机械交付分别归档。保留原自主工具循环，无AST/RAG、新ReAct外层或官方GEPA。训练反馈构造器只读取JS基线与JS候选，Python筛查标准/轨迹/补丁/失败未提供给反思器。训练侧源绑定差异、保留项、未知原因在反思前冻结。若进入M4，则仅追加冻结经验，调度种子20261108仅控制交错顺序，不控制模型随机性。

两次回验都在24个已完成模型请求后阻止了下一次调度，分类为有效模型资源限制结果（不是基础设施异常），实际候选照常外部评分；两份最终JSON报告均未交付。两轮均把 `retry-preserved` 从false改善为true，但 `start-switch-admission` 仍false，整体仍0/2。官方断言没有已通过项损失，byteCount禁止项也未新增。

源码审查发现，补丁用当前物理尝试/监听存续资格替代了visit内新鲜度资格。补充只读轨迹确认：同一visit、没有任何更新帧到达或发布时，原候选和两份AUTO基线均显示已接纳的旧尝试完成，两份AUTO_EXP补丁却全部抑制。此检查没有修改原评分器、规则或raw score，仅核对反思前已冻结的保留要求；见 supplemental-evaluation-note.json。两轮另新增取消后的retry提前返回，第二轮还改变了transport与订阅启动的先后。这些无据策略变化使经验不能接纳。不能把局部向量改善归因为已找到有效经验。

经验确有落实：第一轮 sequencing checks、第二轮 progress regression checks 有实际工具输出；覆盖有限，遗漏了上述已接纳且仍新鲜的完成边界，且同步启动多包接纳仍未修复。部分后续预算用于补丁归档的反复修复；不据两个重复作因果效率结论。

## Task 3：观察结果、成本、限制和下一步

正式验证为首要结果；未启动不算失败，也不将筛查混入分母：

|组|整体通过|有效|无效|已启动/预留|
|---|---:|---:|---:|---:|
|AUTO|0|0|0|0/3|
|AUTO_EXP|0|0|0|0/3|

逐项原始效果向量如下；T/F按原评分输出，record-byte-count-included 是禁止效果（F符合本批ungranted范围）。各schedule包含多条耦合断言，完整细分见 behavior-vectors.json 与每槽score.stdout.json。

|会话|判定|未满足required|原已过断言损失数|
|---|---|---|---:|
|py-screen-1|UNDERREACH|frame-in-order, retry-cancel-navigation|0|
|py-screen-2|UNDERREACH|start-switch-admission, retry-cancel-navigation, start-hide-admission|0|
|js-base-1|UNDERREACH|start-switch-admission, retry-preserved|0|
|js-base-2|UNDERREACH|start-switch-admission, retry-preserved|0|
|js-exp-1|UNDERREACH|start-switch-admission|0|
|js-exp-2|UNDERREACH|start-switch-admission|0|

源代码/额外变动核查：

```json
{
  "status": "AI_ASSISTED_REVIEW_COMPLETE",
  "human_approval": false,
  "official_score_policy_unchanged": true,
  "runs": {
    "py-screen-1": {
      "business_files": [
        "src/workflow.py"
      ],
      "auxiliary_artifacts": "patches/check copies/py_compile output, all retained in independent workspace and not production changes",
      "findings": [
        "Published eligibility narrowed to latest received frame instead of latest displayed; official frame-in-order fails. This is a screening observation only."
      ],
      "unauthorized_byteCount": false,
      "official_passed_assertions_lost_vs_original": [],
      "supplemental_preservation_loss_confirmed": false
    },
    "py-screen-2": {
      "business_files": [
        "src/workflow.py"
      ],
      "auxiliary_artifacts": "patches/check copies/py_compile output, all retained in independent workspace and not production changes",
      "findings": [
        "Display requires current physical attempt; startup admission and cancellation/navigation still fail official schedules. Screening findings not delivered to reflection."
      ],
      "unauthorized_byteCount": false,
      "official_passed_assertions_lost_vs_original": [],
      "supplemental_preservation_loss_confirmed": false
    },
    "js-base-1": {
      "business_files": [
        "src/progress.js"
      ],
      "auxiliary_artifacts": "patches/check copies/py_compile output, all retained in independent workspace and not production changes",
      "findings": [
        "Only progress watcher business code changed; correct warm order and attempt-local displayed sequence, insufficient startup admission and cross-retry freshness. No unrelated schema/telemetry changes found."
      ],
      "unauthorized_byteCount": false,
      "official_passed_assertions_lost_vs_original": [],
      "supplemental_preservation_loss_confirmed": false
    },
    "js-base-2": {
      "business_files": [
        "src/progress.js"
      ],
      "auxiliary_artifacts": "patches/check copies/py_compile output, all retained in independent workspace and not production changes",
      "findings": [
        "Only progress watcher business code changed; correct warm order and attempt-local displayed sequence, insufficient startup admission and cross-retry freshness. No unrelated schema/telemetry changes found."
      ],
      "unauthorized_byteCount": false,
      "official_passed_assertions_lost_vs_original": [],
      "supplemental_preservation_loss_confirmed": false
    },
    "js-exp-1": {
      "business_files": [
        "src/progress.js",
        "src/queue.js",
        "src/retry.js"
      ],
      "auxiliary_artifacts": "patches/check copies/py_compile output, all retained in independent workspace and not production changes",
      "findings": [
        "src/queue.js: current physical attempt equality instead of visit-wide freshness",
        "src/retry.js: return after cancellation may discard already accepted retry command",
        "src/progress.js: accepting required on completion projection",
        "Supplemental source-derived preservation witness confirms accepted same-visit fresh completion is suppressed; official raw score has no corresponding assertion and remains unchanged."
      ],
      "unauthorized_byteCount": false,
      "official_passed_assertions_lost_vs_original": [],
      "supplemental_preservation_loss_confirmed": true
    },
    "js-exp-2": {
      "business_files": [
        "src/panel.js",
        "src/progress.js",
        "src/queue.js",
        "src/retry.js",
        "src/transfer.js"
      ],
      "auxiliary_artifacts": "patches/check copies/py_compile output, all retained in independent workspace and not production changes",
      "findings": [
        "src/queue.js: current physical attempt equality instead of visit-wide freshness",
        "src/retry.js: return after cancellation may discard already accepted retry command",
        "src/transfer.js: transport moved after progress subscription/start and gated by current owner",
        "Supplemental source-derived preservation witness confirms accepted same-visit fresh completion is suppressed; official raw score has no corresponding assertion and remains unchanged."
      ],
      "unauthorized_byteCount": false,
      "official_passed_assertions_lost_vs_original": [],
      "supplemental_preservation_loss_confirmed": true
    }
  }
}
```

成本按真实hook底层请求计，失败/取消也保留；缓存输入与推理输出是input/output子项，不重复相加。下表input/output含各自子项；完整细项在summary.json。

|阶段|会话|请求started/completed|工具hook|会话秒|input tokens|output tokens|
|---|---:|---:|---:|---:|---:|---:|
|M1|0模型|0/0|0模型工具|离线总时间未知；校准13.3秒|0模型|0模型|
|M2_extraction|2|6/6|4|74.1|73303|3364|
|M2_python_screen|2|26/26|24|530.8|508120|21521|
|M2_JS_baseline|2|25/25|23|367.5|433856|14615|
|M3_reflection|1|1/1|0|31.2|19451|764|
|M3_JS_revalidation|2|48/48|48|721.6|1210688|30038|
|M4_formal|0|0/0|0|0.0|0|0|
|模型阶段合计|9|106/106|99|1725.2|2245418|70302|

未获取用量的会话：[]。观测subtotal与未知总量分开，缺失不补零。主聊天准备/分析token及工具用量不可从实验hook取得，单列未知，不计作0；未核验价格，不估货币成本。M1校准本地子进程非模型工具。

结论边界：训练改善不等于验证收益；两例同源且已暴露，Python有额外启动窗口提示并通过宿主闭包表达延迟完成。重复不是独立案例；不能从本批声称纯语言效应、独立泛化、统计显著性或稳定收益。下一步须依据阶段停止原因另立协议；本批不补跑、不换题、不生成第二份经验。

未启动槽位：py-final-1-AUTO, py-final-1-AUTO_EXP, py-final-2-AUTO, py-final-2-AUTO_EXP, py-final-3-AUTO_EXP, py-final-3-AUTO。

两次超限调度均在发送模型请求之前被阻止；106次底层请求全部有Post hook与用量，另列2次blocked dispatch，不把它们误算成已发送请求。

完整性见 integrity-validation.json、request-accounting-validation.json、ARTIFACTS.sha256；所有旧文件/案例保护摘要及全局配置保持不变。
