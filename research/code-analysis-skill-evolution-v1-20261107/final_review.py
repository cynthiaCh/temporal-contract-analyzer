"""Serialize unblinded executing-agent semantic review of anonymous reports."""
import csv,json,hashlib,importlib.util,re
from datetime import datetime,timezone
from pathlib import Path
OUT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('baseline_notes',OUT/'make_baseline_review.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
# Same approved standard/source-only applicability; no quality total.
base2=dict(b.U2);base2['S6']=('P','卸载时取消保存的重试句柄','说明pending/unmount和相邻非规范，但未说明close仅隐藏这一源码事实。初次反馈审查对此过度给全覆盖，最终统一修正，原反馈保留。','src/BackgroundExportPanel.jsx:14-38')
base1=dict(b.U1A);base1['S5']=('P','若安装期间已经中止，安装返回后再停止监听','已有晚清理事实，不应将整项理解完全判反；关键关系另句无条件“取消先移除”不严谨，缺少noop和返回前句柄边界。初次反馈为X，最终保守评部分。','src/transfer.js:5-13')
N1={
'S1':('P','start 同步派发初始包','仍未展开initialPacket可为函数这一启动重入入口。','src/progress-source.js:26-28'),
'S2':('C','目前先 start 后注册监听','原始顺序准确。','src/progress.js:9-11'),
'S3':('C','Promise 结果在完成时交给两者','同步/异步、record/receive顺序准确。','src/progress.js:3-7'),
'S4':('C','进度历史无当前访问判断，面板显示有当前访问判断','效果事实准确。','src/queue.js:11-15'),
'S5':('C','abort 回调当时调用的仍是初始空清理函数','明确noop、watch返回后赋值及补偿检查，限定先清理描述。','src/transfer.js:5-14'),
'S6':('C','选择操作在 enqueueTransfer 返回前也尚未给 visit.handle 赋值','明确晚发布/失效返回handle处理。','src/panel.js:17-25'),
'S7':('C','重试先取消原句柄，再在同一访问入队','保留同visit/newattempt事实。','src/retry.js:5-14'),
'R1':('P','避免较早完成解码的完整进度帧使当前显示倒退','首句将帧新旧换成较早解码完成，与后文“旧结果新后显示”正确说明不一致。记局部方向错误，不认定整份理解全反。其余目标/保留范围正确。','task.md; src/progress.js:3-7'),
'R2':('P','不能从显示的当前访问限制推断历史也须丢弃','合理效果区分，但未单列失去资格后新输入这一边界。未见历史事件不扣分。','src/progress.js:3-11; src/queue.js:11-15'),
'R3':('P','已收到事件的 Promise 完成后仍调用 record','明确已接纳完成，但新输入是否接纳仍未独立分析。','src/progress.js:3-11'),
'R4':('C','队列记录字段及重试、导航、取消和清理行为属于明确保留范围','保留声明/源码准确。','task.md; README.md:8-25'),
'A1':('C','该次同步初始事件无法由该观察者接收','原因明确。','src/progress.js:9-10'),
'A2':('U','只能说明源码允许的顺序窗口','未伪造历史补丁或实际轨迹；版本边界合理。','source-only applicability'),
'A3':('P','transport 调用期间取消','补上启动调用返回前窗口，但验证仍仅transport取消及onDetach，不是start回调改变owner后旧源新输入。','src/progress-source.js:26-30; src/transfer.js:5-14'),
'A4':('P','历史记录和面板显示的提交条件不同','完成及效果条件清楚，输入资格未展开。','src/progress.js:3-11'),
'A5':('P','需先明确可比较的帧字段','保留事实仍在，但建议验证未单列retry；且把可比较帧字段作为验证前提，源码未要求一定存在这类字段，可控制输入顺序，不应强填schema。','task.md; README.md:10-12; src/retry.js:5-14'),
'A6':('C','这些场景只检验所设交错，不证明所有宿主回调路径','未知/未运行边界保留；新增无依据前提另记issue，不以本项抵消。','src/progress-source.js:26-30')}
N2={**N1,
'S1':('P','start() 同步派发 initialPacket','未说明initialPacket函数求值回调。','src/progress-source.js:26-28'),
'S2':('C','watch 目前先 start()，后注册监听器','顺序准确。','src/progress.js:9-11'),
'S3':('C','完成后依次 record、receive','事实正确。','src/progress.js:3-7'),
'S4':('C','进度历史无当前访问判断','消费者区分正确。','src/queue.js:11-15'),
'S5':('C','stopProgress 初始为空函数，watch 返回后才赋值','noop/返回时序明确。','src/transfer.js:5-14'),
'S6':('C','入队返回后才把句柄赋给访问','发布时序明确。','src/panel.js:17-25'),
'S7':('C','重试先取消旧句柄，再入队、赋新句柄和发布通知','retry事实保留。','src/retry.js:5-14'),
'R1':('C','较早的完整进度帧因异步解码较晚完成','任务方向正确。','task.md'),
'R2':('P','这区分了包被接收、解码完成及各效果提交','分阶段命名有用，但未说明失效后新输入是否接纳/待确认资格。','src/progress.js:3-11'),
'R3':('P','历史仍可写入，显示由 current 判断阻止','完成效果区分明确，输入边界未查清。','src/queue.js:11-15'),
'R4':('C','须保留普通流式进度、诊断遥测、后续使用','保留要求正确。','task.md; README.md:14-25'),
'A1':('C','当前监听器收不到','同步/注册原因正确。','src/progress.js:9-10'),
'A2':('U','不能据此断言它实际发生','正确原始版本/条件窗口边界。','source-only applicability'),
'A3':('P','在这些调用返回前','返回前owner/句柄窗口更清楚，未提出启动回调切换后旧源fresh input组合。','src/transfer.js:5-14; src/progress-source.js:26-30'),
'A4':('P','这区分了包被接收、解码完成及各效果提交','仍无独立新输入资格。','src/progress.js:3-11'),
'A5':('P','构造 onDetach 同步 select/hide、transport 同步取消','保留声明及源事实在，但验证范围未再明确retry，较基线收窄。','src/retry.js:5-14; task.md'),
'A6':('C','不能证明所有宿主回调行为','未知与建议验证界限正确。','src/progress-source.js:26-30')}
W1={
'S1':('C','置 loading、增加计数','请求前状态token事实正确。','src/usePreparation.js:18-22'),
'S2':('C','没有重试、去重、拒绝处理或卸载清理','当前回调事实明确，未填status字段。','src/usePreparation.js:23-27'),
'S3':('C','将快照中的 visible、loading 写入元素属性','找到消费者，没有声称实挂行为已测。','src/DownloadDialog.jsx:9-14'),
'S4':('C','API 将检查、调度和取消直接转交给全局注入函数','接口和时序未知准确。','src/preparation-api.js:3-20'),
'S5':('C','旧请求先完成即可把它清为 false','旧/新请求共享状态关系有源支持，不断言唯一产品政策。','src/usePreparation.js:19-27,36-40'),
'S6':('P','并于卸载时取消已保存的调度句柄','相邻pending/unmount正确，未明确close仅隐藏。与基线同规则。','src/BackgroundExportPanel.jsx:14-38'),
'R1':('C','pending 不能提交文件完成效果，应继续检查','原任务要求正确并保持status形状未知。','task.md'),
'R2':('U','loading、retryScheduled 各应表达哪一段期间，任务及对话框源码尚未规定','明确阶段/字段未知，不强制隐含唯一loading政策。分析源不含标准，合理未知。','src/usePreparation.js:18-27; src/DownloadDialog.jsx:13'),
'R3':('U','不能仅凭 visible 推定已发起工作的完成效果须被丢弃','原始代码有交错，政策未知保留合理。','src/usePreparation.js:23-40'),
'R4':('C','分别观察后续检查和完成效果','前台/后台及close/reopen/完成效果分开。','task.md; src/BackgroundExportPanel.jsx:14-38'),
'A1':('C','区分单次请求结束、等待下一次检查和整体活动结束','明确不同生命周期边界。','src/usePreparation.js:18-27'),
'A2':('C','将快照中的 visible、loading 写入元素属性','状态源/消费者准确。','src/DownloadDialog.jsx:9-14'),
'A3':('C','pending 回调后是否安排下一次检查、等待期快照如何变化','明确回调后/下一次检查前等待间隔。','src/preparation-api.js:10-20'),
'A4':('C','pending 回调后是否安排下一次检查','等待、调度、完成分别建议观察。','src/usePreparation.js:18-27'),
'A5':('C','这只是相邻实现，不能直接视作对话框的业务契约','前后台政策未一刀切。','src/BackgroundExportPanel.jsx:14-38'),
'A6':('U','文件交付的调用方、接口及 completed 是否等同交付均未提供','schema/字段/宿主保证未知保留。','src/preparation-api.js:3-20')}
W2={**W1,
'S1':('C','置 loading=true，增加 checkCount','准确。','src/usePreparation.js:18-22'),
'S2':('C','完成回调无条件置 loading=false','准确truthiness/completed/无retry。','src/usePreparation.js:23-27'),
'S3':('C','把 snapshot 的 visible、loading 写入 DOM 属性','消费者准确，无挂载已验证说法。','src/DownloadDialog.jsx:9-14'),
'S4':('C','全局传输及调度函数的实现、返回值与回调时序保证未提供','未知准确。','src/preparation-api.js:3-20'),
'S5':('C','close 或 reopen 可在请求未完成时改变 visible 或 token','交错事实及旧token效果正确。','src/usePreparation.js:19-40'),
'S6':('P','它有卸载清理，但它是另一个组件','pending/unmount正确，close只隐藏未明确。','src/BackgroundExportPanel.jsx:14-38'),
'R1':('C','pending 不能产生文件交付，且需要后续检查','直接要求准确。','task.md'),
'R2':('U','该字段表示单次请求进行中，还是整个准备活动仍在进行中，需要依据产品契约确定','合理区分字段语义未知，没有把后台当强制规范。','src/DownloadDialog.jsx:9-14'),
'R3':('U','源码没有规定这些交错应如何呈现给用户','事实和政策分开。','src/usePreparation.js:23-40'),
'R4':('C','分别构造 close 后完成、reopen 新 token 后旧请求完成','多效果/生命周期覆盖。','task.md; src/usePreparation.js:23-40'),
'A1':('C','每次请求结束即将 loading 置为 false','结合整体等待/活动定义段，明确请求与活动差别。','src/usePreparation.js:23-27'),
'A2':('C','把 snapshot 的 visible、loading 写入 DOM 属性','消费者准确。','src/DownloadDialog.jsx:9-14'),
'A3':('C','两次检查之间的等待区间','明确间隙观察而非仅最终交付。','src/preparation-api.js:10-20'),
'A4':('C','观察检查次数、等待期间的 loading 与 visible、completed 写入时机','独立观察对象明确。','src/usePreparation.js:18-27'),
'A5':('C','不能仅从相邻组件在 pending 分支保留 loading=true 的写法推定','未强制同后台取消/等待政策。','src/BackgroundExportPanel.jsx:21-38'),
'A6':('U','是否需要支持这些情况取决于外部接口契约','额外scheduler/throw顺序明确条件性，没有强填业务义务。','src/preparation-api.js:3-20')}
# Map by anonymous text only. Labels remain outside review; reviewer already knows methods, so unblinded.
reviews={'Ra3f06b1575':base1,'Rf25a25f051':b.U1B,'R686c13e770':base2,'Rbea8292385':N1,'Rcefea0a0a3':N2,'R9104baed2d':W1,'R7dec5644c1':W2,'R4f09e9464c':None}
def main():
 assert not (OUT/'review.freeze.json').exists();idx=json.loads((OUT/'anonymous-review/index.json').read_text());rows=[]
 for entry in idx:
  aid=entry['anonymous_id'];unit=entry['unit'];text=(OUT/'anonymous-review'/aid/'report.md').read_text();review=reviews[aid] or {k:('F','','TLS失败无最终报告，不是语义遗漏。',v[3]) for k,v in W1.items()}
  for item,(code,quote,reason,source) in review.items():
   assert not quote or quote in text,(aid,item,quote)
   line=text[:text.find(quote)].count('\n')+1 if quote else None
   rows.append(dict(anonymous_id=aid,unit=unit,standard_id=unit+'-'+item,assessment=b.labels[code],report_quote=quote,report_reference=f'anonymous-review/{aid}/report.md:'+str(line) if line else 'raw failure record',source_citation=source,reason=reason,reviewer_mode='unblinded executing-agent proxy; not independent human blind evaluation'))
 with (OUT/'review.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
 issues=[dict(anonymous_id='Ra3f06b1575',type='局部无条件表述',quote='取消先触发移除监听再调用 onCancel',reason='已有安装中断后返回清理的限定，但此句过强；最终S5部分而非整项矛盾，保留原反思反馈以记录实际输入'),dict(anonymous_id='Rbea8292385',type='局部方向表述矛盾',quote='避免较早完成解码的完整进度帧使当前显示倒退',reason='把帧新旧/晚完成误换成较早解码完成，后文又正确；属于表达/关系一致性退步，不能由篇幅抵消'),dict(anonymous_id='Rbea8292385',type='无依据的验证前提',quote='需先明确可比较的帧字段',reason='字段协议未知，不应强制字段存在作为受控验证前提；可通过已知输入先后构造场景，未指定修复算法')]
 (OUT/'review-issues.json').write_text(json.dumps(issues,ensure_ascii=False,indent=2)+'\n')
 # Mechanical reference existence/bounds only; semantic support judged in review.csv.
 audits=[]
 for entry in idx:
  text=(OUT/'anonymous-review'/entry['anonymous_id']/'report.md').read_text();refs=[]
  for name,lo,hi in re.findall(r'((?:src/[\w.-]+|README\.md)):(\d+)(?:[-–](\d+))?',text):
   f=OUT/'materials'/entry['unit']/'candidate'/name;total=len(f.read_text().splitlines()) if f.exists() else 0;refs.append(dict(path=name,start=int(lo),end=int(hi or lo),exists=f.exists(),within_bounds=0<int(lo)<=int(hi or lo)<=total))
  audits.append(dict(anonymous_id=entry['anonymous_id'],parsed_references=len(refs),bad_paths_or_ranges=[r for r in refs if not r['exists'] or not r['within_bounds']],scope='mechanical first-range check; semantic source support in proxy review; not full parser'))
 (OUT/'citation-audit.json').write_text(json.dumps(audits,ensure_ascii=False,indent=2)+'\n')
 files=[OUT/'review.csv',OUT/'review-issues.json',OUT/'citation-audit.json']+[f for f in (OUT/'anonymous-review').rglob('*') if f.is_file()]
 freeze=dict(at=datetime.now(timezone.utc).isoformat(),reviewer_mode='unblinded executing-agent proxy',rows=len(rows),independent_human_blind_review=False,private_label_map_not_read_for_summary=True,files={str(f.relative_to(OUT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},label_map_sha256=hashlib.sha256((OUT/'private-report-labels.json').read_bytes()).hexdigest())
 (OUT/'review.freeze.json').write_text(json.dumps(freeze,ensure_ascii=False,indent=2)+'\n');print('REVIEW_FROZEN',len(rows))
if __name__=='__main__':main()
