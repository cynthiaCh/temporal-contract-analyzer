"""Reproduce final descriptive report, including the preserved protocol deviation."""
import json
from datetime import datetime
from pathlib import Path
from collections import Counter
import analyze,evidence_review
from run import *

def main():
 analyze.main();evidence_review.main()
 summary=read(OUT/'summary.json');rows=read(OUT/'results.json');vectors=read(OUT/'raw-vectors.json');runs=read(OUT/'runs.json');dev=read(OUT/'protocol-deviation.json')
 assert len(rows)==len(read(OUT/'invocations.json'))==24
 def aggregate(exclude):
  out={}
  for arm in ARMS:
   rs=[r for r in rows if r['arm']==arm and r['case'] not in exclude];vs=[v for v in vectors if v['arm']==arm and v['case'] not in exclude]
   out[arm]=dict(whole_pass=sum(v['whole_pass'] for v in vs),scored=len(vs),required_passed=sum(v['required_passed'] for v in vs),required_total=sum(v['required_total'] for v in vs),input_tokens=sum((r.get('usage') or {}).get('input_tokens',0) for r in rs),output_tokens=sum((r.get('usage') or {}).get('output_tokens',0) for r in rs),model_seconds=round(sum(analyze.seconds(r) or 0 for r in rs),3),delivered_questions=sum(len(r['question_ids']) for r in rs),original_losses=sum(bool(v['lost_original_passed']) for v in vs))
  return out
 subset=aggregate({dev['affected_case']});summary['strict_query_subset']=dict(excluded_case=dev['affected_case'],case_count=3,independent_case_count=0,arms=subset,interpretation='Post-hoc input-hygiene exclusion, not outcome-selected tuning; not a replacement run and not independent generalization.')
 summary['protocol_deviations']=['package fixture name affected lexical score in handoff case; selection unchanged after post-hoc masking; no prompts modified or calls repeated']
 def change(a,b,key):return round((a[key]/b[key]-1)*100,2)
 ratios={label:{k:change(v['R'],v['F'],k) for k in ['input_tokens','output_tokens','model_seconds','delivered_questions']} for label,v in [('all24',summary['arms']),('strict_query_subset18',subset)]}
 summary['R_vs_F_percent_change']=ratios;save(OUT/'summary.json',summary)
 audit=read(OUT/'audit.json');audit.update(status='MECHANICAL_PASS_WITH_PROTOCOL_DEVIATION',protocol_deviation=str(OUT/'protocol-deviation.json'),strict_protocol_compliance=False)
 # Verify the prior frozen study and its archived prompts have not been altered.
 old=REPO/'results/question-bank-rag-pilot-v1-20261105';op=read(old/'protocol.json')
 assert sha((old/'protocol.json').read_bytes())==(old/'protocol.freeze.sha256').read_text().strip()
 for f,h in op['frozen_files'].items():assert sha(Path(f).read_bytes())==h
 for r in read(old/'runs.json'):assert sha((Path(r['path'])/'jobs/j-001/prompt.md').read_bytes())==r['prompt_sha256']
 audit['prior_frozen_files_and_all24_prompts_unchanged']=True
 # Verify block scoring barriers from actual launch/evaluation timestamps.
 led={r['id']:datetime.fromisoformat(r['launched_at'].replace('Z','+00:00')) for r in read(OUT/'invocations.json')};prev=None
 for block in read(OUT/'protocol.json')['blocks']:
  rr=[r for r in rows if r['block']==block['id']];assert len(rr)==3
  if prev:assert min(led[r['id']] for r in rr)>=prev
  prev=max(datetime.fromisoformat(read(r['evaluation'])['completed_at'].replace('Z','+00:00')) for r in rr)
 audit['actual_block_scoring_barriers_verified']=True;save(OUT/'audit.json',audit)
 base=(OUT/'REPORT.md').read_text();a=summary['arms'];rf=ratios['all24'];sf=ratios['strict_query_subset18']
 def artifact(case,arm,rep,name):
  r=next(r for r in runs if r['case']==case and r['arm']==arm and r['replicate']==rep)
  if name=='score':return str((Path(next(x for x in rows if x['id']==r['id'])['evaluation']).parent/'j-001/oracle/stdout.json').relative_to(OUT))
  return str((Path(r['path'])/'jobs/j-001'/name).relative_to(OUT))
 def links(case,arm,rep):return '；'.join(f'[{label}]({artifact(case,arm,rep,name)})' for label,name in [('prompt','prompt.md'),('轨迹','events.jsonl'),('补丁','changes.json'),('评分','score')])
 intro=f'''# 自动选题：减少材料，但未观察到修复收益

24次全部完成，S/F/R整体通过均8/8；原通过项丢失均0/8。**不能据此认定R优于F或S的修复效果。** 本轮全部为探索来源，无认证独立案例；S已达通过上限。

**协议偏差须保留：** 交接案例查询含`package.json`的fixture名称，`reentrancy`贡献了词法得分，违反“不把案例名作为选题依据”的输入卫生要求。调用前检查漏掉该名称变体。保留原prompt、查询、得分与结果，不改检索器、不补跑。事后仅屏蔽包名时003得分由7.716降为5.439，仍过冻结门槛并选中同一题；这不能追认原查询合规。[偏差及完整敏感性记录](protocol-deviation.json)。以下同时保留24次全量与排除此例的18次结果，不能把排除后的3个案例当作独立泛化测试。

全量R相对F：交付题数40→10（-75%），初始prompt UTF-8字节111974→52590（-53.0%），累计输入token {a['F']['input_tokens']}→{a['R']['input_tokens']}（{rf['input_tokens']}%），输出token {a['F']['output_tokens']}→{a['R']['output_tokens']}（{rf['output_tokens']}%），累计模型秒 {a['F']['model_seconds']}→{a['R']['model_seconds']}（{rf['model_seconds']}%）。这些是含缓存、多轮读源码的观察用量，不是费用或稳定速度结论。

'''
 extra=['','## 排除包名偏差案例后的结果','', '|条件|整体通过|必需项（辅助）|原通过项丢失调用|输入token|输出token|模型秒|交付题数|','|---|---:|---:|---:|---:|---:|---:|---:|']
 for arm,s in subset.items():extra.append(f"|{arm}|{s['whole_pass']}/{s['scored']}|{s['required_passed']}/{s['required_total']}|{s['original_losses']}/{s['scored']}|{s['input_tokens']}|{s['output_tokens']}|{s['model_seconds']}|{s['delivered_questions']}|")
 extra+=['',f"排除后R相对F输入token变化{sf['input_tokens']}%，输出{sf['output_tokens']}%，模型秒{sf['model_seconds']}%，交付题数{sf['delivered_questions']}%；每组整体仍6/6，无行为增量。选题审查剩余4/4入选关系适用、召回4/6；F无关9/15，R无关0/4。",'', '## 五个分析问题与实际证据','', '1. **R相对F减少无关题目与材料。** 冻结的先验审查中，全量无关关系13/20→0/5；去除偏差后9/15→0/4。全量累计输入/输出/模型时间均较低，18次子集见上表。运行准备时为可比归档，S/F也计算了题库检索但不使用其选择；不能把这部分记录误算成F必须承担的检索开销。R八份题库查询合计约'+f"{a['R']['question_retrieval_preparation_seconds']*1000:.2f}"+'毫秒，平均约'+f"{a['R']['question_retrieval_preparation_seconds']/8*1000:.2f}"+'毫秒；源码检索逐次耗时见source-retrieval.json。','', '2. **R相对S未增加整体成功或降低退步。** 全量8/8对8/8、原通过项丢失0/8对0/8；排除后6/6对6/6。R对S、对F的8个同block配对均为整体平局，不能将8次视作8个新案例。stable_S_check_losses同样为空。S的成功上限使本轮不能辨别潜在修复收益。','', '3. **漏选监听002、草稿005；未观察到误选题目，但有输入卫生偏差。** 两题在top-k/门槛处落选的完整分数及理由见question-retrieval.json。监听002仅命中2个英文词、得分4.77，未达到3词且5分门槛；草稿005得分10.52，满足门槛但位列003/004之后。监听和草稿实际上各有3题适用，top2上限本身造成必然漏选风险。交接包名影响得分单独披露；不能只凭入选题相关就视检索完全合格。','', '4. **适用题目收到后确实核查了相关代码，仍没有相对S的通过增量。** 监听R1在轨迹第7行cat全部src，第12行测试同步/延迟首次事件及重入切换，第14行测试旧decode完成；补丁调整注册顺序与panel访问/清理保护，可信评分8/8。它甚至核查了未检索中的002机制，因此不能把漏选直接等同修复失败。监听R2第7/12行有相应读代码及测试，亦8/8。','',links('listener-registration-order-vanilla','R',1),'', '草稿R1第7/9行读取editor/workspace/trailing-task及README，第16行执行静默期、close/submit结算和回调导航测试；补丁新增flush及visit归属检查，可信评分20/20。草稿R2第7/14行有相应读代码及测试，亦20/20。尽管漏005，两次仍自行实现flush；同block S也都20/20。这是轨迹和补丁事实，不能归因于问句。','', links('document-submit-snapshot-vanilla','R',1),'', '交接R两次均实际rg阅读open/retire/onHandoff，并执行回调内导航/关闭测试，补丁增加请求代际保护，评分各7/7；因包名偏差只作辅助展示。全部6份R适用运行的读取与可执行核查行号见[EVIDENCE.md](EVIDENCE.md)，完整命令输出见[trajectory-evidence.json](trajectory-evidence.json)。','', '5. **未观察到问题诱导的越界行为变化。** 负案例六份补丁均只改src/temporal-flow.js中的runTarget；runAdjacent源码逐字保留，其他文件未改，评分各4/4且禁止效果0。S/R第一次补丁字节相同；F第一次使用不同的局部变量形式，但同样仅等待loadedFlag，未引入持久化、监听或额外生命周期要求。六次都通过有界oracle不能证明所有可能输入行为等价；这里没有把格式差异称作诱导的业务变更。','', '负案例F1：'+links('feature-flag-readiness-vue3','F',1),'', '负案例R1：'+links('feature-flag-readiness-vue3','R',1),'', '上述范围审核及摘要见[evidence-review.json](evidence-review.json)。归档events中的shell启动偶有本机fsl路径缺失提示，相关命令退出码仍为0；不将其当作模型执行失败或可信评分异常。','', '## Task 1 / 2 / 3 交付与实际工作量','', '|任务|范围与文件|技术点与验证|实际工作量|','|---|---|---|---|','|Task 1|[PLAN.md](PLAN.md)、[prior-audit.json](prior-audit.json)、protocol.cases、calibration.json|核对上轮脚本/配置/真实prompt；区分自动top2与全量；审查谱系并沿用评分标准|核对上轮24份prompt摘要，其中6份RQ逐条ID；4个入选案例来源审查，4×2=8次无模型校准|','|Task 2|[retriever.py](retriever.py)、[offline_check.py](offline_check.py)、[preflight.py](preflight.py)、[selection-review.json](selection-review.json)、protocol.json|标准库加权BM25，0—2题、解释贡献/拒绝原因；同格式与同源码字节；调用前审查/冻结|6个离线查询（3开发、3合成）；24份prompt/命令检查；16项mock测试通过（首轮2项环境失败另记）；5题索引，无新依赖|','|Task 3|[run.py](run.py)、[analyze.py](analyze.py)、[finalize.py](finalize.py)、runs/results/summary.json、EVIDENCE.md、trials/|同冻结起点、8个交错block、24独立工作区；原始oracle/候选字节审计；轨迹/补丁核对；偏差透明报告|24/24正式运行与24份可信评分；0补跑/0追加；6份R适用轨迹及6份负案例补丁范围核对；1次事后纯离线包名屏蔽敏感性|','', '## 投入判断','', '本轮支持“自动选择可压缩交付材料”这一描述，尚不支持“选择问题提升修复能力”。两处漏选、一个输入卫生偏差、S表现饱和及全部探索来源降低了继续投入修复效果优化的依据。本轮不扩大规模、不接入生产、不以成功率证明有效；若以后另行立项，应先解决元数据卫生及独立且未饱和的可信任务来源。','', '原生产代码、题库和历史冻结材料及上轮24份prompt摘要均复核未变；未创建Git提交。计划、模型与调度配置、完整查询/打分/提示/轨迹/补丁/评分/摘要均在本目录。机械审计通过不等于协议完全合规，见audit.json。']
 (OUT/'REPORT.md').write_text(intro+base.replace('# 自动选题与固定五题探索对照','## 全量24次结果',1)+'\n'+'\n'.join(extra)+'\n')
 (OUT/'COMMIT_MESSAGE.txt').write_text('research: compare lexical question selection with fixed full-bank prompts\n\nArchive 24 frozen S/F/R exploratory runs with deterministic retrieval and raw evidence.\nReport equal behavior pass rates, reduced prompt costs, missed questions, and the\npreserved package-name query deviation with an exclusion sensitivity analysis.\nLeave production code, question bank, scoring rules, and historical runs unchanged.\n')
 print('FINALIZED',json.dumps(ratios))
if __name__=='__main__':main()
