"""Evidence pointers and scope checks, supplementary to unchanged behavior scoring."""
import json,re
from pathlib import Path
from run import OUT,read,save,sha,ARMS,CASES

def relative(p):return str(Path(p).relative_to(OUT))
def main():
 rows=read(OUT/'results.json');trajectories=read(OUT/'trajectory-evidence.json');rv=[];negative=[]
 for r in rows:
  d=Path(r['path'])/'jobs/j-001';t=next(t for t in trajectories if t['id']==r['id']);changes=read(d/'changes.json')
  if r['case']=='feature-flag-readiness-vue3' and r.get('evaluation'):
   base=Path(r['path'])/'input/src/temporal-flow.js';scored=Path(r['evaluation']).parent/'j-001/candidate/src/temporal-flow.js'
   def adjacent(s):return s[s.index('async function runAdjacent'):s.index('module.exports')].strip()
   a,b=adjacent(base.read_text()),adjacent(scored.read_text())
   negative.append(dict(id=r['id'],arm=r['arm'],replicate=r['replicate'],changed_paths=t['changed_paths'],only_target_flow_file_changed=t['changed_paths']==['src/temporal-flow.js'],adjacent_source_unchanged=a==b,adjacent_before_sha256=sha(a),adjacent_after_sha256=sha(b),changes=relative(d/'changes.json'),raw_oracle=relative(Path(r['evaluation']).parent/'j-001/oracle/stdout.json')))
  if r['arm']=='R' and r['question_ids']:
   read_cmds=[];test_cmds=[]
   for c in t['commands']:
    if re.search(r'\b(cat|sed|rg)\b',c['command']):read_cmds.append(dict(events_line=c['line'],command=c['command'],exit_code=c['exit_code']))
    if 'node' in c['command'] and ('assert' in c['command'] or 'throw' in c['command']):test_cmds.append(dict(events_line=c['line'],command=c['command'],exit_code=c['exit_code']))
   rv.append(dict(case=r['case'],replicate=r['replicate'],selected=r['question_ids'],id=r['id'],prompt=relative(d/'prompt.md'),events=relative(d/'events.jsonl'),changes=relative(d/'changes.json'),raw_oracle=relative(Path(r['evaluation']).parent/'j-001/oracle/stdout.json') if r.get('evaluation') else None,read_commands=read_cmds,executable_check_commands=test_cmds,interpretation='Commands provide code-reading and concrete test evidence; they do not prove the prompt caused that reasoning or exhaustive coverage. Compare original raw stdout and patch.'))
 save(OUT/'evidence-review.json',dict(retrieved_applicable_runs=rv,negative_scope_audit=negative,notes='Supplementary source scope audit; no scoring standard changed. Primary original behavior score remains authoritative within its bounded scope.'))
 lines=['# 轨迹与补丁证据索引','', '选题审查先于正式调用；这里是行为完成后的证据核对。链接全部相对本实验目录，评分路径指向实际被冻结评分的候选，不能以workspace后续内容替代。','']
 for r in rv:
  lines += [f"## {r['case']} R / repeat {r['replicate']}", '',f"交付 {', '.join(r['selected'])}：[prompt]({r['prompt']})；[轨迹]({r['events']})；[补丁]({r['changes']})；[原始评分]({r['raw_oracle']})。", '']
  for label,key in [('读代码','read_commands'),('可执行核查','executable_check_commands')]:
   for c in r[key]:
    # First line and line pointer keep the index readable; exact command in JSON/event.
    first=c['command'].splitlines()[0]
    lines.append(f"- {label}，events.jsonl 第 {c['events_line']} 行，退出码 {c['exit_code']}：`{first[:180]}`")
  lines += ['','这些命令证明接触了相关源码并运行了相应检查；不能从成功/自述推断题目是因果原因，也不能认为覆盖全部事件顺序。','']
 lines += ['## 不适用案例的改动范围','']
 for r in negative:lines.append(f"- {r['arm']} / repeat {r['replicate']}：仅改target flow文件={r['only_target_flow_file_changed']}，adjacent源码逐字保留={r['adjacent_source_unchanged']}；[补丁]({r['changes']})，[评分]({r['raw_oracle']})。")
 (OUT/'EVIDENCE.md').write_text('\n'.join(lines)+'\n')
 print('evidence runs',len(rv),'negative checks',len(negative))
if __name__=='__main__':main()
