"""Archive source-bound feedback authored by the executing agent; no model judge."""
import json,csv
from pathlib import Path
OUT=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
def snippet(unit,path,lo,hi):
 lines=(OUT/'materials'/unit/'candidate'/path).read_text().splitlines();return dict(path=path,start=lo,end=hi,text='\n'.join(str(i)+': '+lines[i-1] for i in range(lo,hi+1)))
def main():
 assert (OUT/'K0-complete.json').exists();reviews=list(csv.DictReader((OUT/'baseline-review.csv').open()));gaps=[]
 def gap(id,expect,calls,ids,difference,evidence,unknown):
  matches=[r for r in reviews if r['call_id'] in calls and r['standard_id'] in ids]
  gaps.append(dict(gap_id=id,standard_requires=expect,report_actual=[dict(call_id=r['call_id'],standard_id=r['standard_id'],quote=r['report_quote']) for r in matches],difference=difference,source_evidence=evidence,limits_and_unknown=unknown))
 gap('G1','标出可能重入的调用前后，必要状态/清理句柄何时才发布；区分当前实现和未提供的补丁。',['a02','a04'],['U1-S5','U1-S6'], 'a02把取消描述为先移除监听再onCancel，遗漏stopProgress尚为noop时条件；a04未展开该窗口。两者未说明enqueue返回前visit.handle仍为空。',[snippet('U1','src/transfer.js',3,16),snippet('U1','src/panel.js',4,26)],'只分析原始源码，不要求复述历史补丁发布方式或唯一原因。')
 gap('G2','比较启动回调与释放回调的不同事件边界，提出有源支持的组合顺序，而非仅列举关闭/重开。',['a02','a04'],['U1-A3'], '均关注释放onDetach重入，未展开initialPacket可为函数、调用/派发时owner改变与监听/句柄接到返回值之间的关系。应作为条件性待验证窗口，不声称该原始版本已出现历史A2记录。',[snippet('U1','src/progress-source.js',24,30),snippet('U1','src/progress.js',2,11)],'没有历史补丁或驱动轨迹，不要求断定实际调用栈。')
 gap('G3','分别分析输入进入、已启动工作完成和各类效果提交的条件。',['a02','a04'],['U1-R3','U1-A4'], '报告已正确区分history/display，但没有把新输入接纳与先前接纳的解码完成分成独立边界；不得以当前访问不同就全面取消历史。',[snippet('U1','src/progress.js',2,11),snippet('U1','src/queue.js',8,18)],'具体接纳资格和持久义务从任务/调用方查证，不能发明跨项目统一政策。')
 gap('G4','单次请求结束与整体活动结束需分别说明，展开两次回调之间的等待区间及状态消费者。',['a01'],['U2-A1','U2-A3','U2-A4','U2-R2'], '已提pending到ready、调度及loading/retryScheduled/completed观察，但没有明确pending返回后到下一次检查前的间隙，也未明确loading表达整个活动还是单次请求仍需定义。分析应指出这些待核关系，不凭字段名规定loading必须全程true。',[snippet('U2','src/usePreparation.js',18,27),snippet('U2','src/DownloadDialog.jsx',9,14),snippet('U2','src/BackgroundExportPanel.jsx',19,34)],'原任务未定义完整字段表达；相邻后台只是对照，不能照搬政策。')
 data=dict(reviewer_mode='unblinded executing-agent proxy, not independent human blind evaluation',standard_confirmation='user confirmed all draft S/R/A items within original evidence/unknown limits',baseline_reports_available=3,baseline_failed_call='a03',failure_reason='TLS stream disconnected on third native request; retry was blocked as specified; no final report. This is execution failure, not evidence of semantic omission and not something a skill can fix.',gaps=gaps,preserve=['Original source facts/line citations and original task preservation are mostly accurate.','Preserve separation of history/display and foreground/background; do not convert source facts into universal business policy.','Keep status schema, loading representation, true download consumer, external host guarantees and unobserved historical patch facts as unknown when evidence is absent.','Only propose verification; no tests or patches in this analysis-only task.'])
 (OUT/'difference-feedback.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 reports=[]
 for r in read(OUT/'requests.json'):
  if r['phase']!='K0':continue
  f=Path(r['path'])/'report.md';reports.append(dict(call_id=r['call_id'],unit=r['unit'],replicate=r['replicate'],status=r['status'],report=f.read_text() if f.exists() else None))
 prompt='''你是一次分析技能反思更新的生成器，本次不是GEPA搜索。请读取以下K0、四个基线槽位的报告/失败记录及来源核对的代理差异反馈，提出至多一次通用分析技能更新。无工具权限，不运行代码。

只修改通用查证和分析步骤。不得在skill中包含案例名、文件名/路径、程序标识、标准/反馈ID、隐藏断言、案例专用事件序列或结论、参考补丁或直接修复步骤。不把案例的未知产品政策升级为普遍规则。保持分析报告交付，不要求修改代码或执行验证。若缺乏有据改进，可原样返回K0，不为变化而变化。不要输出完整内部思维链。

返回JSON：skill为完整可复用技能（≤6000 Unicode字符）；changes是简短列表，每项含gap、change、expected_action，说明针对的反馈缺口、改动和预期可观察分析动作。changes可引用研究反馈编号，skill不能带这些标识。

<K0>\n'''+(OUT/'analysis_skill_K0.md').read_text()+'\n</K0>\n<four-baseline-slots>\n'+json.dumps(reports,ensure_ascii=False,indent=2)+'\n</four-baseline-slots>\n<verified-feedback>\n'+json.dumps(data,ensure_ascii=False,indent=2)+'\n</verified-feedback>\n'
 (OUT/'reflection.prompt.md').write_text(prompt)
 print('Source-bound feedback and full reflection prompt saved; chars',len(prompt))
if __name__=='__main__':main()
