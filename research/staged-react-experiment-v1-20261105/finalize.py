"""Render audited artifacts after exactly the frozen 16 slots; no model calls."""
from collections import Counter
from pathlib import Path
import json
import subprocess
from analyze import main as analyze
from run import OUT, REPO, CASES, read, save, sha, frozen


def rel(path):
    return str(Path(path).relative_to(OUT))


def main():
    assert read(OUT/'completion.json')['invocations']==16
    analyze()
    s=read(OUT/'summary.json');traces=read(OUT/'trajectory-evidence.json');rows=read(OUT/'analysis-runs.json')
    assert len(rows)==16 and len(read(OUT/'invocations.json'))==16
    assert not list((OUT/'.runtime').glob('*')), 'never archive auth profiles'
    by={(t['case'],t['arm'],t['replicate']):t for t in traces}
    def links(case,arm,rep):
        t=by[(case,arm,rep)];r=next(r for r in rows if r['id']==t['id']);d=Path(r['path'])/'jobs/j-001'
        return ' · '.join(f'[{label}]({rel(path)})' for label,path in [('prompt',d/'prompt.md'),('轨迹',d/'events.jsonl'),('补丁',d/'changes.json'),('回答',d/'cli-output/answer.md')])
    evidence=['# 逐运行证据索引','', '只列实际工具调用与归档，不以 Agent 自述确认效果。完整 stdout 在对应 events.jsonl，可信结果在 raw-vectors.json 所指 oracle。','']
    process=[]
    for r in sorted(rows,key=lambda r:r['sequence']):
        t=by[(r['case'],r['arm'],r['replicate'])]
        evidence += [f"## {r['sequence']:02d} {r['case']} / {r['arm']}{r['replicate']}",'',
          links(r['case'],r['arm'],r['replicate']),'',f"分类 `{r['analysis_category']}`；工具 {r['tool_calls']}；阶段记录 {r['stage_characters']} 字符；修改路径：{', '.join(t['changed_paths']) or '无'}。",'',
          f"输入token {(r.get('usage') or {}).get('input_tokens')}；输出token {(r.get('usage') or {}).get('output_tokens')}；模型运行秒 {r['model_seconds']}。",'',
          '|轨迹行|退出码|实际命令（前180字符；完整内容见轨迹）|','|---:|---:|---|']
        for c in t['commands']:
            cmd=c['command'][:180].replace('|','\\|').replace('\n',' ↵ ').replace('`','\\`')
            evidence.append(f"|{c['line']}|{c['exit_code']}|{cmd}|")
        if r['arm']=='B':
            evidence += ['',f"阶段格式检查：{t['stage'].get('format_compliant')}；阶段1/2记录早于首个补丁：{t['stage'].get('stages_1_2_recorded_before_first_edit')}。",'']
            process.append(dict(id=r['id'],case=r['case'],replicate=r['replicate'],stage=t['stage'],
                                candidate_check_failures=r['command_failures']))
        v=next((v for v in read(OUT/'raw-vectors.json') if v['id']==r['id']),None)
        if v: evidence += ['',f"可信评分：[{v['verdict']}]({rel(v['raw_oracle'])})，必需 {v['required_passed']}/{v['required_total']}，缺失 {v['missing_required_effects']}。",'']
    (OUT/'EVIDENCE.md').write_text('\n'.join(evidence)+'\n')
    valid_b=[t for t in traces if t['arm']=='B' and t['id']!='e-46b34adef8794a04']
    findings=dict(scope='researcher post-run review, no independent reviewer; no prompt changes or model reruns',
      records=process,valid_B_count=len(valid_b),
      valid_B_format_compliant=sum(t['stage'].get('format_compliant') is True for t in valid_b),
      valid_B_pre_edit_stage_order=sum(t['stage'].get('stages_1_2_recorded_before_first_edit') is True for t in valid_b),
      max_record_characters=max(r['characters'] for t in valid_b for r in t['stage']['records']),
      backward_transition_records=sum(t['stage'].get('returns',0) for t in valid_b),
      semantic_findings=[
       dict(case=CASES[0],finding='Both arms read SchemaForm outside initial RAG and change installation to wait for setValue. This is relevant gap closure, not B-exclusive evidence gain.'),
       dict(case=CASES[2],finding='B twice revised ad-hoc telemetry test expectations after tool failure. Actual shared-feed source supports revision; original tests/scorer untouched. Whole verdict still fails. B1 also changes queue attempt display ownership, gains retry-preserved; B2 does not, so gain does not repeat.'),
       dict(case=CASES[1],replicate=2,finding='B clears loading before pending/ready split; trusted pending snapshots show loading=false while retryScheduled=true. Local harness tests completion/cancellation but does not assert waiting-state loading. Stage1 unknown status shape becomes unsupported extra accepted representations in isReady; no causal claim that this extra parsing caused loading failure.'),
       dict(case=CASES[3],finding='Both arms preserve runAdjacent verbatim and pass; B adds evidence records and checks without behavior gain.'),
       dict(finding='No unbounded loop, repeated stage-report churn or pre-record candidate edit observed in valid B traces. Source-cited records can still omit the decisive event order; formatting is not a semantic gate.')])
    save(OUT/'process-review.json',findings)
    a=s['arms']['A'];b=s['arms']['B'];pa=s['paired_cost']['A'];pb=s['paired_cost']['B'];delta=s['paired_cost_delta']
    pairs=s['pairs'];pA=sum(q['A'] for q in pairs);pB=sum(q['B'] for q in pairs)
    lines=['# 分阶段证据核查未改善整体修复，出现一次配对损失','',
      f"完成 **16/16 正式槽位、0补跑、0追加模型调用**。首个B因隔离漏挂CLI helper而无工具能力，保留为执行异常；剩余15份有有效工具轨迹与可信评分。**主要比较限于 {len(pairs)} 个环境匹配且有效的配对：A {pA}/{len(pairs)}、B {pB}/{len(pairs)} 整体通过；B胜{s['pair_wins']}、负{s['pair_losses']}、平{s['pair_ties']}。** 不把基础设施失败算作B语义失败。",'',
      '传输题B第一次多保留一个retry检查项，第二次未重复；两组两次均未完成整个传输修复。下载题第二次A通过、B漏pending期间的loading等待状态。故本轮不支持分阶段提示词带来稳定修复收益，且观测到一次损失。不能由此推断一般任务中B必然更差。','',
      '## 条件、冻结与来源','',
      'A为现有自主执行加共同材料，已具有读文件、改代码、运行检查和依工具结果调整的能力。B在同一个Agent、同一工具循环上增加三阶段目标、简短证据/计划记录和返回条件，名称为**分阶段ReAct提示词条件**。现有运行器没有阶段回调接口；没有实现强制状态机，也没有引入多Agent或角色提示优化。','',
      '固定gpt-6-sol/low、workspace-write、approval never、600秒/槽位；沿用最近可信实验的输出设置，无显式输出token上限。相同原任务、冻结起点、源码RAG、固定五题及顺序；AST报告两组均不交付。源检索和题库render逐字节复制上一轮实现。完整A/B提示见EVIDENCE索引及每个jobs/j-001/prompt.md；公共材料及候选摘要见common-digests.json。B.md在调用前冻结，之后未改。','',
      '种子2026110503只控制调度，不是模型采样种子。每个案例/重复成对交错，第二次反转组顺序，顺序见runs.json和protocol.schedule。每槽位独立候选、CLI profile、输出与阶段目录；没有共享补丁或反馈。原始hidden评分、参考修复和来源索引均在研究侧，未挂载到Agent。','',
      '|案例|选择依据（本轮前）|时序机制|来源分类|','|---|---|---|---|',
      '|本地配置迁移|assistance-applicability A/R各0/2|组件API延迟注册、配置安装|private-incident clean-room；已开发暴露|',
      '|下载轮询恢复low-cue|model-effort中gpt-6-sol/low/none为UNDERREACH|pending轮询、close/reopen、后台所有权|clean-room reconstruction；已开发暴露|',
      '|传输进度组合v4|question-bank pilot A/R/RQ/RG各0/2|同步start重入、异步解码、记录/显示有效性分离|authored development，同源扩展|',
      '|功能开关就绪|最近S/F/R各2/2|首次点击与就绪顺序、相邻控制保留|clean-room reconstruction；已研究暴露|','',
      '这是按历史失败定向选择的3难例+1稳定对照，**认证独立泛化案例0**。没有把同源变体算作新独立事故。原始provenance的human review/oracle review等认证多处仍pending；本轮“可信评分”指原有评分器、原始向量和参考校准均一致，不代表新取得独立人审认证。历史条件材料不同，历史失败不能保证本轮A仍失败。historical-selection.json保存选择依据和归档行；PLAN/protocol在看到本轮B结果前已冻结。','',
      '## 逐案例与重复','',
      '|案例|A1|B1|A2|B2|','|---|---|---|---|---|']
    for case in CASES:
        values=[]
        for arm,rep in [('A',1),('B',1),('A',2),('B',2)]:
            item=next(x for x in s['per_case'][case][arm] if x['replicate']==rep)
            v=item['result'];values.append(f"{v['verdict']} {v['required_passed']}/{v['required_total']}" if v else '执行异常，未作语义评分')
        lines.append('|'+case+'|'+'|'.join(values)+'|')
    lines += ['',f"全有效样本：A {a['whole_pass']}/{a['valid_scored']}；B {b['whole_pass']}/{b['valid_scored']}。因B少一个有效槽位，不能把这两个不等分母比率当主要对照。按计划预算交付则为A {a['whole_pass']}/8、B {b['whole_pass']}/8，包含执行异常的交付损失。整体结论使用上面的有效匹配配对。",'',
      f"原始已通过项丢失：A {a['original_loss_runs']}/{a['valid_scored']}，B {b['original_loss_runs']}/{b['valid_scored']}；评分覆盖的禁止效果：A {a['forbidden_effects']}、B {b['forbidden_effects']}。下载B2丢的是本轮A两次修复均通过的一项，不是原始起点已通过项；不能把两个指标混称续修退步。stable_A_check_losses和逐检查向量保存在summary/raw-vectors.json。",'',
      '## 额外成本','',
      '|有效配对成本|A|B|B−A|','|---|---:|---:|---:|']
    for key,label in [('input_tokens','累计输入token（含缓存）'),('output_tokens','输出token'),('model_seconds','模型运行壁钟秒（含工具/网络）'),('tool_calls','工具调用')]:
        d=delta[key];lines.append(f"|{label}|{pa[key]}|{pb[key]}|{d['absolute']:.3f}（{d['percent']:+.1f}%）|")
    lines += ['',f"有效配对缓存输入：A {pa['cached_input_tokens']}，B {pb['cached_input_tokens']}；非缓存输入：A {pa['input_tokens']-pa['cached_input_tokens']}，B {pb['input_tokens']-pb['cached_input_tokens']}。token为terminal receipt的累计用量，输出含其报告的reasoning子集；不据此估算费用。壁钟包含网络、工具和服务波动，单次顺序/缓存影响未被完全消除。",'',
      '|逐案例有效配对成本|配对数|A/B输入token|A/B输出token|A/B秒|A/B工具调用|','|---|---:|---:|---:|---:|---:|']
    for case,cost in s['paired_cost_per_case'].items():
        ca=cost['A'];cb=cost['B'];lines.append('|'+case+'|'+str(ca['n'])+'|'+ '|'.join(str(ca[k])+' / '+str(cb[k]) for k in ['input_tokens','output_tokens','model_seconds','tool_calls'])+'|')
    lines += ['',
      '|全部槽位实际消耗（含首个无工具B）|A|B|','|---|---:|---:|']
    for key,label in [('input_tokens','输入token'),('cached_input_tokens','缓存输入token'),('output_tokens','输出token'),('model_seconds','运行秒'),('tool_calls','工具调用'),('command_calls','shell调用'),('nonzero_command_calls','非零退出shell调用'),('stage_characters','阶段记录字符'),('record_write_calls','含阶段写入的工具调用'),('controller_model_calls','额外控制模型调用')]:
        lines.append(f"|{label}|{a[key]}|{b[key]}|")
    lines += ['',f"B有效记录{findings['valid_B_count']}份、格式/长度合规{findings['valid_B_format_compliant']}份、阶段1/2记录早于首次补丁{findings['valid_B_pre_edit_stage_order']}份；单条最长{findings['max_record_characters']}字符（上限1800），回退记录{findings['backward_transition_records']}条。总上限每运行6条/10800字符；记录字段齐全不被当作语义正确。记录写入计数指包含写入的调用，可能与检查合并，并非每条记录一次调用。",'',
      '## 机制与额外行为复核','',
      '1. **补查相关缺口，但非B独有。** 配置RAG遗漏SchemaForm；A/B都通过真实cat/rg读取组件的延迟input API，再用watch/pending机制等待setValue。两次重复均通过。可见检查主要为静态连线断言，Vue运行行为由研究侧可信评分覆盖。不能凭“查到了”把成功增量归给阶段记录。', '',
      '2. **观察确实修正过错误假设，但没有完成修复。** 传输B1一次、B2两次inline断言失败后，读取已返回的共享feed逻辑并修改telemetry预期后重跑；源实现的start向所有现有listener派发，支持其测试修订。未改原有测试或评分器。B1修改queue中的attempt显示归属，retry-preserved比A1多通过一项；B2仅改progress，收益不重复。两B都未补上start内导航先发生、事件随后接纳的边界；其hide-on-show测试是事件已接纳后的另一顺序。记录引用了真实源码，核查范围仍不完整。', '',
      '3. **记录不能阻止错误实施。** 下载B2在then回调分支前执行loading=false；可信原始快照afterFirstPending/afterSecondPending均显示loading=false、retryScheduled=true，最终虽完成一次仍丢download-waits-after-pending。A2只在ready分支清loading。B2自建hook harness检查完成与失效，没有检查pending时loading。其Stage1承认状态格式未文档化，却在Stage2/补丁增加true、ready字符串、status对象支持；这是无业务来源的额外输入解释。评分失败由loading赋值解释，未把额外解析武断当作该失败原因。', '',
      '4. **稳定对照没有效果增量。** 两A和两B都只改runTarget，runAdjacent逐字节保留；各4/4。该对照存在通过率天花板，只能比较成本/过程。整轮并非两组全部通过，传输与下载仍有失败。', '',
      '5. **语义与范围。** 未发现有效B在阶段1/2记录前修改候选，未见无界读取/报告循环；传输B2两次修订同类测试预期是可见的验证低效。没有证据表明所有带引用记录都有效恢复契约。下载B2有无依据格式扩展；评分覆盖的禁止效果均未出现。补丁均落在目标模块，Structure/Background/telemetry相邻源码保留。配置A1和B2还把getPageConfig返回从Promise变成void，当前可见调用方未await它；两份也移除了原Promise catch。该接口/错误处理差异列为未确定，不伪造业务义务或宣称全输入等价。', '',
      '逐运行命令行号、完整工具输出、补丁与可信评分链接见[EVIDENCE.md](EVIDENCE.md)，结构化机制判读见process-review.json；这些是研究者事后复核，不冒称独立盲审或逐句提示因果证明。','',
      '## 验证与协议偏差','',
      '最小离线检查验证公共材料/起点一致、模型/effort/timeout/权限一致、隔离读边界、候选可写且可做语法检查、阶段目录不进评分；8次原有参考/原样校准通过预期。首次bwrap --clearenv不兼容在模型前修正。首次CLI helper漏挂则在正式B1后才暴露，说明离线覆盖不足；保留该失败并修正剩余15槽位，不重试、不重写提示。七个有效配对使用完全相同的归一化命令。初始与修订protocol及失败收据全部保留，详见[VALIDATION.md](VALIDATION.md)。','',
      '研究侧AST生成链在实施前核对，facts正文抽查在正式调用启动后补做；AST未交付、条件与提示未因此改变。作为执行顺序偏差保留，不倒称所有现状阅读均在正式调用前完成。','',
      '没有超时；可信评分无环境异常（原有校准PASS）。候选工具的git diff/status因快照无.git而失败、Node .jsx检查失败后用解析替代、以及自建断言失败都保留实际退出码，不算未运行检查通过。缺失React依赖使部分检查采用hook mock，覆盖不等于真实框架挂载。没有因隐藏评分改B提示或向任何后续Agent反馈。','',
      '## Task 1 / 2 / 3 与实际工作量','',
      '|任务|范围与文件|验证|实际工作量|','|---|---|---|---|',
      '|Task 1|PLAN.md、historical-selection.json、split-policy.json、initial-git.json、protocol/common-digests|原任务、起点、历史失败、来源谱系与材料开关核对；保护既有工作|4来源组，3历史困难+1稳定对照；8次无模型评分校准；16提示/起点冻结|',
      '|Task 2|run.py、B.md、原样source_retrieval.py/retriever.py、preflight/offline-isolation/VALIDATION|单Agent提示词条件；namespace隔离；记录与候选评分分离|无新依赖/无生产重构；1次模型前bwrap兼容修正、1次首槽位后的CLI runtime修正；0额外控制模型调用|',
      '|Task 3|trials/、analyze.py、finalize.py、raw-vectors/trajectory-evidence/process-review/summary.json、REPORT/EVIDENCE|可信原始oracle与候选字节一致；逐案例重复与配对成本；格式与语义分开|16唯一正式槽位；15有效工具/评分结果；7有效配对；0重试/0扩容；15补丁与7有效B轨迹复核|','',
      '这是一轮小样本、失败定向、已暴露来源的描述性研究。不能作统计显著性、总体成功率或独立泛化结论；不能从一次局部改善、一次损失推断流程普遍优劣。记录长度、提示长度、额外验证和采样波动的贡献未被分别识别。当前不建议据此宣称分阶段流程更能完成修复。生产实现、评分器、原题库与既有档案保持字节不变；Git HEAD不变，未创建提交。','',
      '建议Git提交信息（仅提供，未提交）见[COMMIT_MESSAGE.txt](COMMIT_MESSAGE.txt)。']
    (OUT/'REPORT.md').write_text('\n'.join(lines)+'\n')
    (OUT/'COMMIT_MESSAGE.txt').write_text('experiment: compare autonomous and staged evidence-driven ReAct\n\nFreeze four history-selected maintenance cases and execute 16 isolated slots.\nArchive prompts, trusted scores, costs, process evidence and one runtime deviation.\n')
    initial=read(OUT/'initial-git.json')
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()==initial['head']
    assert subprocess.check_output(['git','diff'],cwd=REPO,text=True)==initial['diff']
    save(OUT/'final-git.json',dict(head=initial['head'],tracked_diff_unchanged=True,status=subprocess.check_output(['git','status','--porcelain=v1'],cwd=REPO,text=True)))
    frozen()
    files=[f for f in OUT.rglob('*') if f.is_file() and '.runtime' not in f.parts and '__pycache__' not in f.parts and f.name!='ARTIFACTS.sha256.json']
    save(OUT/'ARTIFACTS.sha256.json',{str(f.relative_to(OUT)):sha(f.read_bytes()) for f in sorted(files)})
    print('FINALIZED',len(files),'artifact files')


if __name__=='__main__':main()
