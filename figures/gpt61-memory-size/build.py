"""Add GPT-6.1 to Fig3 using the shared generate_bootstrap_indices.py draws."""
import csv,json,statistics
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
RUN=REPO/'experiments/testing-runs/tempoevo-gpt61-sol-medium-library-size-test30-workers8-20261123_180106'
INDEX=REPO/'experiments/testing-runs/tempoevo-gpt61-sol-medium-latent-experience-test30-workers8-20261122_041732/table1-bootstrap/bootstrap_indices'
order=[r['case_id'] for r in csv.DictReader((INDEX/'case_id_order.csv').open(encoding='utf-8-sig'))]
draws=[[int(r[f'draw_{i:03d}']) for i in range(1,31)] for r in csv.DictReader((INDEX/'bootstrap_indices_1000x30.csv').open(encoding='utf-8-sig'))]
assert len(order)==30 and len(draws)==1000
points=[]
for size,file in [(20,RUN/'memory20/completion.json'),(40,RUN/'memory40-merged-results.json')]:
 rows={r['case_id']:r for r in json.loads(file.read_text())['cases']}
 assert set(rows)==set(order) and all(r['status']=='scored' and type(r['gold_passed']) is bool for r in rows.values())
 values=[int(rows[c]['gold_passed']) for c in order]
 samples=[sum(values[i] for i in d)*100/30 for d in draws]
 points.append(dict(size=size,passed=sum(values),total=30,bootstrap_mean=statistics.mean(samples),bootstrap_sd=statistics.stdev(samples),source=str(file.relative_to(REPO))))
old=json.loads((REPO/'experiments/testing-runs/deepseek-library-size-ablation-20261122/summary.json').read_text())
fixed=json.loads((HERE/'fixed-points.json').read_text())
new=[fixed['baseline'],*points,fixed['full']]
data=dict(gpt61=new,gpt56=old['gpt'],deepseek=old['deepseek'],bootstrap=dict(generator='tools/generate_bootstrap_indices.py',indices=str(INDEX.relative_to(REPO)),replicates=1000,draws=30,seed=20260925,sd_ddof=1),note='GPT-5.6 and DeepSeek published points unchanged. GPT-6.1 0/61 preserved from Table1/user; 20/40 use paired shared indices. Sizes denote frozen library entries, not historical training checkpoints.')
(HERE/'summary.json').write_text(json.dumps(data,indent=2)+'\n')
plt.rcParams.update({'font.family':'serif','font.serif':['DejaVu Serif'],'font.size':13,'axes.labelsize':15,'xtick.labelsize':13,'ytick.labelsize':13,'pdf.fonttype':42,'ps.fonttype':42})
fig,ax=plt.subplots(figsize=(5.8,3.2))
ax.errorbar(old['gpt']['x'],old['gpt']['mean'],yerr=old['gpt']['sd'],color='#2166ac',marker='o',linewidth=2,markersize=7,capsize=4,label='GPT-5.6 Sol / medium')
d=old['deepseek'];ax.errorbar([p['size'] for p in d],[p['bootstrap_mean'] for p in d],yerr=[p['bootstrap_sd'] for p in d],color='#b35806',marker='s',linestyle='--',linewidth=2,markersize=6,capsize=4,label='DeepSeek Flash / low')
ax.errorbar([p['size'] for p in new],[p['bootstrap_mean'] for p in new],yerr=[p['bootstrap_sd'] for p in new],color='#238443',marker='^',linestyle='-.',linewidth=2,markersize=7,capsize=4,label='GPT-6.1 Sol / medium')
ax.set(xlabel='Experience entries',ylabel='Pass rate (%)',xlim=(-5,66),ylim=(0,100),xticks=[0,20,40,60],yticks=[0,20,40,60,80,100])
ax.grid(axis='y',color='#dddddd',linewidth=.8);ax.set_axisbelow(True)
ax.spines[['top','right']].set_visible(False)
ax.legend(loc='lower right',frameon=False,fontsize=11)
fig.tight_layout(pad=.7)
for ext in ['pdf','png']:fig.savefig(HERE/f'Acc-MemorySize-GPT61.{ext}',dpi=300)
for p in new:print(p['size'],f"{p['bootstrap_mean']:.1f} ± {p['bootstrap_sd']:.1f}")
