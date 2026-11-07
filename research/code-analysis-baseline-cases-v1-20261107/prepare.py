"""Offline input verification and frozen source-only prompts. Never calls a model."""
import hashlib,json,random,shutil,subprocess
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parent.parent
ST=ROOT/'research/code-analysis-standard-cases-v1-20261107'
OLD=ROOT/'research/code-analysis-skill-evolution-v1-20261107'
def sha(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
def save(p,obj):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def main():
 assert not (OUT/'schedule.json').exists()
 d=json.loads((ST/'source-manifest.json').read_text());freeze=json.loads((OLD/'K0.freeze.json').read_text())
 assert sha(OLD/'analysis_skill_K0.md')==freeze['files']['analysis_skill_K0.md']['sha256']
 shutil.copyfile(OLD/'analysis_skill_K0.md',OUT/'analysis_skill_K0.md')
 shutil.copyfile(OLD/'report.schema.json',OUT/'report.schema.json')
 common='''当前任务仅为代码分析报告。原始维护任务只作为分析背景，不执行维护、不修改候选文件、不运行测试或评分，不产生代码补丁。

<original-task-background>
{{TASK}}</original-task-background>

<analysis-skill>
{{SKILL}}</analysis-skill>

# 统一分析报告协议

只分析隔离候选工作区的源码与文档。允许只读列出、检索和查看文件；不要执行候选程序。不得读取研究标准、确认记录、评分、参考补丁、历史模型输出或其他运行结果。

返回 JSON 对象，唯一字段为 report，按以下六部分组织：
1. 原任务目标与需要保留的行为；
2. 关键源码事实及路径、行号；
3. 相关事件顺序及其依据；
4. 不同消费者、阶段或效果是否采用不同条件；
5. 能确认的要求、仅有线索的判断及未知项；
6. 建议验证的行为范围。

只要求简短依据和引用，不输出完整内部思维链。区分实现事实、任务或文档要求、假设与未知；不要把建议验证写成已经验证。

report 不超过 6000 个 Unicode 字符（标题、空白、标点、英文均计入）。归档不裁剪；超限、格式错误和失败输出原样保留，不重生成，不以篇幅评价质量。
'''
 (OUT/'common-prompt-template.md').write_text(common)
 cases=[];conf=[]
 for c in d['cases']:
  cid=c['id'];base=OUT/'materials'/cid;base.mkdir(parents=True)
  shutil.copytree(ST/c['candidate_root'],base/'candidate')
  shutil.copyfile(ST/c['task']['path'],base/'task.md')
  a=json.loads((ROOT/c['primary_archive']['manifest']).read_text())
  inventory={f['candidate_path']:f['sha256'] for f in c['files']}
  actual={str(f.relative_to(base/'candidate')):sha(f) for f in (base/'candidate').rglob('*') if f.is_file()}
  assert actual==inventory==a['input_files']
  assert sha(base/'task.md')==c['task']['sha256'] and (base/'task.md').read_text()==a['task']
  assert sha(ST/c['report'])==c['report_sha256'] and not c['approved'] and c['confirmation']=='待确认'
  prompt=common.replace('{{TASK}}',(base/'task.md').read_text()).replace('{{SKILL}}',(OUT/'analysis_skill_K0.md').read_text())
  (base/'prompt.md').write_text(prompt)
  cases.append(dict(case=cid,case_id=c['case_id'],unit=c['independent_unit_id'],source_manifest=str(ST/'source-manifest.json'),source_archive=c['primary_archive'],candidate_files=inventory,task_sha256=sha(base/'task.md'),prompt_sha256=sha(base/'prompt.md'),known_exposure=c['known_exposure']))
  conf.append(dict(case=cid,user_confirmed_standard_items=[],pending_requirement_items=[cid+'-R'+str(i) for i in range(1,4)],pending_questions=[cid+'-Q1',cid+'-Q2'],standard_sha256=sha(ST/c['report']),source_facts='S1-S6 are source-checkable draft facts, not user-approved normative policies',policy='Explicit task and exact visible documentation may be identified as such; pending business-policy omissions are descriptive coverage observations, never definitive business errors or counted losses.',approved=False))
 rng=random.Random(2026110708);order=[]
 for rep in (1,2):
  cs=['C1','C2','C3'];rng.shuffle(cs)
  for cid in cs:order.append(dict(call_id='a'+str(len(order)+1).zfill(2),case=cid,repeat=rep,sequence=len(order)+1))
 save(OUT/'schedule.json',dict(seed=2026110708,seed_role='schedule only, not model sampling seed',order=order))
 save(OUT/'source-verification.json',dict(status='PASS',cases=cases,K0=dict(source=str(OLD/'analysis_skill_K0.md'),sha256=sha(OUT/'analysis_skill_K0.md'),bytes=(OUT/'analysis_skill_K0.md').stat().st_size,freeze_source=str(OLD/'K0.freeze.json')),standards_manifest_sha256=sha(ST/'source-manifest.json'),standard_validation_sha256=sha(ST/'validation.json')))
 save(OUT/'confirmation-status.json',dict(status='all standards pending, no approval inferred from task authorization',cases=conf,independent_human_review=False))
 print(json.dumps({'status':'OFFLINE_INPUTS_PASS','schedule':order,'K0_sha256':sha(OUT/'analysis_skill_K0.md')}))
if __name__=='__main__':main()
