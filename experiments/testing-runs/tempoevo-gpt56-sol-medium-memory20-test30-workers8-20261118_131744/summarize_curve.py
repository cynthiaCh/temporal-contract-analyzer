"""Report raw and shared-valid library-size ablation points without score selection."""
import csv,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def build():
    plan=json.loads((ROOT/'plan.json').read_text())
    paths={0:Path(plan['zero_experience_run']),20:ROOT,61:Path(plan['parent_with_experience_run'])}
    records={};raw={};sources={}
    for size,p in paths.items():
        f=p/'completion.json';d=json.loads(f.read_text());assert d['recorded_cases']==d['expected_cases']==30
        rows=d['cases'];assert len(rows)==30 and len({x['case_id'] for x in rows})==30
        records[size]={x['case_id']:x for x in rows};raw[size]=d;sources[size]=dict(root=str(p),sha256=hashlib.sha256(f.read_bytes()).hexdigest())
    assert set(records[0])==set(records[20])==set(records[61])
    common=sorted(cid for cid in records[0] if all(type(records[s][cid].get('gold_passed')) is bool for s in records))
    points=[]
    for size in [0,20,61]:
        rows=list(records[size].values());passed=sum(x['gold_passed'] is True for x in rows);valid=sum(type(x['gold_passed']) is bool for x in rows);cp=sum(records[size][cid]['gold_passed'] for cid in common)
        points.append(dict(experience_entries=size,passed=passed,valid=valid,unscored=30-valid,pass_rate=passed/valid if valid else None,common_passed=cp,common_valid=len(common),common_pass_rate=cp/len(common) if common else None))
    curve=dict(study='Frozen approved-library-size ablation; NOT training progress or historical checkpoint replay',model='gpt-5.6-sol',reasoning_effort='medium',case_count=30,seed=20261118,sample_replicates=1,points=points,common_valid_case_ids=common,sources=sources,interpretation='0entries is Auto-Contract-only, not Latent. Fixed Action24req600s and final Gold. Prior0/61 results reused;20 is new. Errors excluded from valid denominators. Primary paired curve uses the same intersection of valid cases. One subset and one repair trial per arm; no monotonicity or generalization claim.')
    (ROOT/'curve.json').write_text(json.dumps(curve,indent=2)+'\n')
    with (ROOT/'curve.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(points[0]));w.writeheader();w.writerows(points)
    text='# 固定30题的经验库规模消融\n\nGPT-5.6-sol medium，8并发，一次Action和最终评分；0条为仅Auto-Contract，20条为固定种子20261118抽取的当前经验子集，61条为原完整库。0/61复用已有结果，本轮只新增20条。完整库未修改，评估中不更新经验。\n\n| 可用经验条数 | 有效通过率 | 无评分 | 共同有效case上的通过率 |\n|---|---|---:|---|\n'
    for p in points:
        rawrate=f"{100*p['pass_rate']:.1f}%（{p['passed']}/{p['valid']}）" if p['valid'] else '无有效评分'
        commonrate=f"{100*p['common_pass_rate']:.1f}%（{p['common_passed']}/{p['common_valid']}）" if p['common_valid'] else '无共同有效评分'
        text+=f"| {p['experience_entries']} | {rawrate} | {p['unscored']} | {commonrate} |\n"
    text+='\n这是单个固定随机子集的库规模消融，不是真实训练学习曲线；不能保证增加经验后单调上升。当前经验含合并/修订版本，20条不代表历史第20条经验时的知识状态。冻结20条是可用库上限，每个case实际选择0至5条，并另报实际使用率。固定测试case已有历史暴露/共享机制，不是独立未见泛化认证。\n'
    (ROOT/'CURVE_REPORT.md').write_text(text)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(6.2,4.1))
    if common:
        ys=[p['common_pass_rate']*100 for p in points]
        ax.plot([p['experience_entries'] for p in points],ys,'o-',color='#2563eb',linewidth=1.7)
        for p,y in zip(points,ys):ax.annotate(f"{y:.1f}% ({p['common_passed']}/{p['common_valid']})",(p['experience_entries'],y),xytext=(0,10),textcoords='offset points',ha='center',fontsize=9)
        ax.set_ylabel('Pass rate on shared valid cases (%)')
    else:ax.text(.5,.5,'No shared valid-scored cases',transform=ax.transAxes,ha='center')
    ax.set_xlabel('Visible approved experience entries');ax.set_xticks([0,20,61]);ax.set_xlim(-6,68);ax.set_ylim(0,105);ax.grid(axis='y',alpha=.22);ax.set_title('Library-size ablation: GPT-5.6-sol medium')
    fig.text(.5,.01,'One frozen subset; prior 0/61 arms reused. Not a training learning curve.',ha='center',fontsize=8)
    fig.tight_layout(rect=(0,.05,1,1))
    for suffix in ['png','svg','pdf']:fig.savefig(ROOT/('library-size-curve.'+suffix),dpi=180)
    plt.close(fig)
    return curve

if __name__=='__main__':print(json.dumps(build()['points']))
