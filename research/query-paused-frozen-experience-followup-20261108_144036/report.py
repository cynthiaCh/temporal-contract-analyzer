"""Human-readable report from the completed, unchanged raw scoring and usage."""
import sys,json
from pathlib import Path
sys.dont_write_bytecode=True
A=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text())
s=read(A/'summary.json');v=read(A/'behavior-vectors.json');cfg=read(A/'frozen-config.json');integ=read(A/'integrity-validation.json');scope=read(A/'scope-review.json');g=s['groups'];t=s['total_cost']
def cost(key):return str(g['A'][key])+' | '+str(g['B'][key])
lines=['# 冻结经验后的同题对照报告','',s['conclusion'],'',
'## Task 1：来源、协议变化与离线检查','',
f"实际案例：`{s['case']}`，由旧 manifest/cohort 的一致 ID 确定，未按目录名猜测、未替换案例。新批次从 HEAD `{read(A/'initial-state.json')['HEAD']}` 开始；原有用户修改及旧批次全部保留，跟踪 diff 与起始一致。",'',
'旧批次 `query-paused-same-case-low-20261108_140200` 的 AUTO 开发为 26/29、26/29，整体0/2；AUTO_EXP 开发为27/29、29/29，整体1/2。旧经验准入失败及停止结果保持不变，不并入本次正式分母。一次开发回验损失 `cached-prior-consumed-success`、`retained-context-query-flag`，没有隐去。','',
'本次是看过开发结果后提出、在正式调用前冻结的探索性后续实验。仅把候选准入改为“有改善信号即可参加对照，允许局部退步”，不改变原评分器、正确答案、29项要求或整题通过判定。不是未见案例独立测试，不是整个研究过程的事先预注册。','',
'候选、任务、自动 Contract 实际交付文本、NEW_EXPERIENCE.md 均逐字节复用。A 为旧 AUTO 实际 prompt；B 严格等于 A 加两个换行再加原经验全文，与旧 AUTO_EXP 实际 prompt 相同。没有重新抽取、人工润色、反思、GEPA、第二份经验、开发补丁或评分反馈交付模型。来源/摘要见 sources.json、protocol.json、source-evidence/。','',
f"维护配置：`gpt-5.6-terra / low`，priority；CLI `{cfg['CLI_version']}`，SHA256 `{cfg['CLI_sha256']}`，Node `{cfg['node_actual']}`；与四个旧维护会话一致。每槽24请求/600秒，stdout16MiB、JSON report≤6000字符，并发1，总计最多6槽/144请求/3600会话秒。服务端 effort/路由没有独立证明，实际 hook model 与 CLI effort 声明均已核验。",'',
'调用前本地核验两组隔离命名空间的读写/验证、合法 cp/diff/for 命令及工具 RPC；宿主快照、归档与计量目录不可见；候选核验前后未变。原运行器模块逐字节复用，复用15项离线归档测试及10份版本对应评分校准记录，无重跑校准或隐藏模型预跑。offline-validation.json 记录离线实验模型请求、维护执行、案例评分重跑均为0。','',
'协议、prompt、输入、经验、配置、评分版本、调度与分析规则先写入 protocol.json 并冻结 protocol.sha256；所有正式启动时间都晚于冻结。调度种子20261108只控制块内顺序，不控制模型采样。','',
'## Task 2：六槽实际执行与整体结果','',
'冻结顺序：block-1-A、block-1-B、block-2-A、block-2-B、block-3-B、block-3-A。每槽独立工作区与独立会话，无记忆/补丁传递，无重试或追加槽位。外部评分在模型停止后执行，不向维护模型或后续会话反馈；全部槽位结束后统一分析。','',
'| 槽位 | 条件 | 有效 | 整体 | 行为通过 | 底层请求 | 工具 | 秒 | 异常/资源 |','|---|---|---|---|---:|---:|---:|---:|---|']
for x in s['per_slot']:
 lines.append(f"| {x['slot']} | {x.get('condition')} | {x['valid']} | {x.get('verdict')} | {x.get('passed_items')}/29 | {x.get('native',{}).get('started',0)} | {x.get('native',{}).get('tool_attempts',0)} | {x.get('seconds',0):.2f} | {x.get('failure_class') or '无'} |")
lines+=['','| 组别 | 完整通过/有效分母 | 通过率 | 已启动 |','|---|---:|---:|---:|']
for arm in ['A','B']:
 z=g[arm];rate=f"{100*z['complete_pass_rate']:.1f}%" if z['complete_pass_rate'] is not None else '不可计算';lines.append(f"| {arm}/{z['condition']} | {z['complete_passed']}/{z['valid_denominator']} | {rate} | {z['started']} |")
d=s['pass_rate_difference_B_minus_A'];lines+=['',f"B-A整体通过率差：{100*d:+.1f}个百分点。" if d is not None else 'B-A差值不可计算。',s['conclusion'],'',f"未启动槽位：{json.dumps(s['unstarted'],ensure_ascii=False)}。停止记录：{json.dumps(s['stop'],ensure_ascii=False)}。资源耗尽按原 runner 分类单列，正常失败未剔除、未补跑。所有已启动槽位均保存完整归档。",'',
'工具级非零返回另见 tool-diagnostics.json：6个槽位各有一次 git diff/check 在无 .git 的独立工作区返回129。这些是模型自验证工具诊断，不是 Python 自动归档 diff 失败或基础设施故障；全部保留，没有以此重试会话或剔除行为失败。两组工作区条件与旧批次一致。六槽输出格式均有效。','',
'复用函数：runner.session/command/verify/source_proof，Archive.prepare/finalize/collect/write_manifest 与 GuardServer；control.py 的 score 回调原样复制旧函数。仅新建 prepare/preflight/freeze/control 与离线分析/报告适配。未重写框架，未修改生产代码、案例原始源码、评分规则、旧冻结文件或全局配置，未新增依赖、未创建提交。','',
'会话流程：Python 冻结输入→复制独立业务工作区→挂载业务目录与合法运行工具→外层保存事件、stderr、请求/工具/token→停止模型→保存最终候选、自动 patch.diff、回答和计量→外部原评分器评价同一最终候选→核对评分前后摘要。归档目录不挂载给模型；机械归档职责和公共 prompt 对两组完全一致。diff 0/1正常，其余记录工具异常；不删除模型新增文件，不请求模型修复归档。','',
'## Task 3：分项得失、成本、限制与结论','',
'目标三项：'+', '.join('`'+x+'`' for x in v['targets'])+'。以下给出全部29项次数，完整每槽向量与原始 scorer 输出均保留。','',
'| 行为 | 原始候选 | 目标 | A通过次数/有效分母 | B通过次数/有效分母 |','|---|---|---|---:|---:|']
for k in v['item_order']:lines.append(f"| {k} | {'通过' if v['original_candidate'][k] else '失败'} | {'是' if k in v['targets'] else ''} | {g['A']['per_behavior_pass_counts'][k]}/{g['A']['valid_denominator']} | {g['B']['per_behavior_pass_counts'][k]}/{g['B']['valid_denominator']} |")
lines+=['','相对原始候选21项原正确行为的损失：','']
for x in s['per_slot']:lines.append(f"- {x['slot']}："+('、'.join(x.get('original_correct_losses',[])) or '无')+'。')
lines+=['','块内B相对A的描述性得失（不是同一采样种子，不据此断言单次因果）：','']
for x in v['block_comparisons']:lines.append(f"- 块{x['repeat']}：新增通过 {', '.join(x['B_gains_over_A']) or '无'}；新增损失 {', '.join(x['B_losses_against_A']) or '无'}。")
lines+=['','补丁范围与无据改动由本会话代码复核（无独立人工审阅、未另调用评委模型）：','']
for x in scope['runs']:lines.append('- '+x['slot']+'：'+x['review'])
lines+=['','| 成本 | A | B |','|---|---:|---:|', '| 实际请求 started | '+cost('requests_started')+' |','| 请求 completed | '+cost('requests_completed')+' |','| 阻止的派发 | '+cost('blocked_dispatches')+' |','| 工具调用 | '+cost('tool_calls')+' |',f"| 会话秒数 | {g['A']['seconds']:.2f} | {g['B']['seconds']:.2f} |"]
for key in ['input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens']:lines.append(f"| {key} | {g['A']['observed_tokens'][key]} | {g['B']['observed_tokens'][key]} |")
lines+=['',f"成本变化 B-A：请求 {g['B']['requests_started']-g['A']['requests_started']:+d}，工具调用 {g['B']['tool_calls']-g['A']['tool_calls']:+d}，会话时间 {g['B']['seconds']-g['A']['seconds']:+.2f}秒，input tokens {g['B']['observed_tokens']['input_tokens']-g['A']['observed_tokens']['input_tokens']:+d}，output tokens {g['B']['observed_tokens']['output_tokens']-g['A']['observed_tokens']['output_tokens']:+d}。",'',f"合计：{t['sessions']}个维护会话、{t['requests_started']}次底层请求、{t['tool_calls']}次工具调用、{t['seconds']:.2f}会话秒。计量缺失：{t['usage_incomplete']}。缓存输入和reasoning输出是各自总量子集，不能重复相加；不估算货币费用。主控聊天准备/分析本身的平台token与请求不可见，不计入维护成本，也不声称为0。",'',
'本轮正式调用只包含授权维护会话。Contract提取、GEPA、反思、经验生成、额外模型评委、隐藏模型预跑和重试均为0；离线准备阶段维护执行与评分重跑为0。正式外部评分每已启动槽位一次，没有评分补跑。','',
f"完整性检查：{integ['status']}，{integ['frozen_files']}份冻结文件及{integ['protected_files']}份既有文件摘要核验通过；原始候选、最终快照/工作区、评分输入及评分前后摘要一致。每槽 SHA清单核验、实际prompt、模型与计量核验均保留于 integrity-validation.json。",'',
'限制：各组三次，只是同题探索性后续；已经看过该案例的开发结果，不能称独立测试、新题泛化、稳定有效或统计显著，也不能据此概括自进化整体成功/失败。调度种子不控制模型随机性；经验增加了上下文长度，成本以实际计量报告。不能声称已经节省请求或提高普遍修复率。后续可比结论需要采用同版运行器的额外对照，但本次不自动追加任何运行或更新生产经验库。','',
'材料：PLAN.md、sources.json、protocol.json/sha256、schedule.json、prompts/、offline-validation.json、actual-schedule.json、runs/*/archive/{events.jsonl,stderr.log,patch.diff,final-candidate,score,usage.json,receipt.json,ARTIFACTS.sha256}、behavior-vectors.json、behavior-counts.csv、summary.json、scope-review.json、integrity-validation.json、ARTIFACTS.sha256。','',
'推荐提交（仅建议，未创建提交）：','', '```text','research: record frozen-experience same-case follow-up','', 'Reuse the frozen low repair runner and unchanged experience for six blocked A/B sessions.', 'Archive prompts, patches, unchanged oracle scores, behavior vectors and usage.', 'Document exploratory admission change, regressions and small-sample limits.','```','']
(A/'REPORT.md').write_text('\n'.join(lines))
(A/'COMMIT_MESSAGE.txt').write_text('research: record frozen-experience same-case follow-up\n\nReuse the frozen low repair runner and unchanged experience for six blocked A/B sessions.\nArchive all prompts, patches, oracle scores, behavior vectors and usage.\nDocument the exploratory admission change and small-sample limits.\n')
print('REPORT.md written')
