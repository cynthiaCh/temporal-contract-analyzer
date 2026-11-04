"""Descriptive discovery-data replay of a candidate A/D gate; never calls a model."""
import argparse
import csv
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from temporal_contract_analyzer import archive
from temporal_contract_analyzer.routing import decide, prefilter, POLICY


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--matrix',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--node')
    args=parser.parse_args();root=args.output.resolve();root.mkdir(parents=True,exist_ok=False)
    data=json.loads(args.matrix.read_text());pairs={}
    for row in data:
        if row['condition'] not in ('none','review'):continue
        key=(row['case'],row['model'],row['effort'])
        if row['condition'] in pairs.setdefault(key,{}):raise ValueError('Duplicate arm')
        pairs[key][row['condition']]=row
    rows=[];decisions=[];groups=set()
    for key,arms in sorted(pairs.items()):
        assert set(arms)=={'none','review'}
        a,d=arms['none'],arms['review'];folder=Path(d['path']);m=json.loads((folder/'manifest.json').read_text())
        assert a['experiment']==d['experiment']
        store=folder.parent.with_name(folder.parent.name[:-len('-experiments')])
        archive.verify(m['report_id'],store)
        report=json.loads(archive.artifact(m['report_id'],'report.json',store))
        sources=archive.read_sources(m['report_id'],store)
        # Decide before reading either arm's outcome/evaluation.
        decision=decide(m['task'],report,sources,args.node)
        selected=arms[decision['condition']]
        latest=max((folder/'evaluations').glob('*/summary.json'),key=lambda p:p.stat().st_mtime_ns)
        evaluation=json.loads(latest.read_text())
        assert evaluation['calibration_verdict']=='PASS'
        progress={}
        for condition,arm in arms.items():
            assert evaluation['jobs'][arm['job']]['status']==arm['outcome'], 'Stale outcome export'
            outcome=json.loads((folder/evaluation['jobs'][arm['job']]['result_path']).read_text())
            progress[condition]=dict(missing=outcome['missing_required_effects'],forbidden=outcome['observed_forbidden_effects'])
        rawjobs={j['id']:j for j in m['jobs']}
        j=rawjobs[selected['job']]
        chosen=progress[decision['condition']]
        def delta(baseline):
            previous=progress[baseline]
            gained=['required:'+x for x in sorted(set(previous['missing'])-set(chosen['missing']))]
            gained+=['forbidden:'+x for x in sorted(set(previous['forbidden'])-set(chosen['forbidden']))]
            lost=['required:'+x for x in sorted(set(chosen['missing'])-set(previous['missing']))]
            lost+=['forbidden:'+x for x in sorted(set(chosen['forbidden'])-set(previous['forbidden']))]
            return gained,lost
        gained_D,lost_D=delta('review');gained_A,lost_A=delta('none')
        # Source grouping is used only for the validation limitation report.
        parts=Path(m['case']['manifest']).parts
        source_group=parts[1] if len(parts)>1 and parts[0]=='case-clusters' else m['case']['manifest']
        groups.add(source_group)
        rows.append(dict(case=key[0],model=key[1],effort=key[2],source_group=source_group,
            action=decision['action'],condition=decision['condition'],reason=decision['reason'],family=decision['family'],
            A_outcome=a['outcome'],D_outcome=d['outcome'],replayed_outcome=selected['outcome'],
            selected_experiment=selected['experiment'],selected_job=selected['job'],
            A_missing=len(progress['none']['missing']),D_missing=len(progress['review']['missing']),
            selected_missing=len(progress[decision['condition']]['missing']),
            selected_forbidden=len(progress[decision['condition']]['forbidden']),
            A_missing_effects=progress['none']['missing'],D_missing_effects=progress['review']['missing'],selected_missing_effects=chosen['missing'],
            A_forbidden_effects=progress['none']['forbidden'],D_forbidden_effects=progress['review']['forbidden'],selected_forbidden_effects=chosen['forbidden'],
            gained_vs_D=gained_D,lost_vs_D=lost_D,gained_vs_A=gained_A,lost_vs_A=lost_A,
            selected_report_characters=j['report_characters'],
            A_input_tokens=(rawjobs[a['job']].get('usage') or {}).get('input_tokens'),
            A_output_tokens=(rawjobs[a['job']].get('usage') or {}).get('output_tokens'),
            D_input_tokens=(rawjobs[d['job']].get('usage') or {}).get('input_tokens'),
            D_output_tokens=(rawjobs[d['job']].get('usage') or {}).get('output_tokens'),
            selected_input_tokens=(j.get('usage') or {}).get('input_tokens'),
            selected_output_tokens=(j.get('usage') or {}).get('output_tokens'),
            D_report_characters=rawjobs[d['job']]['report_characters']))
        decisions.append(dict(case=key[0],model=key[1],effort=key[2],report_id=m['report_id'],decision=decision))
    summary=dict(policy=POLICY,qualification='POST-HOC DISCOVERY REPLAY, NOT NEW AGENT RUNS OR HELD-OUT VALIDATION',
        configurations=len(rows),discovery_cases=len({r['case'] for r in rows}),source_groups=len(groups),
        A_success=sum(r['A_outcome']=='passed' for r in rows),D_success=sum(r['D_outcome']=='passed' for r in rows),
        replayed_success=sum(r['replayed_outcome']=='passed' for r in rows),
        D_deliveries=sum(r['action']=='D' for r in rows),A_deliveries=sum(r['action']=='A' for r in rows),
        A_missing=sum(r['A_missing'] for r in rows),D_missing=sum(r['D_missing'] for r in rows),
        selected_missing=sum(r['selected_missing'] for r in rows),
        gained_vs_D=sum(len(r['gained_vs_D']) for r in rows),lost_vs_D=sum(len(r['lost_vs_D']) for r in rows),
        configurations_with_losses_vs_D=sum(bool(r['lost_vs_D']) for r in rows),
        selected_report_characters=sum(r['selected_report_characters'] for r in rows),
        fixed_D_report_characters=sum(r['D_report_characters'] for r in rows),new_model_calls=0,
        validation='Only 3 source groups; the two download variants share a family. Independent families are needed before generalization claims.')
    for prefix in ('A','D','selected'):
        for kind in ('input_tokens','output_tokens'):
            values=[r[prefix+'_'+kind] for r in rows]
            summary[prefix+'_'+kind]=sum(values) if all(type(v) is int for v in values) else None
    for name,value in [('summary.json',summary),('replay.json',rows),('decisions.json',decisions)]:archive.atomic_json(root/name,value)
    with (root/'replay.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    lines=['# 选择性 A/D 门控：探索数据回放','',
        '**这是在制定候选规则的同一批旧 A/D 输出上作的回放，不是新增模型实验或独立验证。**',
        '决策函数只读任务与冻结源码证据，不读案例/模型 ID、评分、失败列表或经验；这些元数据仅用于回放结果配对和统计。','',
        '| 方案 | 整体成功（回放） | D 材料交付次数 |', '|---|---:|---:|',
        f"| 固定 A | {summary['A_success']}/{len(rows)} | 0 |",
        f"| 固定 D | {summary['D_success']}/{len(rows)} | {len(rows)} |",
        f"| 候选门控 | {summary['replayed_success']}/{len(rows)} | {summary['D_deliveries']} |",'',
        '| 案例 | 门控选择 | A 成功 | D 成功 | 回放成功 |', '|---|---|---:|---:|---:|']
    for case in sorted({r['case'] for r in rows}):
        group=[r for r in rows if r['case']==case]
        lines.append('| '+' | '.join([case,','.join(sorted({r['action'] for r in group})),
            f"{sum(r['A_outcome']=='passed' for r in group)}/{len(group)}",f"{sum(r['D_outcome']=='passed' for r in group)}/{len(group)}",
            f"{sum(r['replayed_outcome']=='passed' for r in group)}/{len(group)}"])+' |')
    lines+=['','## 调用候选规则','',
        '- pending/ready 状态轮询任务，且任务相关同文件有 lifecycle 与 guard 的具体源码证据：D 候选。',
        '- 初始消息/状态缺失任务，且任务目标或可识别的本地导入依赖上有 connect-before-listen 证据：D 候选。',
        '- 审计/历史保留、重试与乱序/重入等组合契约：超出候选适用范围，A。',
        '- 任务不匹配、扫描不完整、证据空或关联不明：A。','',
        '## 局限与下一步','',
        '四道题只有三个来源组；模型和推理强度重复不是独立任务。此候选策略是事后提出，不能将回放成绩当作部署成功率。',
        '按来源家族划分开发和验证：冻结候选规则后，用未用于制定规则的新任务比较固定 A、固定 D 与门控，并保留全部调用/放弃记录。当前数据不够建立跨家族可靠门控。',
        '任务预筛可不扫描就放弃；潜在匹配仍需静态扫描。工作台为冻结输入仍会扫描每次输入；减少的是 D 材料交付，模型仍每任务运行一次。',
        f"相同旧输出上：固定 D 缺失必需效果 {summary['D_missing']} 项，门控缺失 {summary['selected_missing']} 项；总数相同不表示每个组合无退步。",
        f"相对固定D，门控选择总共新增通过{summary['gained_vs_D']}项，也丢失{summary['lost_vs_D']}项；{summary['configurations_with_losses_vs_D']}个配置有至少一项丢失。不是逐配置无退步策略。",
        '具体取舍见 replay.csv 的 gained_vs_D/lost_vs_D 与 gained_vs_A/lost_vs_A，均保留检查项ID；A/D/所选的禁止效果列表也分别保留。']
    lines+=['','## 回放中的实际观察用量','',
        '| 方案 | 输入 token（含缓存） | 输出 token |','|---|---:|---:|',
        f"| 固定 A | {summary['A_input_tokens']} | {summary['A_output_tokens']} |",
        f"| 固定 D | {summary['D_input_tokens']} | {summary['D_output_tokens']} |",
        f"| 候选门控 | {summary['selected_input_tokens']} | {summary['selected_output_tokens']} |",'',
        '这些用量来自被选择的旧 Agent 输出，尚非新运行的成本。D 材料交付少25%，观察到的输入/输出 token 只少约1–2%；不能据此宣称算力节省25%。']
    (root/'REPORT.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
