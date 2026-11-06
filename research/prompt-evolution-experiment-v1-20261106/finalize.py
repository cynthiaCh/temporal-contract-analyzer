"""Render final descriptive report and evidence index; never calls a model."""
from difflib import unified_diff
import json
from pathlib import Path
import subprocess
from analyze import main as analyze,resources
from run import OUT,REPO,DEV,HOLDOUT,PRIOR,read,save,sha,check_frozen


def relative(path):return str(Path(path).relative_to(OUT))


def main():
    completion=read(OUT/'completion.json');assert completion['status']!='RUNNING'
    analyze();s=read(OUT/'summary.json');rows=read(OUT/'analysis-runs.json');traces=read(OUT/'trajectory-evidence.json')
    assert not list((OUT/'.runtime').glob('*')),'no credentials may remain'
    assert (OUT/'P0.md').read_text()+'\n'+(OUT/'RECORD_GUARD.md').read_text()==(PRIOR/'B.md').read_text()
    current=s['selected']['selected'] if s['selected'] else None
    for variant in ['P1','P2']:
        if (OUT/(variant+'.md')).exists():
            diff=''.join(unified_diff((OUT/'P0.md').read_text().splitlines(True),(OUT/(variant+'.md')).read_text().splitlines(True),fromfile='P0.md',tofile=variant+'.md'))
            (OUT/(variant+'.diff')).write_text(diff)
    evidence=['# 完整调用与证据索引','', '每次修复从独立冻结起点开始。评分在隔离空间外运行，未回传至修复Agent；优化器仅见开发反馈摘要。','']
    for entry in read(OUT/'invocations.json'):
        if entry['kind']=='optimizer':
            v=entry['label'];d=OUT/'candidates'/v;receipt=read(d/'result.json')
            evidence += [f"## {entry['sequence']:02d} 优化调用 {v}",'',
                ' · '.join(f'[{label}]({relative(path)})' for label,path in [('指令',d/'prompt.md'),('输入摘要',d/'packet-hashes.json'),('开发反馈packet',d/'workspace/development-feedback.json'),('轨迹',d/'events.jsonl'),('原始回答',d/'cli-output/answer.md'),('卫生检查',d/'validation.json')]),'',
                f"基于{receipt['current']}；正文{receipt['validation']['characters']}字符；有效{receipt['validation']['valid']}；用量{receipt['usage']}。",'']
            t=next(t for t in traces if t['split']=='optimizer' and t['variant']==v)
        else:
            r=next(r for r in rows if r['label']==entry['label']);d=Path(r['path'])/'jobs/j-001'
            evidence += [f"## {entry['sequence']:02d} {r['label']}",'',
                ' · '.join(f'[{label}]({relative(path)})' for label,path in [('完整prompt',d/'prompt.md'),('工具轨迹',d/'events.jsonl'),('阶段记录',d/'stages/records.jsonl'),('补丁',d/'changes.json'),('回答',d/'cli-output/answer.md')] if path.exists()),'',
                f"正文来源{r['variant']}；评分{r['score']}；输入/输出token {(r.get('usage') or {}).get('input_tokens')} / {(r.get('usage') or {}).get('output_tokens')}；工具{r['tool_calls']}；阶段字符{r['stage_characters']}。",'']
            if r.get('raw_oracle'):evidence += [f"[原始可信评分]({relative(r['raw_oracle'])})",'']
            t=next(t for t in traces if t.get('id')==r['id'])
        evidence += ['|轨迹行|工具类型|退出/状态|实际命令摘要|','|---:|---|---|---|']
        for tool in t['tools']:
            item=tool['item'];command=item.get('command',json.dumps(item.get('changes',[]),ensure_ascii=False))[:180].replace('|','\\|').replace('\n',' ↵ ')
            evidence.append(f"|{tool['line']}|{tool['kind']}|{item.get('exit_code',item.get('status',''))}|{command}|")
        evidence.append('')
    (OUT/'EVIDENCE.md').write_text('\n'.join(evidence)+'\n')
    h=s['holdout'];a=h['P0'];b=h['Pstar'];delta=s['holdout_cost_delta'];cost=s['costs']
    heading='两轮自动改写未找到开发集更优prompt，保留P0' if current=='P0' else f'自动选择{current}，用留出结果检查迁移' if current else 'prompt演化实验提前停止：保留原始故障'
    lines=['# '+heading,'',
      f"状态：{completion['status']}。执行{s['invocations']}/16上限调用：{s['repairs']}次修复、{s['optimizer_calls']}次优化；没有补跑或人工重写候选。开发P0整体{s['development']['P0']['whole_pass']}/2、必需{s['development']['P0']['required_passed']}/{s['development']['P0']['required_total']}。最终选择 **{current or '未产生'}**。",'']
    if current=='P0':
        lines += ['**没有发生被接受的prompt更新。P*与P0正文及留出完整输入逐字节相同。** 本轮实现了反馈→自动改写→重跑→保守选择，但两轮候选没有通过预定接受规则。留出两组的任何分数/成本差异都属于同prompt独立运行波动，不能称作演化收益。','']
    elif current:
        lines += [f"开发选择内表现改善后冻结{current}，再运行优化器隔离的留出任务。开发增益包含评分反馈与额外调用预算，不是独立泛化成绩，也不能归因于prompt某一句话。",'']
    lines += [f"留出P0整体{a['whole_pass']}/{a['valid']}，P*整体{b['whole_pass']}/{b['valid']}；有效配对{len(s['pairs'])}，P*胜{s['wins']}、负{s['losses']}、平{s['ties']}。",'']
    if a['valid']==4 and b['valid']==4 and a['whole_pass']==4 and b['whole_pass']==4:
        lines += ['留出两组均全过，存在通过率天花板；没有成功率提升证据。成本和轨迹只作描述性比较。','']
    lines += ['## Task 1：冻结假设、预算与划分','',
      '本轮测试“开发反馈能否自动找到更好的执行prompt，并迁移到优化器未见任务”。不是参数训练，不更新模型权重；也不是生产系统每次任务自动改prompt。仍是单Agent工具循环，串行优化/修复调用，由外层脚本管理候选版本及接受/拒绝。阶段执行本身仍为提示词约束，无强制语义状态机。','',
      '固定gpt-6-sol/low、workspace-write、approval never、600秒/调用，沿用CLI输出设置无新增token硬上限。P0沿用上轮B正文，记录限制拆为共同RECORD_GUARD，正文+后缀可重建旧B字节。P1/P2仅改变流程正文；原任务、冻结起点、源码RAG、固定五题与顺序、工具权限、运行环境相同。AST交付两组均关闭。','',
      '|划分|案例|来源与解释范围|','|---|---|---|',
      f"|开发|{DEV[0]}|clean-room重建，研究暴露，前轮曾失败|",
      f"|开发|{DEV[1]}|authored development同源扩展，前轮重复不稳定|",
      f"|优化器留出|{HOLDOUT[0]}|authored extension；与开发不同source unit，历史已有成绩|",
      f"|优化器留出|{HOLDOUT[1]}|private-incident clean-room；与开发不同source unit，历史已有成绩|",'',
      '留出仅指本轮优化器没有收到这些任务/源码/成绩；不是整个研究或模型从未见过。全部来源有研究暴露，独立泛化案例0；没有把同源变体计作独立事故。近期附加材料基线在留出两题有天花板风险，按冻结计划保留，没有为制造失败换题或降低模型。','',
      '预算在首次调用前冻结：开发P0/P1/P2各2次=6，优化调用2次，留出2题×P0/P*×2重复=8，总上限16；无效候选跳过相应开发槽位，不补齐。调度种子2026110601只控制顺序，模型无可控采样种子。留出同case/rep成对交错，第二次反转组顺序。','',
      '## Task 2：自动改写、筛选与隔离实现','',
      'run.py复用原工作台和已验证的完整CLI挂载，通过独立命名空间阻断研究侧目录/其他运行访问。优化器只得到DEV白名单输入：原任务与原始源码、当前/已评分prompt、修复补丁、shell工具轨迹摘录和评分布尔摘要。每条输出最多6000字符，截断明确标记；完整各类工具事件仍在研究归档。没有评分器源码、参考补丁、隐藏测试输入/断言、留出数据或上一轮完整研究报告。开发反馈是本轮授权的额外信息通道，修复Agent仍只收到公共材料和当前通用prompt。','',
      '候选正文上限5000字符，禁止案例名、路径、程序标识符、检查ID或答案代码；记录限制为固定后缀。原始优化回答与卫生检查全部保存，机械合规不等于语义正确。不存在人工根据评分补句或第三轮。','',
      '**接受规则**：两道开发题均可信评分；无禁止效果/原通过项丢失；不丢当前最优在任一题已通过的检查；(整体PASS数, 必需项通过总数)字典序严格增加。平局保留旧版。不用耗时或token噪声选胜者，不用留出结果选择prompt。','',
      '|版本|正文字符|开发整体|必需项|决定|','|---|---:|---:|---:|---|']
    for v in ['P0','P1','P2']:
        dev=s['development'][v];path=OUT/(v+'.md');rec=next((r for r in s['selection'] if r['candidate']==v),None)
        decision='初始版本' if v=='P0' else ('接受' if rec and rec['decision']['accept'] else '拒绝' if rec else '未完成')
        if rec:decision+='：'+rec['decision']['reason']
        lines.append(f"|[{v}]({v}.md)|{len(path.read_text()) if path.exists() else 0}|{dev['whole_pass']}/{dev['valid']}|{dev['required_passed']}/{dev['required_total']}|{decision}|")
    lines += ['', '每题/版本只有一次开发运行；分数变化混合了prompt与采样波动。即使接受也只是开发选择内增益，不能说明差异稳定。完整决定见selection.json，分析从原始向量重放该规则。','',
      '## Task 3：留出与重复波动','',
      '|案例|P0第1次|P*第1次|P0第2次|P*第2次|','|---|---|---|---|---|']
    for c in HOLDOUT:
        vals=[]
        for arm,rep in [('P0',1),('Pstar',1),('P0',2),('Pstar',2)]:
            r=next((r for r in rows if r['split']=='holdout' and r['case']==c and r['arm']==arm and r['replicate']==rep),None)
            vals.append(f"{r['score']['verdict']} {r['score']['required_passed']}/{r['score']['required_total']}" if r and r['score'] else r['category'] if r else '未运行')
        lines.append('|'+c+'|'+'|'.join(vals)+'|')
    lines += ['',f"留出原始已通过项损失：P0 {a['original_loss_runs']}/{a['valid']}、P* {b['original_loss_runs']}/{b['valid']}；禁止效果运行：P0 {a['forbidden_runs']}、P* {b['forbidden_runs']}。逐检查得失及可信原始oracle链接见summary.json、analysis-runs.json和EVIDENCE.md。",'',
      '## 资源：搜索投入与最终执行分开','',
      '|范围|调用数|输入token（含缓存）|非缓存输入|输出token|壁钟秒（含工具/网络）|工具调用|','|---|---:|---:|---:|---:|---:|---:|']
    for key,label in [('development','开发评分6槽位'),('optimizer','自动改写2槽位'),('holdout','留出8槽位'),('all','全实验')]:
        r=cost[key];lines.append('|'+label+'|'+'|'.join(str(r[k]) for k in ['n','input_tokens','uncached_input_tokens','output_tokens','seconds','tool_calls'])+'|')
    extra=[r for r in rows if r['split']=='development' and r['variant']!='P0']
    optrows=[read(OUT/'candidates'/v/'result.json') for v in ['P1','P2'] if (OUT/'candidates'/v/'result.json').exists()]
    extraresources=resources(extra+[dict(r,tool_calls=next(t for t in traces if t['split']=='optimizer' and t['variant']==r['variant'])['tools'].__len__()) for r in optrows])
    save(OUT/'search-overhead.json',dict(extra_beyond_P0_development=extraresources,definition='P1/P2 development repairs plus two optimizer calls; excludes baseline development and heldout evaluation'))
    lines += ['',f"相对只跑P0开发对照，额外搜索包括P1/P2开发修复与两次改写：{extraresources['n']}调用、输入{extraresources['input_tokens']}、输出{extraresources['output_tokens']} token、{extraresources['seconds']}秒。全开发+优化成本均已列出，没有只报告最终prompt成本。",'',
      '|留出执行成本|P0|P*|P*−P0|','|---|---:|---:|---:|']
    for key,label in [('input_tokens','输入token'),('output_tokens','输出token'),('seconds','运行秒'),('tool_calls','工具调用')]:
        d=delta[key];pct=f"{d['percent']:+.1f}%" if d['percent'] is not None else '不可比'
        lines.append(f"|{label}|{a['resources'][key]}|{b['resources'][key]}|{d['absolute']:.3f}（{pct}）|")
    lines += ['', '累计输入含重复上下文与缓存，不能直接当费用；未估算金额。时间含工具、服务和网络波动。搜索带来的额外评分信息和预算与自动改写共同存在，未用等总预算的其他搜索方法控制，不能声称这是最优优化器或收益仅由某种流程结构造成。','',
      '## 过程证据与实际改写','',
      'P1强化了“接纳时机、回调返回后资格、重试/后续路径”及“检查是否真正触达争议路径”。P2再次强调所有权变化、启动/回调两时点有效性、不同副作用是否继续以及可证伪验证。两版都是通用正文，原始输出见P1.md/P2.md，与P0的逐行差异见P1.diff/P2.diff；不存在把源码路径或参考答案直接塞进prompt。','',
      'P1下载修复新增generation及卸载保护，却让close仅隐藏界面、未失效当前generation或取消重试；工具/补丁与开发评分共同显示关闭后pending仍可继续。其下载必需项5/8，原通过的close-ignores-pending丢失；传输仍8/10。选择器按原通过项丢失拒绝它。这说明自动改写的语义看似合理，并不保证执行实现更好；拒绝规则在开发范围内阻止了采用已观察到的退步。','',
      'P2下载已增加close/reopen失效与取消，却仍在响应分支前无条件清loading，下载7/8；其自建hook检查通过，没有覆盖pending等待状态。P2传输在queue显示前增加attempt检查，retry-preserved变为通过，传输9/10，start-switch-admission仍失败。两项相加仍16/18，但整体从1/2变为0/2，且丢失P0已通过的等待检查，不能以总检查数相同认定版本更优。阶段记录与通用提醒没有保证相关不变量落实到代码和断言中。','',
      '14份补丁均只涉及目标模块：开发下载只改hook，传输改progress及P2的queue；留出文档只改editor/workspace，本地配置只改Personnel editor。相邻Background、telemetry、search preview、Structure源码均保留。有界评分与范围核对不证明所有未测输入/接口完全等价；本轮也未采用任何新prompt进入生产。','',
      '优化器实际读取轨迹及所有修复检查、阶段产物、补丁、最终回答、原始可信评分见[EVIDENCE.md](EVIDENCE.md)。这些是研究者事后源码/轨迹复核，未冒称独立盲审；不凭模型自述判定查证有效。开发/留出后验成绩没有被根Agent手工注入候选或反馈至下一轮留出修复。','',
      '## 验证、工作量与限制','',
      '离线helper启动、命名空间读边界、合成写入/语法、阶段评分边界、选择器/卫生合成检查通过；4案例×原样/参考共8次运行前无模型校准符合UNDERREACH/PASS，每次可信修复评分还包含原运行器自带参考校准。公共材料/起点冻结，P1/P2生成前的优化packet及生成后候选摘要可核对；P*在留出前冻结。分析验证原始评分、候选字节、oracle哈希、选择重放与修复命令一致性，详见audit.json和[VALIDATION.md](VALIDATION.md)。','',
      f"实际工作量：4案例来源审查与材料准备；8次无模型校准；{s['repairs']}次独立修复、{s['optimizer_calls']}次优化；{len(s['selection'])}次自动接受/拒绝决定；{len(s['pairs'])}个有效留出配对；0人工补写候选、0追加轮次、0生产改动。运行/验证异常单列audit.json；不将未评分或执行异常冒充行为失败。",'',
      '规模仅两开发案例、两候选、两留出来源、每留出两重复；案例均研究暴露，留出基线可能饱和。不能作显著性、总体成功率、独立泛化或prompt逐句因果结论。若未找到新版本，就应停止并报告未找到，而不是继续改到碰巧获胜。此实验不部署到生产、不设置持续自动更新，也不修改任何模型权重。','',
      '计划/实现：PLAN.md、OPTIMIZER.md、run.py；版本与选择：P0/P1/P2/Pstar.md、selection.json、selected.freeze.json；结果：summary.json、REPORT/EVIDENCE、trials/、candidates/。Git提交信息仅建议于COMMIT_MESSAGE.txt，未创建提交。']
    (OUT/'REPORT.md').write_text('\n'.join(lines)+'\n')
    (OUT/'COMMIT_MESSAGE.txt').write_text('experiment: evaluate feedback-driven prompt evolution\n\nRun two development-only prompt revisions with conservative automatic selection.\nFreeze the selected workflow and archive held-out behavior, search cost and traces.\n')
    original=read(OUT/'initial-git.json')
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()==original['head']
    assert subprocess.check_output(['git','diff'],cwd=REPO,text=True)==original['diff']
    save(OUT/'final-git.json',dict(head=original['head'],tracked_diff_unchanged=True,status=subprocess.check_output(['git','status','--short'],cwd=REPO,text=True)))
    if current=='P0':
        for c in HOLDOUT:
            assert len({r['prompt_sha256'] for r in rows if r['split']=='holdout' and r['case']==c})<=1
    check_frozen()
    files=[f for f in OUT.rglob('*') if f.is_file() and '__pycache__' not in f.parts and '.runtime' not in f.parts and f.name!='ARTIFACTS.sha256.json']
    save(OUT/'ARTIFACTS.sha256.json',{relative(f):sha(f.read_bytes()) for f in sorted(files)})
    print('FINALIZED',current,len(files),'files')


if __name__=='__main__':main()
