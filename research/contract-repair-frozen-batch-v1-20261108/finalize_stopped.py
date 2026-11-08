"""Finalize this stopped batch without changing its frozen runner or inputs."""
import csv, hashlib, json, subprocess
from pathlib import Path

O=Path(__file__).resolve().parent;R=O.parent.parent
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,x):(O/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')

def main():
 actual=read(O/'actual-schedule.json');cohort=read(O/'cohort.json')['cases']
 assert len(actual)==2 and all(r['phase']=='extract' and r['status']=='INVALID' for r in actual)
 assert [r['slot'] for r in actual]==['x01','x02']
 assert not (O/'automatic-contract-freeze.json').exists()
 assert not (O/'first-formal-gate.json').exists()
 approval=read(O/'experience-approval.json');assert approval['status']=='confirmed' and approval['experience_sha256']==sha(O/'EXPERIENCE.md')
 protocol=read(O/'protocol.json');assert all(sha(f)==h for f,h in protocol['files'].items())
 index={r['slot']:r for r in actual};extractions=[]
 for n,c in enumerate(cohort,1):
  slot='x%02d'%n;rec=index.get(slot)
  row={'slot':slot,'case':c['case'],'source_group':c['source_group'],'status':rec['status'] if rec else 'NOT_STARTED','failure_class':'infrastructure_tool_policy_mismatch' if rec else None,'not_started_reason':None if rec else 'batch_stopped_after_two_consecutive_infrastructure_failures','contract_delivered':False,'full_source_body_gate_passed':False if rec else None,'requests':rec['native']['started'] if rec else None,'completed_requests':rec['native']['completed'] if rec else None,'completed_tool_items':rec['tools'] if rec else None,'hook_tool_attempts':rec['native']['tool_attempts'] if rec else None,'blocked_tool_calls':rec['native']['blocked_tools'] if rec else None,'seconds':rec['seconds'] if rec else None,'input_tokens':rec['usage']['input_tokens'] if rec else None,'cached_input_tokens':rec['usage']['cached_input_tokens'] if rec else None,'cache_write_input_tokens':rec['usage']['cache_write_input_tokens'] if rec else None,'output_tokens':rec['usage']['output_tokens'] if rec else None,'reasoning_output_tokens':rec['usage']['reasoning_output_tokens'] if rec else None}
  extractions.append(row)
 with (O/'extraction-results.csv').open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(extractions[0]));writer.writeheader();writer.writerows(extractions)
 rows=list(csv.DictReader((O/'case-results.csv').open()));assert len(rows)==80 and all(r['status']=='NOT_STARTED' for r in rows)
 for row in rows:row['not_started_reason']='batch_stopped_during_extraction_after_two_consecutive_infrastructure_failures'
 with (O/'case-results.csv').open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
 slots=[{'slot':r['slot'],'case':r['case'],'phase':'extract','status':r['status'],'reason':r['failure_class'] or r['not_started_reason']} for r in extractions]+[{'slot':r['slot'],'case':r['case'],'condition':r['condition'],'repeat':r['repeat'],'phase':'repair','status':r['status'],'reason':r['not_started_reason']} for r in rows]
 save('slot-status.json',{'slots':slots,'planned':90,'launched':2,'valid':0,'invalid_extraction':2,'not_started':88,'no_replacement_or_automatic_retry':True})
 costs=read(O/'costs.json');costs['enhancement_experience']={'expert_confirmation':'confirmed E1-v1','separate_generation_or_reflection_calls':0,'enhanced_repair_sessions':0,'extra_enhancement_model_tokens':0,'note':'E1 authored by the main executor in the prior preparation turn; no separately metered experiment model call for authoring. Main-chat orchestration/authoring tokens are not exposed by the CLI meters and not claimed zero.'}
 costs['accounting_scope']='Native experiment CLI requests only; five completed requests fully have PostModelRequest usage. Main assistant preparation/analysis/chat tokens and human time are unavailable, excluded rather than invented.'
 costs['failed_extractions_included']=True;save('costs.json',costs)
 summary=read(O/'summary.json')
 summary.update(status='STOPPED_INFRASTRUCTURE_BEFORE_MAINTENANCE',experience=approval,launched_extractions=2,valid_extractions=0,invalid_extractions=2,not_started_extractions=8,launched_maintenance=0,valid_maintenance=0,invalid_maintenance=0,not_started_maintenance=80,costs=costs,stopping_reason='Two consecutive research-side extraction command-guard failures; native CLI killed on read-only shell loops.',automatic_retries=0,automatic_reruns_after_fix=0,completed_experiment=False)
 summary['comparisons']={'H_vs_N':None,'M_vs_H':None,'E_vs_M':None,'reason':'No maintenance condition launched; valid maintenance denominator zero. Extraction guard failures do not measure Contract correctness or E1 effects.'}
 summary['per_source']={group:{'cases':[c['case'] for c in cohort if c['source_group']==group],'extraction_launched':sum(r['source_group']==group and r['status']!='NOT_STARTED' for r in extractions),'extraction_valid':0,'maintenance_planned':8*sum(c['source_group']==group for c in cohort),'maintenance_launched':0,'maintenance_valid':0,'behavioral_results':None} for group in ['same_source_variant','other_source']}
 summary['exceptions']=[{'slot':r['slot'],'case':r['case'],'failure_class':'infrastructure_tool_policy_mismatch','exit_code':r['exit_code'],'raw_receipt':str(O/'runs'/r['slot']/'receipt.json'),'raw_events':str(O/'runs'/r['slot']/'events.jsonl')} for r in actual]
 summary['patch_scope_review']={'historical_H_u03':'unsupported :dialog token convention; potential untested regression, not erased by PASS','this_batch':'No maintenance patches; review not applicable, not certified clean.'}
 save('summary.json',summary)
 save('execution-config.json',{'frozen_protocol_sha256':sha(O/'protocol.json'),'frozen_config_sha256':sha(O/'frozen-config.json'),'approval':approval,'actual_extraction_models':sorted({e['event']['model'] for r in actual for e in read(O/'runs'/r['slot']/'meter/ledger.json')['events'] if e['event'].get('hook_event_name')=='PostModelRequest'}),'extraction_effort':'low explicitly in archived argv and profile','repair_model_planned':'gpt-5.6-terra','repair_effort_planned':'medium','repair_model_actually_called':False,'service_tier':'priority configured; server route not independently attested','guard_and_runner_changes_after_launch':False,'model_switches':0})
 save('launch-and-stop.json',{'approval_received':'User: 确认 E1-v1','launch_order':['x01','x02'],'maintenance_schedule_used':False,'stop_threshold':2,'observed_consecutive_infrastructure_failures':2,'stop_applied':True,'remaining_slots':88,'future_batch_not_authorized_as_automatic_retry':True})
 save('scope-review.json',{'maintenance_patches':[],'reason':'No maintenance slots launched, so no new patch can receive a scope PASS. Historical u03 finding remains in DIAGNOSIS.md.','new_unsupported_conventions':None,'new_behavioral_regressions':None})
 with (O/'scope-review.csv').open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=['slot','condition','scope_status','evidence']);writer.writeheader()
  writer.writerows({'slot':r['slot'],'condition':r['condition'],'scope_status':'NOT_APPLICABLE_NOT_STARTED','evidence':'No patch delivered; batch stopped during extraction.'} for r in rows)
 commit='''research: diagnose U2 failures and archive stopped frozen batch

Trace the archived U2 close/reopen failures through delivered Contracts,
source reads, patches, visible validation and original scoring. Flag the
unsupported :dialog convention and preserve historical policy uncertainty.

Freeze ten source-grounded cases, four repair conditions and full-batch limits;
record explicit E1-v1 confirmation. Archive both failed extraction sessions,
all five native requests and usage, and the read-command guard diagnosis.
Apply the predeclared infrastructure stop with eight extractions and all
eighty maintenance slots unstarted. Do not retry, alter frozen inputs,
claim behavioral gains, or change production, scorers or global settings.
'''
 (O/'COMMIT_MESSAGE.txt').write_text(commit)
 report='''# 固定经验批量对照：基础设施停止，行为效果不可评价

2026-11-08（Asia/Shanghai）。本轮按预先冻结规则执行，**发起2/10次提取，2次均因研究侧工具门失配无效；0/80个维护槽位启动**。没有四组行为结果，不将无效提取说成模型Contract失败或经验无效。全部失败和未执行槽位保留，没有补跑或选择成功案例。

## Task 1：已有失败究竟在哪一环，经验针对什么

[DIAGNOSIS.md](DIAGNOSIS.md)逐项核对旧模型组唯一有效运行u02的关闭／重开五项失败：应有行为与依据边界、完整提取输出和实际截取M、Agent成功源码读取/判断、最终补丁、真实自检、原始快照/预期、可确认原因和未知。证据索引完整读取200份非运行时历史归档，历史protocol所有文件摘要均匹配。

可确认的链条是：完整提取已识别旧回调写共享状态的风险并保留政策未知；维护交接只取第1栏，丢失风险/未知/验证建议；补丁只在卸载使active失效，close/reopen仍照旧；自检驱动pending→ready与卸载，未驱动关闭／重开。原评分还把输入没有完整规定的关闭政策当必答，故不能判断主要失败就是Contract提取。确定的D（验证未覆盖）与E（评价具体依据不足）并存，因果仍有F；不能凭H相对M得分就认定完整提取遗漏或正确生命周期Contract未落实。

尤其，“重开当前完成一次”原始失败不是当前文件没有完成，而是最终集合同时包含旧、新token。原通过的close-pending项因新retry而丢失，作为历史向量退步保留，但不自动升级为明确产品违规。

人工组u03即便整体PASS，仍新增了无来源的`:dialog` token后缀约定；原H的authorization suffix是授权指令后缀，没有给出此编码，本轮也无授权迁移指令。原测试未触发该分支，记为无依据约定和潜在未测退步，未冒称动态证明。HEAD只读调查未发现替换已冻结实际runner/输入/配置的内容证据，提交来源过程仍未知；未回退用户改动。

单一经验[E1-v1](EXPERIENCE.md)只针对修复验证事件替代：分别驱动有来源的公开事件，卸载不能替代关闭／重开，不把未知政策写成统一取消答案。用户随后明确回复“确认 E1-v1”，[experience-approval.json](experience-approval.json)绑定原文SHA；冻结文件保留生成时“AI提炼，待专家确认”字样，实际确认状态以批准记录为准。没有改经验正文、生成第二版或启动GEPA。

本轮新停止点在提取工具基础设施，尚未到达E1作用的修复阶段；语言经验不能掩盖它。

## Task 2：实际规模、来源、有效性和成本

十例及理由在新评分和正式调用前固定；见[PLAN.md](PLAN.md)、[cohort.json](cohort.json)、[source-scope.json](source-scope.json)。原low-cue U2和旧C1因既有评分要求未决政策暂缓，没有修改旧评分凑数。保留轮询、Promise、监听/解码、异步paint、debounce/flush、timer retry、readiness机制，包含历史困难/不稳定任务及容易任务。50次无模型校准保留全部原始输出：起点均UNDERREACH，bounded reference均PASS，现有mutants均检出；校准不等于政策批准。

经验来源旧U2只作诊断；批内同源显式变体1例、未参与E1提炼的其他来源9例。全部来自历史研究暴露题库，audit/document/error有辅助模板关联。“其他来源”不是独立泛化认证；见[exposure-index.json](exposure-index.json)。逐例及逐来源实际覆盖如下，重复不是独立案例。

|案例|来源|提取状态|维护已启动/计划|
|---|---|---|---:|
|download-polling-restoration-explicit-react18|U2同源变体，开发诊断|x01基础设施无效|0/8|
|audit-commit-attribution-vanilla|其他来源，未用于E1提炼|x02基础设施无效|0/8|
|transfer-progress-composition-v4-vanilla|其他来源|未启动|0/8|
|cached-feed-lifecycle-repair-vanilla|其他来源，listener派生|未启动|0/8|
|document-submit-snapshot-vanilla|其他来源，与audit辅助模板有关联|未启动|0/8|
|commit-ack-boundary-vanilla|其他来源，容易任务|未启动|0/8|
|upload-finalize-barrier-vanilla|其他来源|未启动|0/8|
|feature-flag-readiness-vue3|其他来源，容易任务|未启动|0/8|
|local-config-readiness-low-cue-vue2|其他来源，历史不稳定|未启动|0/8|
|error-reporting-retired-request-vanilla|其他来源，与audit辅助模板有关联|未启动|0/8|

原计划80维护+10新提取，复用0；每会话600秒/12请求/最终report6000字符，总预留1080请求/54000会话秒，串行独立workspace/profile/meter。提取gpt-6-sol/low、修复计划gpt-5.6-terra/medium，priority客户端配置，CLI与二进制及工具版本见[frozen-config.json](frozen-config.json)、[execution-config.json](execution-config.json)。实际5个PostModelRequest都记录gpt-6-sol；修复模型尚未实际调用，没有静默换模型。服务器tier路由未独立认证。

### 停止的直接原因

x01请求编号读取`/workspace/src/*`和package.json；x02请求编号读取README、package.json和五份候选源码。两次均使用`for …; do echo …; nl …; done`。冻结`request_guard.py`的read_command只允许简单读取命令，拒绝循环和变量；PreToolUse拒绝后kill_cli终止原生CLI，两次exit=137。没有服务请求失败或拥塞证据；模型尝试的是候选内只读读取，不是越界或写文件。该命令门与正常读取方式不相容，分类为**基础设施工具策略失配**，不当成Contract提取质量失败。

这次离线预检遗漏了常见shell批量读取：namespace/Python直读、runtime、backend、只读写保护和预算硬门虽通过，未检验代表性模型读取命令经过该解析器的结果。其PASS范围不足以证明提取正文访问可靠。已零模型复现两条拒绝，并确认等价的直接`nl`可被允许；详见[infrastructure-diagnosis.json](infrastructure-diagnosis.json)。没有在冻结工具门上改规则再补跑。

x01归档了文件列表和源码检索片段，未完成正文读取门；x02仅完成文件列表。两次都没有Contract正文或最终答复。连续2次基础设施异常满足既定停止条件；剩余8次提取、80个维护槽位全部未启动。首个正式维护源码读取门从未触发，不冒称已经通过。实际顺序、部分轨迹、hook原始事件及退出记录在[actual-schedule.json](actual-schedule.json)、[runs/x01](runs/x01)、[runs/x02](runs/x02)，全部90槽状态在[slot-status.json](slot-status.json)。

|提取槽位|底层请求|完成工具项/工具尝试/拦截|输入token（含缓存）|缓存输入|输出token|推理输出子项|会话秒|
|---|---:|---|---:|---:|---:|---:|---:|
|x01|3|2/3/1|34476|22400|266|0|14.50|
|x02|2|1/2/1|22585|11136|201|7|9.79|
|合计|5|3/5/2|57061|33536|467|7|24.29|

5个已发起请求都有完成hook及token_usage，计入全部失败提取成本；cache-write token为0。缓存已包含在输入，推理已包含在输出，不能再相加。没有正式维护/增强调用，也无额外反思、judge、模型预跑或自动重试。[costs.json](costs.json)单列50次无模型评分约69.15秒，不将它计成模型token。CLI计量不包含本聊天主Agent的准备/分析token及人时，这些不可取得，不伪称0；没有核验货币费率或账单，费用不编造。

N/H实际提示、M/E模板及固定K1已保留。H是AI辅助手工整理的有来源参考，不冒充独立人类专家产出。自动Contract均未成功生成，所以没有M/E实际补全prompt、自动Contract冻结或维护补丁；缺失不以空Contract或占位轨迹填充。经验已经获准，但没有实际施加到修复会话。

## Task 3：四组结果、退步与适用边界

|条件|计划维护槽|已启动|有效|无效|未启动|整体/目标行为通过|
|---|---:|---:|---:|---:|---:|---|
|无Contract N|20|0|0|0|20|不可评价，分母0|
|人工整理参考H|20|0|0|0|20|不可评价，分母0|
|自动Contract M|20|0|0|0|20|不可评价，分母0|
|经验增强E|20|0|0|0|20|不可评价，分母0|

维护无效槽为0，**不是2**；两次无效发生在另计的Contract提取阶段。提取分母为计划10、启动2、有效0、无效2、未启动8。维护计划80、启动0、有效0、未启动80。[extraction-results.csv](extraction-results.csv)和[case-results.csv](case-results.csv)分别保存，无结果字段留空，未启动不计失败、不写0%成功率。

H相对N是否有帮助、M与H差距、E相对M是否改善，以及来源变体/其他来源/不适用任务是否受益或受损，全部**不可评价**。没有补丁，不能声称没有退步或通过范围检查；[scope-review.csv](scope-review.csv)明确标为未启动、不适用。历史H u03风险独立保留，没有用有限PASS消除，也没有把历史风险冒充本批新失败。

本批停止于基础设施有效性，不能把未交付Contract归因于提取能力，也不能把没有维护收益当E1无效。没有完成预定80槽对照，没有观察到专家经验改善或恶化；不称长期自演化或GEPA效果实验，不更新生产经验库，不选择成功案例。任何后续工具门修复及重新运行必须作为另一个明确声明的批次，保留本批失败及成本，不自动覆盖或补跑本轮。

冻结253个文件摘要仍全部匹配；旧历史保护、全局配置、HEAD与邻接bench既有两个文件diff保持，临时凭证清理，见[validation.json](validation.json)。本执行没有创建提交。[COMMIT_MESSAGE.txt](COMMIT_MESSAGE.txt)提供Git subject/body建议。
'''
 (O/'REPORT.md').write_text(report)
 # Update the artifact inventory after all output writes; original protocol remains intact.
 files=[p for p in O.rglob('*') if p.is_file() and '.runtime' not in p.parts and '__pycache__' not in p.parts and p.name!='ARTIFACTS.sha256']
 (O/'ARTIFACTS.sha256').write_text(''.join(sha(p)+'  '+str(p.relative_to(O))+'\n' for p in sorted(files)))
 print('STOP finalized: extraction 2 invalid / 8 unstarted; maintenance 0 launched / 80 unstarted; all frozen hashes match.')

if __name__=='__main__':main()
