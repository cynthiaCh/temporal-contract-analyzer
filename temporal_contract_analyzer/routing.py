"""Opt-in discovery candidate: deliver D only for matched task/source evidence.

No outcome, case/model ID, oracle check or learned experience is an input.
Default/manual A/D experiments retain their original definitions.
"""
import json
import re
import shutil

from . import archive
from .context import parse_sources, resolve_module
from .core import EvidenceError, sha

POLICY = 'selective-ad-v1-discovery-candidate'
QUALIFICATION = ('规则来自少量已见任务的探索；未校准、未证明跨任务泛化。'
                 '选择 A 不表示源码安全，选择 D 不表示工具判断成立或一定有收益。')
GENERIC = set('a an the to of and or in on with for is be by from that this it as task maintenance '
              'fix update change changes state initial later first missing immediately after before '
              'opening online user users existing behavior including sometimes even though appear updates '
              'now can only still becomes keeps checking delivers file panel dialog code src module '
              'js jsx ts tsx py function const return preserve while do not'.split())


def tokens(text):
    text=re.sub(r'([a-z])([A-Z])',r'\1 \2',text).replace('_',' ')
    return set(re.findall(r'[a-z][a-z0-9]*|[\u4e00-\u9fff]{2,}',text.lower()))


def task_features(task):
    if not isinstance(task,str) or not task.strip():raise EvidenceError('Routing requires the original task')
    hit=lambda pattern:bool(re.search(pattern,task,re.I|re.S))
    features=dict(
        pending=hit(r'\bpending\b|准备中|未就绪|等待中'),
        ready=hit(r'\bready\b|准备好|就绪'),
        checking=hit(r'\b(check\w*|poll\w*|retr(?:y|ies|ying|ied))\b|轮询|重试|检查'),
        initial=hit(r'\b(initial|bootstrap|first)\b|初始|首次|最初'),
        missing=hit(r'\b(missing|miss\w*|lost|absent)\b|\bno\s+initial\b|丢失|缺失|没有|看不到'),
        subscription=hit(r'\b(listen\w*|subscrib\w*|connect\w*|presence|channel|event\w*|panel)\b|监听|订阅|连接|事件|面板|在线'),
        retained_effect=hit(r'\b(audit|history|record\w*)\b|审计|历史|记录'),
        retry_or_cancel=hit(r'\b(retr(?:y|ies|ying|ied)|cancel\w*)\b|重试|取消'),
        ordering=hit(r'out.of.order|roll.{0,30}back|reentran\w*|reverse\w*|乱序|逆序|重入'))
    return features


def prefilter(task):
    features=task_features(task)
    if features['retained_effect'] and features['retry_or_cancel'] and features['ordering']:
        return features,None,'composition-outside-candidate-scope'
    if features['pending'] and features['ready'] and features['checking']:
        return features,'polling-status-transition','task-candidate'
    if features['initial'] and features['missing'] and features['subscription']:
        return features,'initial-subscription-delivery','task-candidate'
    return features,None,'no-supported-task-family'


def decide(task, report=None, sources=None, node=None):
    features,family,reason=prefilter(task)
    result=dict(schema_version='temporal-selective-ad-1',policy=POLICY,status='discovery-candidate',
                condition='none',action='A',needs_scan=bool(family and report is None),
                family=family,features=features,reason=reason,evidence=[],target_paths=[],
                qualification=QUALIFICATION)
    if not family:return result
    if report is None:
        result['reason']='source-evidence-required';return result
    if report.get('status')!='parsed':
        result['reason']='incomplete-source-scan';return result
    files={f['path']:f for f in report.get('files',[])}
    events={e['id']:e for f in files.values() for e in f.get('events',[])}
    positive=re.sub(r'do not change[^.\n]*|不要修改[^。\n]*|while preserving[^.\n]*|without changing[^.\n]*', '',task,flags=re.I)
    anchors=tokens(positive)-GENERIC
    roots=[]
    for path,file in files.items():
        functions=[f for f in file.get('functions',[]) if f.get('parent')=='<module>']
        named=[f for f in functions if anchors.intersection(tokens(str(f.get('name',''))))]
        # A filename alone cannot promote every function in a multi-consumer file.
        if not named and anchors.intersection(tokens(path)) and len(functions)==1:named=functions
        for f in named:
            roots.append(dict(file=path,start_line=f['line'],end_line=f['end_line'],symbol=f.get('name')))
    targets={r['file'] for r in roots}
    result['target_paths']=sorted(targets)
    result['target_ranges']=roots
    if not targets:
        result['reason']='no-task-source-alignment';return result
    allowed=({'continuation-lifecycle-boundaries','continuation-guard-state-review'} if family=='polling-status-transition'
             else {'connect-before-listen'})
    valid=[]
    for finding in report.get('findings',[]):
        ids=finding.get('evidence',[]);path=finding.get('path')
        if (finding.get('rule') in allowed and path in files and len(ids)>=2
                and all(i in events and events[i].get('path')==path and events[i].get('line',0)>0 for i in ids)):
            valid.append(finding)
    if not valid:
        result['reason']='no-supported-concrete-rule-evidence';return result
    reached=list(roots);parser_status='not-needed'
    def contains(event,ranges):
        return any(r['file']==event.get('path') and r['start_line']<=event.get('line',0)<=r['end_line'] for r in ranges)
    if sources:
        parsed,info=parse_sources(sources,node);parser_status=info['status']
        frontier=list(roots)
        for _ in range(2):
            next_ranges=[]
            for scope in frontier:
                path=scope['file']
                for ref in parsed.get(path,{}).get('references',[]):
                    if ref.get('usage')!='call' or not scope['start_line']<=ref['start_line']<=scope['end_line']:continue
                    binding=ref['binding'];target=path;definition=binding
                    if binding.get('kind')=='import-definition':
                        target,error=resolve_module(path,binding['module'],sources,{})
                        if error:continue
                        definition=parsed.get(target,{}).get('exports',{}).get(binding['symbol'],{})
                    if definition.get('kind')!='local-definition':continue
                    item=dict(file=target,start_line=definition['start_line'],end_line=definition['end_line'],symbol=definition.get('symbol'))
                    if not any(r['file']==target and r['start_line']<=item['start_line'] and r['end_line']>=item['end_line'] for r in reached+next_ranges):
                        next_ranges.append(item)
            reached+=next_ranges;frontier=next_ranges
    selected=[f for f in valid if all(contains(events[e],reached) for e in f['evidence'])]
    if family=='polling-status-transition':
        # Both generic lifecycle leads must concern the same reachable file.
        grouped={p:{f['rule'] for f in selected if f['path']==p} for p in {r['file'] for r in reached}}
        eligible={p for p,rules in grouped.items() if allowed.issubset(rules)}
        selected=[f for f in selected if f['path'] in eligible]
    result['relation_scope']=dict(kind='syntactic-identifier-call-reachability',max_depth=2,
                                  parser_status=parser_status,reached_ranges=reached,
                                  reached_paths=sorted({r['file'] for r in reached}),
                                  qualification='限定函数/声明范围内的词法调用候选，不是完整调用图或运行时关系证明。')
    if not selected:
        result['reason']='rule-evidence-not-linked-to-task-target';return result
    result.update(condition='review',action='D',reason='candidate-task-and-source-evidence-match',
                  evidence=[dict(finding_id=f['id'],rule=f['rule'],path=f['path'],scope=f.get('scope'),evidence=f['evidence']) for f in selected])
    return result


def prepare_selective(workbench, data):
    if 'conditions' in data:raise EvidenceError('Selective mode chooses its own A/D condition')
    if type(data.get('repeats',1)) is not int or data.get('repeats',1)!=1:
        raise EvidenceError('Selective pilot prepares one job per case')
    # Reuse one frozen input/report. Workbench eligibility still requires a
    # complete parsed scan even for A; standalone prefilter can abstain unscanned.
    manifest=workbench.prepare_case(dict(data,conditions=['none'],repeats=1))
    try:
        return _finish_selective(workbench,manifest)
    except Exception:
        shutil.rmtree(workbench.folder(manifest['id']))
        raise


def _finish_selective(workbench, manifest):
    folder=workbench.folder(manifest['id'])
    report=json.loads(archive.artifact(manifest['report_id'],'report.json',workbench.store))
    sources=archive.read_sources(manifest['report_id'],workbench.store)
    decision=decide(manifest['task'],report,sources,workbench.node)
    job=manifest['jobs'][0];directory=folder/'jobs'/job['id']
    if decision['condition']=='review':
        material=archive.layer_text(manifest['report_id'],'review',workbench.store)
        prompt=(directory/'prompt.md').read_text()+'\n<temporal-review-material>\n'+material+'\n</temporal-review-material>\n'
        (directory/'prompt.md').write_text(prompt,encoding='utf-8');(directory/'report.md').write_text(material,encoding='utf-8')
        job.update(condition='review',report_characters=len(material),prompt_sha256=sha(prompt.encode()),report_sha256=sha(material.encode()))
        manifest['conditions']=['review']
    archive.atomic_json(folder/'routing.json',decision)
    manifest['routing']=dict(policy=POLICY,action=decision['action'],reason=decision['reason'],
                            status=decision['status'],decision_sha256=sha((folder/'routing.json').read_bytes()),
                            qualification=QUALIFICATION)
    archive.atomic_json(folder/'manifest.json',manifest)
    return manifest


def validate_routing(workbench, manifest):
    folder=workbench.folder(manifest['id']);path=folder/'routing.json'
    if not path.is_file() or sha(path.read_bytes())!=manifest['routing']['decision_sha256']:
        raise EvidenceError('冻结门控决定已改变')
    decision=json.loads(path.read_text())
    if (manifest['conditions']!=[decision['condition']] or len(manifest['jobs'])!=1
            or manifest['jobs'][0]['condition']!=decision['condition']):
        raise EvidenceError('门控决定与交付条件不一致')
