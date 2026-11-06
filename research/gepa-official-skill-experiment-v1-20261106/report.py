"""Final report generation; no model or optimizer calls."""
from runtime import *
from datetime import datetime

def main():
 s=read(OUT/'summary.json');assert s['status']=='COMPLETE';xs=read(OUT/'candidate-lineage.json');rows=s['results'];test=[r for r in rows if r['phase']=='test'];costs=s['costs'];t=costs['total'];p=read(OUT/'protocol.json');elapsed=read(OUT/'completion.json')['at']-datetime.fromisoformat(p['created_at'].replace('Z','+00:00')).timestamp()
 lines=['# 官方GEPA时序技能优化实验报告','','## Task 1：方法对齐与冻结边界','',
 '真正运行了官方GEPA候选搜索和基于轨迹的反思优化；本轮没有找到优于K0的版本。固定官方commit `8e9ae9ed063f6a0259c93db595b96953fdab0e6d`，包metadata 0.1.4，完整源码构建安装在独立.venv，未复制算法片段冒称官方实现。来源：[官方仓库](https://github.com/gepa-ai/gepa)、[官方论文2507.19457v2](https://arxiv.org/abs/2507.19457)。详见OFFICIAL_METHOD.md与environment/。',
 '', '调用官方`gepa.optimize`、结构化adapter协议、EvaluationBatch和GEPAResult。官方控制per-instance Pareto父候选选择、epoch-shuffled两例train批次、单组件round-robin反思变异与解析、严格改善接纳、全val评分及档案。未提供自写候选生成器。实际5次父选择均指向K0，候选池始终只有seed，Pareto选择因此退化为单成员选择，未观察到多候选间的前沿探索。merge受支持但use_merge=False，未启用/未发生。',
 '', '仅进化temporal_skill文本；原始Codex自主执行路径、gpt-6-sol/low、600秒、工作区/工具权限、源码BM25、固定五题、AST不交付、评分标准与BASE/END均固定。没有接入实验性ReAct控制器；Pre/PostModelRequest只记账，不观察工具内容或续行。反思使用同一既有登录CLI的官方callable接口，5个CLI会话/5个底层请求，无工具调用，无账号或模型切换。该受限适配不是论文完整复现。',
 '', 'train为transfer进度组合与download轮询恢复；val为document提交快照与feature-flag首次就绪；test为local-config就绪、listener注册顺序、commit确认边界。按来源cluster与独立unit核对不跨组。全部案例有历史研究暴露，独立泛化案例数0，只是探索性测试。选择依据、暴露、候选文件、公共材料、原题库摘要与调度种子2026110604均在正式模型调用前冻结（PLAN/split/protocol）。',
 '', '## Task 2：实现、实际执行与预算','',
 '正式模型前完成无模型适配核查：隔离工作区、请求计数/进程硬守卫、候选边界、官方合成变异/解析/接纳/选择与checkpoint恢复；七案例原样/参考共14次可信评分校准，参考全部PASS。合成调用不是模型或维护任务执行，不计效果证据。正式cache_evaluation=False；实际评分缓存命中0，provider输入缓存token另外报告。合成cache开关/恢复检查不代表对所有缓存命中路径的验证。正式运行从未恢复、重试失败会话或补跑。',
 '', '优化22/24次真实任务：seed val2 + 五轮父train10 + 子train10；官方metric_calls=22，与任务账本一致。adapter batch调用11次，样本级真实评估22次；优化执行CLI22个、反思CLI5个，底层请求并不等于CLI会话。5个新文本全部完成边界审查和评估，无泄漏拒绝，无人工改写；官方pool只有K0（新增接纳0），五提案全部被官方严格train改进门槛拒绝。',
 '', '反思底层请求5/6。停止发生在剩余任务预算2不足新一轮最坏六次预留时，不扩充规模。Kstar在test前冻结为K0，B组取消，仅按预先顺序执行六次A基线，剩余test预算6保留。正式优化/反思/test失败、超时及可信验证异常均0。但记录45次非零shell命令，包含无.git、无匹配检索、缺少React相关依赖、JSX语法检查不适配及自写断言失败；这些候选可见检查限制与整会话/可信评分失败分开，不宣称所有工具检查通过。',
 '', '档案：PLAN.md、protocol/split/config、K0/Kstar/versions、candidates与candidate-lineage、官方gepa-run原生状态/parents/frontier、official-events/result、reflection-data与完整prompt/输出、materials与全部实际任务prompt、trials中的原始events/工具输出/changes/patch/可信评分/用量、三类账本、preflight/offline、curves、summary、EVIDENCE及audit。全部新增位于本研究目录；生产依赖、prompt、分析器、AST、评分器、题库与历史文件未改，未创建提交。',
 '', '## Task 3：行为、成本、轨迹和局限','','### 开发与验证曲线','','| GEPA轮次 | 父K0整体通过 | 子候选整体通过 | 丢失父版本已通过检查 | 官方接纳 |','|---|---:|---:|---:|---|']
 for x in xs:
  q=x['paired_sample_tradeoffs'];lines.append(f"| {x['iteration']} | {sum(i['parent_whole'] for i in q):.0f}/{len(q)} | {sum(i['child_whole'] for i in q):.0f}/{len(q)} | {sum(len(i['previously_passed_check_losses']) for i in q)} | 否 |")
 lines+=['', '原始曲线见train-curve.csv/svg。父K0五批均1/2；子提案依次1/2、0/2、1/2、1/2、1/2。不能将这些不同文本/重复的9/20混成一个条件的稳定通过率。val仅实际测了seed一次（document与feature各1，平均1.0）；被拒提案没有val分数，val-curve.json保留这一事实。',
 '', '退步单列：提案2丢失配对父K0已通过的transfer重试保留与download pending等待状态；提案4丢失transfer重试保留。其余提案没有配对检查损失；不能用其他检查收益抵消。K0的transfer局部检查本身在8/10与9/10间波动，所有十次transfer仍整体失败。未观察到可信评分标记的禁止副作用，但有限检查不能排除所有不必要行为变化。',
 '', '### 最终测试','','| 案例 | A：K0两次重复 | B：Kstar |','|---|---|---|']
 for c in TEST:
  rr=[r for r in test if r['case']==c];lines.append(f"| {c} | {sum(r['metric']==1 for r in rr)}/{len(rr)} | 取消（Kstar=K0） |")
 lines+=['',f"基线共{sum(r['metric']==1 for r in test)}/{len(test)}整体通过；没有新版本测试收益可报告。所有{len(rows)}次真实维护执行都有实际文件补丁；其中{sum(r['metric']==1 for r in rows)}次可信整体通过，补丁存在不等于任务全部完成。最终test未丢失原通过检查/明确通过断言。条件未发出的断言另存，不误判为false或默认为成功。",'', '### 成本（CLI原始用量）','','| 阶段 | 真实任务/CLI会话 | 底层请求 | 输入token（含缓存） | 缓存输入 | 输出token | 含评分秒数 | 工具调用 |','|---|---:|---:|---:|---:|---:|---:|---:|']
 for key,label in [('execution_train','train执行'),('validation_selection','val选择'),('reflection','全部反思搜索'),('final_test','最终test'),('total','合计')]:
  c=costs[key];lines.append(f"| {label} | {c['task_executions']}/{c['codex_sessions']} | {c['native_requests']} | {c['input_tokens']:,} | {c['cached_input_tokens']:,} | {c['output_tokens']:,} | {c['seconds']:.1f} | {c['tool_calls']} |")
 lines += ['',f'冻结至测试结束的实际墙钟约{elapsed/60:.1f}分钟；阶段秒数为会话含评分时间相加，不含全部准备、审查等待和进程间间隔。成本不虚构美元账单。全部搜索成本包含父/子train、val选择和反思，未把被拒候选成本剔除。', '', '### 实际轨迹证据与机制边界','',
 '基线transfer运行`e-154720bb7bb64f25`的events第11行实际读取transfer/progress/progress-source/queue/telemetry；第18行自写检查失败，第21行另一检查通过；第23/25/27行git检查因隔离工作区无.git失败。patch.diff只修改progress监听注册顺序和显示排序。可信整体仍失败，重试/启动切换未覆盖。提案1的`e-3df2db08080046ff`仍只改progress，结果同为8/10。新文本不等于新增可观察核查行动。',
 '', '提案2的download运行`e-0f86af18a30343df`在pending回调先清loading后安排retry，可信等待状态失败；对应父运行通过。其实际补丁与工具检查保存在该任务jobs/j-001，不凭模型“已验证”判定正确。提案2/4的transfer仍仅改progress，配对父运行分别改过progress+queue+transfer、progress+queue并保留了重试检查。修改范围收窄与检查损失同现，但小样本不能证明是技能干预的因果效应。',
 '', '冻结可见源码queue第11–18行区分record/receive并在createTransfer返回后登记handle，transfer第10–13行在transport和进度监听调用后继续操作；进度源存在同步初始回调。执行者已实际读到相关模块，因此纯信息不可见不足以解释全部失败。仍无法仅从轨迹判定模型是否建立了正确完整契约、遗漏了哪一层返回后的状态、或正确判断未落实到补丁。所有提案transfer补丁均只改progress，可信启动切换一直失败，支持继续检查契约到补丁以及验证覆盖的断点。',
 '', '五份反思输入包含十次父train执行的真实读取位置、工具输出、实际diff、可见验证、整任务分数和有任务/源码依据的自然语言行为差异；完整证据未丢弃，有界摘要的截断显式标记。隐藏检查名、oracle代码和参考补丁没有进入反思输入或技能。官方StatelessReflectionLM每轮从所选父K0与最新父轨迹重新提案，被拒子轨迹不会自动成为下一轮反思历史；这是所用官方配置的实际行为，不声称跨轮积累学会。',
 '', '### 结论与下一步','',
 '问题1：是，真正运行官方GEPA的选择、轨迹反思、变异、子候选评估和拒绝，产生5个新提案；没有获接纳的新pool成员，merge未发生。',
 '', '问题2：在本轮明确分布和预算内未找到优于K0的版本，Kstar=K0；最终仅测基线6/6，不能伪造B结果或把波动算收益。拒绝4个持平提案与1个退步提案，不足以否定GEPA。',
 '', '区分力限制尤为明显：val K0已满分，在固定最早索引平局规则下不存在更高分可供选择，即使候选在train改善并追平val也不能替换seed。这在结果前已记录为风险，但本轮实际发生。训练反馈是源码绑定自然语言诊断且有轨迹，但可能仍不足以让执行者落实完整调用顺序；仅五个提案、两例train/val、暴露且大多通过的test，均限制结论。没有证据将无收益唯一归为预算、数据、反馈、候选或执行模型能力。',
 '', '建议暂不发布技能或直接扩大搜索预算。优先分析启动回调返回后的所有权/不同副作用，并补足候选可见验证对该顺序的覆盖；之后另行预注册更有选择区分力、项目隔离且未暴露的val/test再评估GEPA。关键模块已读的证据不支持先把主要投入放在扩大通用检索上。本轮不据test继续优化。',
 '', '建议Git commit subject：`research: add pinned official GEPA temporal-skill pilot`','', 'Body：`Integrate the official GEPA adapter with frozen splits, trace-grounded feedback and hard execution budgets. Archive five rejected proposals, K0 selection, baseline-only final evaluation and reproducibility evidence; leave production and historical experiments unchanged.`','']
 (OUT/'REPORT.md').write_text('\n'.join(lines))
if __name__=='__main__':main()
