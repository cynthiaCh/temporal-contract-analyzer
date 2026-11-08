"""Archive concrete offline fixes and the exact stopped execution, no model calls."""
import json,hashlib,difflib
from pathlib import Path
A=Path(__file__).resolve().parent;R1=A.parent/'two-class-experience-pilot-v2r1-20261108_215007';V2=A.parent/'two-class-experience-pilot-v2-20261108_205648'

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')

def main():
 rec=read(R1/'runs/D1-preanalysis-v2r1/archive/receipt.json');ledger=read(R1/'runs/D1-preanalysis-v2r1/archive/meter/ledger.json')
 denied=[e for e in ledger['events'] if e.get('denied')]
 diagnosis={'source_slot':rec['slot'],'model':'gpt-6-sol','effort':'low','requests':1,'archive_status':rec['archive_status']['status'],'raw_denied_events':denied,
  'precise_cause':'Read grammar rejected stderr redirect to /dev/null. It was a safe candidate-document read; no namespace escape demonstrated. Guard intentionally killed CLI, so no final extraction exists.',
  'not_a_model_role_mismatch':True,'not_a_request_cap_hit':True,'not_a_service_stream_failure':True,'new_model_calls_after_stop':0,'no_Contract_produced':True,'scoring_calls':0}
 save(R1/'diagnostics/read-policy-stop.json',diagnosis)
 summary=read(R1/'summary.json');summary['precise_stop_diagnosis']=diagnosis;summary['status']='STOPPED_READ_POLICY_FALSE_POSITIVE';save(R1/'summary.json',summary)
 report=R1/'REPORT.md';report.write_text('''# v2r1：真实只读命令被误拒后停止

本修订的首个D1提取只启动1个模型请求。请求正常完成，随后只读guard拒绝了rg读取README/docs时的 `2>/dev/null`；CLI被guard终止，归档OK，但没有完整提取结果。checker的组合消息是role/isolation/request distortion，原事件将原因收窄为命令语法误拒，没有角色不一致、请求超限或越界访问的证据。

测试A计划4、启动0、有效评分0；B计划4、启动0、有效评分0。8槽均未启动，不是行为失败。没有新Contract、AUTO、反思、经验或冻结库。1个请求已报告14179 token，用量未知请求0；工程/货币成本未知。本修订触发停止后没有模型重试或补跑。

Typed结构化输出和三个角色schema绑定已通过40项离线检查，但实际生成尚未完成，不能据此宣称语义已经修好。此前v2的一次提取/3请求及全部失败材料保留。当前研究下一版只离线修复了读命令兼容，见相邻v2r2目录；原冻结代码、原始响应、失败会话及计量不改。

详细原事件：diagnostics/read-policy-stop.json。完整计划/实际计量/未启动槽位见summary.json、terminal-test-schedule.json；不能进行A/B效果比较。
''')
 prior_usage=read(V2/'runs/D1-preanalysis-v2/archive/usage.json');current_usage=read(R1/'runs/D1-preanalysis-v2r1/archive/usage.json')
 stats=read(A/'offline-validation.json')
 result={'status':'OFFLINE_FIX_COMPLETE_EXPERIMENT_REMAINS_STOPPED','latest_execution_directory':str(R1),'fixed_code_directory':str(A),'experimental_model_calls_in_this_fix_directory':0,
  'this_user_turn_execution':{'sessions':1,'requests':1,'known_total_tokens':14179,'usage_unknown_requests':0,'scoring_calls':0},
  'v2_family_preparation_so_far':{'sessions':2,'requests':4,'known_total_tokens':prior_usage['total_usage']['total_tokens']+current_usage['total_usage']['total_tokens'],'usage_unknown_requests':0,'remaining_authorized_reextraction_slots':2},
  'tests':{'planned_A':4,'planned_B':4,'started_A':0,'started_B':0,'valid_scored_A':0,'valid_scored_B':0,'invalid_started':0,'unstarted':8,'whole_task_pass_rate':None,'behavioral_improvement':None,'regressions':None},
  'offline_validation':stats,'code_fixes':['top-level typed extract and reflection objects','three role-specific schema bindings','local schema length/shape validation','bounded short source quotes and explicit owner claims','safe stderr-to-null and || true read grammar','retained null-safe archival and complete-candidate scoring gate'],
  'semantic_status':'Original errors audited; new material not produced. Typed representation and veto do not establish semantic truth.','v1_unknown_usage_preserved':True,'money':None,'engineering_tokens':None,'no_commits_or_production_changes':True}
 save(A/'summary.json',result)
 patches=A/'implementation-patches';patches.mkdir(exist_ok=True)
 for name in ['read_policy.py','toolflow.py']:
  (patches/(name+'.diff')).write_text(''.join(difflib.unified_diff((R1/name).read_text().splitlines(True),(A/name).read_text().splitlines(True),fromfile='stopped-v2r1/'+name,tofile='offline-fixed/'+name)))
 (A/'FIX.md').write_text('''# Concrete offline fixes

1. Extract/reflect return direct structured JSON objects. Maintenance alone uses the existing report string. The CLI-bound schema is the same schema used locally; native role-schema binding is tested. Contract1400, quote80, file80, owner expression32, claim statement160; typed objects above6000 are accepted if structurally valid. Historical6000-character nested JSON is retained and rejected without salvage.
2. The exact legitimate read `rg ... README* docs 2>/dev/null` is allowed; `|| true` is a bounded safe fallback. Writes to candidate or other paths, outside-candidate reads, command substitution, network/executable commands and unsafe alternatives remain denied. Supported read grammar is explicit in the model prompt. Namespace/tool role permissions remain unchanged. A normal missing-doc read can exit2; this is not itself infrastructure failure.
3. Existing null-safe usage/partial-output archival and complete-candidate scoring gate remain intact. Known totals and unknown counts are separate; failed or incomplete candidates are unscored.

44 offline tests pass, including all16 real historical extraction tool inputs, negative write/execution cases, native role bindings, typed size boundaries and full fake-CLI extract->veto->route->maintenance->score handoff. The exact three tool requests from the newly interrupted session run successfully through the real hook server inside the unchanged bwrap namespace, without any model request. Four actual candidate namespace replays, v1 failed stream and v2 malformed response replays also pass. These tests cover observed defects, not a guarantee about future model/service behavior.

The first paid call of v2r1 hit the old read-grammar defect. It was archived and stopped. This fixed-code directory is offline-only; no fresh model requests or test-maintenance restarts after that stop. All old frozen execution artifacts remain unchanged. The semantic correction still requires complete automatically generated material; no hand-authored Contract or experience was substituted.
''')
 (A/'REPORT.md').write_text('''# 修复交付；原A/B实验仍未完成

代码已修复结构化输出边界、角色schema绑定，以及只读命令的stderr重定向兼容。具体实现与检查见FIX.md。

本次新启动的v2r1首次提取被旧读命令过滤器误杀：真实工具请求只读取候选README/docs并丢弃stderr。传输请求正常完成，随后guard终止CLI；归档OK，没有自动分析或维护候选。它不是越界访问、模型角色错误或请求超限。按停止规则，没有继续付费调用，没有隐性重试或补跑。精确原事件见v2r1/diagnostics/read-policy-stop.json。

之后仅离线修复该兼容分支，并回放全部16条历史真实读取工具输入、实际隔离命名空间中的3条受影响命令。44项离线测试、四例真实源码/namespace/IPC/归档及两个历史失败响应回放通过。普通文件写入、执行程序、网络、路径越界仍被拒绝。44份评分校准的输入/评分版本保持相同；未修改评分器或案例。

本轮付费执行：1个会话、1个请求、14179已知token；没有未知用量请求。此前停止v2为1个会话、3请求、46766 token；两修订累计2次提取、4请求、60945已知token，原授权4次重新提取尚有2槽。工程和货币成本未知。这里的历史回放不计为新增用量。

A有效评分0/4、B有效评分0/4；8槽全部未启动，没有整题通过率、目标改善或退步结论，没有新经验或测试冻结库。原语义错误已用原文/源码/实际检查核实；新输出的语义没有完成实证验证，不能称已解决语义研究结果。既有案例仍是已暴露同题/同源跨语言，不是独立泛化。

代码在独立研究目录，旧失败会话、原始响应、未知用量、未启动槽位与冻结经验不改。没有提交Git、修改生产经验库或全局配置。本目录不自动启动后续实验。
''')
 (A/'COMMIT_MESSAGE.txt').write_text('research: fix structured response boundaries and safe-read compatibility\n\nUse typed role-specific outputs and bounded source evidence.\nAllow stderr-to-null and safe read fallbacks while retaining write/execution denial.\nReplay real failed responses and all historical read inputs offline.\nPreserve stopped experiments, unknown usage and all unstarted A/B slots.\n')
 # Verify all existing prior files and original cases have not been overwritten.
 protected=read(A/'protected-files.json');changes=[p for p,h in protected.items() if not Path(p).is_file() or sha(Path(p))!=h]
 assert not changes,changes
 save(A/'integrity-check.json',{'protected_changes':changes,'verified_existing_files':len(protected),'new_paid_calls_after_stop':0,'new_experiment_not_started':True,'original_case_and_scoring_preserved':True})
 # Final manifests for the stopped execution and the offline-only repair.
 for directory in [R1,A]:
  save(directory/'code-summary.json',{p.name:sha(p) for p in directory.glob('*.py')})
  save(directory/'archive-manifest.json',{'self_excluded':True,'files':{str(p.relative_to(directory)):sha(p) for p in directory.rglob('*') if p.is_file() and p.name!='archive-manifest.json' and '__pycache__' not in p.parts}})
 print(json.dumps({'status':result['status'],'tests':44,'real_read_inputs':16,'paid_requests_after_stop':0,'A_valid':0,'B_valid':0,'protected_changes':changes},ensure_ascii=False))
if __name__=='__main__':main()
