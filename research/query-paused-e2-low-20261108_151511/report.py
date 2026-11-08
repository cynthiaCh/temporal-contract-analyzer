"""Post-schedule readable E2 report; consumes frozen/raw evidence, no model/scorer calls."""
import sys,json
from pathlib import Path
sys.dont_write_bytecode=True
A=Path(__file__).resolve().parent
read=lambda p:json.loads(Path(p).read_text())
s=read(A/'summary.json');v=read(A/'behavior-vectors.json');g=s['groups'];t=s['total_cost'];tr=s['reflection_cost'];it=read(A/'integrity-validation.json');scope=read(A/'scope-review.json');diagnostics=read(A/'tool-diagnostics.json')
lines=['# E2：一次经验修订及同题对照','',s['conclusion'],'',
'## Task 1：离线定位、唯一E2与冻结','',
f"实际案例 `{s['case']}` 来自原manifest，模型、原始候选、任务、固定自动Contract、CLI/工具、Node与评分版本不变。只新增本研究目录；起始HEAD `{read(A/'initial-state.json')['HEAD']}`，用户既有修改与历史文件保留。",'',
'第1步结论：E1没有明确要求把取消能力消费记录迁到单次尝试。三份B公开说明都主动选择了该实现，且实际补丁可核对。E1强调尝试分类，但未明确区分共享消费记录的归属、继承/重置时机与单次控制器生命周期，可能留下被过度推广的空间。公开说明证明选择了什么，不能证明不可见内部推理，也不能证明某句经验是唯一原因。','',
'源码与旧标准共同规定：getter惰性标记其所属共享query，返回来源attempt的controller；共享标记只在实际执行入口重置，创建新暂停尝试不重置；最后观察者离开按既有共享标记结算。三份E1-B补丁都改为依据attempt消费作取消判定，其中一份虽仍同时写query标记，也不再按该标记作判断。','',
'两条失效链：先前消费成功后创建新暂停尝试，原共享消费状态被忽略；旧context延迟读取时，未使当前暂停尝试按共享消费状态结算。原评分均观察到2次调用而标准是1次。可见自验证覆盖同次取消、未消费缓存刷新等，遗漏这两条跨尝试链。完整证据见 DIAGNOSIS.md、diagnosis.json、evidence/ 与 training-feedback.json。','',
'正向证据同样反馈：E1-B三次均修好三项目标，保留其初始终结/idle结算/续行竞态、合法缓存刷新和未消费完成关系。反思器同时收到原始源码、实际变化、原评分观察与标准依据；未收到人工修补候选、参考答案或旧完整成功补丁。原开发同E1曾29/29只作为因果限制记录，不混入新分母。','',
f"只执行一次Reflection，沿用原开发反思配置 `gpt-5.6-terra / medium`、12请求/600秒上限，实际{tr['native']['started']}次请求、{tr['seconds']:.2f}秒、工具调用{tr['native'].get('tool_attempts',0)}。E2原样取唯一JSON report，SHA256 `{s['E2_sha256']}`，未人工润色、未生成第二候选或E3。E2原文见 NEW_EXPERIENCE.md，原E1见 E1.md，完整反思prompt/轨迹在 reflection-input.md 和 training-runs/reflection/archive/。",'',
'E2明确加入共享记录与单次控制器/结算资格的不同生命周期，并加入旧上下文晚读、暂停创建保留记录等验证。其第2段“读取是否只在实际执行入口惰性记录”可能混淆惰性标记与入口重置，已在调用前的experience-review.json如实记下；原文不修改，不宣称文本无歧义或预先保证成功。','',
'离线检查模型调用/维护执行/评分重跑均为0，版本对应的15项归档测试和10份评分校准复用，实际命名空间读写/验证、工具RPC、归档隐藏与角色参数检查通过。本地反思无hook时没有ledger文件，检查脚本原先错误假定存在，修正后通过；保留失败夹具与offline-preflight-correction.json，未改实际会话计量或归档运行器。','',
'分两段冻结：reflection-protocol.json/sha256在反思前冻结诊断、反馈、实际反思prompt、角色配置、六槽调度和分析规则；experience-freeze.json与protocol.json/sha256在所有维护前冻结原始E2、实际两组prompt及反思归档。A逐字节复用上一批AUTO；B严格为A加两个换行再加E2，公共任务/工具/输出/自动归档职责完全相同。维护看不到诊断、补丁、标准评分反馈或旧E1。','',
'## Task 2：六槽实际执行与整题指标','',
'维护配置不变：gpt-5.6-terra/low、priority，每槽24底层请求/600秒，stdout≤16MiB、唯一JSON report≤6000字符，并发1；六槽合计最多144请求/3600会话秒。反思另有原来的12请求/600秒单次上限，合计最多7会话/156请求/4200秒，未提高任何角色单次预算。服务端路由/effort无独立证明，CLI声明及hook model实际检查，限制与旧批相同。','',
'种子20261108只用于块内A/B调度，顺序A、B、A、B、B、A，不控制采样。每槽同一起点、独立工作区/会话，不传递记忆、补丁或评分。外部原评分在停止模型并归档最终候选后执行，六槽全部结束后统一分析；没有按中间质量改变顺序、剔除正常失败或补跑。','',
'| 槽位 | 条件 | 有效 | 整题 | 分项 | 请求 | 工具 | 秒 | 模型/基础设施异常 |','|---|---|---|---|---:|---:|---:|---:|---|']
for x in s['per_slot']:lines.append(f"| {x['slot']} | {x.get('condition')} | {x['valid']} | {x.get('verdict')} | {x.get('passed_items')}/29 | {x.get('native',{}).get('started',0)} | {x.get('native',{}).get('tool_attempts',0)} | {x.get('seconds',0):.2f} | {x.get('failure_class') or '无'} |")
lines+=['','| 组别 | 完整通过/有效分母 | 通过率 |','|---|---:|---:|']
for arm in ['A','B']:
 z=g[arm];rate=f"{100*z['complete_pass_rate']:.1f}%" if z['complete_pass_rate'] is not None else '不可计算';lines.append(f"| {arm}/{'AUTO' if arm=='A' else 'AUTO_EXP(E2)'} | {z['complete_passed']}/{z['valid_denominator']} | {rate} |")
d=s['pass_rate_difference_B_minus_A'];lines+=['',f"B-A整题通过率差：{100*d:+.1f}个百分点。" if d is not None else '有效分母不足，B-A差不可计算。',s['conclusion'],'',
f"全部已启动槽位和异常见 actual-schedule.json，未启动槽位：{json.dumps(s['unstarted'],ensure_ascii=False)}；停止记录：{json.dumps(s['stop'],ensure_ascii=False)}。有效性沿用旧规则；正常行为失败或资源耗尽不为提高成功率而剔除，缺失评分不代填成功或失败。",'',
'历史单列：原开发AUTO 0/2（26、26/29）、E1 1/2（27、29/29）；上一冻结E1正式AUTO 0/3（27、26、27/29）、E1 0/3（27、27、27/29）。这些已经见过的结果只用于开发背景，不并入本轮正式分母。本轮E2使用先前同题反馈训练，不是未见案例的独立测试或整个研究过程事先预注册。','',
'## Task 3：完整得失、成本、完整性与停止','',
'| 行为 | 原始通过 | 目标 | A通过次数/有效分母 | E2通过次数/有效分母 |','|---|---|---|---:|---:|']
for k in v['item_order']:lines.append(f"| {k} | {v['original_candidate'][k]} | {'是' if k in v['targets'] else ''} | {g['A']['per_behavior_pass_counts'][k]}/{g['A']['valid_denominator']} | {g['B']['per_behavior_pass_counts'][k]}/{g['B']['valid_denominator']} |")
lines+=['','每槽原正确行为损失：','']
for x in s['per_slot']:lines.append('- '+x['slot']+'：'+(', '.join(x.get('original_correct_losses',[])) or '无')+'。')
lines+=['','块内E2相对A的描述性得失（不是共同采样种子，不单独证明因果）：','']
for x in v['block_comparisons']:lines.append(f"- 块{x['repeat']}：增加通过 {', '.join(x['B_gains_over_A']) or '无'}；增加损失 {', '.join(x['B_losses_against_A']) or '无'}。")
lines+=['','六份补丁均逐一复核，无独立人工审阅或额外模型评委：','']
for x in scope['runs']:lines.append('- '+x['slot']+'：'+x['review'])
lines+=['','工具级诊断（保留所有原输出，不把自验证命令失败混为评分、归档或基础设施异常）：','']
for x in diagnostics['runs']:lines.append('- '+x['slot']+'：'+('; '.join('事件'+str(z['event_line'])+' exit='+str(z['exit_code'])+('，无.git的git诊断' if z['git_non_repository_warning'] else '，见原命令输出') for z in x['nonzero_tool_commands']) or '无非零命令')+'。')
lines+=['','补充诊断：block-1-A一次git status返回128，一次自验因只等待一个微任务而过早断言缓存成功，随后按可见说明增加微任务等待并通过；这是会话内必要自验证，没有重启维护或重跑外部评分。block-1-B曾find ..寻找AGENTS，在隔离命名空间的/etc和/proc遭遇权限错误，属于偏离仅/workspace说明的工具行为；没有观察到宿主归档/评分器暴露，也未事后改变有效分母。详见tool-diagnostics.json和原始事件。','','| 维护成本 | A | E2 |','|---|---:|---:|']
for key in ['requests_started','requests_completed','blocked_dispatches','tool_calls']:lines.append(f"| {key} | {g['A'][key]} | {g['B'][key]} |")
lines.append(f"| 会话秒数 | {g['A']['seconds']:.2f} | {g['B']['seconds']:.2f} |")
for key in ['input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens']:lines.append(f"| {key} | {g['A']['observed_tokens'][key]} | {g['B']['observed_tokens'][key]} |")
lines+=['',f"维护合计：{t['sessions']}会话、{t['requests_started']}请求、{t['tool_calls']}工具调用、{t['seconds']:.2f}秒；计量缺失：{t['usage_incomplete']}。E2-A请求差{g['B']['requests_started']-g['A']['requests_started']:+d}、工具差{g['B']['tool_calls']-g['A']['tool_calls']:+d}、时间差{g['B']['seconds']-g['A']['seconds']:+.2f}秒。",'',
f"反思另计：{tr['native']['started']}请求、{tr['seconds']:.2f}秒；token={json.dumps(tr['usage']['observed_usage_subtotal'],ensure_ascii=False)}。全部角色合计{s['all_roles_cost']['sessions']}会话、{s['all_roles_cost']['requests_started']}请求、{s['all_roles_cost']['seconds']:.2f}秒。缓存输入和reasoning输出是各自总量子集，不重复相加；不估算货币费用。主控准备/分析聊天的平台请求和token不可见，不混入维护成本、不声称为0。",'',
f"正式原评分调用{s['formal_external_scores']}次，评分补跑0；Contract重新提取、GEPA、第二次反思/E3、额外模型评委、隐藏模型预跑、会话重试均为0。E2由唯一一次反思生成，不是人工写的经验或补丁。",'',
f"完整性：{it['status']}。{it['frozen_files']}份冻结文件及{it['protected_files']}份既有文件摘要通过；维护原始候选一致，最终快照等于工作区，评分前/后候选与该最终快照摘要一致；实际prompt唯一差异为E2；反思原始report等于E2。每槽事件、工具/stderr、patch.diff、最终候选、原评分/全行为向量、用量和SHA清单保存在各archive目录。",'',
'复用而非重写：原runner.py、archive.py、native_backend.py、GuardServer/guard_client/request_guard/read_policy、配置/模型目录/输出schema逐字节复用；control.py与score函数沿用上一批。新增prepare/preflight/reflection/freeze及离线分析报告适配。Python负责所有机械快照、事件/stderr/计量、最终补丁与评分归档，归档不挂载给模型，不请模型备份/修补归档，不删除它产生的额外业务文件。未修改生产代码、原案例、评分规则、全局配置、旧批次或创建Git提交。','',
'结论范围仅此同题小规模探索。各组三次不支持统计显著、稳定有效或新题泛化，E2又使用了先前本题反馈；不得把开发或E1历史池化增强证据，也不能只挑E2成功补丁。经验文本的措辞歧义已保留在审查记录，不因结果好坏事后改写。','']
if d is None or g['A']['valid_denominator']!=3 or g['B']['valid_denominator']!=3:lines+=['有效性不足，结论受限；不自动补跑，不产生第二候选。']
elif d<=0:lines+=['本轮仍无整题收益：按用户预先约定，停止继续打磨这条经验，保留负结果。下一研究问题是经验文本是否足以解除这一瓶颈，而不是本批继续生成E3、改模型/评分或扩大案例。']
else:lines+=['本轮观察到整题增量；仍只完成这一轮，不要求每次100%，不自动扩展、不生成E3或更新生产经验库。']
lines+=['','主要材料：DIAGNOSIS.md、training-feedback.json、reflection-input.md、E1.md、NEW_EXPERIENCE.md、两段protocol/sha256、experience-freeze.json、prompts/、schedule.json、reflection-receipt.json、actual-schedule.json、training-runs/、runs/、behavior-vectors.json/csv、summary.json、scope-review.json、tool-diagnostics.json、integrity-validation.json、ARTIFACTS.sha256。','',
'推荐提交（未创建）：','', '```text','research: revise frozen experience once and evaluate E2','', 'Ground the revision in three repeated regressions and preserved target gains.', 'Freeze one reflector-generated E2 and archive six unchanged-budget A/B sessions.', 'Report whole-task outcomes, regressions, costs and same-case limitations.','```','']
(A/'REPORT.md').write_text('\n'.join(lines))
(A/'COMMIT_MESSAGE.txt').write_text('research: revise frozen experience once and evaluate E2\n\nGround the revision in repeated regressions and preserved target gains.\nFreeze one E2 and archive six unchanged-budget A/B sessions.\nReport whole-task results, regressions, costs and same-case limitations.\n')
print('REPORT.md written')
