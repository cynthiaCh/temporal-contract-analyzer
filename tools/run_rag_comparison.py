"""Run task-only RAG on the same failed patches; reuse verified historical controls."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import sys
import threading

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from temporal_contract_analyzer import archive
from temporal_contract_analyzer.repair import source_job
from temporal_contract_analyzer.workbench import Workbench


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--matrix',required=True,type=Path)
    parser.add_argument('--controls',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--bench-root',required=True,type=Path)
    parser.add_argument('--node',required=True)
    parser.add_argument('--execute',action='store_true')
    args=parser.parse_args();os.environ['TCA_BENCH_ROOT']=str(args.bench_root.resolve())
    root=args.output.resolve();root.mkdir(parents=True,exist_ok=False)
    parents=[r for r in json.loads(args.matrix.read_text()) if r['condition']=='review' and r['outcome']=='failed']
    controls=json.loads(args.controls.read_text())
    grouped={};index=[];results=[];lock=threading.Lock()
    # Reject mismatched historical sources/settings before any real model call.
    for r in parents:
        p=Path(r['path']);store=p.parent.with_name(p.parent.name[:-len('-experiments')]);wb=Workbench(store,node=args.node)
        parent,candidate,source=source_job(wb,r['experiment'],r['job'])
        matches=[c for c in controls if c['parent']==r['experiment']]
        if len(matches)!=2 or {c['condition'] for c in matches}!={'review','hypothesis_review'}:
            raise ValueError('Expected two verified historical controls for '+r['experiment'])
        for c in matches:
            old=Path(c['path']);m=json.loads((old/'manifest.json').read_text());saved=json.loads((old/'retry-source.json').read_text())
            if (m['input_files']!=source['candidate_files'] or saved!=source or
                    any(m[k]!=parent[k] for k in ('model','effort','timeout','mode')) or
                    any(m.get(k)!=parent.get(k) for k in ('local_codex','model_override','config_source','model_catalog')) or
                    c['regression']['status'] not in {'preserved','regressed'}):
                raise ValueError('Historical comparison mismatch for '+r['experiment'])
        grouped.setdefault(r['model'],[]).append(r)
    archive.atomic_json(root/'plan.json',dict(created_at=archive.now(),execute=args.execute,
        jobs=len(parents),condition='rag_only',query='original task only',
        retrieval='local BM25 of candidate source/Markdown + bounded definitions/imports; no embeddings',
        budget='inherit explicit parent model/effort/timeout',
        controls='historical same-patch v2 D/hypothesis runs, not contemporaneous randomized controls',
        matrix=str(args.matrix.resolve()),historical_source=str(args.controls.resolve()),
        parents=[dict(experiment=r['experiment'],job=r['job'],path=r['path']) for r in parents]))
    archive.atomic_json(root/'historical-controls.json',controls)
    def save():
        archive.atomic_json(root/'runs.json',index);archive.atomic_json(root/'results.json',results)
        lines=['# 单独 RAG 与历史同补丁对照','',
               'RAG：原任务 + 从已评分候选快照按任务检索的代码/文档；不提供 D 解释、失败标识或假设。',
               '对照复用 v2 的同父补丁记录；已核对输入、显式模型、推理强度、配置路线和超时。这是历史探索性比较，不是新一轮随机配对。','',
               '| 条件 | 已评分 | 整体成功 | 无退步且改善 | 退步候选 | 新增通过项 | 丢失原通过项 |',
               '|---|---:|---:|---:|---:|---:|---:|']
        for cond,data in [('review',controls),('hypothesis_review',controls),('rag_only',results)]:
            g=[r for r in data if r['condition']==cond and r['outcome'] in {'passed','failed'}]
            lines.append('| '+' | '.join([cond,str(len(g)),str(sum(r['outcome']=='passed' for r in g)),
                str(sum(r['regression'].get('eligible',False) and bool(r['regression'].get('gained')) for r in g)),
                str(sum(r['regression'].get('status')=='regressed' for r in g)),
                str(sum(len(r['regression'].get('gained',[])) for r in g)),str(sum(len(r['regression'].get('lost',[])) for r in g))])+' |')
        lines+=['','| 模型 | 推理 | 案例 | RAG 结果 | 新增 | 丢失 | 材料 |','|---|---|---|---|---:|---:|---|']
        for r in sorted(results,key=lambda r:(r['model'],r['effort'],r['case'])):
            lines.append('| '+' | '.join([r['model'],r['effort'],r['case'],r['outcome'],str(len(r['regression'].get('gained',[]))),
                str(len(r['regression'].get('lost',[]))),f"[manifest]({r['path']}/manifest.json)"])+' |')
        lines+=['','每组合仅一次；实际 token 不等量；同任务与已见案例的开发比较，不作盲测、泛化或统计显著性结论。']
        (root/'COMPARISON.md').write_text('\n'.join(lines)+'\n')
    def worker(model,rows):
        for r in sorted(rows,key=lambda r:(r['effort'],r['case'])):
            p=Path(r['path']);store=p.parent.with_name(p.parent.name[:-len('-experiments')]);wb=Workbench(store,node=args.node)
            m=wb.prepare_rag(r['experiment'],r['job']);folder=wb.folder(m['id'])
            rec=dict(model=model,parent=r['experiment'],parent_job=r['job'],id=m['id'],path=str(folder))
            with lock:
                index.append(rec);save();print(json.dumps(dict(event='prepared',**rec)),flush=True)
            if not args.execute:continue
            wb.start(m['id']);wb.thread.join();m=wb.read(m['id']);j=m['jobs'][0];e=j.get('evaluation',{})
            out=dict(model=model,effort=m['effort'],case=m['case']['id'],experiment=m['id'],parent=r['experiment'],
                job=j['id'],condition=j['condition'],process=j['status'],outcome=j.get('task_success','unverified'),
                regression=e.get('regression',{}),usage=j.get('usage'),scenario_progress=e.get('scenario_progress'),path=str(folder))
            with lock:
                results.append(out);save();print(json.dumps(dict(event='evaluated',**out)),flush=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures=[pool.submit(worker,model,rows) for model,rows in grouped.items()]
        for future in as_completed(futures):future.result()
    print(json.dumps(dict(event='complete',jobs=len(results))),flush=True)


if __name__=='__main__':main()
