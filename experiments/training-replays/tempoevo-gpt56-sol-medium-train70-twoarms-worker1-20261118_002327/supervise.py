"""Authorized one-worker training replay supervisor and table export."""
from pathlib import Path
from datetime import datetime,timezone
import json,subprocess,sys,shutil
ROOT=Path(__file__).resolve().parent
REPO=Path('/home/sribd/Downloads/wangshu/temporal-contract-analyzer')
cmd=[sys.executable,'-B',str(REPO/'tools/tempoevo-docker/run_training_replay.py'),'--root',str(ROOT),'--execute']
with (ROOT/'replay.log').open('a') as log:rc=subprocess.run(cmd,cwd=REPO,stdout=log,stderr=subprocess.STDOUT).returncode
(ROOT/'run-exit.json').write_text(json.dumps(dict(exit_code=rc,finished_at_utc=datetime.now(timezone.utc).isoformat()),indent=2)+'\n')
archive=REPO/'experiments/training-replays'/ROOT.name
shutil.copyfile(ROOT/'run-exit.json',archive/'run-exit.json')
if (ROOT/'completion.json').exists():
    arms=json.loads((ROOT/'completion.json').read_text())['arms']
    def cell(name):
        a=arms[name]
        rate=f"{100*a['pass_rate']:.1f}%" if a['pass_rate'] is not None else 'N/A'
        return f"**{rate}（{a['passed']}/{a['valid']}）**，{a['unscored']}例执行异常，最多3轮"
    table="""| 集合 | 执行模型 | case / cluster数 | Latent通过率 | 仅Auto-Contract（无经验） | 带经验最终通过率 |
|---|---|---:|---|---|---|
| 训练集 | GPT-6.1-sol medium | 70 / 24 | **51.2%**，覆盖70/70 | **82.6%（19/23）**，仅覆盖23/70，最多3轮 | **92.9%（65/70）**，最多3轮 |
| 训练集 | GPT-5.6-sol medium | 70 / 24 | **31.9%（22/69）**，覆盖69/70 | AUTO_CELL | MEMORY_CELL |
| 测试集 | GPT-5.6-sol medium | 30 / 14 | **16.7%（5/30）** | **34.5%（10/29）**，1例执行异常 | **82.1%（23/28）**，2例执行异常 |
| 测试集 | GPT-6.1-sol medium | 30 / 14 | **72.4%（21/29）**，重跑，1例评分异常 | **53.3%（16/30）** | **90.0%（27/30）** |

执行／评分异常不计入有效通过率分母。GPT-5.6训练集本轮两组各从70例原始源码重新运行，最多3轮，固定0/61经验库，全程1并发。61条经验含这些训练case的历史来源；该行是训练集复测，不是独立测试泛化率，也不是对GPT-6.1历史在线训练过程的重建。经验提取发生在修复评分后；提取异常不撤销已完成的有效修复评分，单独记录在completion.json。新候选仅归档，不加入固定经验库。
""".replace('AUTO_CELL',cell('auto_contract')).replace('MEMORY_CELL',cell('with_experience'))
    (ROOT/'BIG_TABLE.md').write_text(table);shutil.copyfile(ROOT/'BIG_TABLE.md',archive/'BIG_TABLE.md')
subprocess.run(['git','add','--',str(archive.relative_to(REPO))],cwd=REPO,check=True)
subprocess.run(['git','commit','--only','-m','Export GPT5.6 train70 replay completion and big comparison table','--',str(archive.relative_to(REPO))],cwd=REPO)
sys.exit(rc)
