"""Encode executing Agent's evidence-based review; no automatic semantic judge."""
import csv,json,re
from pathlib import Path
from run import OUT,ROOT,read,save,sha
ST=ROOT/'research/code-analysis-standard-cases-v1-20261107'

def main():
 assert read(OUT/'execution-complete.json')['status']=='ALL_SIX_SLOTS_FINISHED'
 rows=[]
 evidence={
 'C1':{
  1:('S1;S2;S3',[('src/channel.js',8,20),('src/subscription.js',3,11)]),
  2:('S1;S2;S4',[('src/channel.js',14,19),('src/subscription.js',9,11),('src/presence-panel.js',18,25)]),
  3:('S5;R1',[('src/metrics-consumer.js',3,5),('src/channel.js',24,31)]),
  4:('S2;S3',[('src/presence-panel.js',4,13),('src/subscription.js',4,11)]),
  5:('S1;S2;S3;S6;U1;U2',[('src/subscription.js',3,11),('src/presence-panel.js',7,13),('src/workspace-navigation.js',3,10)]),
  6:('R3;S4;S5',[('src/presence-panel.js',18,25),('src/metrics-consumer.js',3,5),('src/subscription.js',4,11)])},
 'C2':{
  1:('S1;S2',[('src/editor.js',17,20),('src/draft-store.js',10,16)]),
  2:('S5;S6',[('src/trailing-task.js',8,25),('src/search-preview.js',3,8)]),
  3:('S1;R1;R2',[('src/editor.js',17,20),('README.md',3,7)]),
  4:('S3;S4;S6;R3',[('src/editor.js',22,23),('src/workspace.js',11,16),('README.md',15,24)]),
  5:('S2;R3;U1;U2',[('src/draft-store.js',10,16),('src/workspace.js',3,6),('README.md',9,13)]),
  6:('R1;R2;R3;S6',[('src/editor.js',17,20),('README.md',5,7),('README.md',15,24),('src/search-preview.js',3,8)])},
 'C3':{
  1:('S1;S2',[('src/controller.js',5,10)]),
  2:('S3;S4;S5',[('src/controller.js',11,13),('src/observations.js',1,1)]),
  3:('S2;S4;R1',[('src/controller.js',7,13),('README.md',3,3)]),
  4:('S3;S4;S5;R2;R3',[('src/controller.js',11,12),('src/observations.js',1,1),('README.md',3,3)]),
  5:('U1;U2;U3',[('src/controller.js',8,13)]),
  6:('S6;R1;R2;R3',[('src/controller.js',8,15),('src/search-preview.js',3,8),('README.md',5,5)])}}
 specs={
 'a01':[(1,'满足',[5,6,7],'源码事实与引用','定位监听入口、decode/receive和原始先connect后注册，引用与源码相符。'),(2,'满足',[12],'事件关系','正确区分同步漏收与deferred顺序，迟到解码与移除监听分开；不把迟到政策写成已定业务要求。重入赋值窗口的额外说法另在A5限定。'),(3,'满足',[9,15],'消费者区分','明确面板与metrics首事件政策不同，依据原任务和metrics注释；政策尚待用户确认，不计业务得失。'),(4,'满足',[5,6,12],'阶段与效果','描述先release再订阅返回赋值；移除监听与已开始decode的完成分别说明。'),(5,'部分满足',[12,18],'可达性依据不足','已将重入称线索并保留真实transport/跨房间政策未知，但“show的订阅赋值完成前”没有具体原始调用链或前提。给定单面板同步connect在注册前发事件，不会自行证明该窗口；仍需外部channel/其他监听者或调用方证据。不能据此认定窗口必达，也不能证明绝不可能；不是已证实源码事实错误。'),(6,'满足',[21],'验证建议','同步/deferred、后续update、导航、复用channel、迟到decode与metrics均有具体观察范围；未声称执行。')],
 'a06':[(1,'满足',[5,6,7],'源码事实与引用','定位入口、同步/Promise decode和先connect后监听；引用虽为块入口行，但对应事实在同一函数块内。'),(2,'满足',[12,13],'事件关系','在正常同步调用链前提下区分同步和微任务顺序；无历史补丁混入。额外重入可能性另看A5。'),(3,'满足',[9,17],'消费者区分','面板初始状态与metrics仅增量分开；待确认规范不当作业务得失。'),(4,'满足',[5,6,14],'阶段与效果','先release、订阅后保存返回值及异步decode不被移除取消均有说明。'),(5,'部分满足',[14,20],'可达性依据不足','“这些是源码允许的顺序”比已给出的原始调用证据更宽；虽说非已观察故障、真实transport未知，却没限定show赋值前receive来自何路径。只记可达性论证不完整，不判已发生故障或反向业务理解错误。'),(6,'满足',[23],'验证建议','首事件/update、select/hide、复用、迟到decode和metrics范围均有覆盖。')],
 'a02':[(1,'满足',[5],'源码事实与引用','明确原始edit立即写、store先写后同步通知，非原始延迟故障。'),(2,'满足',[5,8,11],'工具关系','push/flush/cancel和旧批次先清理再work、后续可排队均解释；预览取消与草稿效果分开。'),(3,'满足',[2,8,11],'原始与目标分开','先说明原始立即写，再在“使用trailing task时”和“延迟保存后”讨论边界，不把目标待实现情境当原始观察。README的结算政策覆盖仅作描述。'),(4,'满足',[11],'效果与归属','分别说明store、save badge、收据和visit通知，且没有将代码缺少校验直接当现存可达故障。'),(5,'满足',[8,14],'依据与未知','引用inline回调和请求开始优先文档；注入timers语义、具体实现保留未知。'),(6,'满足',[17],'验证建议','批次/第二批、离开/提交/dispose、同步重入和预览都有对应观察。')],
 'a04':[(1,'满足',[5,8],'源码事实与引用','明确逐次同步写入，列出写入和通知顺序及现有submit路径。'),(2,'满足',[5,17],'工具关系','区分合并、flush清待办后工作、cancel丢弃；正文与建议合起来覆盖后续批次和预览。'),(3,'满足',[8,14],'原始与目标分开','以“若改用延迟任务”限定交错分析，未把原始代码当作已接入helper。'),(4,'满足',[11],'效果与归属','区分持久store、按id状态订阅、入口收据和visit通知；描述selection已含visit而submit未检查，未断言必有现存故障。'),(5,'满足',[5,14],'依据与未知','源码inline回调和文档重入有依据；对取消回调交付保证保留未知合理。没有写请求开始优先的文档政策只在待确认R3描述，不判确定错误。'),(6,'满足',[17],'验证建议','批次、离开旧badge、入口提交、重入、无选择及预览都有目标观察。')],
 'a03':[(1,'满足',[5],'源码事实与引用','定位visit/latest/入口字段对象，未声称深拷贝或不可变嵌套值。标准U2的类型未知未逐项列出，但不能把未声称的深度保证反扣为错误。'),(2,'满足',[5,8],'事件关系','明确当前立即把Promise送done、尚未等待；同步catch不能处理后续拒绝。'),(3,'满足',[8,14],'原始与目标分开','结合第5行阅读，当前代码形态与目标异步完成问题已分开。第8行“允许旧提交完成”仅支持身份守卫不取消工作，不证明当前done已登记为完成回调。'),(4,'满足',[11],'效果与归属','无条件审计与current/latest UI守卫分开，失败无审计作为可见README政策识别。'),(5,'满足',[14],'依据与未知','无选择null、新Promise要求、失败传播、依赖异常均保留未知；没有发明全局排序或取消要求。'),(6,'部分满足',[11,17],'验证建议局部遗漏','第11行已经读到预览，建议段针对提交成功/拒绝/导航等关系很具体，但未明确建议验证预览40ms/hide/复用的保留行为。不是没读源码、实际验证退步或确定违反业务要求。')],
 'a05':[(1,'满足',[5],'源码事实与引用','准确定位入口snapshot、visit/owner和无选择返回；未宣称嵌套值深度不可变，不强求复述标准所有未知项。'),(2,'满足',[5,8],'事件关系','明确立即处理Promise返回值与异步拒绝边界，当前源码事实正确。'),(3,'满足',[8],'原始与目标分开','明确标“异步适配所需的顺序”，未将其说成现有完成回调。乱序/关闭情境作为可能性，不假定实际发生。'),(4,'满足',[11],'效果与归属','历史独立于current/latest，UI受其限制；原始守卫与README目标分别引用。'),(5,'满足',[14],'依据与未知','失败Promise传播、依赖是否异步或抛错、外部约定未定义时不补造政策。无选择Promise协调未单列，但第5行已有null事实，没有新增相反要求。'),(6,'部分满足',[11,17],'验证建议局部遗漏','已在第11行描述独立40ms预览，但第17行验证范围没有对应预览保留建议。只记建议范围局部缺项，不推断维护效果或未读源码。')]}
 records={r['call_id']:r for r in read(OUT/'requests.json')}
 reports=read(ST/'source-manifest.json')['cases'];stdfiles={c['id']:ST/c['report'] for c in reports}
 def add(call,item,judgment,lines,category,reason,kind='analysis_item',coverage='',source_override=None):
  r=records[call];cid=r['case'];f=OUT/'runs'/call/'report.md';rlines=f.read_text().splitlines()
  fullid=cid+'-'+item
  refs,src=evidence[cid][int(item[1:])] if item.startswith('A') else source_override
  stdids=[fullid]+[cid+'-'+x for x in refs.split(';') if x]
  stdtext=stdfiles[cid].read_text().splitlines();stdloc=[]
  for sid in dict.fromkeys(stdids):
   matches=[i for i,l in enumerate(stdtext,1) if re.match(r'^\| '+re.escape(sid)+r' \|',l) or l.startswith('- '+sid+'：')]
   assert len(matches)==1,(sid,matches)
   stdloc.append(str(stdfiles[cid].relative_to(ROOT))+':'+str(matches[0]))
  source_refs=[]
  for name,start,end in src:
   q=OUT/'materials'/cid/'candidate'/name;assert 1<=start<=end<=len(q.read_text().splitlines())
   source_refs.append(str(q.relative_to(OUT))+':'+str(start)+(('-'+str(end)) if end!=start else ''))
  rows.append(dict(call_id=call,case=cid,repeat=r['repeat'],row_kind=kind,item_id=fullid,judgment=judgment,category=category,report_refs=';'.join(str(f.relative_to(OUT))+':'+str(i) for i in lines),report_quotes=json.dumps([{'line':i,'text':rlines[i-1]} for i in lines],ensure_ascii=False),standard_ids=';'.join(dict.fromkeys(stdids)),standard_refs=';'.join(stdloc),source_refs=';'.join(source_refs),tool_refs=';'.join('runs/'+call+'/events.jsonl:'+str(t['line']) for t in r['tool_index']),review_reason=reason,business_policy_approval='pending',policy_coverage_observation=coverage,counts_as_definite_business_error=False,definite_source_fact_error=False,evaluator='AI代理评价（未盲化，非独立人工复核）'))
 for call in records:
  for idx,j,ls,cat,reason in specs[call]:add(call,'A'+str(idx),j,ls,cat,reason)
 # These rows do not turn pending normative policies into scored errors.
 policy_lines={'a01':[[2,15],[5,12,18],[21]],'a06':[[2,17],[5,14,20],[23]],'a02':[[2,5],[2,11],[8,11,17]],'a04':[[2,5],[2,17],[11,17]],'a03':[[2,14],[2,11],[2,11]],'a05':[[2,14],[2,11],[2,11]]}
 for call,r in records.items():
  cid=r['case']
  for n,ls in enumerate(policy_lines[call],1):
   src=evidence[cid][3 if n==1 else 4 if n==2 else 6][1]
   coverage='已识别可见任务／文档约定；仅描述覆盖，尚非人工批准政策'
   reason='标准R条目仍待确认。报告引用任务／候选文档的要求是可追溯表述，不能因尚未批准而称其无依据，也不把未覆盖政策计作确定错误。'
   if cid=='C2' and call=='a04' and n==3:
    coverage='部分覆盖：入口收据/visit通知与重入已说明；README:10-12后发导航请求优先未明确写出'
    reason+=' 这是单例单次的文档覆盖差异；不计确定业务遗漏，不与另一案例拼成重复缺口。'
   add(call,'R'+str(n),'证据不足',ls,'标准政策待确认',reason,'pending_policy',coverage,('',src))
 with (OUT/'review.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 save(OUT/'review.freeze.json',dict(status='AI_PROXY_REVIEW_FROZEN_BEFORE_SUMMARY',review_sha256=sha(OUT/'review.csv'),analysis_rows=36,pending_policy_rows=18,independent_human_review=False,blinded=False,LLM_judge_calls=0,algorithmic_semantic_grading=False,policy='Judgments were assigned by executing Agent reading original reports and frozen source; script only encodes decisions and verifies references. No summed quality score.'))
 print('Stored 36 analysis items + 18 unconfirmed-policy rows; no quality total')
if __name__=='__main__':main()
