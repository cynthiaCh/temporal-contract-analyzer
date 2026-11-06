Work only on the candidate-visible files in this workspace. Do not inspect sibling experiment jobs, original repositories or report stores.

Document switching currently bypasses the departure handoff already used by
explicit close. Make `open(id)` perform that same handoff before showing the
target document. Preserve navigation semantics, close/dispose behavior, stored
document text, and all public interfaces.

<candidate-assistance>
# Retrieved candidate context

Raw source, configuration and documentation excerpts selected using the original task only. Retrieval is incomplete; inspect other candidate files when needed.

## README.md:1-12
```
# Document workspace departure handoff

`workspace.js` manages one visible document. Edits write synchronously to the
document store. Explicit close already performs a departure handoff so the host
can commit departure metadata or redirect to a conflict document.

A handoff integration may synchronously call the supplied navigation API. A
navigation call that starts later takes precedence, even if it returns before an
older call. `dispose()` is a silent teardown and does not run business handoff.

The workspace exposes synchronous `open`, `edit`, `close`, and `dispose` methods.
Keep these public interfaces and the document store's `read` and `write` methods.
```

## package.json:1-6
```
{
  "name": "handoff-redirect-reentrancy-fixture",
  "version": "1.0.0",
  "private": true,
  "type": "module"
}
```

## src/document-store.js:1-7
```
export function createDocumentStore(initial = {}) {
  const records = new Map(Object.entries(initial));
  return {
    read(id) { return records.get(id) ?? ""; },
    write(id, text) { records.set(id, text); return { id, text }; },
  };
}
```

## src/workspace.js:1-25
```
export function createWorkspace({ store, renderDocument, onHandoff = () => {} }) {
  let current = null;
  function retire(withHandoff) {
    const leaving = current;
    current = null;
    renderDocument(null);
    if (leaving && withHandoff) {
      onHandoff({ id: leaving.id, text: store.read(leaving.id) }, navigation);
    }
  }
  const navigation = {
    open(id) {
      // Switching currently bypasses the business handoff used by close.
      retire(false);
      current = { id };
      renderDocument({ id, text: store.read(id) });
    },
    edit(text) {
      if (current) store.write(current.id, text);
    },
    close() { retire(true); },
    dispose() { retire(false); },
  };
  return navigation;
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

</candidate-assistance>
