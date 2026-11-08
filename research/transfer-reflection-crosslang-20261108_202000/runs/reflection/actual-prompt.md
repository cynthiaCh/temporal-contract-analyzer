根据以下训练例的源绑定差异与真实维护结果，只进行一次 Reflection，输出一份新的通用时序修复经验。不修改模型权重，不进行搜索或第二轮改写。
经验必须覆盖：适用机制/前提、应查证的事件关系、应采取的验证动作、应保留的相邻行为、可能不适用情况。
严禁写入任何案例ID、测试/评分断言名称、测试专用值、可直接复制的补丁、具体文件名或JS API名称；用跨语言事件/身份/生命周期关系描述。不能把推测变成新业务政策。不要提及验证题。只输出经验正文。
返回JSON，唯一字段report，最多6000个Unicode字符。不能调用工具。

训练原任务：
A transfer with a warm progress source shows no initial progress until a later
packet arrives. Restore the initial progress update without changing the public
transfer, retry, navigation, cleanup, audit, or queue-record behavior. Full
progress frames may decode out of order; do not allow an older frame to roll the
current display backward. Preserve ordinary streaming, diagnostic telemetry,
and subsequent uses.


训练候选可见文档和源码：
SOURCE README.md
# Transfer retry panel with decoded progress

This workspace selects files, starts transfers, records queue and progress
history, and paints progress for the open panel. Run it with Node v16.20.2; it
has no dependencies. `src/workspace.js` exports the workspace and the source
helpers used by the host application.

Selecting a file creates a visit. Retry replaces the physical attempt without
opening another visit. Selecting the same file again does open another visit.
The feed object is shared by attempts and visits for that file. Its `start()`
method may synchronously emit cached data, and `decode(packet)` may return a
value or a Promise.

`recordProgress` appends transfer history. `showProgress` paints the panel.
The queue adapter in `src/queue.js` shows how those two outputs currently relate
to a visit. Queue records, notices, cancellation, retry, navigation, and cleanup
retain their existing behavior. Queue records remain
`{fileId, attemptId, visitId, kind}` unless a separate authorization adds
`byteCount` from `file.size`.

The same feed API also has a diagnostic consumer in `src/telemetry.js`.
It is not the panel and must keep its existing behavior while the panel defect
is repaired. `src/progress-source.js` is the host-visible feed implementation;
the navigation and transfer modules show how ownership is handed off when a
listener is released. Host callbacks are synchronous unless their code returns
a Promise.


SOURCE src/notice.js
// A queued notice describes the accepted attempt in its originating visit.
export function publishQueued(state, visit, handle) {
  state.showQueued({ fileId: visit.file.id, attemptId: handle.attemptId,
    visitId: visit.id, status: "queued" });
}


SOURCE src/retry.js
import { enqueueTransfer } from "./queue.js";
import { publishQueued } from "./notice.js";

// A retry click accepts exactly one command for the current visit and file.
export function retryTransfer(state) {
  const visit = state.current;
  if (!visit || !visit.handle || state.disposed) return null;
  const previous = visit.handle;
  previous.cancel();
  const handle = enqueueTransfer(state, visit, "retry");
  if (state.current === visit) visit.handle = handle;
  else handle.cancel();
  if (state.current === visit) publishQueued(state, visit, handle);
  return handle;
}


SOURCE src/transfer.js
import { watchTransferProgress } from "./progress.js";

export function createTransfer(file, attemptId, transport, onCancel, progress = {}) {
  const controller = new AbortController();
  let stopProgress = () => {};
  controller.signal.addEventListener("abort", () => {
    stopProgress();
    onCancel({ file, attemptId, signal: controller.signal });
  }, { once: true });
  transport({ file, attemptId, signal: controller.signal });
  if (file.progressFeed) {
    stopProgress = watchTransferProgress(file.progressFeed, progress.receive, progress.record);
    if (controller.signal.aborted) stopProgress();
  }
  return { file, attemptId, signal: controller.signal,
    cancel() { if (!controller.signal.aborted) controller.abort(); } };
}


SOURCE src/queue.js
import { createTransfer } from "./transfer.js";

// Queue records are retained even when their originating panel visit ends.
export function makeQueueRecord(file, attemptId, visitId, kind) {
  return { fileId: file.id, attemptId, visitId, kind };
}

export function enqueueTransfer(state, visit, kind) {
  const attemptId = ++state.nextAttempt;
  state.record(makeQueueRecord(visit.file, attemptId, visit.id, kind));
  const progress = {
    record(frame) { state.recordProgress({ fileId: visit.file.id, attemptId, frame }); },
    receive(frame) {
      if (state.current === visit) state.showProgress({ fileId: visit.file.id, attemptId, frame });
    },
  };
  const handle = createTransfer(visit.file, attemptId, state.transport, state.onCancel, progress);
  state.tasks.set(attemptId, handle);
  return handle;
}


SOURCE src/telemetry.js
// Diagnostics count live deltas only. A cached bootstrap is panel state, not a delta.
export function collectProgressTelemetry(feed, recordDelta) {
  const listener = event => {
    const deliver = frame => recordDelta(frame);
    const decoded = feed.decode(event.detail);
    if (decoded && typeof decoded.then === "function") decoded.then(deliver);
    else deliver(decoded);
  };
  feed.start();
  feed.target.addEventListener("progress", listener);
  return () => feed.target.removeEventListener("progress", listener);
}


SOURCE src/panel.js
import { enqueueTransfer } from "./queue.js";
import { publishQueued } from "./notice.js";

export function releaseVisit(visit) {
  const handle = visit.handle;
  visit.handle = null;
  if (handle) handle.cancel();
}

export function selectFile(state, file) {
  if (state.disposed) return null;
  const requestId = ++state.nextVisit;
  const previous = state.current;
  state.current = null;
  if (previous) releaseVisit(previous);
  if (state.disposed || state.nextVisit !== requestId) return null;
  const visit = { id: requestId, file, handle: null };
  state.current = visit;
  const handle = enqueueTransfer(state, visit, "select");
  if (state.current === visit) {
    visit.handle = handle;
    publishQueued(state, visit, handle);
  } else {
    handle.cancel();
  }
  return handle;
}

export function hidePanel(state) {
  state.nextVisit++;
  const previous = state.current;
  state.current = null;
  if (previous) releaseVisit(previous);
}

export function disposeWorkspace(state) {
  if (state.disposed) return;
  state.disposed = true;
  hidePanel(state);
  for (const handle of state.tasks.values()) handle.cancel();
}


SOURCE src/progress.js
// The source is shared by visits of the same file. Decoding may settle later.
export function watchTransferProgress(feed, receive, record) {
  const listener = event => {
    const deliver = frame => { record(frame); receive(frame); };
    const decoded = feed.decode(event.detail);
    if (decoded && typeof decoded.then === "function") decoded.then(deliver);
    else deliver(decoded);
  };
  feed.start();
  feed.target.addEventListener("progress", listener);
  return () => feed.target.removeEventListener("progress", listener);
}


SOURCE src/progress-source.js
class ProgressEvent extends Event {
  constructor(packet) {
    super("progress");
    this.detail = packet;
  }
}

// Removal commits before notifying the host. The host callback is synchronous
// and may call workspace.select(...) or workspace.hide(). Repeated removal is inert.
export function createProgressFeed({ initialPacket, decode = value => value, onDetach = () => {} }) {
  const target = new EventTarget();
  const listeners = new Set();
  const add = target.addEventListener.bind(target);
  const remove = target.removeEventListener.bind(target);
  target.addEventListener = (type, listener, options) => {
    add(type, listener, options);
    if (type === "progress") listeners.add(listener);
  };
  target.removeEventListener = (type, listener, options) => {
    remove(type, listener, options);
    if (type === "progress" && listeners.delete(listener)) onDetach();
  };
  return {
    target,
    decode,
    start() {
      const packet = typeof initialPacket === "function" ? initialPacket() : initialPacket;
      if (packet !== undefined) target.dispatchEvent(new ProgressEvent(packet));
    },
    emit(packet) { target.dispatchEvent(new ProgressEvent(packet)); },
  };
}


SOURCE src/workspace.js
import { selectFile, hidePanel, disposeWorkspace } from "./panel.js";
import { retryTransfer } from "./retry.js";

export function createTransferWorkspace({ transport, onCancel, record, showQueued, recordProgress = () => {}, showProgress = () => {} }) {
  const state = { transport, onCancel, record, showQueued, recordProgress, showProgress, current: null,
    nextVisit: 0, nextAttempt: 0, tasks: new Map(), disposed: false };
  return {
    select(file) { return selectFile(state, file); },
    retry() { return retryTransfer(state); },
    hide() { hidePanel(state); },
    dispose() { disposeWorkspace(state); },
    snapshot() {
      const visit = state.current;
      return { visitId: visit ? visit.id : null, fileId: visit ? visit.file.id : null,
        attemptId: visit && visit.handle ? visit.handle.attemptId : null,
        disposed: state.disposed, attempts: state.nextAttempt };
    },
  };
}

export { createTransfer } from "./transfer.js";
export { makeQueueRecord, enqueueTransfer } from "./queue.js";
export { publishQueued } from "./notice.js";
export { releaseVisit, selectFile, hidePanel, disposeWorkspace } from "./panel.js";
export { retryTransfer } from "./retry.js";
export { collectProgressTelemetry } from "./telemetry.js";
export { createProgressFeed } from "./progress-source.js";


评价侧源绑定差异投影及实际训练结果：
{
  "AI_assisted_evaluator_projection": true,
  "standard_contract_not_delivered": true,
  "reference_patch_not_delivered": true,
  "validation_material_not_read": true,
  "runs": [
    {
      "repeat": 1,
      "source_bound_differences": [
        {
          "relation": "Invalidate admission immediately when synchronous delivery replaces the current visit, including before setup returns its cleanup handle. Already admitted completion still records history.",
          "sources": [
            {
              "file": "README.md",
              "sha256": "dd7e418532233021f6bce86d712b6a6dd1f1f5a4796812eb8d2069444c9ab26c"
            },
            {
              "file": "src/progress.js",
              "sha256": "69812c6d3f111528ec61c6807c25d727ba291e93c1b19f2d9e6e978d08f35061"
            },
            {
              "file": "src/transfer.js",
              "sha256": "fd27be4d41174cd20fea6d50e5b6be08da089f46779823c699709b64846fc4f8"
            },
            {
              "file": "src/queue.js",
              "sha256": "7018d36249fb316c093c8fd992e8eabb1dc9a5ea82c054107120e007293bce4d"
            },
            {
              "file": "src/panel.js",
              "sha256": "9c0ac97b224ade688d62bde60f1b3327e7b565a22ec4bf16450ae1269190269e"
            }
          ],
          "observed_training_trace": [
            {
              "step": 1,
              "type": "host.select",
              "fileId": "A"
            },
            {
              "step": 2,
              "type": "queue.record",
              "fileId": "A",
              "attemptId": 1,
              "visitId": 1,
              "kind": "select"
            },
            {
              "step": 3,
              "type": "transport",
              "fileId": "A",
              "attemptId": 1
            },
            {
              "step": 4,
              "type": "feed.start",
              "fileId": "A",
              "starts": 1
            },
            {
              "step": 5,
              "type": "feed.emit",
              "fileId": "A",
              "seq": 1,
              "deferred": false
            },
            {
              "step": 6,
              "type": "progress.audit",
              "fileId": "A",
              "attemptId": 1,
              "seq": 1
            },
            {
              "step": 7,
              "type": "progress.visible",
              "fileId": "A",
              "attemptId": 1,
              "seq": 1
            },
            {
              "step": 8,
              "type": "host.select",
              "fileId": "B"
            },
            {
              "step": 9,
              "type": "queue.record",
              "fileId": "B",
              "attemptId": 2,
              "visitId": 2,
              "kind": "select"
            },
            {
              "step": 10,
              "type": "transport",
              "fileId": "B",
              "attemptId": 2
            },
            {
              "step": 11,
              "type": "feed.start",
              "fileId": "B",
              "starts": 1
            },
            {
              "step": 12,
              "type": "feed.emit",
              "fileId": "B",
              "seq": 1,
              "deferred": false
            },
            {
              "step": 13,
              "type": "progress.audit",
              "fileId": "B",
              "attemptId": 2,
              "seq": 1
            },
            {
              "step": 14,
              "type": "progress.visible",
              "fileId": "B",
              "attemptId": 2,
              "seq": 1
            },
            {
              "step": 15,
              "type": "queue.notice",
              "fileId": "B",
              "attemptId": 2,
              "visitId": 2,
              "status": "queued"
            },
            {
              "step": 16,
              "type": "feed.emit",
              "fileId": "A",
              "seq": 2,
              "deferred": false
            },
            {
              "step": 17,
              "type": "progress.audit",
              "fileId": "A",
              "attemptId": 1,
              "seq": 2
            },
            {
              "step": 18,
              "type": "feed.detach",
              "fileId": "A"
            },
            {
              "step": 19,
              "type": "cancel",
              "fileId": "A",
              "attemptId": 1
            },
            {
              "step": 20,
              "type": "feed.detach",
              "fileId": "B"
            },
            {
              "step": 21,
              "type": "cancel",
              "fileId": "B",
              "attemptId": 2
            }
          ],
          "evidence_source": "runs/js-base-1/score.stdout.json schedules/start-switch-admission",
          "note": "This relation failed external observation; root-cause responsibility remains a hypothesis until traced to actual patched code."
        },
        {
          "relation": "Retry remains in its visit and accepts one command; its cancellation/queue ordering is preserved, while stale completions cannot roll current display back across attempts.",
          "sources": [
            {
              "file": "README.md",
              "sha256": "dd7e418532233021f6bce86d712b6a6dd1f1f5a4796812eb8d2069444c9ab26c"
            },
            {
              "file": "src/retry.js",
              "sha256": "69f8b3b9e8f1f97f5a66e39a2fdad4c13e0668662ba4f32942e9bed3b2d382ff"
            },
            {
              "file": "src/notice.js",
              "sha256": "73e745110bf4f17ec126903f39780c134e0286ac8859939d0f0e3383f944fe56"
            },
            {
              "file": "src/queue.js",
              "sha256": "7018d36249fb316c093c8fd992e8eabb1dc9a5ea82c054107120e007293bce4d"
            }
          ],
          "observed_training_trace": [
            {
              "step": 1,
              "type": "host.select",
              "fileId": "A"
            },
            {
              "step": 2,
              "type": "queue.record",
              "fileId": "A",
              "attemptId": 1,
              "visitId": 1,
              "kind": "select"
            },
            {
              "step": 3,
              "type": "transport",
              "fileId": "A",
              "attemptId": 1
            },
            {
              "step": 4,
              "type": "feed.start",
              "fileId": "A",
              "starts": 1
            },
            {
              "step": 5,
              "type": "feed.emit",
              "fileId": "A",
              "seq": 1,
              "deferred": false
            },
            {
              "step": 6,
              "type": "progress.audit",
              "fileId": "A",
              "attemptId": 1,
              "seq": 1
            },
            {
              "step": 7,
              "type": "progress.visible",
              "fileId": "A",
              "attemptId": 1,
              "seq": 1
            },
            {
              "step": 8,
              "type": "queue.notice",
              "fileId": "A",
              "attemptId": 1,
              "visitId": 1,
              "status": "queued"
            },
            {
              "step": 9,
              "type": "feed.emit",
              "fileId": "A",
              "seq": 2,
              "deferred": true
            },
            {
              "step": 10,
              "type": "feed.detach",
              "fileId": "A"
            },
            {
              "step": 11,
              "type": "cancel",
              "fileId": "A",
              "attemptId": 1
            },
            {
              "step": 12,
              "type": "queue.record",
              "fileId": "A",
              "attemptId": 2,
              "visitId": 1,
              "kind": "retry"
            },
            {
              "step": 13,
              "type": "transport",
              "fileId": "A",
              "attemptId": 2
            },
            {
              "step": 14,
              "type": "feed.start",
              "fileId": "A",
              "starts": 2
            },
            {
              "step": 15,
              "type": "feed.emit",
              "fileId": "A",
              "seq": 3,
              "deferred": false
            },
            {
              "step": 16,
              "type": "progress.audit",
              "fileId": "A",
              "attemptId": 2,
              "seq": 3
            },
            {
              "step": 17,
              "type": "progress.visible",
              "fileId": "A",
              "attemptId": 2,
              "seq": 3
            },
            {
              "step": 18,
              "type": "queue.notice",
              "fileId": "A",
              "attemptId": 2,
              "visitId": 1,
              "status": "queued"
            },
            {
              "step": 19,
              "type": "progress.audit",
              "fileId": "A",
              "attemptId": 1,
              "seq": 2
            },
            {
              "step": 20,
              "type": "progress.visible",
              "fileId": "A",
              "attemptId": 1,
              "seq": 2
            },
            {
              "step": 21,
              "type": "feed.detach",
              "fileId": "A"
            },
            {
              "step": 22,
              "type": "cancel",
              "fileId": "A",
              "attemptId": 2
            }
          ],
          "evidence_source": "runs/js-base-1/score.stdout.json schedules/retry-preserved",
          "note": "This relation failed external observation; root-cause responsibility remains a hypothesis until traced to actual patched code."
        }
      ],
      "preserve_observed_relations": [
        "Install the panel receiver before a synchronous producer can emit; retain ordinary streaming.",
        "Separate admission lifetime, accepted completion/history lifetime and current-view eligibility.",
        "Preserve ordinary stream publication and audit while repairing startup.",
        "Visible full-frame freshness follows packet arrival, not decode completion or payload magnitude; history retains accepted completions.",
        "Retire ownership before synchronous cleanup, then revalidate the outer navigation request before starting its destination.",
        "A synchronous cleanup navigation/hide supersedes the outer navigation destination.",
        "Admission, completion/history, visit-wide freshness and cleanup priority must compose on a single event path.",
        "Keep the independent diagnostic consumer live-delta-only and preserve its cleanup and accepted completion."
      ],
      "passed_assertions_evaluation_side_only_count": 56,
      "model_report": "{\"report\":\"已交付：修改 src/progress.js。面板进度现在先注册监听器再启动进度源，因此同步缓存首包会立即显示；每个源帧按接收顺序编号，异步解码完成较晚的旧帧仍会进入 record 审计，但不会使 receive/display 回退。未修改传输、重试、导航、清理、队列记录或 telemetry 代码。\\n\\n补丁已归档：/workspace/patches/initial-progress-ordering.patch（反向 dry-run 通过）。\\n\\n验证：/runtime/node --version = v18.17.0；语法检查通过。内联回归检查通过：缓存首包与后续流式帧、乱序异步解码（显示保持新帧、审计保留全部帧）、独立 telemetry 的 live-delta 行为、重试/队列记录/取消与监听器清理。\\n\\n未覆盖范围：项目未提供测试套件或依赖安装配置，未执行外部端到端测试。\"}",
      "actual_patch": "diff -ruN /home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-reflection-crosslang-20261108_202000/materials/transfer-progress-composition-v4-vanilla/candidate/patches/initial-progress-ordering.patch /home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-reflection-crosslang-20261108_202000/runs/js-base-1/workspace/patches/initial-progress-ordering.patch\n--- /home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-reflection-crosslang-20261108_202000/materials/transfer-progress-composition-v4-vanilla/candidate/patches/initial-progress-ordering.patch\t1970-01-01 08:00:00.000000000 +0800\n+++ /home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-reflection-crosslang-20261108_202000/runs/js-base-1/workspace/patches/initial-progress-ordering.patch\t2026-11-08 12:35:02.581535277 +0800\n@@ -0,0 +1,26 @@\n+--- a/src/progress.js\n++++ b/src/progress.js\n+@@ -1,12 +1,21 @@\n+ // The source is shared by visits of the same file. Decoding may settle later.\n+ export function watchTransferProgress(feed, receive, record) {\n++  let nextFrame = 0;\n++  let displayedFrame = -1;\n+   const listener = event => {\n+-    const deliver = frame => { record(frame); receive(frame); };\n++    const frameNumber = nextFrame++;\n++    const deliver = frame => {\n++      record(frame);\n++      if (frameNumber > displayedFrame) {\n++        displayedFrame = frameNumber;\n++        receive(frame);\n++      }\n++    };\n+     const decoded = feed.decode(event.detail);\n+     if (decoded && typeof decoded.then === \"function\") decoded.then(deliver);\n+     else deliver(decoded);\n+   };\n+-  feed.start();\n+   feed.target.addEventListener(\"progress\", listener);\n++  feed.start();\n+   return () => feed.target.removeEventListener(\"progress\", listener);\n+ }\ndiff -ruN /home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-reflection-crosslang-20261108_202000/materials/transfer-progress-composition-v4-vanilla/candidate/src/progress.js /home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-reflection-crosslang-20261108_202000/runs/js-base-1/workspace/src/progress.js\n--- /home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-reflection-crosslang-20261108_202000/materials/transfer-progress-composition-v4-vanilla/candidate/src/progress.js\t2026-10-04 01:06:18.007455648 +0800\n+++ /home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-reflection-crosslang-20261108_202000/runs/js-base-1/workspace/src/progress.js\t2026-11-08 12:33:59.064464930 +0800\n@@ -1,12 +1,21 @@\n // The source is shared by visits of the same file. Decoding may settle later.\n export function watchTransferProgress(feed, receive, record) {\n+  let nextFrame = 0;\n+  let displayedFrame = -1;\n   const listener = event => {\n-    const deliver = frame => { record(frame); receive(frame); };\n+    const frameNumber = nextFrame++;\n+    const deliver = frame => {\n+      record(frame);\n+      if (frameNumber > displayedFrame) {\n+        displayedFrame = frameNumber;\n+        receive(frame);\n+      }\n+    };\n     const decoded = feed.decode(event.detail);\n     if (decoded && typeof decoded.then === \"function\") decoded.then(deliver);\n     else deliver(decoded);\n   };\n-  feed.start();\n   feed.target.addEventListener(\"progress\", listener);\n+  feed.start();\n   return () => feed.target.removeEventListener(\"progress\", listener);\n }\n",
      "unknown_causes": "Observed schedule failure does not alone establish which missing guard or ownership scope caused it; training traces and patch must be inspected."
    },
    {
      "repeat": 2,
      "source_bound_differences": [
        {
          "relation": "Invalidate admission immediately when synchronous delivery replaces the current visit, including before setup returns its cleanup handle. Already admitted completion still records history.",
          "sources": [
            {
              "file": "README.md",
              "sha256": "dd7e418532233021f6bce86d712b6a6dd1f1f5a4796812eb8d2069444c9ab26c"
            },
            {
              "file": "src/progress.js",
              "sha256": "69812c6d3f111528ec61c6807c25d727ba291e93c1b19f2d9e6e978d08f35061"
            },
            {
              "file": "src/transfer.js",
              "sha256": "fd27be4d41174cd20fea6d50e5b6be08da089f46779823c699709b64846fc4f8"
            },
            {
              "file": "src/queue.js",
              "sha256": "7018d36249fb316c093c8fd992e8eabb1dc9a5ea82c054107120e007293bce4d"
            },
            {
              "file": "src/panel.js",
              "sha256": "9c0ac97b224ade688d62bde60f1b3327e7b565a22ec4bf16450ae1269190269e"
            }
          ],
          "observed_training_trace": [
            {
              "step": 1,
              "type": "host.select",
              "fileId": "A"
            },
            {
              "step": 2,
              "type": "queue.record",
              "fileId": "A",
              "attemptId": 1,
              "visitId": 1,
              "kind": "select"
            },
            {
              "step": 3,
              "type": "transport",
              "fileId": "A",
              "attemptId": 1
            },
            {
              "step": 4,
              "type": "feed.start",
              "fileId": "A",
              "starts": 1
            },
            {
              "step": 5,
              "type": "feed.emit",
              "fileId": "A",
              "seq": 1,
              "deferred": false
            },
            {
              "step": 6,
              "type": "progress.audit",
              "fileId": "A",
              "attemptId": 1,
              "seq": 1
            },
            {
              "step": 7,
              "type": "progress.visible",
              "fileId": "A",
              "attemptId": 1,
              "seq": 1
            },
            {
              "step": 8,
              "type": "host.select",
              "fileId": "B"
            },
            {
              "step": 9,
              "type": "queue.record",
              "fileId": "B",
              "attemptId": 2,
              "visitId": 2,
              "kind": "select"
            },
            {
              "step": 10,
              "type": "transport",
              "fileId": "B",
              "attemptId": 2
            },
            {
              "step": 11,
              "type": "feed.start",
              "fileId": "B",
              "starts": 1
            },
            {
              "step": 12,
              "type": "feed.emit",
              "fileId": "B",
              "seq": 1,
              "deferred": false
            },
            {
              "step": 13,
              "type": "progress.audit",
              "fileId": "B",
              "attemptId": 2,
              "seq": 1
            },
            {
              "step": 14,
              "type": "progress.visible",
              "fileId": "B",
              "attemptId": 2,
              "seq": 1
            },
            {
              "step": 15,
              "type": "queue.notice",
              "fileId": "B",
              "attemptId": 2,
              "visitId": 2,
              "status": "queued"
            },
            {
              "step": 16,
              "type": "feed.emit",
              "fileId": "A",
              "seq": 2,
              "deferred": false
            },
            {
              "step": 17,
              "type": "progress.audit",
              "fileId": "A",
              "attemptId": 1,
              "seq": 2
            },
            {
              "step": 18,
              "type": "feed.detach",
              "fileId": "A"
            },
            {
              "step": 19,
              "type": "cancel",
              "fileId": "A",
              "attemptId": 1
            },
            {
              "step": 20,
              "type": "feed.detach",
              "fileId": "B"
            },
            {
              "step": 21,
              "type": "cancel",
              "fileId": "B",
              "attemptId": 2
            }
          ],
          "evidence_source": "runs/js-base-2/score.stdout.json schedules/start-switch-admission",
          "note": "This relation failed external observation; root-cause responsibility remains a hypothesis until traced to actual patched code."
        },
        {
          "relation": "Retry remains in its visit and accepts one command; its cancellation/queue ordering is preserved, while stale completions cannot roll current display back across attempts.",
          "sources": [
            {
              "file": "README.md",
              "sha256": "dd7e418532233021f6bce86d712b6a6dd1f1f5a4796812eb8d2069444c9ab26c"
            },
            {
              "file": "src/retry.js",
              "sha256": "69f8b3b9e8f1f97f5a66e39a2fdad4c13e0668662ba4f32942e9bed3b2d382ff"
            },
            {
              "file": "src/notice.js",
              "sha256": "73e745110bf4f17ec126903f39780c134e0286ac8859939d0f0e3383f944fe56"
            },
            {
              "file": "src/queue.js",
              "sha256": "7018d36249fb316c093c8fd992e8eabb1dc9a5ea82c054107120e007293bce4d"
            }
          ],
          "observed_training_trace": [
            {
              "step": 1,
              "type": "host.select",
              "fileId": "A"
            },
            {
              "step": 2,
              "type": "queue.record",
              "fileId": "A",
              "attemptId": 1,
              "visitId": 1,
              "kind": "select"
            },
            {
              "step": 3,
              "type": "transport",
              "fileId": "A",
              "attemptId": 1
            },
            {
              "step": 4,
              "type": "feed.start",
              "fileId": "A",
              "starts": 1
            },
            {
              "step": 5,
              "type": "feed.emit",
              "fileId": "A",
              "seq": 1,
              "deferred": false
            },
            {
              "step": 6,
              "type": "progress.audit",
              "fileId": "A",
              "attemptId": 1,
              "seq": 1
            },
            {
              "step": 7,
              "type": "progress.visible",
              "fileId": "A",
              "attemptId": 1,
              "seq": 1
            },
            {
              "step": 8,
              "type": "queue.notice",
              "fileId": "A",
              "attemptId": 1,
              "visitId": 1,
              "status": "queued"
            },
            {
              "step": 9,
              "type": "feed.emit",
              "fileId": "A",
              "seq": 2,
              "deferred": true
            },
            {
              "step": 10,
              "type": "feed.detach",
              "fileId": "A"
            },
            {
              "step": 11,
              "type": "cancel",
              "fileId": "A",
              "attemptId": 1
            },
            {
              "step": 12,
              "type": "queue.record",
              "fileId": "A",
              "attemptId": 2,
              "visitId": 1,
              "kind": "retry"
            },
            {
              "step": 13,
              "type": "transport",
              "fileId": "A",
              "attemptId": 2
            },
            {
              "step": 14,
              "type": "feed.start",
              "fileId": "A",
              "starts": 2
            },
            {
              "step": 15,
              "type": "feed.emit",
              "fileId": "A",
              "seq": 3,
              "deferred": false
            },
            {
              "step": 16,
              "type": "progress.audit",
              "fileId": "A",
              "attemptId": 2,
              "seq": 3
            },
            {
              "step": 17,
              "type": "progress.visible",
              "fileId": "A",
              "attemptId": 2,
              "seq": 3
            },
            {
              "step": 18,
              "type": "queue.notice",
              "fileId": "A",
              "attemptId": 2,
              "visitId": 1,
              "status": "queued"
            },
            {
              "step": 19,
              "type": "progress.audit",
              "fileId": "A",
              "attemptId": 1,
              "seq": 2
            },
            {
              "step": 20,
              "type": "progress.visible",
              "fileId": "A",
              "attemptId": 1,
              "seq": 2
            },
            {
              "step": 21,
              "type": "feed.detach",
              "fileId": "A"
            },
            {
              "step": 22,
              "type": "cancel",
              "fileId": "A",
              "attemptId": 2
            }
          ],
          "evidence_source": "runs/js-base-2/score.stdout.json schedules/retry-preserved",
          "note": "This relation failed external observation; root-cause responsibility remains a hypothesis until traced to actual patched code."
        }
      ],
      "preserve_observed_relations": [
        "Install the panel receiver before a synchronous producer can emit; retain ordinary streaming.",
        "Separate admission lifetime, accepted completion/history lifetime and current-view eligibility.",
        "Preserve ordinary stream publication and audit while repairing startup.",
        "Visible full-frame freshness follows packet arrival, not decode completion or payload magnitude; history retains accepted completions.",
        "Retire ownership before synchronous cleanup, then revalidate the outer navigation request before starting its destination.",
        "A synchronous cleanup navigation/hide supersedes the outer navigation destination.",
        "Admission, completion/history, visit-wide freshness and cleanup priority must compose on a single event path.",
        "Keep the independent diagnostic consumer live-delta-only and preserve its cleanup and accepted completion."
      ],
      "passed_assertions_evaluation_side_only_count": 56,
      "model_report": "{\"report\":\"已交付：修改 src/progress.js。面板监听器现先注册再启动，缓存首包会触发初始进度；每个成功解码帧仍写入进度历史，但仅比当前已显示帧更新的帧可刷新面板，避免异步乱序解码造成回退。遥测模块未修改，仍忽略缓存引导包。\\n\\n补丁已归档为 /workspace/progress-initial-frame.patch。\\n\\n验证：使用 /runtime/node（--version：v18.17.0）运行了首包、普通流、异步乱序、遥测、重试、隐藏清理、取消及队列记录的断言，均通过；并运行了 /runtime/node --check src/progress.js。\\n\\n未覆盖范围：项目未提供测试脚本或测试套件；未在声明的 Node 16.20.2 环境运行（/runtime/node 为 v18.17.0）。\"}",
      "actual_patch": "diff -ruN /home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-reflection-crosslang-20261108_202000/materials/transfer-progress-composition-v4-vanilla/candidate/progress-initial-frame.patch /home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-reflection-crosslang-20261108_202000/runs/js-base-2/workspace/progress-initial-frame.patch\n--- /home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-reflection-crosslang-20261108_202000/materials/transfer-progress-composition-v4-vanilla/candidate/progress-initial-frame.patch\t1970-01-01 08:00:00.000000000 +0800\n+++ /home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-reflection-crosslang-20261108_202000/runs/js-base-2/workspace/progress-initial-frame.patch\t2026-11-08 12:38:55.916998188 +0800\n@@ -0,0 +1,27 @@\n+--- a/src/progress.js\n++++ b/src/progress.js\n+@@ -1,12 +1,23 @@\n+ export function watchTransferProgress(feed, receive, record) {\n++  let nextFrame = 0;\n++  let displayedFrame = 0;\n+   const listener = event => {\n+-    const deliver = frame => { record(frame); receive(frame); };\n++    const frameNumber = ++nextFrame;\n++    const deliver = frame => {\n++      record(frame);\n++      // Decoding can settle out of order. History retains every decoded frame,\n++      // but the panel only accepts a frame newer than the one it is showing.\n++      if (frameNumber > displayedFrame) {\n++        displayedFrame = frameNumber;\n++        receive(frame);\n++      }\n++    };\n+     const decoded = feed.decode(event.detail);\n+     if (decoded && typeof decoded.then === \"function\") decoded.then(deliver);\n+     else deliver(decoded);\n+   };\n+-  feed.start();\n+   feed.target.addEventListener(\"progress\", listener);\n++  feed.start();\n+   return () => feed.target.removeEventListener(\"progress\", listener);\n+ }\ndiff -ruN /home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-reflection-crosslang-20261108_202000/materials/transfer-progress-composition-v4-vanilla/candidate/src/progress.js /home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-reflection-crosslang-20261108_202000/runs/js-base-2/workspace/src/progress.js\n--- /home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-reflection-crosslang-20261108_202000/materials/transfer-progress-composition-v4-vanilla/candidate/src/progress.js\t2026-10-04 01:06:18.007455648 +0800\n+++ /home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/transfer-reflection-crosslang-20261108_202000/runs/js-base-2/workspace/src/progress.js\t2026-11-08 12:37:03.819415892 +0800\n@@ -1,12 +1,23 @@\n // The source is shared by visits of the same file. Decoding may settle later.\n export function watchTransferProgress(feed, receive, record) {\n+  let nextFrame = 0;\n+  let displayedFrame = 0;\n   const listener = event => {\n-    const deliver = frame => { record(frame); receive(frame); };\n+    const frameNumber = ++nextFrame;\n+    const deliver = frame => {\n+      record(frame);\n+      // Decoding can settle out of order. History retains every decoded frame,\n+      // but the panel only accepts a frame newer than the one it is showing.\n+      if (frameNumber > displayedFrame) {\n+        displayedFrame = frameNumber;\n+        receive(frame);\n+      }\n+    };\n     const decoded = feed.decode(event.detail);\n     if (decoded && typeof decoded.then === \"function\") decoded.then(deliver);\n     else deliver(decoded);\n   };\n-  feed.start();\n   feed.target.addEventListener(\"progress\", listener);\n+  feed.start();\n   return () => feed.target.removeEventListener(\"progress\", listener);\n }\n",
      "unknown_causes": "Observed schedule failure does not alone establish which missing guard or ownership scope caused it; training traces and patch must be inspected."
    }
  ],
  "preservation_requirements": [
    "All accepted history exactly once even after retirement; no newly admitted retired work.",
    "Current visit UI and visit-wide arrival freshness; accepted retry command/queue record and cancellation ordering.",
    "Idempotent cleanup/navigation precedence, four-field queue schema without added authorization.",
    "Diagnostic consumer retains distinct live-delta policy and cleanup."
  ],
  "unknowns": [
    "Failures may share a cause; counts are not independent obligations.",
    "Host asynchronous rejection and physical-completion policy outside visible specification remain unknown."
  ]
}