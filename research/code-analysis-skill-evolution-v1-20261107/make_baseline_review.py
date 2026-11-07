"""Serialize current executing agent's source-based semantic review; no judge model."""
import csv,json
from pathlib import Path
OUT=Path(__file__).resolve().parent
# Judgments entered by the executing agent after reading actual reports and sources.
# C=correct, P=partial, O=omitted, X=contradiction, U=reasonable unknown, F=failed/no semantic rating.
U1A={
'S1':('P','start() 可同步发出缓存数据','未展开initialPacket可为函数并在派发前运行，影响启动重入分析。','src/progress-source.js:26-28'),
'S2':('C','feed.start() 在 addEventListener 之前','准确原始监听顺序。','src/progress.js:9-11'),
'S3':('C','Promise 结果则在兑现后同样交付','区分同步/Promise，交付先记录再显示。','src/progress.js:3-7'),
'S4':('C','前者由 recordProgress 写入，后者受当前 visit 限制','效果消费者区分准确。','src/queue.js:11-15'),
'S5':('X','取消先触发移除监听再调用 onCancel','该句无条件成立的表述不准确；stopProgress初为noop，watch返回前abort不会立即移除。此前提到安装返回后停止，未在关键关系中限定。','src/transfer.js:5-13'),
'S6':('P','select 建立新 visit、入队并发布 queued','缺少enqueue返回后才赋visit.handle/若失效取消返回handle的关键关系。','src/panel.js:17-25'),
'S7':('C','retry 在当前 visit 内取消旧尝试','同visit、新attempt及取消/排队关系准确。','src/retry.js:5-14'),
'R1':('C','同时保留公开传输、重试、导航、清理、审计、队列记录','原目标及保留范围明确。','task.md; README.md:8-25'),
'R2':('P','已进入 Promise 链的交付是否仍发生','没有单列失效后新输入的接纳资格，不能要求其复述不可见历史A2事实。','src/queue.js:11-15; src/progress-source.js:26-30'),
'R3':('P','进度历史与面板显示是两个输出','已分效果，但未把新输入接纳与已接纳解码完成分成两个边界。','src/progress.js:3-11; src/queue.js:11-15'),
'R4':('C','诊断路径应保持其只记录实时 delta 的语义','保留正常/乱序、retry/queue/telemetry，未假称有限检查证明全部。','task.md; README.md:8-25'),
'A1':('C','初始事件发生时，此处监听器尚未注册','找到同步启动/监听顺序原因。','src/progress.js:9-10'),
'A2':('U','当前调用顺序是 feed.start() 在 addEventListener 之前','原始版本分析准确，未见历史补丁不应要求其描述补丁。','src/progress.js:9-10; source-only applicability'),
'A3':('O','取消时 onDetach 重入','只覆盖teardown重入，未提出启动中owner改变、旧源随后新输入的待查窗口。非要求断定历史实际发生。','src/progress-source.js:26-28; src/transfer.js:5-13; src/panel.js:17-25'),
'A4':('P','已进入 Promise 链的交付是否仍发生','存在迟到完成关注，但缺失新输入接纳这一独立资格。','src/progress.js:3-11'),
'A5':('C','分别观察显示与历史','覆盖正常/逆序与保留项，未全面取消历史。','task.md; src/queue.js:11-15'),
'A6':('C','不能单独确定未定义的帧新旧规则','未知和建议检查边界明确，未声称已运行。','README.md:10-12; src/progress.js:5-7')}
U1B={**U1A,
'S1':('P','`start()` 可同步派发初始包','未展开initialPacket函数的同步调用点。','src/progress-source.js:26-28'),
'S2':('C','先调用 `feed.start()`，再注册事件监听器','原始顺序准确。','src/progress.js:9-11'),
'S3':('C','交付先记录、再调用显示接收方','同步/Promise事实正确。','src/progress.js:3-7'),
'S4':('C','面板显示仅检查当前访问是否相同','record与receive消费者准确。','src/queue.js:11-15'),
'S5':('O','随后订阅文件的进度源','没有说明stopProgress初为noop、赋值在watch返回后。','src/transfer.js:5-13'),
'S6':('P','建立新访问并入队传输','没有句柄发布/晚返回处理顺序。','src/panel.js:17-25'),
'S7':('C','重试沿用当前访问并更换尝试','准确。','src/retry.js:5-14'),
'R1':('C','原任务要求保留传输、重试、导航、清理、审计和队列记录行为','目标保留覆盖。','task.md; README.md:14-25'),
'R2':('P','进度历史与面板显示是两个对外效果','没有新输入接纳边界；不扣未见历史记录。','src/progress.js:3-11'),
'R3':('P','现有交付顺序为先记录后显示','未分别讨论新输入与已接纳完成。','src/queue.js:11-15'),
'R4':('C','诊断路径明确将缓存初始状态与实时增量区分','保留项正确。','README.md:21-25'),
'A1':('C','本次新监听器无法接收该事件','同步/注册关系准确。','src/progress.js:9-10'),
'A2':('U','当前实现中','没有虚构历史补丁，不扣不可见版本信息。','source-only applicability'),
'A3':('O','移除监听器回调中的重入','只提释放重入，未启动时窗。','src/progress-source.js:26-28; src/panel.js:17-25'),
'A4':('P','现有交付顺序为先记录后显示','效果区分存在，新输入/已接纳边界缺失。','src/progress.js:3-11'),
'A5':('C','建议验证同步初始包、后续普通包以及 Promise 乱序兑现','保留验证建议明确。','task.md'),
'A6':('C','不能证明未展示的主机实现行为','未知及验证未执行明确。','src/progress-source.js:26-28')}
U2={
'S1':('C','设置 loading、增加 checkCount','请求前状态和token准确。','src/usePreparation.js:18-22'),
'S2':('C','清除 loading；只要 status 为真就把本次请求 token 加入 completed，没有调度下一次检查','当前完成回调准确，无伪造schema。','src/usePreparation.js:23-27'),
'S3':('C','把 visible、loading 写入 section 属性','找到真实状态消费者，不把snapshot当实挂验证。','src/DownloadDialog.jsx:9-14'),
'S4':('C','重试调度与取消分别代理到注入的全局函数','接口/宿主未知准确。','src/preparation-api.js:3-20'),
'S5':('C','回调没有检查当前可见性或请求 token 是否仍为当前 token','close/reopen/旧回调事实准确。','src/usePreparation.js:23-40'),
'S6':('C','不能据此断定下载对话框应沿用其全部细节','后台相邻实现区分准确。','src/BackgroundExportPanel.jsx:14-38'),
'R1':('C','pending 应触发后续检查，交付必须晚于 ready','直接原任务要求准确。','task.md'),
'R2':('P','loading/retryScheduled 状态和 completed 写入时点','提状态观察，但没显式单列pending返回到retry触发前的等待区间及状态表达政策未知。不是强制模型凭隐藏标准断言loading=true。','src/usePreparation.js:20-27; src/DownloadDialog.jsx:13'),
'R3':('U','没有证据确定关闭、重新打开、卸载及重复启动时应如何处理','报告原始源码缺guard，政策未知合理，不能硬判全取消。','src/usePreparation.js:23-40'),
'R4':('C','这些现有行为与改动的关系需要保留并核实','前后台、交付、close/reopen均建议分别查证。','task.md; src/BackgroundExportPanel.jsx:38'),
'A1':('P','一次对话框检查中','区分原请求回调与调度点，但没有明确请求settle不等于整体准备终止。','src/usePreparation.js:18-27'),
'A2':('C','把 visible、loading 写入 section 属性','找到了状态源和消费者。','src/DownloadDialog.jsx:9-14'),
'A3':('P','pending→ready','建议总体流程及状态，但未展开请求完成后下一次回调触发前这一间隙。','src/preparation-api.js:10-20'),
'A4':('P','请求次数、调度回调顺序、loading/retryScheduled 状态和 completed 写入时点','已分别列观察对象，缺各中间边界对照。','src/usePreparation.js:18-27'),
'A5':('C','相邻实现，不能据此断定下载对话框应沿用其全部细节','前后台政策没有一刀切。','src/BackgroundExportPanel.jsx:14-38'),
'A6':('U','尚不能确认','status schema、下载消费者、取消政策未知准确；未明确loading整体含义未知，但未作无依据要求。','src/preparation-api.js:3-20; src/DownloadDialog.jsx:13')}
labels={'C':'正确覆盖','P':'部分覆盖','O':'遗漏','X':'与证据矛盾','U':'合理保留未知','F':'未评价：执行失败'}
def main():
 assert (OUT/'K0-complete.json').exists();rows=[]
 for call,unit,review in [('a01','U2',U2),('a02','U1',U1A),('a03','U2',U2),('a04','U1',U1B)]:
  report=(OUT/'runs'/call/'report.md').read_text() if (OUT/'runs'/call/'report.md').exists() else ''
  for item,(status,quote,reason,source) in review.items():
   if not report:status='F';quote='';reason='TLS stream interrupted; retry denied as planned. No final report, not semantic omission.'
   else:assert quote in report,(call,item,quote)
   rows.append(dict(call_id=call,unit=unit,standard_id=unit+'-'+item,assessment=labels[status],report_quote=quote,reason=reason,source_citation=source,reviewer_mode='unblinded executing-agent proxy; not independent human blind review'))
 with (OUT/'baseline-review.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
 print('Baseline review rows',len(rows))
if __name__=='__main__':main()
