Work only on the candidate-visible files in this workspace. Do not inspect sibling experiment jobs, original repositories or report stores.

# Maintenance task

Immediately after opening the billing page, an entitled user's first click on the premium action sometimes does nothing. Fix the issue. Change only the premium action; do not migrate the emergency control.

<candidate-assistance>
# Retrieved candidate context

Raw source, configuration and documentation excerpts selected using the original task only. Retrieval is incomplete; inspect other candidate files when needed.

## src/temporal-flow.js:1-7
```
"use strict";

async function runTarget(input) { let enabled=false; let value="none"; if(input.clickBeforeReady&&enabled)value="premium-action"; await Promise.resolve(); enabled=input.loadedFlag; if(!input.clickBeforeReady&&enabled)value="premium-action"; return {value,events:[value]}; }
async function runAdjacent(input) { const value=input.clickBeforeReady?"emergency-action":"none"; await Promise.resolve(); return {value,events:[value]}; }

module.exports = { runTarget, runAdjacent };
```


# Temporal contract review questions

以下问题是待核查提示，不代表当前项目存在缺陷，也不构成额外业务要求。仅根据当前任务和候选源码决定是否适用。

{
  "id": "TCQ-001",
  "title": "首次事件与监听生效的顺序",
  "core_question": "消费者需要的首次事件，是否可能在监听生效之前同步发生？各消费者对首次事件的要求是否相同？",
  "preconditions": [
    "生产者启动时可能同步发事件，也可能延迟发事件。",
    "当前任务要求该消费者接收初始状态。"
  ],
  "event_orders": [
    {
      "sequence": [
        "启动生产者",
        "同步发出首次事件",
        "注册监听",
        "后续事件到达"
      ],
      "check": "定位首次事件是否存在重放或其他接收路径。"
    },
    {
      "sequence": [
        "注册监听",
        "启动生产者",
        "同步发出首次事件",
        "消费者回调"
      ],
      "check": "核查回调能否立即关闭或切换，以及此时清理能力是否可用。"
    },
    {
      "sequence": [
        "启动生产者",
        "注册监听",
        "延迟首次事件到达"
      ],
      "check": "延迟模式通过不能代替同步模式验证。"
    }
  ],
  "source_evidence_to_seek": [
    "跟踪实际事件派发实现及启动调用链，不能只看函数名。",
    "查监听生效点、首次派发点、缓存重放语义和消费者公开要求。",
    "查共享工具的其他调用方，确认它们需要初始值还是只需要增量。"
  ],
  "verification_methods": [
    "使用可控生产者分别同步派发和延迟派发；记录注册、派发、接收和退订顺序。",
    "比较首次状态、普通更新与其他消费者的输出；在首次回调中关闭或切换。"
  ],
  "non_applicability_and_preserved_behavior": [
    "若生产者保证事件只在注册返回后派发，需核实保证后再判断。",
    "某些消费者刻意只统计增量，不应被迫接收首次快照。",
    "保留公开接口、正常流式更新与资源清理。"
  ]
}

{
  "id": "TCQ-002",
  "title": "异步完成归属于哪一次访问",
  "core_question": "异步结果完成时，如何确认其仍属于可接收该结果的访问，而不是只确认资源标识相同？",
  "preconditions": [
    "接收事件后存在解码、请求或其他异步延续。",
    "界面或消费者可以关闭、切换并重新使用同一资源。"
  ],
  "event_orders": [
    {
      "sequence": [
        "访问甲接收事件并开始异步工作",
        "工作完成",
        "甲仍有效时发布"
      ],
      "check": "正常完成必须保留。"
    },
    {
      "sequence": [
        "访问甲开始异步工作",
        "关闭或切换",
        "旧工作完成"
      ],
      "check": "查当前项目是否允许旧结果产生各类副作用。"
    },
    {
      "sequence": [
        "访问甲开始工作",
        "关闭",
        "同一资源开启访问乙",
        "甲的工作完成"
      ],
      "check": "区分资源身份与访问身份，不能因资源相同自动接纳旧结果。"
    }
  ],
  "source_evidence_to_seek": [
    "查异步回调捕获的所有权与当前状态比较点。",
    "追踪退订、取消与 Promise 完成的真实关系。",
    "从可见任务和消费者实现确定哪些输出受访问约束。"
  ],
  "verification_methods": [
    "用可手动完成的异步结果，分别在正常、关闭、切换、同资源重开后完成。",
    "分别记录显示、持久化和其他副作用；检查后续新工作仍可使用且资源最终释放。"
  ],
  "non_applicability_and_preserved_behavior": [
    "若结果本来属于后台工作或持久历史，访问结束未必使结果失效。",
    "若依赖明确保证取消后不再执行延续，应核查实现与适用范围。"
  ]
}

{
  "id": "TCQ-003",
  "title": "同步重入前后的状态与请求优先级",
  "core_question": "可能同步调用外部回调之前，必要状态是否已可见；回调重入后，外层恢复执行是否仍有权写入当前状态？",
  "preconditions": [
    "启动、持久化、通知或清理会同步调用可重入的宿主代码。",
    "重入路径可以关闭、切换或再次发起操作。"
  ],
  "event_orders": [
    {
      "sequence": [
        "外层开始",
        "发布必要状态",
        "调用外部回调",
        "无重入",
        "外层完成"
      ],
      "check": "保留普通操作与清理能力。"
    },
    {
      "sequence": [
        "外层开始",
        "回调内发起后来操作",
        "后来操作完成",
        "外层恢复并尝试写当前状态"
      ],
      "check": "依据项目规定的优先级判断外层是否仍有写权限。"
    },
    {
      "sequence": [
        "启动中回调关闭",
        "启动返回清理句柄"
      ],
      "check": "查晚返回句柄是否被处理，以及是否覆盖了后来操作的句柄。"
    }
  ],
  "source_evidence_to_seek": [
    "展开到真正的同步派发点，追踪重入调用栈。",
    "找状态发布、失效、句柄登记及外层恢复后的写入。",
    "从任务、文档或现有行为确认请求优先级，不能自行规定最后返回者或最后开始者获胜。"
  ],
  "verification_methods": [
    "在通知、启动和释放回调中注入一次关闭或切换，记录进入与返回顺序。",
    "检查当前对象、句柄归属、后续编辑或事件输出及最终监听数量。",
    "同时覆盖无重入顺序，防止为阻止旧操作而阻断普通操作。"
  ],
  "non_applicability_and_preserved_behavior": [
    "若依赖保证无同步重入，先核实该保证。",
    "请求先后优先级属于项目契约，不应跨项目照搬。",
    "清理旧资源不能误清理新操作拥有的资源。"
  ]
}

{
  "id": "TCQ-004",
  "title": "持久副作用与当前显示分别有效",
  "core_question": "操作或事件已被接纳后，持久记录与当前显示分别依赖哪些有效性条件，能否共用同一个取消或新鲜度判断？",
  "preconditions": [
    "同一次操作产生持久记录、历史或归档，也产生界面显示或通知。",
    "两类输出可能在不同生命周期内仍有意义。"
  ],
  "event_orders": [
    {
      "sequence": [
        "接纳操作并确定归属",
        "完成",
        "记录并在原访问显示"
      ],
      "check": "无中断时两类必要输出都需保留。"
    },
    {
      "sequence": [
        "接纳工作",
        "结束原访问",
        "工作完成"
      ],
      "check": "分别查记录义务是否继续、当前显示是否应抑制。"
    },
    {
      "sequence": [
        "接纳值快照",
        "执行必要的保存",
        "同步回调切换或编辑",
        "生成记录并尝试通知"
      ],
      "check": "按项目契约核查记录身份和值是否保留，以及通知是否仍有归属。"
    }
  ],
  "source_evidence_to_seek": [
    "分别追踪每个副作用的消费者、存储与可见任务要求。",
    "明确接纳边界、操作快照、当前访问及取消范围。",
    "核对回调进入后新事件是否仍可接纳，与已经接纳工作完成是否有效是两个问题。"
  ],
  "verification_methods": [
    "构造完成前关闭、切换、同资源重开和重入编辑顺序，分别观察历史与界面。",
    "对照未中断、已接纳后中断、失效后新事件三类顺序。",
    "核查原有记录字段、次数、返回值和后续使用。"
  ],
  "non_applicability_and_preserved_behavior": [
    "并非所有项目都要求取消后继续记录；必须找到当前项目的依据。",
    "权限撤销、安全要求或事务回滚可能要求取消记录，本题不能替代这些规定。",
    "接纳快照是否冻结身份、值或权限，需要逐项确定。"
  ]
}

{
  "id": "TCQ-005",
  "title": "延迟写入在离开与提交边界如何结算",
  "core_question": "将即时操作改为延迟合并后，离开、提交或关闭返回时，哪些已接纳工作必须完成，哪些允许丢弃？",
  "preconditions": [
    "维护任务把即时写入改为定时合并、批处理或防抖。",
    "已有同步调用者依赖返回前可读取结果，或另有仅临时预览的消费者。"
  ],
  "event_orders": [
    {
      "sequence": [
        "接纳多次编辑",
        "静默期结束",
        "持久化最新值"
      ],
      "check": "核对合并语义与后续批次可继续工作。"
    },
    {
      "sequence": [
        "接纳编辑",
        "期限前离开或提交",
        "调用返回",
        "计时器才到期"
      ],
      "check": "核查返回和归档读取前的持久化义务是否仍满足。"
    },
    {
      "sequence": [
        "接纳临时预览",
        "期限前隐藏",
        "期限到达"
      ],
      "check": "对照此调用方是否应丢弃未发布工作，而不是强制完成。"
    }
  ],
  "source_evidence_to_seek": [
    "找写入迁移前后调用方对读取、同步返回与归档的依赖。",
    "追踪离开时退订显示、结算持久工作、执行外部回调的顺序。",
    "核查 flush 在调用 work 前是否已退休旧批次，防止重入新批次被清掉。"
  ],
  "verification_methods": [
    "用可控计时器覆盖期限前后提交、关闭、切换、同对象重开及第二轮编辑。",
    "在记录捕获与调用返回处读取持久状态，不能只等所有计时器结束再比较。",
    "让持久化回调重入编辑或导航，并检查新批次、显示和资源清理。"
  ],
  "non_applicability_and_preserved_behavior": [
    "隐藏后无价值的临时预览可能应取消，而持久编辑是否必须结算取决于公开要求。",
    "若调用契约本来允许异步持久化，不能自行增加同步等待。",
    "保留相邻消费者的原延迟、取消和复用行为。"
  ]
}

</candidate-assistance>

<base-execution>
Complete the original maintenance task in this candidate workspace using the available tools. Ground decisions in the original task and candidate-visible source, documentation and tests. Supplied assistance and skill checks may be inapplicable and do not create business requirements. Make justified changes, run relevant visible verification, and report what changed, actual checks and unresolved limits. Do not change hidden scoring, seek other experiment jobs, install dependencies or inspect research-side data. Do not answer an auxiliary question in place of doing the maintenance task. A justified no-change outcome is allowed.

</base-execution>

<temporal-contract-skill>
# Temporal contract skill: result ownership and effect validity

Purpose: help complete the original maintenance task. This skill is an aid, not a second task, a request for a prose-only answer, or a new business specification. Apply only what the original task and visible project evidence support.

S1 Applicability. Look for work that can finish after the initiating access, operation, or consumer changes, or a callback that can change ownership while another call is still running. Look for multiple effects such as a stored record and a current display. If these conditions are absent, record why this skill does not apply and continue the maintenance task.

S2 Source evidence. Read the entry, actual producer/decoder or dependency, completion callback, ownership transition/cancel path, and each effect consumer relevant to the change. Cite file:line. Separate task requirements, source facts, hypotheses, and unavailable evidence. Do not infer a dependency guarantee from a function name or add input formats/behaviors because they seem plausible.

S3 Check relations. Identify the resource, access/visit, physical operation/attempt, and accepted value or work when the visible code distinguishes them. Follow when those identities are captured, retired, and compared. Determine from this project whether cancellation removes future inputs, cancels already-started work, or only hides a consumer. For each effect, ask independently what identity and validity it needs; do not assume one guard suits every effect.

S4 Compare concrete orders. Using controllable visible APIs, compare ordinary completion; completion after close/switch; same-resource reuse; and replacement/retry if present. Include synchronous callback reentry when supported by the source. Observe stored effects and visible effects separately. For ordered full results, compare normal completion order and reversed completion order without inventing a frame schema.

S5 Non-applicability and unknowns. Background obligations, rollback, permission withdrawal, or dependencies that truly suppress completion can change the answer. Find visible evidence or keep the question unresolved. Do not impose persistence after cancellation or access-based cancellation on every project. Preserve other consumers of shared helpers and original public interfaces.

S6 Repair and verify. Implement the smallest supported maintenance change, or explain with evidence why no change is needed or why the task remains incomplete. Run relevant candidate-visible checks, inspect their real output and revise if warranted. Verify ordinary use, lifecycle boundaries, distinct effects, reuse, and adjacent behavior only where applicable. Keep failed/unrun checks explicit. A contract discussion or successful self-written smoke check alone is not completion of the original repair.

</temporal-contract-skill>

<external-control>
An external synchronous controller observes real tool outputs in this same Agent session. It keeps collect, inspect and repair_validate states. It can return to evidence collection for an explicit unresolved gap and can request a bounded continuation before final completion. Native tool choice, code interpretation, editing and test design remain your work; the controller does not establish semantic correctness.

Use /stage/checkpoint.json for a brief, current public checkpoint, not internal reasoning. Keep it under 2400 Unicode characters. Fields: state (collect/inspect/repair_validate), action_basis, evidence (list of existing workspace file:line references), observations (brief real outputs), unresolved (list), next_action. At inspect also give applicability (applicable/not_applicable), event_orders (two short concrete orders if applicable, or an empty list and evidence-backed reason if not). Read definitions/callers when a gap affects the decision. You may request collect again by setting state=collect and a concrete unresolved gap. Only concise grounds, no private chain of thought.

After inspection, do the original maintenance work and actual visible verification. Before finishing update the checkpoint with maintenance_status (completed/no_change/incomplete), reason, changed_paths, validation_commands, and remaining limits, as applicable. Records do not replace actual tool observations or a patch. If changed, show the actual repair and performed validation, including failures. If unchanged, cite the reason that no change is needed or why maintenance remains incomplete. Merely answering the skill is insufficient. Do not force a diff or invent requirements to satisfy this controller. At most two requested backward transitions, two edit-gate denials and two Stop continuations; the inherited total 600 seconds covers everything. If a limit is reached, report incompleteness honestly.

</external-control>
