from pathlib import Path
import json
A=Path(__file__).resolve().parent
read=lambda n:json.loads((A/n).read_text())
s=read('summary.json');vs=read('behavior-vectors.json');rows=read('actual-schedule.json');scope=read('scope-review.json') if (A/'scope-review.json').exists() else {'status':'not yet reviewed'}
report='''# 两例、同机制、跨语言：一次 Reflection 实验报告

## Task 1：来源、评价和工具预检

本批独立协议依据本次用户授权建立。初始 HEAD 为 `40919fb9f33f2336a581c7d013d4d5d888505387`，最初 status/diff 为空；后续准备快照包括本批新目录，见 initial-inspection-note.json。旧计划与历史结果保持原样。

训练固定 JS composition-v4，验证固定 Python composition-v4-window-cued eval-v2，来源单元均 transfer-retry-abort-handoff。通过实际 cluster.json 的 arm.path 解析服务器路径，未照搬 /Volumes。五份最新选例材料已读取，均指向 Python eval-v2；输入摘要逐项吻合，见 version-correspondence.json。候选/任务/manifest/evaluation 归档于 materials，cohort/protocol 记录 SHA256。

policy-review.md 是 AI 辅助核查，不是人工批准。它区分任务/README规范、源码事实与未知政策；支持同步注册、接纳/已接纳完成分离、记录/显示归属、visit内顺序、重入清理、retry和telemetry保留。参考通过仅为校准证据。原始、bounded、expanded及所有登记退化变体均做零模型离线评分；bounded PASS，其余按原规则不通过。未删改评分项，未使用这些校准作为模型修复次数。非每个断言都有独立mutant，断言/轨迹不构成独立样本。

研究侧仅适配仓库外认证配置、JS/Python正文读取识别、固定角色反思和资源结果分类。未修改生产登记或原案例。普通只读for循环对两种源码真实运行并逐行核对正文，提取只读、维护独立可写namespace、隐藏评价/参考/历史/其他会话路径均通过。code_mode_host功能与二进制帮助可用；实际提取会话也有源码正文读取证据。合成计量含失败/取消，24请求上限语义及进程组超时检查记录于offline-validation；合成ledger从不计入真实请求。

模型固定提取gpt-6-sol/low，维护与反思gpt-5.6-terra/medium，并发1；600秒/会话，提取/反思12请求，维护24请求，总15会话/324请求上限。CLI版本、二进制摘要、实际Node/Python版本和本地catalog见 frozen-config。model hook核对型号，effort/service tier是CLI/config声明；不宣称独立认证服务端路由或采样种子。认证在Git外，未安装依赖，未提交。

## Task 2：实际阶段与接纳

'''
report+='停止/完成原因：**'+s['stopping']['reason']+'**。\n\n'
for prefix,title in [('py-screen-','Python筛查（不入正式分母）'),('js-base-','JS训练AUTO基线'),('js-exp-','JS训练AUTO_EXP回验')]:
 z=[v for v in vs if v['slot'].startswith(prefix)];valid=[v for v in z if v['infrastructure_valid'] and v['scoring_valid']];report+=f'- {title}：{sum(v["overall_pass"] for v in valid)}/{len(valid)} 整体通过，另有 {len(z)-len(valid)} 无效。\n'
report+='\n经验生成：'+('一次原文 NEW_EXPERIENCE.md 已单独保存，未手工改写或覆盖旧E1。' if s['training_experience_generated'] else '未启动反思，未生成新经验。')+'\n\n'
if s['acceptance'] is not None:report+='接纳记录：\n\n```json\n'+json.dumps(s['acceptance'],ensure_ascii=False,indent=2)+'\n```\n\n'
report+='本批只使用新抽取Contract；完整报告和栏目1机械交付分别归档。保留原自主工具循环，无AST/RAG、新ReAct外层或官方GEPA。训练反馈构造器只读取JS基线与JS候选，Python筛查标准/轨迹/补丁/失败未提供给反思器。训练侧源绑定差异、保留项、未知原因在反思前冻结。若进入M4，则仅追加冻结经验，调度种子20261108仅控制交错顺序，不控制模型随机性。\n\n'
report+='## Task 3：观察结果、成本、限制和下一步\n\n正式验证为首要结果；未启动不算失败，也不将筛查混入分母：\n\n|组|整体通过|有效|无效|已启动/预留|\n|---|---:|---:|---:|---:|\n'
for g,d in s['formal_validation'].items():report+=f'|{g}|{d["pass"]}|{d["valid"]}|{d["invalid"]}|{d["started"]}/{d["planned"]}|\n'
report+='\n逐项原始效果向量如下；T/F按原评分输出，record-byte-count-included 是禁止效果（F符合本批ungranted范围）。各schedule包含多条耦合断言，完整细分见 behavior-vectors.json 与每槽score.stdout.json。\n\n|会话|判定|未满足required|原已过断言损失数|\n|---|---|---|---:|\n'
for v in vs:
 missing=[k for k,x in v['effects'].items() if not x and k!='record-byte-count-included'];report+=f'|{v["slot"]}|{v["raw_verdict"]}|'+', '.join(missing)+f'|{len(v["assertions_lost_vs_original"])}|\n'
report+='\n源代码/额外变动核查：\n\n```json\n'+json.dumps(scope,ensure_ascii=False,indent=2)+'\n```\n\n'
report+='成本按真实hook底层请求计，失败/取消也保留；缓存输入与推理输出是input/output子项，不重复相加。下表input/output含各自子项；完整细项在summary.json。\n\n|阶段|会话|请求started/completed|工具hook|会话秒|input tokens|output tokens|\n|---|---:|---:|---:|---:|---:|---:|\n'
for stage,d in s['stages'].items():
 if stage=='M1':report+=f'|M1|0模型|0/0|0模型工具|离线总时间未知；校准{d["calibration_seconds"]:.1f}秒|0模型|0模型|\n';continue
 u=d['observed_usage_subtotal'];report+=f'|{stage}|{d["sessions"]}|{d["requests_started"]}/{d["requests_completed"]}|{d["tool_hook_attempts"]}|{d["session_seconds"]:.1f}|{u["input_tokens"]}|{u["output_tokens"]}|\n'
d=s['total_cost'];u=d['observed_usage_subtotal'];report+=f'|模型阶段合计|{d["sessions"]}|{d["requests_started"]}/{d["requests_completed"]}|{d["tool_hook_attempts"]}|{d["session_seconds"]:.1f}|{u["input_tokens"]}|{u["output_tokens"]}|\n\n'
report+='未获取用量的会话：'+json.dumps(d['usage_unknown_sessions'],ensure_ascii=False)+'。观测subtotal与未知总量分开，缺失不补零。主聊天准备/分析token及工具用量不可从实验hook取得，单列未知，不计作0；未核验价格，不估货币成本。M1校准本地子进程非模型工具。\n\n'
report+='结论边界：训练改善不等于验证收益；两例同源且已暴露，Python有额外启动窗口提示并通过宿主闭包表达延迟完成。重复不是独立案例；不能从本批声称纯语言效应、独立泛化、统计显著性或稳定收益。下一步须依据阶段停止原因另立协议；本批不补跑、不换题、不生成第二份经验。\n\n'
report+='未启动槽位：'+', '.join(x['slot'] for x in s['unstarted_slots'])+'。\n\n完整性见 integrity-validation.json、request-accounting-validation.json、ARTIFACTS.sha256；所有旧文件/案例保护摘要及全局配置保持不变。\n'
(A/'REPORT.md').write_text(report)
print('REPORT written')
