"""Render reviewed scores/trajectories and explicit negative/limited conclusions."""
from pathlib import Path
from run import OUT,read,save,sha,frozen,DEV,HOLD


def main():
    p=frozen();s=read(OUT/'summary.json');choice=read(OUT/'selection.json');reviews=read(OUT/'process-review.json');g=s['groups'];t=s['total_cost'];selected=s['selected'];held=[r for r in s['results'] if r['split']=='holdout'];dev=[r for r in s['results'] if r['split']=='development']
    lines=['# 第一轮 ReAct 外层控制与时序契约技能演化','',
      f"完成 {s['formal_sessions']}/18 个正式执行会话，未补跑、未追加候选、预留未动用。K1在开发区被{'接纳' if selected=='K1' else '拒绝'}，最终K*={selected}。保留区A {g['holdout-A']['whole_pass']}/{g['holdout-A']['sessions']}、B {g['holdout-B']['whole_pass']}/{g['holdout-B']['sessions']}整体通过。"+('C因K*=K0、与B实际输入字节相同，在最终评估前取消四槽位；不把同条件重复解释为演化收益。' if s['C_cancelled'] else f"C {g['holdout-C']['whole_pass']}/{g['holdout-C']['sessions']}整体通过。"),'',
      '## Task 1：新增的 ReAct 控制与原有能力','',
      'Codex原有能力承担：选择工具、保留会话上下文、解释代码/观察、拟定修复、修改代码和设计/运行候选可见测试。本轮没有把这些能力重新命名为ReAct增量，也没有委派Agent。','',
      '新增的是一个固定、无模型的同步外层控制器：PostToolUse归档真实输出与文件快照并追加状态/证据缺口反馈；有限PreToolUse在缺少检查记录时拒绝修改；Stop根据原维护任务的交付记录、实际补丁与验证观察要求同一session继续。保留collect/inspect/repair_validate状态、可请求回退、至多2次编辑拒绝、2次回退、2次Stop续行及8次观察反馈，全部计入每次600秒预算。A加载相同被动记录器，但不拒绝、不注入、不要求继续；B/C启用上述控制。','',
      '实现复用了本机已有同步 [Codex hooks](https://learn.chatgpt.com/docs/hooks) 与原CLI工具循环，没有每一步新启动Agent。每次正式执行只有一个session ID；原生Stop可在该session内增加继续执行。用量另记录底层模型请求，不将正式会话数冒充网络推理请求数。','',
      '**这不是完整语义状态机。** 机械门核对存在性和启发式引用/工具分类，不证明事件顺序正确、测试足够或任务语义完成。真实开发运行既出现编辑拒绝，也出现Stop续行，证明有实际外层控制；同时出现真实测试通过却未被门识别的误漏，不能声称可靠强制完成。','',
      '固定实现的实际限制见 [IMPLEMENTATION_LIMITS.md](IMPLEMENTATION_LIMITS.md)：文件列表可能被误计为源码观察；本机Bash hook经常只有stdout、没有退出码，分类器漏识别`PASS`及无输出的成功检查。download/K0实际Node通过输出见events33/45/47/59，最终controller validations为空，触发两次继续后带未满足标记放行，但可信评分PASS。续行中的重复记录/重复验证不能全部算作有效查证。判断真实阅读与验证采用原CLI输出，不能用controller计数替代。','',
      '### 冻结与案例划分','',
      '模型gpt-6-sol / low；workspace-write、approval never、600秒/会话；原CLI/helper、工具权限、输出限制不变，无新增输出token硬上限。为了执行已审查的独立hooks，所有组都使用一次性hook trust选项；该选项不关闭工具sandbox。正式前完成同环境隔离/脚本、hooks配置发现、13组合成控制检查及4案例×原样/参考共8次无模型校准；真实hook触发只在正式运行后验证，未伪称预跑模型。','',
      '|分区|案例与来源单元|选择依据及限制|','|---|---|---|',
      '|开发|transfer-progress-composition-v4-vanilla / transfer-retry-abort-handoff|近期可信失败重复；authored development，已暴露|',
      '|开发|download-polling-restoration-low-cue-react18 / download-polling-restoration|历史等待/关闭失效及补丁验证缺口；clean-room已暴露|',
      '|探索性保留|document-submit-snapshot-vanilla / debounced-submit-flush|历史自主两次15/20，近期附加材料又4/4通过，有天花板风险|',
      '|探索性保留|feature-flag-readiness-vue3 / feature-flag-readiness|近期稳定通过，较容易的退步观察任务|','',
      '按来源cluster和independent_unit_id拆分，无同源变体跨区。所有案例研究者已暴露，保留区仅对本轮进化器隔离，独立泛化案例0。原任务、冻结候选、源码BM25和固定五题逐字节一致；AST全部不交付，AST规则保持不变。固定BASE、模型、工具和controller，只演化技能。A的含义是当前公共设置下的自主执行+K0，不与此前裸自主条件混作同一基线。','',
      '完整原计划、模板、调度种子2026110603与停止规则见 [PLAN.md](PLAN.md)、[protocol.json](protocol.json)。K0全量实际prompt在首次调用前冻结；未知K1的组合模板先冻结，生成后实际prompt先审查再冻结；K*、最终A/B/C全量prompt和C取消决定均在保留运行前冻结。没有根据保留成绩修改技能、案例、调度或控制代码。','',
      '## Task 2：技能反馈、变化与接纳','',
      f"[K0](K0.md)为{len((OUT/'K0.md').read_text())}字符，覆盖适用性、源码证据、身份/副作用关系、事件顺序、不适用条件、原任务与修改验证。仅聚焦结果归属与不同副作用有效性。来源是可见题库及既有诊断边界，没有复制案例补丁。",'',
      '进化器只得到本轮两个开发任务的原可见源码/任务、K0、实际命令及输出（逐条截断明确标记）、修复补丁、控制观察和匿名开发评分向量。没有隐藏断言、oracle标签/实现、参考补丁、历史结果、保留任务/源码/轨迹/评分；私有匿名映射留在研究侧。完整packet与摘要见evolution/，没有第二个候选或人工修写候选。','',
      f"自动生成 [K1](K1.md)，{len((OUT/'K1.md').read_text())}字符，父版本及摘要见 [versions.json](versions.json)，逐行差异见 [K1.diff](K1.diff)。其主变化：",'',
      '- S3：分别写出各副作用的接纳与发布条件，检查持久结果和当前显示能否共用守卫。',
      '- S4：追踪源码允许的同步回调在外层返回前/后发生时的所有权、晚返回清理句柄和后续发布；无法驱动的顺序标为未验证。',
      '- Diff还扩展S2的同步首次值证据及S6的最后修改后验证、集成/替代工具区分；进化器元数据主要标S3/S4，并非穷尽每个文本差异。','',
      '这不是仅添加“更加仔细”。元数据列出失败依据、步骤、可观察行动和保留行为风险，见 [K1.proposal.json](K1.proposal.json)。不过下载K0本轮可信评分通过，进化器提出的同步调度风险只是源码允许的待验证可能，不是已测失败；匿名失败项也没有被解释成新业务要求。新技能本身不包含这些开发路径/程序符号/匿名标签或修复代码。','',
      '机械检查与逐项研究侧泄漏审查通过后才启动K1，见 [research-review.json](evolution/research-review.json)、[K1.delivery.freeze.json](K1.delivery.freeze.json)。审查仅确认边界和可观察变化，不预判有效。执行者只收到技能正文，未收到修改元数据或反馈包。','',
      '|开发任务|K0|K1|','|---|---|---|']
    for c in DEV:
        cells=[]
        for k in ['K0','K1']:
            r=next((r for r in dev if r['case']==c and r['skill']==k),None);v=r.get('score') if r else None;cells.append(f"{v['verdict']} {v['required_passed']}/{v['required_total']}" if v else '未执行/未确认')
        lines.append('|'+c+'|'+'|'.join(cells)+'|')
    lines += ['',
      f"开发整体通过K0={choice.get('old_whole','?')}/2，K1={choice.get('new_whole','?')}/2。决定：**{selected}**；原因 `{choice['reason']}`。",'',
      'K1下载在响应分支前无条件清loading；pending重试仍运行，但等待期间不再loading。可信评分丢失K0已通过的等待项及对应场景断言，两者是同一退步的不同粒度，不当两个独立事故。K1自建harness验证retryScheduled、completed、重开/卸载，没有断言pending期间loading。它区分了替代harness的限制，但没有将这一保留义务落实到断言。','',
      'K0/K1传输最终progress.js补丁字节相同：监听提前、帧显示水位、保留记录，没有同时补上事件接纳和当前attempt的显示归属。两者可信8/10；K1的新增技能并未在本次结果中产生可见修复增量。候选因此按预定规则拒绝；不靠总检查数或成本波动抵消K0已通过项丢失。两个开发任务、每版一次不足以认定稳定优劣。','',
      '选择后K*=K0，与B技能/控制/完整输入相同的C四槽位已取消，没有重复执行来制造“演化收益”，也没有第三候选。最终保留区只评估流程增量；**没有独立保留区技能演化增量估计**，不能称K0普遍优于演化技能。','',
      '## Task 3：两项增量、成本和机制','',
      '|探索性保留任务|A1|B1|A2|B2|','|---|---|---|---|']
    for c in HOLD:
        cells=[]
        for a,rp in [('A',1),('B',1),('A',2),('B',2)]:
            r=next(r for r in held if r['case']==c and r['arm']==a and r['replicate']==rp);x=r.get('score');cells.append(f"{x['verdict']} {x['required_passed']}/{x['required_total']}" if x else r['category'])
        lines.append('|'+c+'|'+'|'.join(cells)+'|')
    lines += ['', '|指标|自主A+K0|外层控制B+K0|','|---|---:|---:|']
    for label,key in [('有效可信评分','valid_scores'),('整体通过','whole_pass'),('原样已通过检查丢失运行','original_check_loss_runs'),('原样已通过断言显式失败运行','original_assertion_failure_runs'),('原样条件断言未发出运行','original_assertion_not_emitted_runs'),('禁止效果运行','forbidden_runs'),('未交付候选补丁','maintenance_without_patch')]:lines.append(f"|{label}|{g['holdout-A'][key]}|{g['holdout-B'][key]}|")
    lines += ['', '逐配对检查/断言得失见summary.json，原通过项丢失单列，不能被总分抵消。文档两A/两B各有一项原条件断言未再发出：原样会产生提交notice，修复在flush中close后抑制notice，原oracle仅在非null notice实际发出时添加该断言。当前所有显式断言通过，且notice-at-return等检查通过。原机械缺项按loss字段仍保留并单列为未发出，不冒称显式失败，也不自动算该缺项通过；这是结果模式差异，非评分器修改。所有维护结果以实际补丁、验证输出和可信行为区分；完成门通过/最终自述不作为行为通过证据。相邻模块及不必要行为变化复核见process-review.json；有限评分和源码范围核对不证明所有输入或接口等价。','',
      '|保留区成本（各四次）|A|B|B−A|','|---|---:|---:|---:|']
    for label,key in [('输入token含缓存','input_tokens'),('缓存输入token','cached_input_tokens'),('输出token','output_tokens'),('运行秒含工具/网络','model_seconds'),('工具调用含记录写入','tool_calls'),('底层模型请求尝试','model_request_attempts'),('Stop续行','stop_continuations'),('修改门拒绝','edit_gate_denials')]:
        a=g['holdout-A'][key];b=g['holdout-B'][key];lines.append(f'|{label}|{a}|{b}|{b-a:.3f}|')
    lines += ['', '|范围|正式会话|输入token|输出token|运行秒|工具调用|底层请求尝试|','|---|---:|---:|---:|---:|---:|---:|']
    for name,x in [('K0开发',g['development-K0']),('K1开发',g['development-K1']),('进化器',s['evolver_cost']),('开发+进化全部',s['development_and_evolution_cost']),('相对K0开发额外搜索',s['additional_skill_search_cost']),('完整实验',t)]:lines.append(f"|{name}|{x['sessions']}|{x['input_tokens']}|{x['output_tokens']}|{x['model_seconds']}|{x['tool_calls']}|{x['model_request_attempts']}|")
    lines += ['',
      f"正式会话合计{s['formal_sessions']}，未使用{s['unused_budget']}个预算（四个相同C和一个显式预留）。底层模型请求尝试共{t['model_request_attempts']}，包括原工具循环和Stop续行，并非只发生{s['formal_sessions']}次API请求。每次CLI用量与各PostModelRequest用量之和已核对一致；控制器自身不调用模型。",'',
      f"同步hook处理函数内部计时合计{t['controller_hook_seconds']}秒（不含Python进程启动/排队及计时前读取，已包含在运行时间中，不重复相加），控制反馈{t['controller_feedback_characters']}字符；全实验Stop续行{t['stop_continuations']}次、编辑拒绝{t['edit_gate_denials']}次。Stop续行之后的请求/token逐运行记录control.stop_continuation_suffix_usage。PostToolUse带来的额外推理不能与任务自身行动完全分离；A/B总成本差仅作描述。首次正式调用登记至完成为{s['pipeline_elapsed_seconds']:.3f}秒，含串行评分和研究侧审查间隔；与上表模型运行和不是同一口径。输入含缓存及重复上下文，未换算费用。",'',
      f"正式执行异常 {sum(r['category'].startswith('execution') for r in s['results'])}；评分未确认 {sum(r['category']=='validation-unverified' for r in s['results'])}。底层请求状态、工具非零退出、hook原始观察和限额放行均完整保存，没有把框架/服务错误静默算作语义失败。候选默认Node v22、可信评分Node v16.20.2沿用前轮；缺少React依赖导致替代harness限制，git diff在无.git快照中失败也未被当作检查通过。",'',
      '### 实际机制证据','',
      '[EVIDENCE.md](EVIDENCE.md)逐运行链接完整prompt、工具输出/events行号、补丁、控制事件、评分和用量。[process-review.json](process-review.json)保存研究者事后复核，不是额外审查模型或盲审。','']
    for review in reviews['runs']:
        lines += [f"- **{review['label']}**：{review['finding']}"]
    lines += ['',
      '对进化器的“预计行动改变”与实际执行分开：K1正文确实扩展了关系/顺序检查，但传输补丁完全相同，下载遗漏等待状态；不能据此说Agent已学会这些契约。Stop曾实际促使继续执行，也可能仅增加记录和重复测试，不能把所有继续归为成功纠错。','',
      '### 判断和下一步','',
      f"在这四个有效A/B配对中，A整体{g['holdout-A']['whole_pass']}/4、B整体{g['holdout-B']['whole_pass']}/4，配对得失必须与成本一起看。"+('两组均通过，存在天花板，没有行为收益证据。' if g['holdout-A']['whole_pass']==g['holdout-B']['whole_pass']==4 else '结果只支持本轮有界描述，不推广为流程普遍优劣。'),'',
      '技能演化本轮没有找到可接纳版本；开发退步被保留门阻止进入保留区。这说明选择机制拒绝了已观察到的损失，不证明所有演化都无效，也不证明K0稳定更优。保留区没有K1结果，不能宣称演化收益、迁移成功或独立泛化。','',
      '**下一步暂不扩大实验，先修正研究控制器的观察适配与完成检查。** 优先使用可靠的真实工具状态区分无输出成功、失败、语法检查与行为检查，减少重复记录/重复验证；源码列表与正文观察也应区分。随后再用冻结方案评估契约检查是否真正落到事件顺序和不同副作用的断言。此建议没有在本轮中途实施，也未修改生产工具/题库或追加模型调用。','',
      'A/B同时改变外层控制及其必要记录指令，未分离提示文本、运行控制与更多计算的单独贡献；保留任务已有历史成功，样本小且暴露；反馈匿名化限制进化器定位，技能修改又可能转移注意。一次候选、两开发任务与两保留任务各两重复，仅描述，不作因果、显著性或普遍泛化结论。','',
      '### 交付与仓库保护','',
      '所有新增内容均在本目录：PLAN、K0/K1/Kstar、版本/差异/审查与冻结摘要；BASE/CONTROL/EVOLVER和实际完整prompt；controller/run/preflight/analyze/finalize；materials、evolution、trials（轨迹/补丁/评分/用量）、calibration、schedule、summary/audit/process-review/EVIDENCE及本报告。无新依赖，没有生产prompt、AST/评分器/原题库修改，没有重写历史，没有创建提交。AGENTS根/祖先/仓库扫描未发现；初始四个未跟踪研究目录保留，HEAD和原diff对账见audit.json。','',
      '建议Git提交信息（未创建提交）：','',
      '```text','research: evaluate bounded ReAct control and temporal skill evolution','',
      'Add same-session hook control and one development-only skill revision.',
      'Archive rejection, cancelled duplicate conditions, behavior scores and full costs.','```','']
    s['interpretation']=dict(react_increment='No observed heldout behavior increase: A/B each 4/4; B costs higher and controller observation limits present',skill_evolution_increment='K1 rejected on development preservation loss; no K1 heldout estimate',causal_significance_or_generalization=False)
    s['recommendation']=dict(expand=False,priority='research controller observation adapter and completion verification',production_change_applied=False)
    s['metric_definitions']=dict(original_assertion_loss_runs='Frozen conservative comparison: includes original passed assertion IDs absent from new output; not identical to explicit failures',original_assertion_failure_runs='Original true assertion emitted and explicitly false',original_assertion_not_emitted_runs='Original true conditional assertion absent; neither auto-pass nor explicit failure; see ANALYSIS_NOTES.md')
    save(OUT/'summary.json',s)
    (OUT/'REPORT.md').write_text('\n'.join(lines));(OUT/'COMMIT_MESSAGE.txt').write_text('research: evaluate bounded ReAct control and temporal skill evolution\n\nAdd same-session hook control and one development-only skill revision.\nArchive rejection, cancelled duplicate conditions, behavior scores and full costs.\n')
    print('REPORT_WRITTEN',flush=True)
if __name__=='__main__':main()
