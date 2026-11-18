"""Secondary descriptive plots with explicit missing-result bounds; no experiments."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter, MaxNLocator

HERE=Path(__file__).resolve().parent

def render(run_id):
    out=HERE/'reports'/run_id
    rows=json.loads((out/'plot-data.json').read_text())
    x=[r['checkpoint'] for r in rows]
    nan=float('nan')
    complete=[r['completed']==30 for r in rows]
    conditional=[r['pass_over_valid'] if done and r['valid_gold'] else nan for r,done in zip(rows,complete)]
    lower=[r['passed']/30 if done else nan for r,done in zip(rows,complete)]
    upper=[(r['passed']+30-r['valid_gold'])/30 if done else nan for r,done in zip(rows,complete)]
    coverage=[r['coverage'] if done else nan for r,done in zip(rows,complete)]
    experience=[r['approved_entries'] if r['approved_entries'] is not None else nan for r in rows]
    fig,axes=plt.subplots(3,1,figsize=(9,9),sharex=True,layout='constrained')
    axes[0].plot(x,conditional,'o-',color='#1864ab',label='PASS / valid Gold (conditional)')
    axes[0].fill_between(x,lower,upper,color='#adb5bd',alpha=.4,label='Missing-result bounds on fixed 30; not a CI')
    axes[0].vlines(x,lower,upper,color='#868e96',linewidth=2,alpha=.7)
    for r,done in zip(rows,complete):
        if done and r['valid_gold']:
            axes[0].annotate(f"{r['passed']}/{r['valid_gold']}",(r['checkpoint'],r['pass_over_valid']),xytext=(0,8),textcoords='offset points',ha='center',fontsize=8)
    axes[0].set(ylabel='Observed pass proportion',ylim=(0,1),title='Fixed 30-case, same-source development evaluation')
    axes[0].legend(loc='upper left',fontsize=8)
    axes[1].plot(x,coverage,'o-',color='#d9480f')
    axes[1].set(ylabel='Valid Gold / 30',ylim=(0,1.05))
    axes[2].plot(x,experience,'s-',color='#2b8a3e')
    axes[2].set(ylabel='Approved experience entries',xlabel='Processed and review-closed training cases',xticks=x)
    axes[2].set_ylim(0,max(1,max((r['approved_entries'] or 0 for r in rows),default=0)+1))
    axes[2].yaxis.set_major_locator(MaxNLocator(integer=True))
    for ax in axes[:2]:ax.yaxis.set_major_formatter(PercentFormatter(1))
    for ax in axes:ax.grid(alpha=.25)
    fig.savefig(out/'coverage-and-experience.png',dpi=200)
    fig.savefig(out/'coverage-and-experience.pdf')
    plt.close(fig)
    bound_rows=[dict(checkpoint=r['checkpoint'],closed=r['completed'],valid_gold=r['valid_gold'],passed=r['passed'],
        lower=r['passed']/30 if done else None,upper=(r['passed']+30-r['valid_gold'])/30 if done else None,
        conditional=r['pass_over_valid'] if done else None) for r,done in zip(rows,complete)]
    (out/'missing-result-bounds.json').write_text(json.dumps(bound_rows,indent=2),encoding='utf8')
    print(json.dumps(dict(output=str(out),closed_checkpoints=sum(complete))))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run-id',required=True)
    render(parser.parse_args().run_id)
