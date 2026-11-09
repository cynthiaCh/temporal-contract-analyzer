"""All slots, raw behavior vectors and known/unknown costs, without learning."""
import hashlib
import json
import subprocess
import time
from pathlib import Path
from archive import save,sha
from feedback import feedback
from report_common import aggregate

A=Path(__file__).resolve().parent;REPO=A.parent.parent
def read(path,default=None):return json.loads(Path(path).read_text()) if Path(path).exists() else default


def main():
    schedule=read(A/'schedule.json');actual=read(A/'actual-schedule.json',[])
    routes={c['alias']:read(A/'routing'/c['alias']/'route.json') for c in read(A/'cases.json')}
    targets=read(A/'reporting-targets.json');rows=[]
    for slot in schedule:
        rec=next((r for r in actual if r['slot']==slot['slot']),None)
        root=A/'runs'/slot['slot']/'archive';alias=slot['alias']
        standards=read(A/'materials'/alias/'standards.json')
        original=read(A/'calibration'/alias/'original/stdout.json')
        valid=bool(rec and rec.get('scoring_admissible') and rec.get('scoring_status')=='COLLECTED'
                   and rec.get('scored_candidate_unchanged') and rec.get('score_result',{}).get('score_valid'))
        score=read(root/'score/stdout.json') if valid else None
        relations=feedback(original,[score],standards)['runs'][0] if score else None
        observed=score['observed_effects'] if score else {r['effect']:None for r in standards}
        compliance={r['effect']:(observed[r['effect']]==r['expected'] if valid else None) for r in standards}
        rows.append({**slot,'started':rec is not None,'valid_score':valid,
            'status':rec.get('status') if rec else 'NOT_STARTED',
            'failure_class':rec.get('failure_class') if rec else None,
            'scoring_status':rec.get('scoring_status') if rec else None,
            'verdict':score['verdict'] if score else None,'whole_task_pass':score['verdict']=='PASS' if score else None,
            'satisfied':sum(compliance.values()) if valid else None,'total_effects':len(standards),
            'observed_effects':observed,'expected_effects':{r['effect']:r['expected'] for r in standards},
            'compliance_vector':compliance,'targets':{k:compliance[k] for k in targets[alias]},
            'newly_satisfied_vs_original':[r['effect'] for r in relations['improvements']] if relations else None,
            'lost_original_successes':[r['effect'] for r in relations['regressions']] if relations else None,
            'retained_original_successes':[r['effect'] for r in relations['retained_original_successes']] if relations else None,
            'failed_checks':relations['failed_checks'] if relations else None,
            'selected_experience':routes[alias]['selected'] if slot['arm']=='B' else None,
            'hit_case':routes[alias]['selected'] is not None,
            'AB_prompts_identical':read(A/'prompts'/alias/'comparison.json')['identical'],
            'actual_prompt_sha256':sha(root/'input/actual-prompt.md') if (root/'input/actual-prompt.md').exists() else None,
            'usage':read(root/'usage.json') if rec else None,'seconds':rec.get('seconds') if rec else None,
            'archive':str(root.relative_to(A)) if rec else None,
            'service_errors':read(root/'service-errors.json') if rec else None,
            'archive_status':read(root/'archive-status.json') if rec else None})
    def group(selected):
        started=[r for r in selected if r['started']];valid=[r for r in selected if r['valid_score']]
        return {'planned':len(selected),'started':len(started),'valid':len(valid),'invalid':len(started)-len(valid),
                'not_started':len(selected)-len(started),'whole_passes':sum(r['whole_task_pass'] for r in valid),
                'pass_denominator':len(valid),'pass_rate':sum(r['whole_task_pass'] for r in valid)/len(valid) if valid else None,
                'rate_display':str(sum(r['whole_task_pass'] for r in valid))+'/'+str(len(valid)) if valid else '通过率不可计算',
                'costs':aggregate(started)}
    percase={}
    for alias in routes:
        arms={arm:group([r for r in rows if r['alias']==alias and r['arm']==arm]) for arm in ['A','B']}
        behavior={}
        for key in next(r['compliance_vector'] for r in rows if r['alias']==alias):
            behavior[key]={}
            for arm in ['A','B']:
                valid=[r for r in rows if r['alias']==alias and r['arm']==arm and r['valid_score']]
                behavior[key][arm]={'passes':sum(r['compliance_vector'][key] for r in valid),'valid':len(valid)}
        pairs=[]
        for repeat in (1,2):
            aa=next(r for r in rows if r['alias']==alias and r['arm']=='A' and r['repeat']==repeat)
            bb=next(r for r in rows if r['alias']==alias and r['arm']=='B' and r['repeat']==repeat)
            comparable=aa['valid_score'] and bb['valid_score']
            pairs.append({'repeat':repeat,'both_valid':comparable,
                'B_new_passes_vs_A':[k for k,v in bb['compliance_vector'].items() if v and aa['compliance_vector'][k] is False] if comparable else None,
                'B_losses_vs_A':[k for k,v in bb['compliance_vector'].items() if v is False and aa['compliance_vector'][k] is True] if comparable else None,
                'interpretation':'Descriptive repeat pairing only; identical fallback prompt differences cannot be attributed to experience.' if read(A/'prompts'/alias/'comparison.json')['identical'] else 'Descriptive repeat pairing only; no sampling or causal control.'})
        percase[alias]={'route':routes[alias],'prompts':read(A/'prompts'/alias/'comparison.json'),'arms':arms,
                       'behavior_pass_counts':behavior,'paired_descriptive_deltas':pairs}
    subsets={}
    for name,selection in [('all',rows),('hit',[r for r in rows if r['hit_case']]),('fallback',[r for r in rows if not r['hit_case']])]:
        subsets[name]={arm:group([r for r in selection if r['arm']==arm]) for arm in ['A','B']}
    costs={'test_total':aggregate([r for r in rows if r['started']]),
           'per_arm':{arm:aggregate([r for r in rows if r['started'] and r['arm']==arm]) for arm in ['A','B']},
           'engineering':{'batch_wall_seconds':time.time()-read(A/'initial-state.json')['time'],
                          'preparation_seconds':read(A/'prepared.json')['seconds'],'tokens':None,'money':None},
           'extraction':{'sessions':0,'requests':0},'reflection':{'sessions':0,'requests':0},
           'judge':{'sessions':0,'requests':0},'new_native_scoring_invocations':sum(r['valid_score'] for r in rows),
           'historical_calibration_invocations':0,
           'prior_development_excluded_from_test_denominators_and_costs':True}
    initial=read(A/'initial-state.json');sources=read(A/'provenance.json')['copied']
    frozen=read(A/'freeze.json')['files']
    integrity={'source_files_unchanged':all(sha(x['source'])==x['sha256'] for x in sources),
      'frozen_files_unchanged':all(sha(p)==h for p,h in frozen.items()),
      'preexisting_index_diff_preserved':hashlib.sha256(subprocess.check_output(['git','diff','--cached','--binary'],cwd=REPO)).hexdigest()==initial['cached_diff_sha256'],
      'preexisting_unstaged_diff_preserved':hashlib.sha256(subprocess.check_output(['git','diff','--binary'],cwd=REPO)).hexdigest()==initial['unstaged_diff_sha256'],
      'head_unchanged':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()==initial['head'],
      'started_slots':sum(r['started'] for r in rows),'valid_scores':sum(r['valid_score'] for r in rows),
      'all_started_prompts_match_frozen':all(r['actual_prompt_sha256']==sha(A/'prompts'/r['alias']/(r['arm']+'.md')) for r in rows if r['actual_prompt_sha256'] is not None),
      'request_cap':192,'requests_known_total':costs['test_total']['requests_started']}
    summary={'status':'completed' if (A/'completion.json').exists() else 'stopped','stop':read(A/'stop.json'),
      'fixed_experience':{'version':read(A/'frozen-library.json')[0]['version'],'text_sha256':read(A/'frozen-library.json')[0]['text_sha256'],
        'object_sha256':read(A/'registry-conversion.json')['source_candidate_sha256'],'exploratory_only':True},
      'schedule':schedule,'slots':rows,'per_case':percase,'subsets':subsets,'costs':costs,'integrity':integrity,
      'interpretation':{'previously_exposed':True,'same_source_cross_language':True,'independent_generalization':False,
        'statistical_significance_claim':False,'fallback_identical_prompts_do_not_establish_experience_equivalence':True,
        'prior_development_whole_passes':'0/2, preserved unchanged','no_training_results_in_test_denominator':True}}
    save(A/'summary.json',summary);save(A/'behavior-vectors.json',{'slots':rows,'per_case':percase})
    save(A/'costs.json',costs);save(A/'integrity.json',integrity)
    lines=['本批固定经验两案例 A/B 探索性对照已'+('完成全部 8 槽。' if (A/'completion.json').exists() else '按停止规则结束，未补跑。'),'',
      '经验为 R03 修订后、其余四条保持不变的五条规则，正文 SHA256：`'+summary['fixed_experience']['text_sha256']+'`。源对象、AI 辅助内容核查、父版本关联和开发回验均在 experience-source/ 原样保存。开发整题 0/2 与全部退步不改变；本批仅按明确授权登记为探索性条件，不是生产接纳或已证有效。','',
      'Test-1（query Python）沿用准入分析 T4，满足五项 requires，排除 no_lazy_shared_mechanism 被源码否定，路由选中该经验。Test-2（document Python eval-v2）沿用准入分析 T3，库中没有 T3 经验，回退 AUTO，A/B 提示相同。路由只得到当前任务、候选源码/文档、原自动分析、绑定当前输入的 AI 语义核查和经验适用描述，没有获得案例 ID、历史成绩、测试标准或开发来源身份。','',
      '所有会话固定 gpt-5.6-terra / low，24 请求、600 秒，并发 1。A/B 共享同一原始候选、任务、自动 Contract 和公共要求；B 仅在命中时追加原样经验正文。独立工作区不继承补丁或会话。调用前冻结 schema/输入/路由/提示/代码/评分版本与调度。提取、反思、评委和连接预跑均为 0。','',
      '|案例/条件|计划|启动|有效|无效|未启动|整题通过/有效评分|','|---|---|---|---|---|---|---|']
    for alias,data in percase.items():
        for arm,g in data['arms'].items():lines.append('|{} / {}|{}|{}|{}|{}|{}|{}|'.format(alias,arm,g['planned'],g['started'],g['valid'],g['invalid'],g['not_started'],g['rate_display']))
    lines+=['','全体与命中/回退子集：','','|集合|A 整题|B 整题|','|---|---|---|']
    for name,data in subsets.items():lines.append('|{}|{}|{}|'.format(name,data['A']['rate_display'],data['B']['rate_display']))
    lines+=['','实际槽位：','','|顺序|案例|条件|重复|状态|整题|满足关系|丢失原通过行为|','|---|---|---|---|---|---|---|---|']
    for r in rows:
        loss=', '.join(r['lost_original_successes']) if r['lost_original_successes'] else ('无' if r['valid_score'] else '未知')
        lines.append('|{}|{}|{}|{}|{}|{}|{}|{}|'.format(r['position'],r['alias'],r['arm'],r['repeat'],r['status'],r['verdict'] or '未评分',str(r['satisfied'])+'/'+str(r['total_effects']) if r['valid_score'] else '—',loss))
    for alias,data in percase.items():
        these=[r for r in rows if r['alias']==alias]
        lines+=['','完整行为向量 '+alias+'（按对应标准判断；禁止行为期望 false）：','','|行为|'+'|'.join(r['arm']+str(r['repeat']) for r in these)+'|','|---|'+'|'.join('---' for _ in these)+'|']
        for key in data['behavior_pass_counts']:
            lines.append('|'+key+'|'+'|'.join(('通过' if r['compliance_vector'][key] else '失败') if r['valid_score'] else '未评分' for r in these)+'|')
        lines+=['','目标行为（描述性计数）：','']
        for key in targets[alias]:lines.append(key+': '+json.dumps(data['behavior_pass_counts'][key],ensure_ascii=False))
        lines+=['','同重复 A/B 完整新增通过与损失：','',json.dumps(data['paired_descriptive_deltas'],ensure_ascii=False)]
    lines+=['','成本（旧开发与历史评分不并入）：','','|范围|会话|请求|已知 tokens 合计|未知请求用量|工具|秒|','|---|---|---|---|---|---|---|']
    for label,c in [('A',costs['per_arm']['A']),('B',costs['per_arm']['B']),('全部新增测试',costs['test_total'])]:
        lines.append('|{}|{}|{}|{}|{}|{}|{}|'.format(label,c['sessions_started'],c['requests_started'],c['known_usage_subtotal']['total_tokens'],c['unknown_usage_requests'],c['tool_attempts'],round(c['seconds'],3) if c['seconds'] is not None else None))
    lines+=['','每案例、每条件成本详见 summary.json 的 per_case；全部已知字段与未知数量见 costs.json。金额及工程准备 tokens 无法从接口读取，保持 null；缺失请求用量不会补零。若无有效评分，整题通过率不可计算，不写 0%。','',
      '停止记录：'+json.dumps(summary['stop'],ensure_ascii=False),'',
      '服务错误、部分输出与归档错误分别保存在各 archive 的 service-errors.json、model-outcome.json、archive-status.json 及原始事件/日志中。未完成候选不进入行为评分。每份有效候选只调用对应原评分器一次，query 保留 29 项，document 保留 23 项必需与 1 项禁止行为。复用 21 份已核对版本的历史校准，不重新评分历史候选。','',
      '结果解释边界：两个案例均已暴露，属于同源跨语言探索，不是独立泛化测试。每条件两次重复仅作描述，不声称统计显著、稳定有效或控制模型采样。Test-2 相同提示下的任何得失只反映独立运行差异，不能归因为经验，也不能证明经验效果等价。不将开发回验并入测试分母，不只报告命中或较好结果。','',
      '公共 Contract 与既有准入输出逐字复用。Test-1 保留原先“不应触发执行”的表述，而新增经验 R03 明确目标允许零入口或已中止信号入口；本批不修改该公共材料。A/B 都受同一辅助 Contract 及“依据任务源码核查、不盲从”公共要求约束，这也是解释结果时的固定条件。','',
      '推荐 Git commit subject: `research: run fixed-experience two-case routed A/B pilot`','',
      '推荐 Git commit body:','','```text','Freeze the R03-revised research experience and reuse admitted Python inputs.',
      'Record source-bound routing, exact A/B prompts and the requested eight-slot order.',
      'Use identical isolated repair budgets with one score per valid candidate.',
      'Report all outcomes, regressions, fallback repeats and known/unknown costs.',
      'Preserve historical interruptions and development losses; do not learn, retry,',
      'modify production experience or claim independent generalization.','```','',
      '未创建 Git 提交、修改历史记录、更新生产经验库或自动启动下一批。']
    (A/'REPORT.md').write_text('\n'.join(lines)+'\n')
    hashes={str(p.relative_to(A)):sha(p) for p in A.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='ARTIFACTS.sha256'}
    (A/'ARTIFACTS.sha256').write_text(''.join(h+'  '+p+'\n' for p,h in sorted(hashes.items())))
    print(json.dumps({'status':summary['status'],'subsets':subsets,'costs':costs,'integrity':integrity},ensure_ascii=False),flush=True)


if __name__=='__main__':main()
