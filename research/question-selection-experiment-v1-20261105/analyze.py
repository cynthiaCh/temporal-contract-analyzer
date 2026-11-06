"""Post-run audit and descriptive case-level results. Never invokes models/probes."""
from datetime import datetime
from collections import Counter
import re
from run import *

def seconds(r):
 return (datetime.fromisoformat(r['completed_at'].replace('Z','+00:00'))-datetime.fromisoformat(r['started_at'].replace('Z','+00:00'))).total_seconds() if r.get('completed_at') and r.get('started_at') else None

def main():
 p=check_frozen();runs=read(OUT/'runs.json');rows=read(OUT/'results.json');ledger=read(OUT/'invocations.json');review=read(OUT/'selection-review.json')
 assert len(runs)==24 and len(ledger)<=24 and len({r['id'] for r in ledger})==len(ledger)
 assert {r['id'] for r in rows}<={r['id'] for r in ledger}<={r['id'] for r in runs}
 assert datetime.fromisoformat(review['reviewed_at'].replace('Z','+00:00'))<min(datetime.fromisoformat(r['launched_at'].replace('Z','+00:00')) for r in ledger)
 vectors=[];trajectories=[];exposures=[];baseline={};cases={}
 for case,meta in p['cases'].items():
  cp=Path(meta['case_manifest']);assert sha(cp.read_bytes())==meta['case_manifest_sha256']
  for f,h in meta['oracle_files'].items():assert sha(Path(f).read_bytes())==h
  cm=read(cp);effects=read(cp.parent/cm['oracle']['effects'])['variants']['ungranted'];cases[case]=effects
  raw=read(OUT/'calibration'/case/'unchanged/oracle/stdout.json');obs=raw['observed_effects']
  baseline[case]={**{'required:'+k:obs[k] is True for k in effects['required']},**{'forbidden:'+k:obs[k] is False for k in effects['forbidden']}}
 for r in rows:
  folder=Path(r['path']);m=read(folder/'manifest.json');j=m['jobs'][0];d=folder/'jobs/j-001';assert sha((d/'prompt.md').read_bytes())==r['prompt_sha256']
  assert m['input_files']==r['input_files']
  material=(OUT/'packets'/r['case']/(r['arm']+'.md')).read_text();assert sha(material)==r['material_sha256']
  assert (d/'report.md').read_text()==material
  for name,h in r['input_files'].items():assert sha((folder/'input'/name).read_bytes())==h
  files={name:(folder/'input'/name).read_bytes() for name in r['input_files']};sp,st=retrieve(m['task'],files);qp,qt=question_retrieve(m['task'],sp)
  old=read(folder/'question-retrieval.json');assert {k:v for k,v in qp.items() if k!='elapsed_seconds'}=={k:v for k,v in old.items() if k!='elapsed_seconds'}
  assert material==st+('' if r['arm']=='S' else '\n'+render([q['id'] for q in load(BANK)] if r['arm']=='F' else qp['selected_ids'],BANK))
  cmd=j.get('command',[])
  if cmd:assert cmd[cmd.index('-m')+1]==MODEL and 'model_reasoning_effort="low"' in cmd
  commands=[];errors=[]
  if (d/'events.jsonl').exists():
   for n,line in enumerate((d/'events.jsonl').read_text().splitlines(),1):
    e=json.loads(line);item=e.get('item',{})
    if e.get('type') in ['error','turn.failed']:errors.append(dict(line=n,event=e))
    if e.get('type')=='item.completed' and item.get('type')=='command_execution':
     commands.append(dict(line=n,command=item.get('command'),exit_code=item.get('exit_code'),output=item.get('aggregated_output','')))
     if re.search(r'provenance\.json|pending-review\.md|temporal-contract-bench|/oracle/|/reference/',item.get('command','')):exposures.append(dict(id=r['id'],line=n,command=item.get('command')))
  change=read(d/'changes.json') if (d/'changes.json').exists() else {}
  trajectories.append(dict(case=r['case'],arm=r['arm'],replicate=r['replicate'],id=r['id'],prompt=str(d/'prompt.md'),events=str(d/'events.jsonl'),changes=str(d/'changes.json'),commands=commands,errors=errors,changed_paths=[x['path'] for x in change.get('files',[])]))
  if not r.get('category','').startswith('behavior-'):continue
  ep=Path(r['evaluation']);ev=read(ep);eroot=ep.parent;meta=p['cases'][r['case']]
  assert ev['calibration_verdict']=='PASS' and ev['manifest_sha256']==meta['case_manifest_sha256']
  assert ev['oracle_files']=={str(Path(f).relative_to(Path(meta['case_manifest']).parent/'oracle')):h for f,h in meta['oracle_files'].items()}
  assert read(eroot/'calibration/stdout.json')['verdict']=='PASS'
  expected=next(x['runtime'] for x in read(OUT/'calibration.json') if x['case']==r['case']);assert ev['runtime']==expected
  raw=read(eroot/'j-001/oracle/stdout.json');obs=raw['observed_effects'];effects=cases[r['case']]
  for k in effects['required']+effects['forbidden']:assert isinstance(obs.get(k),bool)
  for name,h in ev['jobs']['j-001']['candidate_files'].items():assert sha((eroot/'j-001/candidate'/name).read_bytes())==h
  assert raw['verdict']==ev['jobs']['j-001']['verdict']
  assert read(eroot/'j-001/oracle/execution.json')['exit_code']==(0 if raw['verdict']=='PASS' else 1)
  checks={**{'required:'+k:obs[k] is True for k in effects['required']},**{'forbidden:'+k:obs[k] is False for k in effects['forbidden']}}
  lost=[k for k,v in baseline[r['case']].items() if v and not checks[k]]
  vectors.append(dict(case=r['case'],arm=r['arm'],replicate=r['replicate'],id=r['id'],whole_pass=raw['verdict']=='PASS',checks=checks,required_passed=sum(obs[k] for k in effects['required']),required_total=len(effects['required']),forbidden_violated=sum(obs[k] for k in effects['forbidden']),lost_original_passed=lost,original_passed_total=sum(baseline[r['case']].values()),raw_oracle=str(eroot/'j-001/oracle/stdout.json'),scored_candidate=str(eroot/'j-001/candidate'),schedules=raw.get('schedules')))
 summary={};per_case={};comparisons={};losses={}
 for arm in ARMS:
  vs=[v for v in vectors if v['arm']==arm];rs=[r for r in rows if r['arm']==arm]
  summary[arm]=dict(scheduled=8,recorded=len(rs),scored=len(vs),whole_pass=sum(v['whole_pass'] for v in vs),required_passed=sum(v['required_passed'] for v in vs),required_total=sum(v['required_total'] for v in vs),forbidden_violated=sum(v['forbidden_violated'] for v in vs),runs_losing_original_checks=sum(bool(v['lost_original_passed']) for v in vs),input_tokens=sum((r.get('usage') or {}).get('input_tokens',0) for r in rs),cached_input_tokens=sum((r.get('usage') or {}).get('cached_input_tokens',0) for r in rs),output_tokens=sum((r.get('usage') or {}).get('output_tokens',0) for r in rs),model_seconds=round(sum(seconds(r) or 0 for r in rs),3),delivered_questions=sum(len(r['question_ids']) for r in rs),categories=dict(Counter(r['category'] for r in rs)))
 for case in CASES:
  per_case[case]={}
  sv=[v for v in vectors if v['case']==case and v['arm']=='S'];stable=set.intersection(*[{k for k,b in v['checks'].items() if b} for v in sv]) if len(sv)==2 else set()
  losses[case]={a:[dict(replicate=v['replicate'],lost=sorted(k for k in stable if not v['checks'][k])) for v in vectors if v['case']==case and v['arm']==a] for a in ARMS}
  for arm in ARMS:
   vs=sorted([v for v in vectors if v['case']==case and v['arm']==arm],key=lambda v:v['replicate'])
   per_case[case][arm]=dict(whole_pass=sum(v['whole_pass'] for v in vs),scored=len(vs),required_by_repeat=[dict(replicate=v['replicate'],passed=v['required_passed'],total=v['required_total']) for v in vs],runs_losing_original=sum(bool(v['lost_original_passed']) for v in vs))
 for control in ['F','S']:
  pairs=[]
  for case in CASES:
   for rep in [1,2]:
    r=next((v for v in vectors if v['case']==case and v['replicate']==rep and v['arm']=='R'),None);c=next((v for v in vectors if v['case']==case and v['replicate']==rep and v['arm']==control),None)
    if r and c:pairs.append(dict(case=case,replicate=rep,whole_difference=int(r['whole_pass'])-int(c['whole_pass']),R_lost_vs_control=[k for k,v in c['checks'].items() if v and not r['checks'][k]]))
  comparisons['R_vs_'+control]=dict(pairs=pairs,wins=sum(x['whole_difference']>0 for x in pairs),losses=sum(x['whole_difference']<0 for x in pairs),ties=sum(x['whole_difference']==0 for x in pairs),denominator=len(pairs))
 for a in ARMS:
  rr=[r for r in runs if r['arm']==a]
  summary[a]['initial_prompt_bytes']=sum((Path(r['path'])/'jobs/j-001/prompt.md').stat().st_size for r in rr)
  summary[a]['source_retrieval_preparation_seconds']=sum(read(Path(r['path'])/'source-retrieval.json')['elapsed_seconds'] for r in rr)
  summary[a]['question_retrieval_preparation_seconds']=sum(read(Path(r['path'])/'question-retrieval.json')['elapsed_seconds'] for r in rr)
 retrieval={}
 for case in CASES:
  rr=read(OUT/'packets'/case/'retrieval.json');r=next(r for r in runs if r['case']==case);sp=read(Path(r['path'])/'source-retrieval.json')
  retrieval[case]=dict(selected=rr['selected_ids'],question_seconds=rr['elapsed_seconds'],source_seconds=sp['elapsed_seconds'],review=review['cases'][case])
 summary_all=dict(arms=summary,per_case=per_case,comparisons=comparisons,stable_S_check_losses=losses,retrieval=retrieval,independent_case_count=0,case_count=4,replicates=2,interpretation='Exploratory descriptive, not independent generalization or statistical significance. Checks and repeats are not new cases; original losses compare fresh patches with frozen baseline, not continuation repairs.')
 save(OUT/'summary.json',summary_all);save(OUT/'raw-vectors.json',vectors);save(OUT/'trajectory-evidence.json',trajectories)
 audit=dict(status='PASS',completed_at=archive.now(),prepared=len(runs),invocations=len(ledger),results=len(rows),scored=len(vectors),execution_failures=[r['id'] for r in rows if r['category'].startswith('execution')],validation_unverified=[r['id'] for r in rows if r['category']=='validation-unverified'],selection_review_precedes_launch=True,frozen_hashes_replayed=True,prompts_and_retrieval_replayed=True,graded_bytes_oracle_runtime_verified=True,explicit_restricted_path_commands=exposures,hermetic_isolation_certified=False)
 save(OUT/'audit.json',audit)
 lines=['# 自动选题与固定五题探索对照','',f"记录 {len(rows)}/24；可信评分 {len(vectors)}。4个案例，每条件2次。独立泛化案例0；不作统计显著性主张。",'','|条件|整体通过/评分（计划8）|必需检查（辅助）|原通过项丢失的调用|输入token|输出token|模型秒|交付题数|','|---|---:|---:|---:|---:|---:|---:|---:|']
 for a,s in summary.items():lines.append(f"|{a}|{s['whole_pass']}/{s['scored']}|{s['required_passed']}/{s['required_total']}|{s['runs_losing_original_checks']}/{s['scored']}|{s['input_tokens']}|{s['output_tokens']}|{s['model_seconds']}|{s['delivered_questions']}|")
 lines+=['','S=同源码RAG；F=S+全部5题；R=S+自动0—2题。token含模型额外读源码的累计输入，不是初始prompt长度或费用。','', '|案例|S整体；必需项每次|F整体；必需项每次|R整体；必需项每次|R选题|','|---|---|---|---|---|']
 for c,arms in per_case.items():
  vals=[]
  for a in ARMS:
   s=arms[a];vals.append(str(s['whole_pass'])+'/'+str(s['scored'])+'；'+', '.join(str(x['passed'])+'/'+str(x['total']) for x in s['required_by_repeat']))
  lines.append('|'+c+'|'+'|'.join(vals)+'|'+(', '.join(retrieval[c]['selected']) or '0条')+'|')
 lines+=['', '## 检索先验审查','', 'selection-review.json在首个正式调用前冻结。研究Agent审查，不冒称独立人工盲审。监听漏002、草稿漏005；交接003完整，负案例拒绝返回。入选5个题目-案例关系全部判适用（5/5）；适用关系召回5/7；完全覆盖2/4案例（包括负案例）。F无关13/20题目-案例关系，R为0/5；两次重复不重复算新相关性样本。这些标签为研究审查，非普遍真值。','', '全量分数、贡献、阈值/拒绝原因和查询见每次question-retrieval.json；完整交付prompt、events.jsonl、changes.json和原始评分路径见runs.json、trajectory-evidence.json、raw-vectors.json。','', '## 解释边界','', '校准4/4 reference PASS、4/4 unchanged UNDERREACH。运行器mock测试16/16；首次系统Python3.8不符评分测试版本要求的2项失败及修正环境记录于runner-validation.md。执行失败和验证异常独立记录audit.json；不补跑。','', '源码检索字节复用上一轮研究实现；生产分析器/评分器、原题库、历史档案未改。随机种子2026110502只控制调度，模型无可控采样种子。R返回0时仍收到同一条件声明。workspace-write继承原配置，不是严格读隔离；显式受限路径命令检查不构成无泄漏证明。']
 (OUT/'REPORT.md').write_text('\n'.join(lines)+'\n')
 print(json.dumps(dict(audit=audit,arms=summary,per_case=per_case),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
