from pathlib import Path
import json,hashlib,subprocess,shutil
R=Path.cwd(); O=R/'research/candidate-contract-repair-exec-v1-20261108'; P=R/'research/candidate-contract-repair-prep-v1-20261107'; X=R/'research/contract-extraction-cross-case-v1-20261107'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def hashes(p):return {str(x.relative_to(p)):sha(x) for x in sorted(p.rglob('*')) if x.is_file()}
initial={'repo_status':subprocess.check_output(['git','status','--porcelain=v1'],text=True),'repo_diff':subprocess.check_output(['git','diff'],text=True),'bench_status':subprocess.check_output(['git','-C',str(R.parent/'temporal-contract-bench-git'),'status','--porcelain=v1'],text=True),'bench_diff':subprocess.check_output(['git','-C',str(R.parent/'temporal-contract-bench-git'),'diff'],text=True),'global_config_sha256':sha(Path.home()/'.codex/config.toml'),'head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'AGENTS':'No AGENTS.md in repository root or ancestor paths; no nested AGENTS in selected materials.'}
save(O/'initial-state.json',initial)
b=json.loads((P/'source-score-bindings.json').read_text()); sel=json.loads((P/'contract-selection.json').read_text())
h={'C1':'- 打开 presence panel 后呈现初始在线用户状态，后续 presence 更新继续呈现。\n- 保留 workspace 导航行为，包括发布时同步选择其他房间或隐藏面板，以及后续访问复用 transport。\n- 不修改 metrics consumer；其既有行为只统计增量，不计同步 bootstrap。\n','C3':'- 每次 submit 在调用入口捕获 doc、actor、text 快照。\n- commit 成功后，按入口快照及 receipt revision 恰好记录一次审计；失败不生成成功审计。\n- 已接纳提交在 close 或 reopen 后继续处理其历史记录。\n- saved/error 反馈只属于当前 visit 的最新提交。\n- submit 返回在结果处理完成后定案的 Promise。\n- 保留编辑器公开方法及其他消费者行为；搜索预览保持 40 ms、hide 丢弃待处理查询并可复用。\n'}
app=[]
for c in ['C1','C3']:
 base=R/'research/code-analysis-standard-cases-v1-20261107/cases'/c
 shutil.copytree(base,O/'materials'/c)
 assert hashes(base/'candidate')==b['cases'][c]['base_candidate_files']
 m=(X/'runs'/sel['cases'][c]['selected_slot']/'contract.md').read_text(); body=m.split('1. 可确认的 Contract\n',1)[1].split('2. 每条的条件、效果、来源及依据',1)[0]
 assert body==(P/'contracts'/c/'M.md').read_text()
 (O/'contracts'/c).mkdir(parents=True);(O/'contracts'/c/'M.md').write_text(body);(O/'contracts'/c/'H.md').write_text(h[c])
 save(O/'contracts'/c/'H.status.json',{'old':json.loads((P/'contracts'/c/'H.status.json').read_text()),'new':'候选可见文档支持','reason':'逐字核对原任务、README与源码注释；确认栏空白不构成机械阻断','independent_human_review':False,'user_approval_record_created':False})
 for g in ['N','M','H']:
  text=(P/'planned-prompts'/c/'N.md').read_text()
  if g!='N':text+='\n\n以下为辅助材料。辅助材料不能替代原维护任务。依据原任务和项目证据核查其适用性；存在冲突或证据不足时回到源码核查，不要盲目执行。\n\nContract：\n'+(body if g=='M' else h[c])
  path=O/'prompts'/c/(g+'.md');path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
 for f in (base/'candidate').rglob('*'):
  if f.is_file():app.append({'case':c,'path':str(f),'sha256':sha(f),'text':f.read_text()})
 app.append({'case':c,'path':str(base/'task.md'),'sha256':sha(base/'task.md'),'text':(base/'task.md').read_text()})
save(O/'source-texts.json',app);save(O/'source-score-bindings.previous.json',b);save(O/'contract-selection.json',sel)
save(O/'protected-history.json', {str(p):sha(p) for folder in [P,X,R/'research/code-analysis-standard-cases-v1-20261107'] for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts})
shutil.copyfile(P/'research-config.toml',O/'research-config.toml');shutil.copyfile(X/'models-cache.snapshot.json',O/'models-cache.snapshot.json')
print(O)
