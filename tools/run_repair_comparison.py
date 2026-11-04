"""Run matched continued-repair pairs selected from an existing matrix export.

This entry point performs real model calls only with --execute. Preparation and
scoring reuse Workbench; no alternate model runner or scorer is implemented.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import sys
import threading

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from temporal_contract_analyzer import archive
from temporal_contract_analyzer.workbench import Workbench


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--matrix',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--bench-root',required=True,type=Path)
    parser.add_argument('--node',required=True)
    parser.add_argument('--execute',action='store_true')
    args=parser.parse_args();os.environ['TCA_BENCH_ROOT']=str(args.bench_root.resolve())
    root=args.output.resolve();root.mkdir(parents=True,exist_ok=False)
    parents=[r for r in json.loads(args.matrix.read_text()) if r['condition']=='review' and r['outcome']=='failed']
    unique={(r['model'],r['effort'],r['case']) for r in parents}
    if len(unique)!=len(parents):raise ValueError('Matrix contains duplicate failed D parents')
    lock=threading.Lock();results=[];records=[]
    def save():
        archive.atomic_json(root/'results.json',results)
        archive.atomic_json(root/'pairs.json',records)
        lines=['# 同补丁 D 再尝试与失败假设辅助对比','',
            '同一已评分 D 失败补丁；同模型、推理强度与单次超时。每组一次；输入输出 token 实测，不声称 token 等量。',
            '控制组为当前补丁重新扫描后的 D，处理组额外收到失败标识、可反证原因假设、调用及状态候选证据。顺序按父 ID 奇偶交替，不是随机试验。', '',
            '| 条件 | 已评分 | 整体成功 | 无退步且新增通过 | 存在退步 | 新增通过项 | 丢失原通过项 |',
            '|---|---:|---:|---:|---:|---:|---:|']
        for cond in ('review','hypothesis_review'):
            g=[r for r in results if r['condition']==cond and r['outcome'] in {'passed','failed'}]
            lines.append('| '+' | '.join([cond,str(len(g)),str(sum(r['outcome']=='passed' for r in g)),
                str(sum(r['regression'].get('eligible',False) and bool(r['regression'].get('gained')) for r in g)),
                str(sum(r['regression'].get('status')=='regressed' for r in g)),
                str(sum(len(r['regression'].get('gained',[])) for r in g)),str(sum(len(r['regression'].get('lost',[])) for r in g))])+' |')
        lines+=['','| 模型 | 推理 | 案例 | 条件 | 结果 | 新增 | 丢失 | 材料 |','|---|---|---|---|---|---:|---:|---|']
        for r in sorted(results,key=lambda r:(r['model'],r['effort'],r['case'],r['condition'])):
            reg=r['regression']
            lines.append('| '+' | '.join([r['model'],r['effort'],r['case'],r['condition'],r['outcome'],
                str(len(reg.get('gained',[]))),str(len(reg.get('lost',[]))),f"[manifest]({r['path']}/manifest.json)"])+' |')
        lines+=['','失败标识为反馈暴露后的开发材料，不能替代公开业务契约。仅为这批已见案例的单次描述性比较，不构成泛化或统计显著性结论。']
        (root/'COMPARISON.md').write_text('\n'.join(lines)+'\n')
    grouped={}
    for row in parents:grouped.setdefault(row['model'],[]).append(row)
    archive.atomic_json(root/'plan.json',dict(created_at=archive.now(),matrix=str(args.matrix.resolve()),
        parent_pairs=len(parents),jobs=2*len(parents),execute=args.execute,
        source_selection='original failed D jobs only',budget='inherit parent model/effort/timeout',
        control='current D from the same evaluated patch',treatment='same D plus explicit failure hypotheses and source relations',
        parents=[dict(experiment=r['experiment'],job=r['job'],path=r['path']) for r in parents]))
    def worker(model,rows):
        for row in sorted(rows,key=lambda r:(r['effort'],r['case'])):
            source=Path(row['path'])
            if not source.parent.name.endswith('-experiments'):raise ValueError('Invalid experiment store path')
            store=source.parent.with_name(source.parent.name[:-len('-experiments')])
            wb=Workbench(store,node=args.node)
            pair=wb.prepare_repair(row['experiment'],row['job'])
            record=dict(model=model,parent=row['experiment'],parent_job=row['job'],id=pair['id'],path=str(wb.folder(pair['id'])))
            with lock:
                records.append(record);save()
                print(json.dumps(dict(event='prepared',**record)),flush=True)
            if not args.execute:continue
            wb.start(pair['id']);wb.thread.join()
            finished=wb.read(pair['id'])
            additions=[]
            for job in finished['jobs']:
                evaluation=job.get('evaluation',{})
                additions.append(dict(model=model,effort=finished['effort'],case=finished['case']['id'],
                    experiment=finished['id'],parent=row['experiment'],job=job['id'],condition=job['condition'],
                    process=job['status'],outcome=job.get('task_success','unverified'),
                    regression=evaluation.get('regression',{}),usage=job.get('usage'),
                    scenario_progress=evaluation.get('scenario_progress'),path=str(wb.folder(finished['id']))))
            with lock:
                results.extend(additions);save()
                print(json.dumps(dict(event='evaluated',model=model,case=finished['case']['id'],effort=finished['effort'],jobs=additions)),flush=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures=[pool.submit(worker,model,rows) for model,rows in grouped.items()]
        for future in as_completed(futures):future.result()
    print(json.dumps(dict(event='complete',pairs=len(records),jobs=len(results))),flush=True)


if __name__=='__main__':main()
