# Retrieved candidate context

Raw source, configuration and documentation excerpts selected using the original task only. Retrieval is incomplete; inspect other candidate files when needed.

## src/channel.js:1-32
```
class PresenceEvent extends Event {
  constructor(detail) {
    super("presence");
    this.detail = detail;
  }
}

export function createPresenceChannel(token, { decode = (value) => value } = {}) {
  const target = new EventTarget();
  const emit = (kind) => target.dispatchEvent(new PresenceEvent(`${token}:${kind}`));
  return {
    target,
    decode,
    connect(bootstrapMode) {
      if (bootstrapMode === "deferred") queueMicrotask(() => emit("bootstrap"));
      else emit("bootstrap");
    },
    emitUpdate() {
      emit("update");
    },
  };
}

export async function observeChannel({ token, bootstrapMode }) {
  const events = [];
  const channel = createPresenceChannel(token);
  channel.connect(bootstrapMode);
  channel.target.addEventListener("presence", (event) => events.push(event.detail));
  await Promise.resolve();
  channel.emitUpdate();
  return { events };
}
```

## src/metrics-consumer.js:1-6
```
import { observeChannel } from "./channel.js";

export function collectMetrics(token) {
  // Metrics deliberately attach after the synchronous bootstrap and count deltas only.
  return observeChannel({ token, bootstrapMode: "synchronous" });
}
```

## src/presence-panel.js:1-27
```
import { createPresenceChannel } from "./channel.js";
import { subscribeChannel } from "./subscription.js";

export function createPresencePanel(publish) {
  let release = () => {};
  return {
    show(channel, bootstrapMode = "synchronous") {
      release();
      release = subscribeChannel(channel, bootstrapMode, publish);
    },
    close() {
      release();
      release = () => {};
    },
  };
}

export async function renderPresence(token, bootstrapMode) {
  const events = [];
  const panel = createPresencePanel((value) => events.push(value));
  const channel = createPresenceChannel(token);
  panel.show(channel, bootstrapMode);
  await Promise.resolve();
  channel.emitUpdate();
  panel.close();
  return { events };
}
```

## src/render-workspace.js:1-10
```
import { collectMetrics } from "./metrics-consumer.js";
import { renderPresence } from "./presence-panel.js";

export async function render({ token, bootstrapMode }) {
  const [presence, metrics] = await Promise.all([
    renderPresence(token, bootstrapMode),
    collectMetrics(token),
  ]);
  return { presence, metrics };
}
```

## src/subscription.js:1-12
```
// The decoder may return a value or a Promise (compressed network frames).
// EventTarget removal detaches reception; an already started decode still settles.
export function subscribeChannel(channel, bootstrapMode, receive) {
  const listener = (event) => {
    const decoded = channel.decode(event.detail);
    if (decoded && typeof decoded.then === "function") decoded.then(receive);
    else receive(decoded);
  };
  channel.connect(bootstrapMode);
  channel.target.addEventListener("presence", listener);
  return () => channel.target.removeEventListener("presence", listener);
}
```

## src/workspace-navigation.js:1-13
```
import { createPresencePanel } from "./presence-panel.js";

// Presence publication can synchronously select a different room or hide the
// panel (for example, a room chooser reacting to an empty bootstrap snapshot).
// Reusing a transport object on a later visit is supported by the workspace.
export function createWorkspaceNavigation(renderState) {
  const panel = createPresencePanel((value) => renderState(value, navigation));
  const navigation = {
    select(channel, mode = "synchronous") { panel.show(channel, mode); },
    hide() { panel.close(); },
  };
  return navigation;
}
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
