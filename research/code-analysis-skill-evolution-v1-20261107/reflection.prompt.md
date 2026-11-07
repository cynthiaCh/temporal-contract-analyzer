你是一次分析技能反思更新的生成器，本次不是GEPA搜索。请读取以下K0、四个基线槽位的报告/失败记录及来源核对的代理差异反馈，提出至多一次通用分析技能更新。无工具权限，不运行代码。

只修改通用查证和分析步骤。不得在skill中包含案例名、文件名/路径、程序标识、标准/反馈ID、隐藏断言、案例专用事件序列或结论、参考补丁或直接修复步骤。不把案例的未知产品政策升级为普遍规则。保持分析报告交付，不要求修改代码或执行验证。若缺乏有据改进，可原样返回K0，不为变化而变化。不要输出完整内部思维链。

返回JSON：skill为完整可复用技能（≤6000 Unicode字符）；changes是简短列表，每项含gap、change、expected_action，说明针对的反馈缺口、改动和预期可观察分析动作。changes可引用研究反馈编号，skill不能带这些标识。

<K0>
# 分析技能 K0：任务、源码与证据

此技能只辅助生成代码分析报告，不要求修改代码或执行原维护任务。

1. 先读取作为分析背景的原任务、候选文档与相关源码，分别整理任务目标、明确要求保留的行为和当前实现。不要把函数名或变量名直接当成业务定义。
2. 沿调用关系标记关键入口、回调、等待或调度点、状态写入和对外效果。查到实际生产者与消费者，引用候选工作区的路径和准确行号。
3. 将源码事实、任务或文档要求、原因假设及未知分开。对缺少定义、依赖保证或调用上下文的内容保留未知，不补造接口、业务政策或唯一原因。
4. 说明与任务有关的关键事件之间有哪些已知先后关系，哪些只是可能的顺序；为重要判断给出简短、可检查的证据。
5. 提出需要验证的事件顺序和观察对象，说明验证能回答什么、仍不能回答什么。本轮只提出验证范围，不运行测试、修复或评分。

</K0>
<four-baseline-slots>
[
  {
    "call_id": "a01",
    "unit": "U2",
    "replicate": 1,
    "status": "completed",
    "report": "1. 任务目标和保留行为\n原任务要求：下载对话框遇到文件准备状态为 pending 时继续检查，只有状态为 ready 后才交付文件。本轮仅分析。候选工作区没有额外需求文档；现有对话框暴露启动、关闭、重新打开及状态快照能力（src/DownloadDialog.jsx:6-14；src/usePreparation.js:30-45）。这些现有行为与改动的关系需要保留并核实。\n\n2. 源码事实及引用\nDownloadDialog 调用 usePreparation(token)，把返回对象暴露给 ref，并把 visible、loading 写入 section 属性（src/DownloadDialog.jsx:6-14）。usePreparation 的初始状态含 visible、loading、retryScheduled、checkCount、completed 和 token（src/usePreparation.js:6-14）。start 指向 check；check 读取当前 token，设置 loading、增加 checkCount，然后调用 checkPreparation（src/usePreparation.js:18-23、30-31）。请求兑现后，当前实现清除 loading；只要 status 为真就把本次请求 token 加入 completed，没有调度下一次检查（src/usePreparation.js:23-27）。close 隐藏对话框；reopen 更换 token、显示对话框并立即检查；snapshot 返回状态副本（src/usePreparation.js:32-45）。\ncheckPreparation 将 token 交给注入的 __preparationTransport；重试调度与取消分别代理到注入的全局函数（src/preparation-api.js:3-20）。另一个消费者 BackgroundExportPanel 在结果为假时调用 schedulePreparationRetry(this.start)，结果为真时记录完成；卸载时取消保存的重试句柄（src/BackgroundExportPanel.jsx:14-35）。该组件是相邻实现，不能据此断定下载对话框应沿用其全部细节。\n\n3. 关键事件关系及依据\n一次对话框检查中，读取 token、设置 loading 和计数先于调用传输；收到 Promise 结果后才清除 loading 并可能追加 completed（src/usePreparation.js:18-27）。reopen 先写入新 token，再调用 check（src/usePreparation.js:36-40）。当前代码没有 pending 后的等待或调度点；调度函数虽已存在，但下载对话框的调用链没有使用它（src/usePreparation.js:4、18-28；src/preparation-api.js:10-20）。异步结果与 close、reopen 或卸载之间的先后不确定；回调没有检查当前可见性或请求 token 是否仍为当前 token（src/usePreparation.js:23-27、32-40）。\n\n4. 行为要求及依据\n依据原任务，pending 应触发后续检查，交付必须晚于 ready。当前实现仅按 status 的真值记录 completed，因此需要确认服务返回的状态形式，才能确定 pending 与 ready 如何判别（src/usePreparation.js:23-26）。现有 API 提供重试调度和取消入口，可作为分析重试时序的依据，但原任务未规定间隔、次数或取消政策（src/preparation-api.js:10-20）。\n\n5. 未知项\n候选源码未定义 pending、ready 的具体返回值或错误格式；未展示 __preparationTransport 与调度器的实现（src/preparation-api.js:3-20）。completed 记录 token，但候选文件没有实际文件传输或浏览器下载调用；它是否就是对外交付信号尚不能确认（src/usePreparation.js:25；src/DownloadDialog.jsx:10-14）。也没有证据确定关闭、重新打开、卸载及重复启动时应如何处理已发请求或待执行重试。\n\n6. 建议验证范围\n后续可观察单次 pending→ready 的请求次数、调度回调顺序、loading/retryScheduled 状态和 completed 写入时点，判断是否持续检查且仅在 ready 后交付。再观察 pending 期间 close、reopen 更换 token、卸载及重复 start 时的回调与完成记录，判断是否发生旧请求影响新会话或重复交付。这些验证只能说明候选实现的可见行为；若无服务状态协议和实际下载消费者，仍不能确认状态含义或真实文件是否已交付。本轮未运行验证。"
  },
  {
    "call_id": "a02",
    "unit": "U1",
    "replicate": 1,
    "status": "completed",
    "report": "1. 任务目标和保留行为\n背景任务要求让已有缓存进度的传输在开始时显示初始进度，并防止较旧的完整进度帧在异步解码后使显示倒退。同时保留公开传输、重试、导航、清理、审计、队列记录、普通流式进度、诊断遥测及后续使用的行为。候选文档明确说明同一文件的 feed 会跨尝试和访问共享，start() 可同步发出缓存数据，decode() 可返回值或 Promise（README.md:8-12）；队列记录的既定形状及其他保留范围见 README.md:14-25。\n\n2. 源码事实及引用\n- 入口 createTransferWorkspace 暴露 select、retry、hide、dispose 和 snapshot，并保存各回调及当前访问状态（src/workspace.js:4-18）。select 建立新 visit、入队并发布 queued；retry 在当前 visit 内取消旧尝试、入队新尝试并发布 queued（src/panel.js:10-26；src/retry.js:4-15）。\n- 入队先递增 attemptId 并写入 {fileId, attemptId, visitId, kind}，再创建进度回调和传输。record 回调写进度历史；receive 仅在该 visit 仍为 current 时调用 showProgress（src/queue.js:3-19）。\n- createTransfer 先调用 transport，再安装进度监听；取消触发 stopProgress 和 onCancel。若安装期间已经中止，安装返回后再停止监听（src/transfer.js:3-16）。\n- watchTransferProgress 的监听器解码事件；同步结果立即依次交给 record、receive，Promise 结果则在兑现后同样交付。当前调用顺序是 feed.start() 在 addEventListener 之前（src/progress.js:2-11）。候选 feed 的 start() 可同步 dispatch 初始包，emit() 派发后续包（src/progress-source.js:23-31）。因此该初始事件发生时，此处监听器尚未注册。\n- 诊断消费者 collectProgressTelemetry 也调用 start() 后注册监听，但只把收到的解码帧交给 recordDelta；文档称缓存启动数据不属于诊断 delta（src/telemetry.js:1-11；README.md:21-23）。移除进度监听时，feed 先完成移除再同步调用可重入的 onDetach（src/progress-source.js:8-22）。\n\n3. 关键事件关系及依据\n- 一次入队中，队列记录先于 createTransfer；createTransfer 内 transport 先于进度监听安装（src/queue.js:8-18；src/transfer.js:10-13）。\n- 现有 watchTransferProgress 中，start 的同步初始派发先于注册监听。因此在候选 feed 的同步派发情形，初始包不会进入该监听器的 decode、record 或 receive；后续 emit 只有在监听已注册时才可进入该路径（src/progress.js:3-11；src/progress-source.js:26-30）。\n- 对已收到的包，decode 调用先于交付；Promise 的兑现时间可能改变不同帧的交付次序。当前 deliver 未比较帧的新旧，直接依次写历史和请求显示（src/progress.js:4-7）。不同 Promise 的具体兑现顺序没有源码保证。\n- 取消先触发移除监听再调用 onCancel；移除可能同步引发 onDetach，进而重入 select 或 hide。相应入口会改变 current，receive 通过 current === visit 限制显示（src/transfer.js:6-9；src/progress-source.js:19-22；src/panel.js:10-18,29-34；src/queue.js:13-15）。已进入 Promise 链的交付是否仍发生，不能仅由移除监听推断。\n\n4. 行为要求及依据\n- 初始显示应覆盖 warm feed 的同步缓存包；依据是背景任务目标，以及 start 可同步派发的候选契约（README.md:8-12；src/progress-source.js:26-29）。\n- 完整帧异步解码可能乱序，当前显示不得被较旧帧回滚；这是背景任务要求。候选接收路径目前没有新旧判断（src/progress.js:4-7；src/queue.js:13-15）。\n- 进度历史与面板显示是两个输出：前者由 recordProgress 写入，后者受当前 visit 限制（README.md:14-16；src/queue.js:11-15）。诊断路径应保持其只记录实时 delta 的语义（src/telemetry.js:1-11）。队列记录形状、重试、导航和取消等保留要求见 README.md:8-25 及背景任务。\n\n5. 未知项\n候选文件未定义完整帧用于判定新旧的字段、单调性或跨尝试比较规则；不能凭变量名推定帧序号。未见具体 host 的 transport、回调或 decode 实现，故无法确定实际异步兑现顺序、重入频率和外部显示效果。候选文档未规定历史记录对乱序完整帧的取舍细则，也未给出除本候选 feed 以外其他 feed 实现的行为保证。\n\n6. 建议验证范围\n本轮未运行测试。建议后续验证：同步初始包在首次选择时能否进入进度历史及当前面板；后续 emit 是否保持正常交付；两个完整帧按接收顺序进入却按相反顺序解码完成时，分别观察显示与历史；同步值和 Promise 混用时观察同样结果。另观察 retry、重新选择同一文件、hide、dispose、取消时 onDetach 重入，以及诊断消费者的缓存包与实时 delta、队列记录和 queued 通知。这些场景可核对可观察的事件顺序及保留行为，但不能单独确定未定义的帧新旧规则或所有外部 feed 的契约。"
  },
  {
    "call_id": "a03",
    "unit": "U2",
    "replicate": 2,
    "status": "failed",
    "report": null
  },
  {
    "call_id": "a04",
    "unit": "U1",
    "replicate": 2,
    "status": "completed",
    "report": "1. 任务目标和保留行为\n原任务要求恢复已有缓存进度源的首次显示，并防止较旧的完整进度帧在异步解码后使显示倒退；本轮仅分析。原任务要求保留传输、重试、导航、清理、审计和队列记录行为。候选文档另说明诊断消费者应维持现有行为，队列记录仍为 `{fileId, attemptId, visitId, kind}`（README.md:14-25）。\n\n2. 源码事实及引用\n工作区通过 `select`、`retry`、`hide`、`dispose` 暴露操作（src/workspace.js:7-16）。选择文件会结束前一次访问、建立新访问并入队传输（src/panel.js:10-25）。入队先写队列记录，再创建传输；进度记录写入 `recordProgress`，面板显示仅检查当前访问是否相同（src/queue.js:8-18）。创建传输先调用 `transport`，随后订阅文件的进度源（src/transfer.js:3-16）。订阅函数先调用 `feed.start()`，再注册事件监听器（src/progress.js:2-11）；候选进度源的 `start()` 可同步派发初始包（src/progress-source.js:23-30）。监听器解码事件，若返回 Promise 则在其兑现时交付；交付先记录、再调用显示接收方（src/progress.js:3-7）。诊断消费者也先启动源再注册监听器，其交付只调用 `recordDelta`（src/telemetry.js:1-11）。\n\n3. 关键事件关系及依据\n当前实现中，传输调用先于进度订阅（src/transfer.js:10-12）；订阅时 `start()` 先于监听器注册（src/progress.js:9-10）。因此，若初始包由候选进度源在 `start()` 内同步派发，本次新监听器无法接收该事件（src/progress-source.js:26-29）。后续 `emit()` 派发的事件可由已注册监听器接收（src/progress-source.js:30；src/progress.js:10）。Promise 解码的交付发生在兑现时，源码没有按事件到达顺序约束不同 Promise 的兑现顺序（src/progress.js:5-7）；较旧帧晚交付时，当前接收方会直接调用显示回调（src/queue.js:13-15）。重试沿用当前访问并更换尝试，先取消旧句柄，再入队新传输（src/retry.js:5-13）。移除监听器先完成移除再调用可重入的主机回调；该回调可能触发重新选择或隐藏（src/progress-source.js:8-22）。\n\n4. 行为要求及依据\n恢复初始进度应针对面板传输路径，同时保留后续流式事件；诊断路径明确将缓存初始状态与实时增量区分（README.md:21-23；src/telemetry.js:1-11）。防倒退要求关注异步解码后的完整帧交付顺序，而不只是事件接收顺序（原任务背景；src/progress.js:3-7）。进度历史与面板显示是两个对外效果，现有交付顺序为先记录后显示（README.md:14-16；src/progress.js:4；src/queue.js:11-15）。队列记录字段及访问、重试、取消等行为有明确保留要求（README.md:8-19）。\n\n5. 未知项\n候选源码未定义完整进度帧的字段、版本或新旧比较规则，也未说明 `decode` 的拒绝处理规则（src/progress.js:3-7）。没有证据表明 `feed.start()` 每次都产生初始包，或共享源的多次启动如何相互影响（README.md:10-12；src/progress-source.js:26-29）。`recordProgress` 是否应保留每个乱序帧、面板是否应按尝试隔离旧异步结果，均不能仅由现有实现推断为业务政策（src/queue.js:11-15）。\n\n6. 建议验证范围\n建议验证同步初始包、后续普通包以及 Promise 乱序兑现时的 `recordProgress` 和 `showProgress` 调用顺序与内容；这可判断初始显示及倒退现象，不能单独确定帧的新旧比较规则。还应观察重试、再次选择同一文件、隐藏、取消和移除监听器回调中的重入，以及诊断增量和队列记录；这可检查要求保留的对外效果，但不能证明未展示的主机实现行为。本轮未运行验证。"
  }
]
</four-baseline-slots>
<verified-feedback>
{
  "reviewer_mode": "unblinded executing-agent proxy, not independent human blind evaluation",
  "standard_confirmation": "user confirmed all draft S/R/A items within original evidence/unknown limits",
  "baseline_reports_available": 3,
  "baseline_failed_call": "a03",
  "failure_reason": "TLS stream disconnected on third native request; retry was blocked as specified; no final report. This is execution failure, not evidence of semantic omission and not something a skill can fix.",
  "gaps": [
    {
      "gap_id": "G1",
      "standard_requires": "标出可能重入的调用前后，必要状态/清理句柄何时才发布；区分当前实现和未提供的补丁。",
      "report_actual": [
        {
          "call_id": "a02",
          "standard_id": "U1-S5",
          "quote": "取消先触发移除监听再调用 onCancel"
        },
        {
          "call_id": "a02",
          "standard_id": "U1-S6",
          "quote": "select 建立新 visit、入队并发布 queued"
        },
        {
          "call_id": "a04",
          "standard_id": "U1-S5",
          "quote": "随后订阅文件的进度源"
        },
        {
          "call_id": "a04",
          "standard_id": "U1-S6",
          "quote": "建立新访问并入队传输"
        }
      ],
      "difference": "a02把取消描述为先移除监听再onCancel，遗漏stopProgress尚为noop时条件；a04未展开该窗口。两者未说明enqueue返回前visit.handle仍为空。",
      "source_evidence": [
        {
          "path": "src/transfer.js",
          "start": 3,
          "end": 16,
          "text": "3: export function createTransfer(file, attemptId, transport, onCancel, progress = {}) {\n4:   const controller = new AbortController();\n5:   let stopProgress = () => {};\n6:   controller.signal.addEventListener(\"abort\", () => {\n7:     stopProgress();\n8:     onCancel({ file, attemptId, signal: controller.signal });\n9:   }, { once: true });\n10:   transport({ file, attemptId, signal: controller.signal });\n11:   if (file.progressFeed) {\n12:     stopProgress = watchTransferProgress(file.progressFeed, progress.receive, progress.record);\n13:     if (controller.signal.aborted) stopProgress();\n14:   }\n15:   return { file, attemptId, signal: controller.signal,\n16:     cancel() { if (!controller.signal.aborted) controller.abort(); } };"
        },
        {
          "path": "src/panel.js",
          "start": 4,
          "end": 26,
          "text": "4: export function releaseVisit(visit) {\n5:   const handle = visit.handle;\n6:   visit.handle = null;\n7:   if (handle) handle.cancel();\n8: }\n9: \n10: export function selectFile(state, file) {\n11:   if (state.disposed) return null;\n12:   const requestId = ++state.nextVisit;\n13:   const previous = state.current;\n14:   state.current = null;\n15:   if (previous) releaseVisit(previous);\n16:   if (state.disposed || state.nextVisit !== requestId) return null;\n17:   const visit = { id: requestId, file, handle: null };\n18:   state.current = visit;\n19:   const handle = enqueueTransfer(state, visit, \"select\");\n20:   if (state.current === visit) {\n21:     visit.handle = handle;\n22:     publishQueued(state, visit, handle);\n23:   } else {\n24:     handle.cancel();\n25:   }\n26:   return handle;"
        }
      ],
      "limits_and_unknown": "只分析原始源码，不要求复述历史补丁发布方式或唯一原因。"
    },
    {
      "gap_id": "G2",
      "standard_requires": "比较启动回调与释放回调的不同事件边界，提出有源支持的组合顺序，而非仅列举关闭/重开。",
      "report_actual": [
        {
          "call_id": "a02",
          "standard_id": "U1-A3",
          "quote": "取消时 onDetach 重入"
        },
        {
          "call_id": "a04",
          "standard_id": "U1-A3",
          "quote": "移除监听器回调中的重入"
        }
      ],
      "difference": "均关注释放onDetach重入，未展开initialPacket可为函数、调用/派发时owner改变与监听/句柄接到返回值之间的关系。应作为条件性待验证窗口，不声称该原始版本已出现历史A2记录。",
      "source_evidence": [
        {
          "path": "src/progress-source.js",
          "start": 24,
          "end": 30,
          "text": "24:     target,\n25:     decode,\n26:     start() {\n27:       const packet = typeof initialPacket === \"function\" ? initialPacket() : initialPacket;\n28:       if (packet !== undefined) target.dispatchEvent(new ProgressEvent(packet));\n29:     },\n30:     emit(packet) { target.dispatchEvent(new ProgressEvent(packet)); },"
        },
        {
          "path": "src/progress.js",
          "start": 2,
          "end": 11,
          "text": "2: export function watchTransferProgress(feed, receive, record) {\n3:   const listener = event => {\n4:     const deliver = frame => { record(frame); receive(frame); };\n5:     const decoded = feed.decode(event.detail);\n6:     if (decoded && typeof decoded.then === \"function\") decoded.then(deliver);\n7:     else deliver(decoded);\n8:   };\n9:   feed.start();\n10:   feed.target.addEventListener(\"progress\", listener);\n11:   return () => feed.target.removeEventListener(\"progress\", listener);"
        }
      ],
      "limits_and_unknown": "没有历史补丁或驱动轨迹，不要求断定实际调用栈。"
    },
    {
      "gap_id": "G3",
      "standard_requires": "分别分析输入进入、已启动工作完成和各类效果提交的条件。",
      "report_actual": [
        {
          "call_id": "a02",
          "standard_id": "U1-R3",
          "quote": "进度历史与面板显示是两个输出"
        },
        {
          "call_id": "a02",
          "standard_id": "U1-A4",
          "quote": "已进入 Promise 链的交付是否仍发生"
        },
        {
          "call_id": "a04",
          "standard_id": "U1-R3",
          "quote": "现有交付顺序为先记录后显示"
        },
        {
          "call_id": "a04",
          "standard_id": "U1-A4",
          "quote": "现有交付顺序为先记录后显示"
        }
      ],
      "difference": "报告已正确区分history/display，但没有把新输入接纳与先前接纳的解码完成分成独立边界；不得以当前访问不同就全面取消历史。",
      "source_evidence": [
        {
          "path": "src/progress.js",
          "start": 2,
          "end": 11,
          "text": "2: export function watchTransferProgress(feed, receive, record) {\n3:   const listener = event => {\n4:     const deliver = frame => { record(frame); receive(frame); };\n5:     const decoded = feed.decode(event.detail);\n6:     if (decoded && typeof decoded.then === \"function\") decoded.then(deliver);\n7:     else deliver(decoded);\n8:   };\n9:   feed.start();\n10:   feed.target.addEventListener(\"progress\", listener);\n11:   return () => feed.target.removeEventListener(\"progress\", listener);"
        },
        {
          "path": "src/queue.js",
          "start": 8,
          "end": 18,
          "text": "8: export function enqueueTransfer(state, visit, kind) {\n9:   const attemptId = ++state.nextAttempt;\n10:   state.record(makeQueueRecord(visit.file, attemptId, visit.id, kind));\n11:   const progress = {\n12:     record(frame) { state.recordProgress({ fileId: visit.file.id, attemptId, frame }); },\n13:     receive(frame) {\n14:       if (state.current === visit) state.showProgress({ fileId: visit.file.id, attemptId, frame });\n15:     },\n16:   };\n17:   const handle = createTransfer(visit.file, attemptId, state.transport, state.onCancel, progress);\n18:   state.tasks.set(attemptId, handle);"
        }
      ],
      "limits_and_unknown": "具体接纳资格和持久义务从任务/调用方查证，不能发明跨项目统一政策。"
    },
    {
      "gap_id": "G4",
      "standard_requires": "单次请求结束与整体活动结束需分别说明，展开两次回调之间的等待区间及状态消费者。",
      "report_actual": [
        {
          "call_id": "a01",
          "standard_id": "U2-R2",
          "quote": "loading/retryScheduled 状态和 completed 写入时点"
        },
        {
          "call_id": "a01",
          "standard_id": "U2-A1",
          "quote": "一次对话框检查中"
        },
        {
          "call_id": "a01",
          "standard_id": "U2-A3",
          "quote": "pending→ready"
        },
        {
          "call_id": "a01",
          "standard_id": "U2-A4",
          "quote": "请求次数、调度回调顺序、loading/retryScheduled 状态和 completed 写入时点"
        }
      ],
      "difference": "已提pending到ready、调度及loading/retryScheduled/completed观察，但没有明确pending返回后到下一次检查前的间隙，也未明确loading表达整个活动还是单次请求仍需定义。分析应指出这些待核关系，不凭字段名规定loading必须全程true。",
      "source_evidence": [
        {
          "path": "src/usePreparation.js",
          "start": 18,
          "end": 27,
          "text": "18:   const check = () => {\n19:     const requestToken = state.current.token;\n20:     state.current.loading = true;\n21:     state.current.checkCount += 1;\n22:     publish();\n23:     checkPreparation(requestToken).then((status) => {\n24:       state.current.loading = false;\n25:       if (status) state.current.completed.push(requestToken);\n26:       publish();\n27:     });"
        },
        {
          "path": "src/DownloadDialog.jsx",
          "start": 9,
          "end": 14,
          "text": "9:   const snapshot = preparation.snapshot();\n10:   return React.createElement(\"section\", {\n11:     \"data-surface\": \"download-dialog\",\n12:     \"data-visible\": String(snapshot.visible),\n13:     \"data-loading\": String(snapshot.loading),\n14:   });"
        },
        {
          "path": "src/BackgroundExportPanel.jsx",
          "start": 19,
          "end": 34,
          "text": "19:   start = () => {\n20:     const token = this.state.token;\n21:     this.setState((state) => ({ loading: true, checkCount: state.checkCount + 1 }));\n22:     api.checkPreparation(token).then((done) => {\n23:       if (!this.active) return;\n24:       if (done) {\n25:         this.retry = null;\n26:         this.setState((state) => ({\n27:           loading: false,\n28:           retryScheduled: false,\n29:           completed: state.completed.includes(token) ? state.completed : [...state.completed, token],\n30:         }));\n31:       } else {\n32:         this.retry = api.schedulePreparationRetry(this.start);\n33:         this.setState({ retryScheduled: true });\n34:       }"
        }
      ],
      "limits_and_unknown": "原任务未定义完整字段表达；相邻后台只是对照，不能照搬政策。"
    }
  ],
  "preserve": [
    "Original source facts/line citations and original task preservation are mostly accurate.",
    "Preserve separation of history/display and foreground/background; do not convert source facts into universal business policy.",
    "Keep status schema, loading representation, true download consumer, external host guarantees and unobserved historical patch facts as unknown when evidence is absent.",
    "Only propose verification; no tests or patches in this analysis-only task."
  ]
}
</verified-feedback>
