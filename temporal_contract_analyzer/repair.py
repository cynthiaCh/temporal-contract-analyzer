"""Development-only, failure-specific continued repair with a matched D control.

Only explicit oracle effect booleans cross the feedback boundary. Hidden test
payloads and reference implementations never enter hypothesis material.
"""
import json
from pathlib import Path
import re
import shutil
import tempfile

from . import archive
from .case_catalog import case_root, inside, read
from .core import EvidenceError, sha
from .context import expand, merge_ranges, parse_sources, resolve_module


FAMILIES = {
    'admission': dict(words=['admission', 'bootstrap', 'registration', 'start'],
        anchors=['start', 'connect', 'subscribe', 'listen', 'select', 'switch', 'abort', 'current'],
        cause='A synchronous start/connect callback may run before ownership, listener or cleanup is established, or may replace the owner before old work is admitted.',
        order='Publish ownership and cleanup → install the appropriate consumer listener → invoke start/connect → revalidate ownership after every reentrant call.',
        test='Use a candidate-visible fake start/connect that synchronously switches or closes the owner; record listener installation, callback entry, ownership changes and new work admission. Disprove this cause if the relevant ownership checks already cover that trace.'),
    'lifecycle': dict(words=['close', 'hide', 'reopen', 'stale', 'decode', 'current', 'visit'],
        anchors=['close', 'hide', 'reopen', 'decode', 'then', 'current', 'generation', 'epoch', 'visible', 'loading', 'receive', 'publish'],
        cause='An asynchronous completion may use a retired visit/generation, or a foreground owner may have been confused with workspace-owned background work.',
        order='Identify the effect owner → invalidate that owner at its actual lifetime boundary → settle old work → independently decide whether recording, retrying and UI publication remain authorized.',
        test='Pause a completion, close/switch/reopen, then settle it before and after a new completion. Record owner identity, loading, retry scheduling and each effect separately. Compare foreground and background callers; if the visible task/source does not establish a lifetime policy, report the ambiguity instead of inventing it.'),
    'ordering': dict(words=['frame', 'reverse', 'fresh', 'order', 'monotonic'],
        anchors=['sequence', 'frame', 'decode', 'then', 'record', 'receive', 'progress', 'visit'],
        cause='Completion order or an attempt-local counter may be used where arrival order across the owning visit is needed.',
        order='Assign an arrival token under its actual owner → decode in either order → record accepted work → publish only if owner and freshness both remain valid.',
        test='Create two deferred frames and settle them in both orders, including a retry between arrivals. Record acceptance, audit and visible commits independently. Disprove the hypothesis if the saved patch already enforces visit-wide monotonic commits.'),
    'cleanup': dict(words=['cleanup', 'nested', 'reentrant', 'retry', 'cancel'],
        anchors=['cleanup', 'stop', 'remove', 'release', 'retry', 'cancel', 'select', 'hide', 'current', 'owner'],
        cause='Cleanup/cancellation may synchronously reenter navigation; an outer continuation may then overwrite the newer owner or lose an already accepted command.',
        order='Retire the previous owner → invoke cleanup/cancellation → revalidate the outer request before starting or assigning a destination; separate accepted command records from current UI ownership.',
        test='Make cleanup/cancel synchronously select another destination and then hide it. Record which destination starts, who owns cleanup, and whether accepted retry records survive. Disprove the cause if all outer continuation assignments already revalidate the request.'),
    'effects': dict(words=['audit', 'history', 'record', 'scope', 'metrics', 'background', 'telemetry'],
        anchors=['record', 'audit', 'history', 'receive', 'show', 'publish', 'background', 'metrics', 'telemetry'],
        cause='A shared guard or helper may apply one consumer’s lifetime or bootstrap policy to another effect with a different owner.',
        order='Trace each caller and effect separately → establish its visible contract → apply only that effect’s validity conditions.',
        test='Invoke both consumers of the shared helper, retire one owner, then complete accepted work. Record history, UI and metrics separately. If the candidate-visible requirements do not distinguish their policies, mark the contract unresolved.'),
}


def effect_rules(record, evaluation):
    """Read the declared rules only when bound to the scored oracle version."""
    case_path = inside(case_root(record), record['manifest'])
    if sha(case_path.read_bytes()) != evaluation.get('manifest_sha256'):
        raise EvidenceError('案例版本已改变，不能把旧评分用作修复反馈')
    case = read(case_path)
    effects = inside(case_path.parent, case['oracle']['effects'])
    probe = inside(case_path.parent, case['oracle']['probe'])
    relative = effects.relative_to(probe.parent).as_posix()
    if sha(effects.read_bytes()) != evaluation.get('oracle_files', {}).get(relative):
        raise EvidenceError('效果规则与已评分 oracle 不匹配')
    value = read(effects)['variants'][record['authorization']]
    required, forbidden = value['required'], value['forbidden']
    if (not isinstance(required,list) or not isinstance(forbidden,list) or
            any(not isinstance(i,str) for i in required+forbidden) or
            len(set(required+forbidden)) != len(required+forbidden)):
        raise EvidenceError('效果规则格式无效')
    return dict(required=required, forbidden=forbidden)


def checks(outcome, rules):
    observed = outcome.get('observed_effects', {})
    keys = rules['required'] + rules['forbidden']
    if not isinstance(observed,dict) or any(type(observed.get(k)) is not bool for k in keys):
        raise EvidenceError('oracle 缺少明确的逐效果布尔结果，不能判断退步')
    missing = [k for k in rules['required'] if not observed[k]]
    forbidden = [k for k in rules['forbidden'] if observed[k]]
    if missing != outcome.get('missing_required_effects') or forbidden != outcome.get('observed_forbidden_effects'):
        raise EvidenceError('oracle 逐效果结果与总体明细不一致')
    expected_verdict = ('UNDERREACH_AND_OVERREACH' if forbidden else 'UNDERREACH') if missing else ('OVERREACH' if forbidden else 'PASS')
    if outcome.get('verdict') != expected_verdict:
        raise EvidenceError('oracle 逐效果结果与判定不一致')
    result={('required:' + k):observed[k] for k in rules['required']}
    result.update({('forbidden:' + k):not observed[k] for k in rules['forbidden']})
    return result


def source_job(workbench, experiment_id, job_id):
    manifest = workbench.read(experiment_id)
    job = next((j for j in manifest['jobs'] if j['id']==job_id), None)
    latest = workbench.latest_evaluation(experiment_id)
    if (manifest['status'] not in {'completed','failed'} or not job or job['status']!='completed'
            or not latest or job.get('evaluation',{}).get('status')!='failed'):
        raise EvidenceError('需要已正常完成、已校准评分且语义失败的补丁')
    evaluation = read(latest)
    if evaluation.get('calibration_verdict')!='PASS':
        raise EvidenceError('参考校准未通过，不能准备修复对照')
    row = evaluation['jobs'][job_id]
    # The candidate copy that was actually scored, never the mutable workspace.
    candidate = latest.parent/job_id/'candidate'
    from .workbench import capture, inventory
    files, _ = capture(candidate)
    if inventory(files) != row.get('candidate_files'):
        raise EvidenceError('已评分候选快照改变或缺失')
    outcome = read(latest.parent/job_id/'oracle/stdout.json')
    rules = effect_rules(manifest['case'], evaluation)
    baseline = checks(outcome, rules)
    if not any(not passed for passed in baseline.values()):
        raise EvidenceError('没有可修复的失败效果')
    return manifest, candidate, dict(schema_version='temporal-repair-source-1',
        experiment_id=experiment_id, job_id=job_id, evaluation_id=evaluation['id'],
        manifest_sha256=evaluation['manifest_sha256'], oracle_files=evaluation['oracle_files'],
        runtime=evaluation['runtime'], rules=rules, checks=baseline,
        candidate_files=row['candidate_files'],
        qualification='Same scored patch in both arms; only the hypothesis arm receives development feedback.')


def words(text):
    return set(re.findall(r'[a-z][a-z0-9]*', re.sub(r'([a-z])([A-Z])',r'\1 \2',text).lower()))


def hypothesis_material(report_id, baseline, changed_files, store, node=None, max_chars=12000):
    report = json.loads(archive.artifact(report_id,'report.json',store))
    sources = archive.read_sources(report_id,store)
    modules = {f['path']:f for f in report['files']}
    parsed, parser = parse_sources(sources,node)
    hypotheses, ranked = [], []
    for number,(check,passed) in enumerate((x for x in baseline.items() if not x[1]),1):
        kind,identifier = check.split(':',1)
        tokens = words(identifier)
        family = max(FAMILIES, key=lambda name:len(tokens.intersection(FAMILIES[name]['words'])))
        spec = FAMILIES[family]
        matched = bool(tokens.intersection(spec['words']))
        h = dict(id='H'+str(number).zfill(3), check=identifier, polarity=kind,
                 status='candidate' if matched else 'unclassified', family=family if matched else 'unknown',
                 cause=spec['cause'] if matched else 'No supported failure family; inspect visible source before proposing a cause.',
                 predicted_order=spec['order'] if matched else 'Unknown.',
                 falsification=spec['test'] if matched else 'Construct a source-backed reproduction of this failed check; do not infer its business contract from its identifier.',
                 evidence=[], state_evidence=[])
        anchors=tokens.union(spec['anchors'] if matched else [])
        scored=[]
        for path,text in sorted(sources.items()):
            if path not in modules:
                continue
            lines=text.splitlines()
            for line,content in enumerate(lines,1):
                score=len(words(content).intersection(anchors))
                if not score:
                    continue
                functions=[f for f in modules[path]['functions'] if f['line']<=line<=f['end_line'] and f.get('parent')=='<module>']
                function=min(functions,key=lambda f:f['end_line']-f['line']) if functions else None
                start,end=(function['line'],function['end_line']) if function else (max(1,line-2),min(len(lines),line+2))
                scored.append((-score, 0 if path in changed_files else 1,path,start,end))
        seen=set()
        for score,changed,path,start,end in sorted(scored):
            key=(path,start,end)
            if key in seen:
                continue
            seen.add(key)
            ranked.append((score,changed,number,dict(file=path,start_line=start,end_line=end,kind='hypothesis-seed',
                reasons=[dict(kind='failure-hypothesis',hypothesis_id=h['id'])])))
        hypotheses.append(h)
    seeds, omitted = [], []
    for _,_,_,candidate in sorted(ranked,key=lambda x:(x[0],x[1],x[2],x[3]['file'],x[3]['start_line'])):
        proposed=merge_ranges(seeds+[candidate],sources)
        if sum(len(s['code']) for s in proposed)>max_chars:
            gap=dict(file=candidate['file'],start_line=candidate['start_line'],end_line=candidate['end_line'],reason='budget-limit')
            if gap not in omitted: omitted.append(gap)
        else:
            seeds=proposed
    # Reverse callers come from resolved identifier calls, not matching names.
    callers=[]
    relations=[]
    for path,module in parsed.items():
        for ref in module.get('references',[]):
            if ref.get('usage')!='call':
                continue
            binding=ref['binding'];target=path;definition=binding
            if binding['kind']=='import-definition':
                target,error=resolve_module(path,binding['module'],sources,{})
                if error: continue
                definition=parsed.get(target,{}).get('exports',{}).get(binding['symbol'],{})
            if definition.get('kind')!='local-definition': continue
            if not any(s['file']==target and s['start_line']<=definition['end_line'] and s['end_line']>=definition['start_line'] for s in seeds): continue
            relation=dict(kind='syntactic-call',from_file=path,line=ref['start_line'],symbol=ref['name'],
                          target_file=target,target_start_line=definition['start_line'],target_end_line=definition['end_line'])
            if relation not in relations:relations.append(relation)
            functions=[f for f in modules.get(path,{}).get('functions',[]) if f['line']<=ref['start_line']<=f['end_line'] and f.get('parent')=='<module>']
            f=min(functions,key=lambda f:f['end_line']-f['line']) if functions else None
            callers.append(dict(file=path,start_line=f['line'] if f else ref['start_line'],end_line=f['end_line'] if f else ref['end_line'],
                                kind='caller',reasons=[relation]))
    for candidate in callers:
        proposed=merge_ranges(seeds+[candidate],sources)
        if sum(len(s['code']) for s in proposed)<=max_chars:seeds=proposed
        else:omitted.append(dict(file=candidate['file'],start_line=candidate['start_line'],end_line=candidate['end_line'],reason='caller-budget-limit'))
    snippets,gaps=expand(seeds,sources,parsed,2,max_chars,{})
    for h in hypotheses:
        h['evidence']=[dict(file=s['file'],start_line=s['start_line'],end_line=s['end_line']) for s in snippets
                       if any(r.get('hypothesis_id')==h['id'] for r in s['reasons'])]
        for s in snippets:
            if not any(r.get('hypothesis_id')==h['id'] for r in s['reasons']):continue
            for offset,line in enumerate(s['code'].splitlines(),s['start_line']):
                names=sorted(words(line).intersection({'owner','current','active','generation','epoch','visit','aborted','visible','loading','sequence'}))
                if names:h['state_evidence'].append(dict(file=s['file'],line=offset,identifiers=names,code=line,kind='lexical-state-occurrence'))
        if not h['evidence']:h['status']='insufficient-source-evidence'
    packet=dict(schema_version='temporal-hypothesis-repair-1',report_id=report_id,hypotheses=hypotheses,
                snippets=snippets,call_relations=relations,unresolved=gaps,omitted=omitted,parser=parser,
                code_chars=sum(len(s['code']) for s in snippets),max_code_chars=max_chars,
                qualification='Feedback-exposed development; hypotheses and syntactic relations are not verified causes or complete dataflow.')
    lines=['# Failure-specific repair hypotheses','',packet['qualification'],'',
           'These check identifiers describe prior evaluation feedback, not new business requirements. Establish the intended contract from the visible task/source; report unresolved policy ambiguity. No hidden expected payloads or reference patch are provided.',
           'Start from the existing patch. Reproduce or falsify each candidate cause using candidate-visible code and test doubles before changing it. Record the event order and evidence in your answer. Preserve already working behavior; do not rewrite unrelated helpers.', '']
    for h in hypotheses:
        lines += ['## '+h['id']+' · '+h['check']+' ('+h['polarity']+')',
                  'Status: '+h['status'], 'Candidate cause: '+h['cause'],
                  'Order to inspect: '+h['predicted_order'],'Falsification procedure: '+h['falsification'],
                  'Source anchors: '+json.dumps(h['evidence'],ensure_ascii=False),
                  'State occurrences (not proven ownership): '+json.dumps(h['state_evidence'],ensure_ascii=False), '']
    lines+=['## Candidate call relations',json.dumps(relations,ensure_ascii=False,indent=2),'','## Source evidence']
    for s in snippets:
        fence='`'*max(3,max((len(v) for v in re.findall(r'`+',s['code'])),default=0)+1)
        lines+=['### '+s['file']+':'+str(s['start_line'])+'–'+str(s['end_line']),fence,s['code'].rstrip(),fence,'']
    lines+=['## Unresolved / omitted',json.dumps(dict(unresolved=gaps,omitted=omitted),ensure_ascii=False,indent=2)]
    return packet,'\n'.join(lines)+'\n'


def prepare_pair(workbench, experiment_id, job_id, treatment='hypothesis_review', paired=True):
    from .workbench import capture, file_modes, inventory, write_files
    if treatment not in {'hypothesis_review','rag_only'} or (not paired and treatment!='rag_only'):
        raise EvidenceError('Unknown continued-repair treatment')
    parent,candidate,source = source_job(workbench,experiment_id,job_id)
    files, _=capture(candidate)
    # Existing prepare() rejects source/store overlap. Reuse it with an outside
    # temporary copy, then bind the pair to its own frozen input before return.
    with tempfile.TemporaryDirectory(prefix='tca-continued-repair-') as temp:
        staging=Path(temp)/'patch';write_files(staging,files,file_modes(candidate,files))
        m=workbench.prepare(dict(candidate=str(staging),task=parent['task'],label=parent['label']+(' · repair pair' if paired else ' · RAG-only'),
            model=parent['model'],effort='medium' if parent['effort']=='local-default' else parent['effort'],
            mode=parent['mode'],timeout=parent['timeout'],repeats=1,conditions=['none']))
    folder=workbench.folder(m['id'])
    try:
        changed={name for name in set(parent['input_files'])|set(source['candidate_files']) if parent['input_files'].get(name)!=source['candidate_files'].get(name)}
        context_file='hypotheses.json'
        if treatment=='rag_only':
            from .rag import build_rag_context
            packet,extra=build_rag_context(m['report_id'],parent['task'],files,workbench.store,workbench.node)
            context_file='rag-context.json'
            source['qualification']='RAG receives task and retrieved public candidate content only. Failure selection/evaluation is researcher-side; controls may be historical.'
        else:
            packet,extra=hypothesis_material(m['report_id'],source['checks'],changed,workbench.store,workbench.node)
        archive.atomic_json(folder/'retry-source.json',source)
        archive.atomic_json(folder/context_file,packet)
        report=archive.layer_text(m['report_id'],'review',workbench.store) if paired or treatment!='rag_only' else ''
        shutil.rmtree(folder/'jobs')
        order=(['review',treatment] if int(experiment_id[-1],16)%2==0 else [treatment,'review']) if paired else [treatment]
        jobs=[]
        common=('Work only on the candidate-visible files in this workspace. Do not inspect sibling experiment jobs, original repositories or report stores.\n\n'
                +parent['task'].strip()+'\n\nThis workspace starts from an existing patch. Continue the task, inspect remaining issues, and preserve behavior that already works. Use candidate-visible checks and record their results.\n')
        for number,condition in enumerate(order,1):
            jid='j-'+str(number).zfill(3);directory=folder/'jobs'/jid;directory.mkdir(parents=True)
            material=extra if condition=='rag_only' else report+ ('\n'+extra if condition=='hypothesis_review' else '')
            tag='retrieved-candidate-context' if condition=='rag_only' else 'temporal-review-material'
            prompt=common+'\n<'+tag+'>\n'+material+'\n</'+tag+'>\n'
            (directory/'prompt.md').write_text(prompt,encoding='utf-8');(directory/'report.md').write_text(material,encoding='utf-8')
            jobs.append(dict(id=jid,repeat=1,condition=condition,status='prepared',prompt_sha256=sha(prompt.encode()),
                report_sha256=sha(material.encode()),report_characters=len(material),delivery='not_started'))
        m.update(jobs=jobs,conditions=order,case=parent['case'],original_candidate=str(candidate),effort=parent['effort'],
                 retry=dict(source_experiment=experiment_id,source_job=job_id,
                    source_sha256=sha((folder/'retry-source.json').read_bytes()),context_sha256=sha((folder/context_file).read_bytes()),
                    context_file=context_file,treatment=treatment,paired=paired,
                    budget='same model, effort and per-job timeout; input/output tokens measured, not equalized',
                    order='deterministic parent-ID parity; not randomization' if paired else 'single RAG arm; historical controls',
                    qualification=source['qualification']))
        for key in ('local_codex','model_override','config_source','model_catalog'):
            if key in parent:m[key]=parent[key]
        archive.atomic_json(folder/'manifest.json',m)
        return m
    except Exception:
        shutil.rmtree(folder)
        raise


def validate_pair(workbench, manifest):
    folder=workbench.folder(manifest['id']);retry=manifest['retry']
    treatment=retry.get('treatment','hypothesis_review')
    context_file=retry.get('context_file','hypotheses.json')
    if (treatment not in {'hypothesis_review','rag_only'} or
            context_file!=('rag-context.json' if treatment=='rag_only' else 'hypotheses.json')):
        raise EvidenceError('Unknown frozen repair context')
    for name,key in (('retry-source.json','source_sha256'),(context_file,'context_sha256')):
        path=folder/name
        if not path.is_file() or sha(path.read_bytes())!=retry[key]:
            raise EvidenceError('冻结修复反馈或假设已改变：'+name)
    source=read(folder/'retry-source.json')
    if manifest['input_files']!=source['candidate_files']:
        raise EvidenceError('修复输入与已评分补丁不同')
    expected=sorted(['review',treatment]) if retry.get('paired',True) else ['rag_only']
    if (sorted(manifest['conditions'])!=expected or sorted(j['condition'] for j in manifest['jobs'])!=expected):
        raise EvidenceError('修复对照条件改变')


def regression_summary(manifest, folder, evaluation):
    source=read(folder/'retry-source.json')
    comparison=dict(status='verified',source_experiment=source['experiment_id'],source_job=source['job_id'],jobs={})
    if (evaluation.get('calibration_verdict')!='PASS' or evaluation.get('manifest_sha256')!=source['manifest_sha256']
            or evaluation.get('oracle_files')!=source['oracle_files'] or evaluation.get('runtime')!=source['runtime']):
        comparison['status']='unverified';comparison['reason']='评分环境或 oracle 与父评分不同，不能判断退步'
    for job in manifest['jobs']:
        result=evaluation['jobs'].get(job['id'],{})
        row=dict(status='unverified',eligible=False)
        if comparison['status']=='verified' and result.get('status') in {'passed','failed'}:
            try:
                current=checks(read(folder/result['result_path']),source['rules'])
                gained=[k for k,v in current.items() if v and not source['checks'][k]]
                lost=[k for k,v in source['checks'].items() if v and not current[k]]
                remaining=[k for k,v in current.items() if not v]
                row=dict(status='regressed' if lost else 'preserved',eligible=not lost,
                         gained=gained,lost=lost,remaining_failed=remaining,
                         prior_passed=sum(source['checks'].values()),now_passed=sum(current.values()),
                         total=len(current),fully_repaired=result['status']=='passed' and not lost,
                         adoption='reject-regression' if lost else 'eligible-no-automatic-promotion')
            except (EvidenceError,KeyError,ValueError,OSError) as error:
                row['reason']=str(error)
        else:row['reason']=comparison.get('reason',result.get('reason','候选未完成有效评分'))
        result['regression']=row
        comparison['jobs'][job['id']]=row
    evaluation['repair_comparison']=comparison
    archive.atomic_json(folder/'evaluations'/evaluation['id']/'summary.json',evaluation)
    return evaluation
