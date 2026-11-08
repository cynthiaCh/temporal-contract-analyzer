"""Report every planned slot, including missing and invalid ones; no model calls."""
import csv, hashlib, json, subprocess
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parent.parent
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,x):(O/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')

def main():
 schedule=read(O/'schedule.json')['order'];cohort=read(O/'cohort.json')['cases'];metrics=read(O/'metric-spec.json')
 actual=read(O/'actual-schedule.json') if (O/'actual-schedule.json').exists() else []
 byslot={r['slot']:r for r in actual};source={c['case']:c['source_group'] for c in cohort}
 rows=[]
 for slot in schedule:
  rec=byslot.get(slot['slot']);spec=metrics[slot['case']]
  row={'slot':slot['slot'],'case':slot['case'],'source_group':source[slot['case']],'condition':slot['condition'],'repeat':slot['repeat'],'status':'NOT_STARTED','failure_class':None,'overall_pass':None,'target_pass':None,'lost_required':None,'new_forbidden':None,'paired_N_lost_required':None,'delivered_patch':None,'extra_unsupported_conventions':None,'scope_review':'not_applicable_not_started','seconds':None,'requests':None,'tools':None,'hook_tool_attempts':None,'input_tokens':None,'cached_input_tokens':None,'cache_write_input_tokens':None,'output_tokens':None,'reasoning_output_tokens':None,'usage_incomplete':None,'raw_verdict':None}
  if rec:
   row.update({k:rec.get(k) for k in ['status','failure_class','seconds','tools','usage_incomplete']})
   row.update(rec.get('usage',{}));row['requests']=rec.get('native',{}).get('started');row['hook_tool_attempts']=rec.get('native',{}).get('tool_attempts');row['raw_verdict']=rec.get('verdict')
   path=O/'runs'/slot['slot'];patch=path/'patch.diff';row['delivered_patch']=patch.exists() and bool(patch.read_text())
   row['scope_review']='pending_manual_patch_review'
   if rec['status']=='VALID' and not rec.get('scoring_anomaly'):
    score=read(path/'score.stdout.json');effects=score['observed_effects'];baseline=spec['baseline_effects']
    row['overall_pass']=score['verdict']=='PASS';row['target_pass']=all(effects.get(k) is True for k in spec['target_effects'])
    row['lost_required']=json.dumps([k for k in spec['required'] if baseline.get(k) is True and effects.get(k) is not True])
    row['new_forbidden']=json.dumps([k for k in spec['forbidden'] if baseline.get(k) is False and effects.get(k) is True])
    nslot=next(s for s in schedule if s['case']==slot['case'] and s['repeat']==slot['repeat'] and s['condition']=='N');nrec=byslot.get(nslot['slot'])
    if nrec and nrec['status']=='VALID' and not nrec.get('scoring_anomaly'):
     ne=read(O/'runs'/nslot['slot']/'score.stdout.json')['observed_effects'];row['paired_N_lost_required']=json.dumps([k for k in spec['required'] if ne.get(k) is True and effects.get(k) is not True])
  rows.append(row)
 with (O/'case-results.csv').open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
 groups={}
 for group in ['N','H','M','E']:
  subset=[r for r in rows if r['condition']==group];valid=[r for r in subset if r['status']=='VALID' and r['overall_pass'] is not None]
  groups[group]={'planned':len(subset),'launched':sum(r['status']!='NOT_STARTED' for r in subset),'valid':len(valid),'invalid':sum(r['status'] not in ['NOT_STARTED','VALID'] for r in subset),'not_started':sum(r['status']=='NOT_STARTED' for r in subset),'overall_passes':sum(bool(r['overall_pass']) for r in valid),'target_passes':sum(bool(r['target_pass']) for r in valid),'overall_rate':sum(bool(r['overall_pass']) for r in valid)/len(valid) if valid else None,'denominator':len(valid)}
 tokenkeys=['input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens']
 costs={}
 for name,records in [('extraction',[r for r in actual if r['phase']=='extract']),('maintenance',[r for r in actual if r['phase']=='repair']),('enhanced',[r for r in actual if r.get('condition')=='E']),('all',actual)]:
  costs[name]={'sessions':len(records),'requests':sum(r.get('native',{}).get('started',0) for r in records),'tools':sum(r.get('tools',0) for r in records),'hook_tool_attempts':sum(r.get('native',{}).get('tool_attempts',0) for r in records),'seconds':sum(r.get('seconds',0) for r in records),**{k:sum(r.get('usage',{}).get(k,0) or 0 for r in records) for k in tokenkeys},'usage_is_lower_bound':any(r.get('usage_incomplete',True) for r in records),'money':None}
 costs['note']='Enhanced is a subset of maintenance; do not sum them twice. Cache is part of input, reasoning is part of output. No monetary price verified.'
 costs['zero_model_calibration']={'invocations':sum(len(c['calibration']) for c in cohort),'seconds':sum(r['seconds'] for c in cohort for r in c['calibration']),'model_requests':0}
 save('costs.json',costs)
 approval=read(O/'experience-approval.json') if (O/'experience-approval.json').exists() else {'status':'pending','experience_sha256':sha(O/'EXPERIENCE.md'),'label':'AI 提炼，待专家确认','question':'Async confirmation requested in this conversation; no answer received/recorded.'}
 save('experience-status.json',approval)
 summary={'status':'PREPARED_AWAITING_EXPERIENCE_CONFIRMATION' if not actual else 'RUN_RECORDS_REQUIRE_SEMANTIC_REVIEW','planned_cases':len(cohort),'planned_maintenance_slots':80,'planned_extractions':10,'launched_maintenance':sum(r['phase']=='repair' for r in actual),'launched_extractions':sum(r['phase']=='extract' for r in actual),'groups':groups,'source_counts':{'experience_source_diagnostic_only':1,'same_source_variant_in_batch':1,'other_sources_not_used_to_derive_E1':9,'independent_generalization':0},'experience':approval,'costs':costs,'comparisons':{'H_vs_N':None,'M_vs_H':None,'E_vs_M':None,'reason':'No completed experiment until explicitly launched and reviewed; missing slots are not failures.'},'unsupported_conventions_review':'Historical H u03 :dialog identified; new patches require individual scope review even if PASS.','all_results_retained':True,'production_updates':False}
 save('summary.json',summary)
 # Protect everything observed before this task. New files are limited to O.
 protected=read(O/'protected-files.json');mismatches=[p for p,h in protected.items() if not Path(p).exists() or sha(p)!=h]
 initial=read(O/'initial-state.json');bench=R.parent/'temporal-contract-bench-git'
 bench_diff=subprocess.check_output(['git','-C',str(bench),'diff'],text=True);bench_status=subprocess.check_output(['git','-C',str(bench),'status','--porcelain=v1'],text=True)
 tracked_diff=subprocess.check_output(['git','-C',str(R),'diff','--name-only'],text=True)
 validation={'protected_file_mismatches':mismatches,'global_config_matches':sha(Path.home()/'.codex/config.toml')==initial['global_config_sha256'],'analyzer_tracked_diff_paths':tracked_diff.splitlines(),'head':subprocess.check_output(['git','-C',str(R),'rev-parse','HEAD'],text=True).strip(),'bench_existing_diff_unchanged':bench_diff==initial['bench']['diff'],'bench_existing_status_unchanged':bench_status==initial['bench']['status'],'auth_runtime_files_remaining':[str(p) for p in (O/'.runtime').rglob('auth.json')] if (O/'.runtime').exists() else [],'no_commit_created_by_this_executor':True}
 save('validation.json',validation)
 assert not mismatches and validation['global_config_matches'] and validation['bench_existing_diff_unchanged'] and validation['bench_existing_status_unchanged'] and not tracked_diff and not validation['auth_runtime_files_remaining']
 if not actual:
  report='''# 固定批量实验：准备完成，等待单项经验确认

2026-11-08，AI辅助调查，非独立盲审。本目录没有正式维护或提取模型调用，没有四组行为比较结果。不得将准备、校准或旧结果说成本轮改善。

## Task 1：失败发生在哪里，经验针对什么

唯一有效旧M运行u02的五项关闭／重开失败已逐项核查任务、完整提取报告、实际截取Contract、工具轨迹、最终补丁、自检及原始评分，见 [DIAGNOSIS.md](DIAGNOSIS.md)。可确认：完整报告已识别旧回调与共享状态风险，但交给维护端时只留第1栏；修复未处理关闭／重开，自检只驱动正常完成和卸载。原评分又包含输入没有明确规定的关闭政策。因此不能声称主要是提取失败，也不能把未知政策写成新经验答案。

原始“重开当前完成一次”失败并非当前文件没有完成，而是旧、新token都进入最终集合。H u03整体PASS仍引入无来源的`:dialog` token编码；原评分未覆盖其分支，已列为无依据约定／潜在退步。HEAD调查未发现替换已冻结执行输入或配置的证据，提交来源过程仍未知；没有回退。

唯一E1-v1针对可确认的验证事件替代：按有来源的公开事件分别验证，卸载不能替代关闭／重开；未知政策仍未知。全文 [EXPERIENCE.md](EXPERIENCE.md)，状态为“AI提炼，待专家确认”，不称专家经验。已在本对话发出一项具体确认请求；未收到明确答复，增强组没有启动。未生成其他版本、GEPA或生产经验更新。

## Task 2：规模、来源、有效性和成本

十例选择在新评分前固定，覆盖轮询、Promise、事件监听/解码、异步paint、debounce/flush、timer retry和组件readiness；见 [PLAN.md](PLAN.md)、[cohort.json](cohort.json)、[source-scope.json](source-scope.json)。原low-cue U2及旧C1因评分政策适用冲突暂缓；没有改原评分凑数。十例起点均UNDERREACH、bounded reference均PASS、全部既有mutants均检出：共50次无模型评分调用，原始结果完整保留于calibration/。这证明有限评分路径可用，不证明全部业务政策或生产正确性。

经验来源旧U2仅作诊断；批内同源显式变体1例、未参与E1提炼的其他来源9例。全部来自历史已研究暴露题库；audit/document/error有辅助模板关联，不称九个独立真实事故。来源及限定范围全部历史路径命中见 [exposure-index.json](exposure-index.json)，未知外部暴露不伪装成未见。

计划80个维护槽（10×4×2）及10次新提取；复用0。实际正式维护0/80、提取0/10、底层模型请求0、token0、模型耗时0。80槽全部NOT_STARTED，无效槽0、有效槽0。无模型评分耗时另记 [costs.json](costs.json)；不得计成模型token或四组有效样本。正式批量整体等待E1确认，避免提前形成不完整组序。

修复gpt-5.6-terra/medium，提取gpt-6-sol/low；CLI、二进制、catalog、后端及研究配置在 [frozen-config.json](frozen-config.json)。每槽600秒/12请求/最终report6000字符，总预留90会话/1080请求/54000会话秒；未沿用49请求全局门。按旧同模型有效运行粗估约2.8–4小时、1190–1487万输入和44–57万输出token；仅是观察外推，不是保证，无核验货币费率。串行、独立workspace/profile/meter，无模型预跑/补跑。离线验证只读提取、可写维护、各框架现有依赖、真实源码正文访问、研究/评分未挂载、请求上限硬停止和工具后端；见 [offline-validation.json](offline-validation.json)。首个正式维护源码读取门仍待真正执行，不冒称离线通过已替代它。

四组公共提示及N/H正文已保存于prompts/；M/E目前是明确标记的模板，自动Contract尚不存在。源自可见材料的H手工整理参考明确为AI辅助，不伪造独立人类专家撰写或批准。固定K1、E1、H及任务/源码/评分/运行器哈希在protocol.json。确认后才允许正式dispatch；10份提取完成后还须在首份维护评分前冻结同一M和M/E实际prompt。

## Task 3：四组结果、退步和适用边界

|组|计划|已启动|有效|无效|未启动|整体/目标通过|
|---|---:|---:|---:|---:|---:|---|
|N|20|0|0|0|20|不可评价（分母0）|
|H|20|0|0|0|20|不可评价（分母0）|
|M|20|0|0|0|20|不可评价（分母0）|
|E|20|0|0|0|20|不可评价（分母0）|

[case-results.csv](case-results.csv)保留全部80个槽位，结果留空；[summary.json](summary.json)不填成功率或虚构效果。不能回答H是否增益、M距H多远、E是否改善，亦不能声称没有退步。历史u03风险单列，不能冲抵其他PASS或冒充本轮失败。

正式后须逐例、逐来源报告整体、预选原目标effect、原通过项丢失、无依据约定、实际交付和成本；H有限PASS也逐份审查补丁。若H不显示增量，报告天花板/区分力；若E只增成本而无行为收益，停止E1，不选赢家、不更新生产库。此时唯一缺失确认是E1-v1是否可作为本轮专家确认经验，未要求重新批准有直接项目来源的要求。

所有原历史、评分、技能、生产和全局配置保护检查见 [validation.json](validation.json)。没有创建提交。建议提交信息见 [COMMIT_MESSAGE.txt](COMMIT_MESSAGE.txt)。
'''
  (O/'REPORT.md').write_text(report)

if __name__=='__main__':main()
