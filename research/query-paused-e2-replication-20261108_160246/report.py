"""Readable post-six-slot report. Never invokes a model, scorer, or adaptive dispatcher."""
import sys,json
from pathlib import Path
sys.dont_write_bytecode=True
A=Path(__file__).resolve().parent;read=lambda p:json.loads(Path(p).read_text())
s=read(A/'summary.json');g=s['groups'];v=read(A/'behavior-vectors.json');t=s['total_cost'];it=read(A/'integrity-validation.json');scope=read(A/'scope-review.json');tools=read(A/'tool-diagnostics.json');src=read(A/'sources.json');cfg=read(A/'frozen-config.json')
lines=['# 冻结E2的同题独立复现','',s['conclusion'],'',
'## Task 1：来源对应、冻结和离线检查','',
f"唯一源批次：`{src['sole_source']}`。实际case由源manifest/cohort核定为 `{s['case']}`。起始HEAD `{read(A/'initial-state.json')['HEAD']}`；跟踪diff与起始状态一致，既有修改/历史文件保留，仅新增本研究目录。",'',
f"E2 SHA256 `{src['E2_sha256']}` 与用户指定值一致。A/B实际prompt均逐字节复用源文件，B严格等于A加两个换行加E2。候选、任务、自动Contract实际交付文本、评分场景/规则、原始行为要求及依赖摘要核验通过，没有修正E2已记录歧义、重新提取、训练、反思或提供历史补丁/评分解释给维护模型。",'',
'源REPORT/summary、experience-freeze、cohort/config/protocol、源六槽实际prompt与配置、原评分与SHA清单、完整性记录均核对；源结果为AUTO 0/3、AUTO+E2 1/3，仅作历史参照，不进入本新批分母。源批已经结束，没有恢复或修改其停止/完成记录。输入与复用摘要见sources.json、source-evidence/。','',
f"CLI `{cfg['CLI_version']}`，二进制SHA `{cfg['CLI_sha256']}`；Node `{cfg['node_actual']}`。runner.session/command/verify/source_proof、Archive、GuardServer及native backend/配置/schema逐字节复用；control.py（含原score）与源完全相同，未增加AST、RAG、检查表、ReAct、工具黑名单或模型请求预算。",'',
'宿主全局默认service_tier已在本次之前由priority变成default；这是与历史保护记录不同的唯一文件。源运行器本来就不加载该文件，而是使用仓库外临时profile。离线命名空间证明：宿主home/config不可见、实际profile字节及完整CLI参数与源一致，仍显式指定low/priority；宿主环境被清空，只保留原协议允许的代理变量。本批保护当前宿主摘要，保留历史差异，未修改全局配置。host-config-isolation.json记录完整证明及可核对的配置边界，不把CLI声明当成服务端路由/effort/tier的独立认证。','',
'第一次准备检查将这个不被加载的宿主默认文件也与历史摘要强比，因此在复制输入前停下；随后本地preflight因runner尚未复制而导入失败，未运行任何模型/评分。适配后仅将宿主默认配置按当前基线保护，要求实际隔离profile/参数一致再继续，所有其他旧保护文件都保持原摘要。offline-preparation-notes.json保留记录，没有重试模型或评分器。','',
'零模型离线检查通过：临时小候选与假事件分别验证无修改、改动/新增/删除及补丁应用、超时保留轨迹/候选、diff异常不覆盖原退出原因、请求封顶/被阻止派发、真实命名空间读写/Node验证与归档隔离。fake CLI为本地Python，fake score回调只写假材料，不是案例评分器。复用源版本对应15项归档测试和10份真实评分校准，真实案例评分预跑0。详见offline-validation.json。','',
'protocol.json/sha256在任何正式调用前冻结本协议、实际两组prompt、所有关键输入/经验摘要、配置、评分版本、六槽调度与解释规则。认证、临时profile和本地夹具都在Git仓库外。','',
'## Task 2：六槽执行及整体结果','',
'固定维护：gpt-5.6-terra/low，priority；每槽最多24请求/600秒，stdout16MiB，原JSON report≤6000字符，并发1；本批最多6维护会话/144请求/累计会话3600秒/6次真实外部评分。每次从同一原始候选独立复制、独立ephemeral会话，不继承记忆、补丁、工具状态或评分反馈。','',
'调度种子2026110803只控制块内顺序，不控制模型采样。冻结顺序A、B、A、B、A、B；三个块各有A和B一次。严格按序，不依据中间表现取消正常槽位、改经验或增加重复。原评分器在模型停止、Python保存最终候选后评分一次，评分不暴露或反馈后续维护，六槽结束后统一分析。','',
'| 槽位 | 条件 | 有效 | 整体 | 行为通过 | 请求 | 工具 | 秒 | 异常/资源 |','|---|---|---|---|---:|---:|---:|---:|---|']
for x in s['per_slot']:lines.append(f"| {x['slot']} | {x.get('condition')} | {x['valid']} | {x.get('verdict')} | {x.get('passed_items')}/29 | {x.get('native',{}).get('started',0)} | {x.get('native',{}).get('tool_attempts',0)} | {x.get('seconds',0):.2f} | {x.get('failure_class') or '无'} |")
lines+=['','| 组别 | 完整通过/有效分母 | 通过率 |','|---|---:|---:|']
for arm in ['A','B']:
 z=g[arm];rate=f"{100*z['complete_pass_rate']:.1f}%" if z['complete_pass_rate'] is not None else '不可计算';lines.append(f"| {arm}/{'AUTO' if arm=='A' else 'AUTO_EXP(E2)'} | {z['complete_passed']}/{z['valid_denominator']} | {rate} |")
d=s['pass_rate_difference_B_minus_A'];lines+=['',f"B-A通过率差：{100*d:+.1f}个百分点。" if d is not None else 'B-A通过率差不可计算。',s['conclusion'],'',
f"未启动槽位：{json.dumps(s['unstarted'],ensure_ascii=False)}。停止记录：{json.dumps(s['stop'],ensure_ascii=False)}。所有已启动槽位及异常、实际计量都在actual-schedule.json；资源耗尽沿用源分类，正常失败未因结果而剔除/改标。无有效评分的缺失不代填成功或失败。",'',
'历史参照单列：源E2批AUTO 0/3（27、27、27/29）、AUTO+E2 1/3（27、29、27/29）。这是历史观察，本次没有把它、开发回验或E1结果并入新分母，也没有以跨批汇总替代本次结果。独立指新会话/工作区，不是未见案例独立测试。','',
'## Task 3：复现解释、完整分项、成本和限制','',
'重点核对两组保留关系：cached-prior-consumed-success、retained-context-query-flag；cached-paused-background、cached-later-consumption。以下给出全部29项次数，完整逐槽向量见behavior-vectors.json；原评分不变，部分通过不改判整题通过。','',
'| 行为 | 原候选通过 | 目标 | A通过次数/有效分母 | B通过次数/有效分母 |','|---|---|---|---:|---:|']
for k in v['item_order']:lines.append(f"| {k} | {v['original_candidate'][k]} | {'是' if k in v['targets'] else ''} | {g['A']['per_behavior_pass_counts'][k]}/{g['A']['valid_denominator']} | {g['B']['per_behavior_pass_counts'][k]}/{g['B']['valid_denominator']} |")
lines+=['','相对原始候选21项原正确行为的损失：','']
for x in s['per_slot']:lines.append('- '+x['slot']+'：'+(', '.join(x.get('original_correct_losses',[])) or '无')+'。')
lines+=['','块内B相对A描述性得失（不声称共同采样种子或单次因果）：','']
for x in v['block_comparisons']:lines.append(f"- 块{x['repeat']}：增加通过 {', '.join(x['B_gains_over_A']) or '无'}；增加损失 {', '.join(x['B_losses_against_A']) or '无'}。")
lines+=['','全部补丁逐份复核（本会话AI辅助，无独立人工审阅/额外模型评委）：','']
for x in scope['runs']:lines.append('- '+x['slot']+'：'+x['review'])
lines+=['','工具非零诊断另列，原始输出全部保留，不事后混作基础设施/归档故障或改变有效分母：','']
for x in tools['runs']:lines.append('- '+x['slot']+'：'+('; '.join('事件'+str(z['event_line'])+' exit='+str(z['exit_code'])+('，无.git工具诊断' if z.get('git_non_repository_warning') else '，详见原输出') for z in x['nonzero_tool_commands']) or '无非零命令')+'。')
for note in tools.get('notes',[]):lines.append('- '+note['slot']+'：'+note['finding'])
lines+=['','| 成本 | A | B |','|---|---:|---:|']
for key in ['requests_started','requests_completed','blocked_dispatches','tool_calls']:lines.append(f"| {key} | {g['A'][key]} | {g['B'][key]} |")
lines.append(f"| 会话秒数 | {g['A']['seconds']:.2f} | {g['B']['seconds']:.2f} |")
for key in ['input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens']:lines.append(f"| {key} | {g['A']['observed_tokens'][key]} | {g['B']['observed_tokens'][key]} |")
lines+=['',f"本批维护合计{t['sessions']}会话、{t['requests_started']}次底层请求、{t['tool_calls']}次工具调用、{t['seconds']:.2f}会话秒；token={json.dumps(t['tokens'],ensure_ascii=False)}，计量缺失={t['usage_incomplete']}。B-A请求差{g['B']['requests_started']-g['A']['requests_started']:+d}，工具差{g['B']['tool_calls']-g['A']['tool_calls']:+d}，时间差{g['B']['seconds']-g['A']['seconds']:+.2f}秒。缓存输入和reasoning输出是各自总量子集，不重复相加；不估算货币费用。",'',
f"真实外部评分{s['formal_external_scores']}次。提取、反思、GEPA、新经验、额外模型评委、真实模型预跑、自动/会话重试、评分补跑均为0。主控聊天准备/分析本身的平台计量不可见，不并入维护成本，也不声称为0。",'',
f"完整性检查：{it['status']}；{it['frozen_files']}份冻结文件及{it['protected_files']}份既有文件摘要核验。候选原始起点一致，最终快照等于业务工作区，评分前后输入摘要与该快照一致。实际prompt、角色参数和请求计量核验保留；宿主当前配置与源批所有文件均未修改。各槽archive包含输入/实际prompt、事件/工具/stderr、原始回答、用量、最终候选、patch.diff、原评分、异常与SHA清单。",'',
'会话与归档复用源Python能力：模型只修业务和必要自验证；Python创建独立业务目录，保存输入摘要/快照/prompt/config、持续事件与计量、停止后的最终源码/差异/回答，并收集外部原评分。归档不挂载给模型，不请模型制作或修补归档；diff 0无差异、1正常差异、其余错误；新增文件不静默删除，归档操作不得改变最终源码。没有修改生产代码、原始案例、评分器/参考实现、E2、自动Contract、全局配置或依赖，未创建提交。','',
'每组三次仍是小样本，结果只描述本次同题复现观察，不支持稳定有效、统计显著或新题泛化。E2曾由本题反馈生成，这不是独立未见测试，也不称整个研究过程事先预注册。无论正负，本轮到此结束，不进入E3、新案例、追加实验或生产经验库。','',
'材料：PLAN.md、sources.json、source-evidence/、host-config-isolation.json、offline-validation.json、protocol.json/sha256、experience-freeze.json、frozen-config.json、schedule.json、prompts/、NEW_EXPERIENCE.md、runs/*/archive/、actual-schedule.json、summary.json、behavior-vectors.json、behavior-counts.csv、scope-review.json、tool-diagnostics.json、integrity-validation.json、ARTIFACTS.sha256。','',
'推荐提交（仅建议，未创建）：','', '```text','research: replicate frozen E2 on the same case','', 'Reuse unchanged E2, prompts, repair runner and evaluator for six fresh A/B sessions.', 'Archive complete behavior vectors, usage, regressions and replication limits.','```','']
(A/'REPORT.md').write_text('\n'.join(lines));(A/'COMMIT_MESSAGE.txt').write_text('research: replicate frozen E2 on the same case\n\nReuse unchanged E2, prompts, runner and evaluator for six fresh A/B sessions.\nArchive complete outcomes, usage, regressions and replication limits.\n')
print('REPORT.md written')
