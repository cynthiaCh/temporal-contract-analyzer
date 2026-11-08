import pathlib as P,json,csv,hashlib,shutil,importlib.util,re
O=P.Path(__file__).resolve().parent;sp=importlib.util.spec_from_file_location('e',O/'execute.py');e=importlib.util.module_from_spec(sp);sp.loader.exec_module(e);r=e.r;save=r.save
s=r.read(O/'summary.json');rows=r.read(O/'actual-schedule.json');assert len(rows)==14 and s['valid_maintenance']==12 and not s['anomalies']
# Evidence flags refer to actual Resource-level commands, never inferred from the final report.
notes={
'c1-r1-A':([20,23],True,False,False,False,False,'event23 prints close cancellation success before later git command exits128; no Vue mount in model self-test'),
'c1-r1-B':([17],True,True,True,False,False,'current ready delivered before old ready; queued-close stale callback forced; lifecycle test success printed before git exits129'),
'c1-r2-A':([16],False,False,False,False,False,'only pending/pending/ready; no close or reopen driven'),
'c1-r2-B':([16],True,False,True,False,False,'old pending after reopen ignored, current pending then queue-close; no forced cancelled callback; success before git exits129'),
'c1-r3-A':([16,21],True,True,False,False,False,'queued-close cancellation and forced old callback; no response interleaving'),
'c1-r3-B':([19],True,True,False,False,False,'queue-close then force old callback then reopen; earlier event16 bad scheduler accounting corrected, source patch unchanged'),
'c2-r1-A':([19],True,False,False,False,True,'queued close and queued dispose; first attempt used unsupported Node flag; no stale response across reopen'),
'c2-r1-B':([22],True,False,False,False,True,'queue-close then reopen current ready, plus dispose-before-pending response; no old/current response interleaving'),
'c2-r2-A':([16,18,27],True,True,False,False,False,'queue-close then forced callback; extra requests used to archive own patch'),
'c2-r2-B':([19],True,True,False,True,True,'queued old retry forced across reopen; current ready; queued dispose and forced old callback'),
'c2-r3-A':([19],True,True,False,False,False,'queue-close forced callback; unsupported Node flag corrected; later patch-archive work'),
'c2-r3-B':([19],True,False,False,False,True,'queue-close then reopen sequential ready and queued dispose; no forced old callback or response interleaving; --check parsed ESM as CJS before correction')}
review={}
for slot,(events,close,forced,response,retry,dispose,note) in notes.items():
 review[slot]={'successful_test_event_lines':events,'resource_close_without_dispose':close,'retry_queued_before_close':close,'forced_old_callback_after_close':forced,'old_response_after_reopen':response,'old_retry_callback_after_reopen':retry,'dispose_test':dispose,'actual_Vue_component_mounted_in_model_selftest':False,'background_policy_test_in_model_selftest':False,'note':note}
save(O/'mechanism-review.json',{'method':'AI-assisted manual reading of actual tool commands/output and patch; no new model calls or candidate executions. Flags apply only to driven test paths, not proofs. Full command evidence and native Vue scoring remain separate.','slots':review})
aggregate={g:{'requests':0,'tools':0,'shell_commands':0,'seconds':0,'usage':{k:0 for k in s['total_cost']['usage']}} for g in ['A','B']}
for cid,case in s['cases'].items():
 for g in ['A','B']:
  c=case['groups'][g]['cost']
  for k in ['requests','tools','shell_commands','seconds']:aggregate[g][k]+=c[k]
  for k in c['usage']:aggregate[g]['usage'][k]+=c['usage'][k]
 vals=[r.sha(O/'runs'/d['slot']/'workspace/src/session.js') for d in rows if d['case']==cid and d['phase']=='repair'];case['all_six_source_repairs_identical']=len(set(vals))==1;case['source_repair_sha256']=vals[0]
 assert case['all_six_source_repairs_identical'] and all(p['all_raw_effects_equal'] for p in case['pairs'])
s['maintenance_aggregate']=aggregate;s['maintenance_B_minus_A']={**{k:aggregate['B'][k]-aggregate['A'][k] for k in ['requests','tools','shell_commands','seconds']},'usage':{k:aggregate['B']['usage'][k]-aggregate['A']['usage'][k] for k in aggregate['A']['usage']}}
s['conclusion']='No observed behavior or patch benefit: both cases A/B 3/3 PASS and all paired raw effects equal. Some actual verification coverage expanded with E1; aggregate requests/time lower, uncacheable input and reasoning output higher, not causal/stable efficiency evidence. Target-model hardness and ceiling control remain unestablished because selection failures were Qwen bare-task runs.'
save(O/'summary.json',s)
with (O/'paired-comparisons.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['case','repeat','A','B','effects_equal','B-A requests','B-A tools','B-A seconds','B-A input','B-A output'])
 for cid,c in s['cases'].items():
  for p in c['pairs']:
   z=p['B_minus_A'];w.writerow([cid,p['repeat'],p['A'],p['B'],p['all_raw_effects_equal'],z['requests'],z['tools'],z['seconds'],z['usage']['input_tokens'],z['usage']['output_tokens']])
for c in r.cases():
 src=P.Path(c['source_case']);d=O/'source'/c['case'];d.mkdir(parents=True,exist_ok=True)
 for rel in ['case.json','provenance/source-record.md']:
  if (src/rel).exists():shutil.copyfile(src/rel,d/P.Path(rel).name)
(O/'CONTRACT_AND_E1.md').write_text('''# 固定材料索引

E1-v1逐字原样，SHA 57527138a98bfa0d34a432ca82e7b863694b33818aa5a9a3c032ad69f4aaed1e；原文、来源运行及批准记录均保留。原文旧“待专家确认”字样不覆盖已有批准及本次明确授权。不改经验，不写生产库。

两个case各只新增一次固定K1自动提取，gpt-6-sol/low。只将原报告第1栏正文交付给维护Agent，其他栏目不交付；完整报告不删改，来源/任务/候选/配置与全文和正文哈希见contracts/<case>/freeze.json。每例A/B及三重复共享此正文。A/B实际提示逐字核对：B只在A尾部追加E1，冻结在该例首个维护评分之前。本索引为事后说明，不替换冻结文本。
''')
header='''# 固定 E1：同 cluster 历史失败派生任务验证

**未观察到加入E1后的修复行为增量。** 两例均为A/B各3/3 PASS，全部配对原始effect向量相同，各例六份源码补丁逐字相同。观察到部分实际自检覆盖增加；成本并非全维增加，不能作稳定或因果效率结论。本轮的历史难度证据来自另一个模型，不能称已成功控制目标Terra的天花板。

## Task 1：来源、筛选及准入

cluster登记canonical arm为`download-polling-restoration-react18`；E1来源是`low-cue-react18` arm的u02/M运行，不是canonical核心。该运行读取close/reopen后，只验证正常完成和卸载；最终代码只有mounted/active守卫，关闭/重开的事件没有相应验证。旧low-cue精确关闭评分存在输入政策缺口，E1只提炼“公开事件与实际验证对应”，不携带统一取消要求。来源及批准见source-relationship.json、experience-source/、EXPERIENCE.md和experience-approval.json。

事前冻结两例：`explicit-vue2-eval-v2`、`explicit-vue3-eval-v2`。它们经explicit React18 arm合成派生并经eval-v2修订，共享同一来源单元；不是从u02补丁直接生成，也不是独立来源。两例的核心Resource逻辑高度相同，差异主要在Vue presenter/框架及业务背景；不能把两例或三重复算成独立事故样本。eval-v2曾受既有目标模型结果影响，已经研究暴露，不是holdout。

|预选例|历史模型/设置|输入条件与有效失败|实际失败关系|限制|
|---|---|---|---|---|
|explicit-vue2-eval-v2|Qwen3-coder:30b、effort未指定、temperature0；v4与quality-v5各1次|裸任务，各1有效/1失败，当前相同起点|均未接入前台轮询，排队关闭/卸载场景也因未排队而失败；v4 TASK_DONE未交付源码补丁，v5修改session但仍缺调度|两套prompt/工具workflow，不能称同输入重复；不是自动Contract组失败|
|explicit-vue3-eval-v2|同上，v4与quality-v5各1次|裸任务，各1有效/1失败，当前相同起点|均未接入前台轮询；v4还错误迁移后台start，违反原保持隐藏/既有活动政策|同上；与E1来源的验证替代共享相关机制，但未证明历史失败根因相同|

四份历史会话逐件验证TASK_DONE、exit0、零工具格式恢复、所有服务调用HTTP200、非上限终止；输入树及最终candidate摘要一致，实际prompt SHA一致。用**当前未改原oracle**重放，原effect向量全部精确相等。Vue2未交付补丁的一次是实际模型会话失败，非拿未修改代码校准冒充历史失败；其证据强度单列。完整逐行表见historical-selection.csv、verified-history.json和history/；历史不同模型、effort、起点、异常与归档副本不合并。history-survey仅为分层元数据调查，不冒称每条均已完整认证。

**难度证据降级：**没有找到所选两例在固定K1自动Contract、无E1下反复失败的历史。目标Terra/medium对每例裸任务和人工Contract各1次已PASS；每个不同输入条件各一次不足以称自动组稳定通过，但已提示天花板风险。不能把Qwen失败升级为Terra自动组仍困难，也不把历史人工Contract称为自动输出。选例因历史失败而有条件性选择偏差。explicit-react18最近相同自动组3/3全过明确排除；low-cue来源及canonical arm存在候选可见前台关闭政策缺口，未强行采用隐藏评分规格；上限/服务/工具异常排除。没有按本轮B结果换例、删例或造变体。

可见政策：DialogResource.close调用invalidate，增加generation、清timer/retry/loading；reopen开启新代；dispose失效并清资源。WorkspaceJob.close只隐藏，start保留其特有的已有行为，不能套前台取消/显示重置；后台dispose的loading快照政策也按代码保留。原任务要求pending继续、ready才交付；新增轮询必须接入既有代际和调度边界。两例的起点、通过参考及六错误变体各8次零模型校准全部符合预期（起点UNDERREACH、bounded PASS、mutants全部检出），另有4次历史原评分重放。不改评分和政策，不因旧作者review-pending字段机械阻断已有可见依据。

## Task 2：冻结、执行和分母

每例新增一次自动Contract提取：c1-x01=4请求/39.5秒，c2-x01=3请求/33.4秒。固定K1及gpt-6-sol/low，只见原任务与候选；没有E1、人工Contract、评分或历史答案。完整原报告保留，按既有规则机械取第1栏正文，不编辑、不补齐其他栏目。每例正文/全文/SHA/来源及A/B实际提示在该例首次维护评分前冻结；见contracts/<case>/freeze.json和prompts/。A/B及三重复用同一正文；B唯一差异为尾部逐字追加批准的E1-v1，无额外案例提醒/脚本/角色提示。

维护全部gpt-5.6-terra/medium；提取gpt-6-sol/low；priority显式配置，hook核对实际型号；服务路由未独立认证。原生Codex自主工具循环，复用修复后读取策略，无实验ReAct。种子2026110804只控制顺序，串行；各槽独立副本从本例相同冻结起点开始。准确命令、独立profile配置摘要、完整prompt、事件、meter及源码正文证据逐槽归档。执行模型不挂研究侧标准/评分/reference/历史或其他槽位。

正式14/14顶层会话结束（2提取+12维护），12/12维护有效、格式有效、评分有效，未启动0、异常0、预算/服务失败0；无反思、技能更新、GEPA、预跑、重试或补跑。按计划结束，没有第三例。每维护24请求/600秒、提取12请求/600秒，全局312请求；实际总109请求，最长维护135.7秒。最终report上限6000 Unicode字符、stdout16MiB，无已核验推理token硬上限。正式读取证据全部计入本轮预算。

|案例|A整体|B整体|原评分向量差异|源码补丁|
|---|---|---|---|---|
|Vue2|3/3 PASS|3/3 PASS|三个配对全部相同|六份完全相同|
|Vue3|3/3 PASS|3/3 PASS|三个配对全部相同|六份完全相同|

原评分真实挂载Vue2/Vue3，并驱动：多轮pending中loading/retryScheduled/未交付、ready交付及timer清理、关闭但组件未卸载、retry已排队后关闭、关闭后旧pending/ready、旧ready/当前ready交错、当前ready先于旧pending、同token重开、多次重开、dispose在途/排队、后台关闭后继续/ready/排队、后台关闭后再次start及重复start等。上述原断言六槽/例均通过；原通过项丢失0、新增forbidden0。后台保留仅在原覆盖范围及相关源码未改范围内成立，不扩称所有API行为已证明。完整分项、中间快照、consumer/assertion观测保留在每槽score.stdout.json；索引见score-comparison.json和case-results.csv。取消是否绝不会触发旧回调、错误/非法状态及其他未规定行为不新增要求。

## Task 3：实际机制、补丁与成本

12份源码修复全部只改src/session.js：将DialogResource.pending的`this.publish()`换为已有`this.schedule(generation)`。调度器原有generation/disposed守卫、cancel及前后台边界都保留。没有改后台、presenter、公共字段或协议。E1未导致不同的源码修复，也未产生已评分行为收益；额外测试和patch归档文件与共同guard字节码副产物单列，原始diff照留，另有source-only.patch。

下表仅指模型实际Resource类自检，**不是Vue组件挂载测试**。真正Vue挂载是研究侧原评分。类对象close时未dispose不能被自检中的dispose代替，也不能冒称已验证完整UI入口。事件行号对应各槽events.jsonl，完整命令输出另存command-evidence.json。

|槽|成功自检event行|排队后close且未dispose|强触发close后的旧retry|重开后旧在途响应|旧retry跨重开|dispose路径|
|---|---|---|---|---|---|---|
'''
report=header
for slot,v in review.items():
 yn=lambda flag:'是' if flag else '否'
 report+='|'+slot+'|'+','.join(map(str,v['successful_test_event_lines']))+'|'+yn(v['retry_queued_before_close'])+'|'+yn(v['forced_old_callback_after_close'])+'|'+yn(v['old_response_after_reopen'])+'|'+yn(v['old_retry_callback_after_reopen'])+'|'+yn(v['dispose_test'])+'|\n'
report+='''
Vue2：B1相对A1增加跨重开的新/旧ready交错，B2相对只测正常轮询的A2增加旧pending/当前pending及排队关闭；B3比A3多顺序重开，但没有在途旧/当前响应交错。Vue3：两组第一重复都测排队关闭及dispose（前者分别排队/在途），未证B整体更广；第二重复B比A多强触发旧retry跨重开和排队dispose；第三重复A强触发旧retry，B没有，B另测排队dispose。所有自检均未实际测试后台，不能靠文字声称前后台全覆盖。E1对应的查证有部分增加，但不一致，也未改变正确补丁位置或原评分行为。详见mechanism-review.json。

自检/交付中的非零命令完整保留：包括缺esbuild、Node18不支持实验flag、ESM按CJS检查、环境变量遗漏、假调度器没有先移除已执行timer、无Git目录，以及自行制作patch文件的格式修正。这些发生在原会话内，最终会话有效；不删轨迹、不补跑，也不伪称基础设施事故。部分命令在打印自检成功后因随后git命令非零退出，按实际输出和执行代码认定自检片段成功，不把整个命令的退出码改为0。

成本如下，逐配对得失见paired-comparisons.csv，不能从三重复推出稳定效率或因果：

|案例|A/B请求|A/B工具|A/B秒|B−A input|B−A output|
|---|---|---|---|---|---|
'''
for cid,case in s['cases'].items():
 a=case['groups']['A']['cost'];b=case['groups']['B']['cost'];report+=f"|{cid.replace('download-polling-restoration-','')}|{a['requests']} / {b['requests']}|{a['tools']} / {b['tools']}|{a['seconds']:.1f} / {b['seconds']:.1f}|{b['usage']['input_tokens']-a['usage']['input_tokens']:+d}|{b['usage']['output_tokens']-a['usage']['output_tokens']:+d}|\n"
a=aggregate['A'];b=aggregate['B'];z=s['maintenance_B_minus_A'];uncached=(b['usage']['input_tokens']-b['usage']['cached_input_tokens'])-(a['usage']['input_tokens']-a['usage']['cached_input_tokens'])
report+=f'''
维护合计A/B：{a['requests']}/{b['requests']}请求、{a['tools']}/{b['tools']}全部工具（其中shell {a['shell_commands']}/{b['shell_commands']}）、{a['seconds']:.1f}/{b['seconds']:.1f}会话秒。B−A为{z['requests']:+d}请求、{z['tools']:+d}工具、{z['seconds']:+.1f}秒、input {z['usage']['input_tokens']:+d}、output {z['usage']['output_tokens']:+d}；cached input {z['usage']['cached_input_tokens']:+d}、reasoning output {z['usage']['reasoning_output_tokens']:+d}，未缓存input反而{uncached:+d}。E1固定文本增加输入，但实际总调用/总token受自检和归档波动影响，不预设成本必然全增，也不把减少全部归因E1；A的patch归档工作明显贡献若干额外调用。

两次共享提取：7请求、5工具、72.9秒，83957 input（75776 cached）、2966 output（107 reasoning）。全批14会话：109请求、98工具（78 shell）、1218.1会话秒；1424208 input（1183488 cached）、46122 output（19874 reasoning），用量完整。缓存/推理为各自input/output子项，不能重复加总；cache-write为0。未核验单价，不估货币；主聊天准备/分析token不可取得，明确排除而非计0。

**最终回答：**在预先选定、同cluster且有多次有效历史失败的两个派生任务中，未观察到E1比相同自动Contract、不加经验的流程更有效。两组均全过，观察到部分查证覆盖增量和描述性成本下降，未观察到行为或补丁增量、已评分退步。由于历史困难来自Qwen裸任务而本轮Terra自动组本就全过，天花板控制并未成功；不能据此判断E1对目标模型真正困难任务有效或无效。两例核心逻辑相近、历史workflow差异、来源暴露及小样本进一步限制结论。

## 保护与结束

启动前已有上一轮机制实验目录未跟踪，跟踪文件diff为空；未找到适用AGENTS.md。本轮保护旧历史及cluster输入，全局配置始末不变；protection-check.json保存逐件摘要复核及HEAD/status。临时认证、运行及候选副本全部在Git外，认证profile会话结束清理；归档排除凭证并核对各评分候选快照摘要。准备阶段有一次零模型文件清单遗漏package-lock.json，修正后再冻结启动；原失败检查保留，不计正式模型调用。

分析为AI辅助，非独立人工复核。不生成E2、不更新生产经验库、不启动第三例、不创建提交。COMMIT_MESSAGE.txt提供建议subject/body。
'''
(O/'REPORT.md').write_text(report)
(O/'COMMIT_MESSAGE.txt').write_text('research: record fixed E1 transfer on historical cluster failures\n\nFreeze two registered Vue derivatives selected from verified Qwen failures,\nwith explicit limits on target-model and automatic-contract comparability.\nRun one K1 extraction and three paired A/B repairs per case without retries.\nRecord 12 valid PASS results, identical source repairs, mixed verification\ncoverage, full costs and the unresolved target-model ceiling limitation.\nPreserve E1, production, scorers, prior research and global configuration;\nexclude credentials and make no production experience update.\n')
e.archive()
# Include common noncredential runtime bytecode so scored candidate snapshots match exactly.
for f in O.glob('runs/*/workspace/**/__pycache__/*.pyc'):
 q=e.A/f.relative_to(O);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,q)
for f in O.glob('runs/*/workspace/__pycache__/*.pyc'):
 q=e.A/f.relative_to(O);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,q)
checks=[]
for d in rows:
 assert r.hashes(e.A/'runs'/d['slot']/'workspace')==d['candidate_files'],d['slot'];checks.append({'slot':d['slot'],'exact_archived_scored_snapshot':True,'model_match':d['model_match'],'infrastructure_valid':d['infrastructure_valid'],'scoring_valid':d.get('scoring_valid')})
assert not list(e.A.rglob('auth.json'));assert not (O/'.runtime').exists() or not any((O/'.runtime').iterdir())
patterns=[rb'sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{30,}',rb'"(?:access_token|refresh_token|id_token)"\s*:\s*"[^"\s]{20,}"'];hits=[str(p.relative_to(e.A)) for p in e.A.rglob('*') if p.is_file() and any(re.search(pat,p.read_bytes()) for pat in patterns)];assert not hits,hits
r.verify();save(e.A/'archive-audit.json',{'status':'PASS','snapshots':checks,'credential_pattern_hits':0,'auth_filenames':0,'outside_runtime_profiles_removed':True,'frozen_protocol_verified':True,'no_extra_model_or_candidate_execution_during_analysis':True})
files={str(p.relative_to(e.A)):r.sha(p) for p in e.A.rglob('*') if p.is_file() and p.name!='ARTIFACTS.sha256'};(e.A/'ARTIFACTS.sha256').write_text(''.join(h+'  '+p+'\n' for p,h in sorted(files.items())))
print('Archived files',len(files));print('maintenance B-A',s['maintenance_B_minus_A']);print('All cases six identical repairs:',[v['all_six_source_repairs_identical'] for v in s['cases'].values()])
