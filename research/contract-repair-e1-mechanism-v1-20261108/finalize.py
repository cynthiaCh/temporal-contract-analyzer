import pathlib as P,json,hashlib,shutil,difflib,importlib.util
O=P.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('execution',O/'execute.py');x=importlib.util.module_from_spec(spec);spec.loader.exec_module(x);r=x.r
c=r.cases()[0];source=P.Path(c['source_case']);dest=O/'source';dest.mkdir(exist_ok=True)
for rel in ['case.json','provenance/source-record.md']:
 p=source/rel;q=dest/p.name;shutil.copyfile(p,q)
assert r.sha(dest/'source-record.md')==c['provenance']['source_record_sha256']
s=r.read(O/'summary.json');s['conclusion']='No observed repair behavior benefit from E1 within existing scoring coverage; 3/3 vs 3/3 ceiling. Mixed self-verification coverage, conditional static risk in r3-B retained; no generalization or causal claim.'
s['all_scored_effects_equal']=len({json.dumps(z['effects'],sort_keys=True) for z in r.read(O/'score-comparison.json')})==1
s['cost_B_minus_A']={k:s['groups']['B']['cost'][k]-s['groups']['A']['cost'][k] for k in ['requests','tools','shell_commands','seconds']};s['cost_B_minus_A']['usage']={k:s['groups']['B']['cost']['usage'][k]-s['groups']['A']['cost']['usage'][k] for k in s['groups']['A']['cost']['usage']}
r.save(O/'summary.json',s)
notes={
'r1-A':{'test_event':21,'close_mounted':True,'queued_retry_then_close':True,'reopen_old_response':True,'reopen_old_retry':False,'note':'旧ready在新活动启动后到达；关闭排队retry后强制调用旧回调。卸载也测试取消后的旧retry。'},
'r1-B':{'test_event':27,'close_mounted':True,'queued_retry_then_close':True,'reopen_old_response':False,'reopen_old_retry':True,'note':'关闭后在途ready；second排队retry跨reopen(third)强制触发；专门排队后close再强制触发。无在新活动已启动后才到达的旧ready自检。event18漏导入失败，event23修正后通过；event25未先安排当前取消却检查，event27完善。'},
'r2-A':{'test_event':18,'close_mounted':True,'queued_retry_then_close':True,'reopen_old_response':True,'reopen_old_retry':False,'note':'旧ready跨reopen，current pending后close，强制旧retry并检查无新请求。cleanup仅最后调用，未独立断言卸载场景。'},
'r2-B':{'test_event':21,'close_mounted':True,'queued_retry_then_close':True,'reopen_old_response':True,'reopen_old_retry':False,'note':'event19未有排队retry时检查cancel而失败；event21补pending→排队→close→强制旧retry，另测卸载时排队retry。修改的是自检，未再改源码。'},
'r3-A':{'test_event':18,'close_mounted':True,'queued_retry_then_close':True,'reopen_old_response':False,'reopen_old_retry':False,'note':'先排队后close并强制旧retry，再reopen(second) pending→ready。没有新旧在途响应跨重开交错。卸载后重触发的是已执行过的retry，不等同独立排队卸载覆盖。'},
'r3-B':{'test_event':18,'close_mounted':True,'queued_retry_then_close':False,'reopen_old_response':True,'reopen_old_retry':False,'note':'close后的旧ready；c→d旧ready/当前ready；卸载后在途ready。没有排队retry后close或旧retry跨reopen。check入口guard在retry回调共享写入之后，条件性风险见REPORT；未新增动态断言。'}}
r.save(O/'mechanism-review.json',{'method':'研究侧静态逐命令阅读；未新增模型或候选执行，未把观察清单发给任何条件。布尔仅指实际自检驱动，不代表完整证明或评分。','slots':notes})
for d in r.read(O/'actual-schedule.json'):
 if d['phase']!='repair':continue
 p=O/'runs'/d['slot'];base=O/'materials'/c['case']/'candidate';parts=[]
 for f in base.rglob('*'):
  if f.is_file() and r.sha(f)!=r.sha(p/'workspace'/f.relative_to(base)):
   rel=str(f.relative_to(base));parts+=difflib.unified_diff(f.read_text().splitlines(True),(p/'workspace'/rel).read_text().splitlines(True),fromfile='a/'+rel,tofile='b/'+rel)
 (p/'source-only.patch').write_text(''.join(parts))
report='''# 固定 E1 机制匹配开发实验

结论：在这个机制匹配的开发案例中，未观察到 E1 相比仅用自动 Contract 的修复行为收益。A/B 各3次均PASS，原评分全部10个effect的布尔结果完全相同，属于现有评分天花板。E1组查证覆盖并未一致增加，并保留一处评分外的条件性静态风险。该结果不能证明E1无效、稳定、因果或独立泛化。

## Task 1：机制匹配、政策与准入

唯一案例 `download-polling-restoration-explicit-react18` 是U2经验来源的显式同源变体、clean-room authored开发案例。E1源于历史修复读到close/reopen却仅验证正常完成和unmount；本例具有相同的请求/排队/仍挂载关闭/重开交错机制，同时候选显式给出generation、retryHandle与invalidateOnClose，便于在可见政策范围内验证。不是独立泛化测试，原经验未修改。

任务只要求pending持续检查、ready后交付。前台DownloadDialog传入`invalidateOnClose:true`，close调用beginGeneration，取消已记录retry并清loading；回调已按generation/disposed失效。reopen更换token并开始新generation；unmount设disposed且清理。后台close仅隐藏面板，工作继续；后台卸载以active=false和clearRetry处理。通用hook的默认invalidateOnClose=false不能推定为同一取消政策。未要求真实网络中止，也未增加错误/无效状态/同token重开等规范。

原任务SHA、6个候选文件、case manifest及6个oracle文件全部与历史cohort匹配；来源记录SHA也一致。复用4项可信零模型校准：unchanged=UNDERREACH（缺等待与持续检查），reference-bounded=PASS，retry-without-invalidation=UNDERREACH，shared-dialog-policy=UNDERREACH_AND_OVERREACH。原low-cue关闭政策争议不移植到本例；cohort的旧awaiting_scope_review状态由本次明确指令和可见政策审查落实，不修改旧档。见[准入](admission.json)、[来源及校准绑定](cohort.json)、[原始校准](calibration/)、[来源原文](source/source-record.md)。没有重跑或改写评分。

## Task 2：冻结、执行与有效分母

没有匹配的有效自动Contract；旧同例x01提取无效，不复用。新增一次固定K1提取，gpt-6-sol/low，实际3请求、41.8秒；提取只见原任务和候选。真实成功工具输出含候选正文，未误拒普通读取循环。按固定四标题机械取第1栏，完整报告保留且未人工编辑；提取源码未改变。冻结正文、SHA、来源、提取提示/配置、A/B提示后才启动任何维护评分。Contract正文较简略，说明pending/ready和活动归属；其余三栏未加入维护提示，也未人工补齐。见[原报告](contracts/download-polling-restoration-explicit-react18/full-report.md)、[冻结](contracts/download-polling-restoration-explicit-react18/freeze.json)。

A=原任务+上一批公共指令+自动Contract；B只在A结尾逐字追加E1-v1。SHA `57527138a98bfa0d34a432ca82e7b863694b33818aa5a9a3c032ad69f4aaed1e`；批准原记录和本次授权均保留。没有案例专用外部提醒、研究测试清单、角色提示或预期补丁。两组都要求修改候选并实际验证。

维护模型全部gpt-5.6-terra/medium，提取gpt-6-sol/low，priority显式配置，hook核对实际型号；服务路由不独立认证。全局配置没改。种子2026110803只控制调度，实际顺序为x01、r1-A、r1-B、r2-A、r2-B、r3-A、r3-B；串行且每槽从相同6文件摘要起点复制。所有运行、候选副本、认证profile和临时文件均在Git仓库外；归档只含筛选产物，排除认证目录、auth.json和凭证。旧runner未启动，未复用历史上下文。

预算7会话/156请求；实际7会话/78请求，6/6维护有效、评分有效、交付格式有效；提取1/1有效；未启动0、无效0、基础设施或评分异常0、资源上限失败0。无预跑、反思、补跑、GEPA、扩例或第二批。每维护≤24请求/600秒、提取≤12请求/600秒，实际维护9/11/17/8/9/21请求，最长215.9秒。report上限6000 Unicode字符、事件输出16MiB，沿用已验证读取后端；没有已验证推理token硬上限。

|配对|A原评分|B原评分|A/B请求|B−A工具调用|B−A秒|
|---|---|---|---|---|---|
|1|PASS|PASS|9 / 11|+2|+58.6|
|2|PASS|PASS|17 / 8|−9|−77.4|
|3|PASS|PASS|9 / 21|+12|+83.6|

评分分项：持续pending检查、ready后一次完成、中间loading/retryScheduled/未完成状态、close后旧pending、close后旧ready、reopen后旧ready及当前ready、后台active轮询、后台关闭后继续，六槽全部满足既有断言；新增forbidden=0、原通过项丢失=0。`background-close-cancels-work`原始effect均false（不是应当为true的成功项）。评分等待断言直接检查首次pending；第二次等待快照保留但无单独完整等待状态断言；最终ready的retry flag也无独立全字段断言，不能扩称所有中间/最终状态已验证。

“retry已排队后关闭”没有专门原评分场景；卸载仅用于worker结束清理，无独立评分断言；同token重开、错误、无效状态、并发start等均未下动态结论。后台和其他原行为只在原oracle覆盖及源码未改范围内报告，不声称全面回归。见[逐effect/状态](score-comparison.json)和各槽原始score.stdout.json。

## Task 3：查证、补丁、行为和成本

全部6槽实际自检都调用close且当时未卸载；没有单纯用unmount代替close。自检均用React hook替身和可控Promise/调度器，不能等同真实React渲染集成测试；研究评分另用原React18运行时，未向维护模型开放。

|槽|成功自检event行|仍挂载close|排队retry后close并强触发旧回调|重开后旧在途响应|旧retry跨reopen|
|---|---|---|---|---|---|
|r1-A|21|是|是|是|否|
|r1-B|27|是|是|否|是|
|r2-A|18|是|是|是|否|
|r2-B|21|是|是|是|否|
|r3-A|18|是|是|否|否|
|r3-B|18|是|否|是|否|

表中“否”指未见该槽模型自检实际驱动，不表示代码或原评分失败；详见[机制复核](mechanism-review.json)及各槽command-evidence.json（对应events.jsonl行号）。关闭后的旧pending等原评分覆盖不补算成模型查证。

配对1：A已测排队关闭和跨重开的旧ready；B增加旧retry跨重开，未见跨重开旧ready自检。B第一次因漏导入schedulePreparationRetry自检失败后修正，再修正取消断言的场景安排；最终通过。B增加显式PENDING判断，并把reopen的beginGeneration前移，A直接对非READY重试；可见协议仅false/true，此差异没有已评分收益。

配对2：两组核心源码同为导入调度、pending登记retry、ready清retry和回调先guard后写共享状态。B初版没有排队却断言取消，补足真正排队关闭及排队卸载自检后通过；未因此再改源码。A大量调用用于自行生成/修正补丁文件，B本对耗时和调用更少，不能把所有成本差异都解释为E1清单开销。

配对3：A直接在retry回调任何共享写入之前检查generation/disposed，并实际测排队关闭。B把guard加在check入口，retry回调先清`retryHandle`和`retryScheduled`再调用check；其自检测旧ready和换token，却漏排队关闭及旧retry跨重开。如果取消不保证已排队回调绝不再触发，旧回调可能先清掉新活动的retry句柄/标志，随后才被check入口guard挡住。该条件性静态风险在A补丁中有先写前guard防护，B没有；原服务取消保证未明确、原评分未覆盖，所以不宣称已动态证实退步，也不让PASS将其掩盖。没有为追求结论追加评分。B也花较多请求修正自行制作的补丁文件。

六份源码修复都只改src/usePreparation.js，后台/组件/API等原候选文件未改。原始diff包含guard生成的`__pycache__/read_policy.cpython-38.pyc`附带文件（6槽均有，不是经验或模型补丁），r2-A/r3-B还生成自己的patch文件；完整保留，另供source-only.patch便于审核。原冻结起点6文件摘要未受这些新文件影响。

|维护成本|A三次合计|B三次合计|B−A|
|---|---|---|---|
|底层请求|35|40|+5（+14.3%）|
|全部工具调用（hook）|32|37|+5|
|其中shell命令|23|26|+3|
|会话秒|428.0|492.8|+64.8（+15.2%）|
|input tokens|518288|637464|+119176|
|其中cached input|465152|554496|+89344|
|output tokens|15766|19643|+3877|
|其中reasoning output|8650|7446|−1204|

提取共享成本：3请求、2工具、41.8秒、36925 input（31744 cached）、1481 output（58 reasoning）。全批：78请求、71工具（51 shell）、962.6会话秒；1192677 input（1051392 cached）、36890 output（16154 reasoning），用量完整。缓存是input子项、推理是output子项，不能重复相加；cache_write均0。单价未核验，不估货币；主聊天准备/分析token无法取得，明确排除，不称为0。完整成本及配对差见summary.json、paired-comparisons.csv、逐槽receipt和meter。

因此，E1改变了部分查证安排和局部补丁，但没有产生本轮评分可观察的修复收益，也没有一致扩大检查覆盖；总体成本增加。保留天花板、混合覆盖与条件性风险，不更换案例，不生成E2，不更新生产经验库。

## 保护与交付

仓库及父级未找到适用AGENTS.md；运行前git status/diff干净。1980个既有历史文件逐字摘要复核未变，全局配置SHA/mtime未变，Git仅新增本实验目录，无提交。认证profile仅在仓库外使用且会话结束删除，归档无auth.json。准备时曾误用task.md路径，按case manifest修正为core_prompt后完成零模型准入；该准备错误未产生正式调用或覆盖任何历史。基础设施停止条件未触发。零模型正文检查、配置、完整提示、冻结来源、轨迹、patch、评分和成本均归档；无新增候选执行或模型分析会话。

建议Git commit subject/body见COMMIT_MESSAGE.txt；未创建提交。
'''
(O/'REPORT.md').write_text(report)
(O/'CONTRACT_AND_E1.md').write_text('''# 冻结材料说明

自动Contract来自唯一x01，机械提取完整报告第一栏，未编辑；内容概括pending/ready及活动归属。完整来源/摘要与A/B提示哈希在contracts/download-polling-restoration-explicit-react18/freeze.json（维护前冻结）。其余三栏不作为维护辅助材料。E1-v1逐字复用已批准版本，SHA 57527138a98bfa0d34a432ca82e7b863694b33818aa5a9a3c032ad69f4aaed1e；原文保留旧“待专家确认”措辞，experience-approval.json与本次用户指令确定当前使用授权。A/B差异仅B结尾追加该原文。没有提取增强、经验改写或生产采纳。本说明是事后索引，不替换冻结材料。
''')
(O/'COMMIT_MESSAGE.txt').write_text('research: record fixed E1 matched-case repair ceiling\n\nRun three serial paired automatic-contract versus exact E1-v1 repairs on\ndownload-polling-restoration-explicit-react18 with one frozen K1 extraction.\nBoth conditions pass 3/3 under unchanged calibrated scoring; retain mixed\nverification coverage and the unscored conditional stale-retry risk in r3-B.\nArchive prompts, configuration, traces, patches, scores and complete usage.\nPreserve prior research, E1, scorers and global config; exclude auth/runtime\ncredentials. No GEPA, retries, expanded cases or production skill updates.\n')
x.archive()
files={str(p.relative_to(x.A)):r.sha(p) for p in x.A.rglob('*') if p.is_file() and p.name!='ARTIFACTS.sha256'}
(x.A/'ARTIFACTS.sha256').write_text(''.join(h+'  '+p+'\n' for p,h in sorted(files.items())))
print('Final archived files:',len(files));print('same effects:',s['all_scored_effects_equal']);print('B-A:',s['cost_B_minus_A'])
