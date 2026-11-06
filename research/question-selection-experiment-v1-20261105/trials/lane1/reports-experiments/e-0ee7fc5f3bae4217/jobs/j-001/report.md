# Retrieved candidate context

Raw source, configuration and documentation excerpts selected using the original task only. Retrieval is incomplete; inspect other candidate files when needed.

## README.md:1-33
```
# Document drafts and submission receipts

The workspace edits persistent document drafts. `open(id)`, `edit(text)`, `close()`
and `submit()` are synchronous; `dispose()` detaches integrations and closes.
When close/open returns, the departed document's last accepted edit is readable
from the store. A close/open request retires its previous save badge immediately.
Reopening a document restores its saved text in a new editor visit.

The store writes a record before notifying subscribers inline. `onSaved` may
navigate or edit through the supplied workspace API. Navigation precedence is
ordered by request start: a request that starts later wins even when an earlier
request returns afterward. Render functions and the receipt archive are output
sinks and never call back into the workspace.

`submit()` accepts the document and latest text selected at its call entry. With
no selection it returns null and creates no receipt. Otherwise it creates exactly
one immutable archive receipt and returns it before the call ends. Accepted text
must be persisted before the archive captures the receipt. Later edits or
navigation cannot change that receipt's document, text, or obligation to exist.
Submitting does not itself navigate. Its visible submission notice belongs only
to the editor visit that accepted the action: it may appear only if that same
visit is still active when the notice is emitted. Reopening the same document
creates a different visit. Any navigation clears the previous submission notice.
An uninterrupted submit must still show its receipt. Further edits remain usable.

The archive provides `capture({id, text})` and `list()`; receipts hold immutable
copies. The store provides `read`, `write`, and `subscribe`; timers provide
`schedule(callback, delay)` and `cancel(handle)`. Keep these interfaces and the
workspace API. The public renderer arguments remain document, save event, or
receipt values (null clears a document/notice).

The adjacent search preview publishes after a 40 ms quiet interval. Hiding it
discards an unpublished query, and a later query starts fresh work.
```

## src/draft-store.js:1-23
```
// A synchronous workspace store, independent of whether an editor is visible.
// Notifications run inline after the record is written. Subscribers may detach
// or subscribe while a notification is being delivered.
export function createDraftStore(initial = {}) {
  const records = new Map(Object.entries(initial));
  const listeners = new Set();
  let revision = 0;
  return {
    read(id) { return records.get(id) ?? ""; },
    write(id, text) {
      records.set(id, text);
      const event = { id, text, revision: ++revision };
      for (const listener of [...listeners]) {
        if (listeners.has(listener)) listener(event);
      }
      return event;
    },
    subscribe(listener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
  };
}
```

## src/editor.js:1-27
```
import { attachSaveStatus } from "./save-status.js";

export function createDraftEditor({ store, timers, renderDocument, renderStatus }) {
  let current = null;
  function close() {
    const leaving = current;
    current = null;
    if (leaving) leaving.stop();
    renderDocument(null);
  }
  return {
    open(id) {
      close();
      current = { id, text: store.read(id), visit: {}, stop: attachSaveStatus(store, id, renderStatus) };
      renderDocument({ id, text: current.text });
    },
    edit(text) {
      if (!current) return;
      current.text = text;
      store.write(current.id, text);
    },
    selection() {
      return current && { id: current.id, text: current.text, visit: current.visit };
    },
    close,
  };
}
```

## src/receipt-archive.js:1-13
```
// A downstream consumer: archived submissions are value snapshots, not live
// references to a draft. capture/list never invoke application integrations.
export function createReceiptArchive() {
  const receipts = [];
  return {
    capture({ id, text }) {
      const receipt = Object.freeze({ id, text });
      receipts.push(receipt);
      return receipt;
    },
    list() { return receipts.map(receipt => ({ ...receipt })); },
  };
}
```

## src/save-status.js:1-8
```
// A mounted document's save badge. A close/open request retires the departing
// badge immediately: it must produce no further output, including during that
// navigation call. Saving the document itself is a separate workspace concern.
export function attachSaveStatus(store, id, renderStatus) {
  return store.subscribe(event => {
    if (event.id === id) renderStatus(event);
  });
}
```

## src/search-preview.js:1-10
```
import { createTrailingTask } from "./trailing-task.js";

export function createSearchPreview({ timers, publish }) {
  const task = createTrailingTask(query => publish({ query }), 40, timers);
  return {
    query(text) { task.push(text); },
    // A hidden preview has no use for a pending query; reopen starts fresh.
    hide() { task.cancel(); },
  };
}
```

## src/trailing-task.js:1-28
```
import { browserTimers } from "./timers.js";

// Coalesce calls until a quiet interval. cancel discards work; flush runs it now.
// Retire the old batch before invoking work, which can enqueue another batch.
export function createTrailingTask(work, delay, timers = browserTimers) {
  let handle = null;
  let pending = null;
  function flush() {
    if (handle !== null) timers.cancel(handle);
    handle = null;
    const args = pending;
    pending = null;
    if (args !== null) work(...args);
  }
  return {
    push(...args) {
      if (handle !== null) timers.cancel(handle);
      pending = args;
      handle = timers.schedule(flush, delay);
    },
    flush,
    cancel() {
      if (handle !== null) timers.cancel(handle);
      handle = null;
      pending = null;
    },
  };
}
```

## src/workspace.js:1-20
```
import { createDraftEditor } from "./editor.js";

export function createWorkspace({ store, archive, timers, renderDocument, renderStatus,
  renderSubmission = () => {}, onSaved = () => {} }) {
  const stop = store.subscribe(event => onSaved(event, navigation));
  const editor = createDraftEditor({ store, timers, renderDocument, renderStatus });
  const navigation = {
    open(id) { renderSubmission(null); editor.open(id); },
    edit(text) { editor.edit(text); },
    close() { renderSubmission(null); editor.close(); },
    submit() {
      const origin = editor.selection();
      if (!origin) return null;
      const receipt = archive.capture({ id: origin.id, text: origin.text });
      renderSubmission(receipt);
      return receipt;
    },
  };
  return { ...navigation, dispose() { stop(); navigation.close(); } };
}
```


# Temporal contract review questions

以下问题是待核查提示，不代表当前项目存在缺陷，也不构成额外业务要求。仅根据当前任务和候选源码决定是否适用。

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
