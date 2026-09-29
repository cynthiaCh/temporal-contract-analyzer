"""Source facts and conservative syntax patterns. No benchmark/oracle imports."""
import collections
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys

from .python_adapter import analyze as python_analyze
from .lifecycle import lifecycle_patterns
from .reentrancy import reentrancy_patterns

VERSION='0.6.0'
ROOT=Path(__file__).resolve().parents[1]
JS_EXT={'.js','.mjs','.cjs','.jsx','.ts','.tsx'}
CODE_EXT=JS_EXT|{'.py','.vue','.go','.java','.rs','.c','.h','.cpp','.cs','.rb'}
EXCLUDED={'oracle','reference','references','mutants','negative-controls','results','studies','evidence','paper','node_modules','vendor','dist','build','__pycache__','.git','.venv','venv'}
MAX_FILE=1024*1024
MAX_TOTAL=25*1024*1024

# These are search clues, never inferred business obligations or type guarantees.
CALL_TAGS={
 'registration': {'addEventListener','addListener','on','once','subscribe','register'},
 'notification': {'dispatchEvent','emit','notify','notify_all','notifyAll'},
 'continuation': {'then','catch','finally','add_done_callback','whenComplete','thenApply'},
 'scheduling': {'queueMicrotask','setTimeout','setInterval','requestAnimationFrame','create_task','ensure_future','call_soon','call_later'},
 'cleanup_or_cancel': {'removeEventListener','removeListener','unsubscribe','abort','cancel','close','aclose','release','dispose','disconnect','clearTimeout','clearInterval','cancelAnimationFrame'},
 'coordination': {'gather','shield','wait_for','join','acquire','wait','task_done','flush'},
 'transaction': {'commit','rollback','begin','transaction'},
 'request': {'fetch','request','get','post'},
 'effect': {'publish','render','renderState','save','write','persist','commit','notify','download'},
}
LIMITS=[
 '结果是语法事实、静态候选调用关系与待核查模式，不是已证明的时序契约、缺陷、严重度或难度分。',
 '同名 API 只作为线索；不做全程序类型/别名/控制流证明。动态派发、对象工厂、函数参数传递的完整目标保持未知。',
 '局部先后表示同一语法块中位置先后；条件、异常、循环、短路及调用是否实际执行仍需核查。',
 'await 是潜在暂停点，并非必然切换；取消请求不等于工作与清理完成；移除监听不保证既有异步工作取消。',
 '语法中的 if/try/finally 不等于已证明保护充分；无模式命中不等于程序安全。',
 '未读取隐藏评分器、参考补丁、模型结果或人工 profile；分析根由操作者提供，文件内容的来源仍需核实。',
]


class EvidenceError(ValueError): pass

def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def sha(raw):return hashlib.sha256(raw).hexdigest()
def normalize(value):return re.sub(r'\s+',' ',value).strip()


def collect(directory):
    root=Path(directory).expanduser()
    if not root.is_dir() or root.is_symlink():raise EvidenceError('请指定真实的候选源码目录（不是符号链接）')
    root=root.resolve()
    if root.name in EXCLUDED or any(part in {'oracle','reference','references','mutants','negative-controls'} for part in root.parts):raise EvidenceError('不能把评分器、结果、参考或依赖目录作为扫描根')
    if (root/'case.json').is_file() or (root/'case-clusters').is_dir():raise EvidenceError('请指向候选工程 base/ 或独立补丁工程，不要扫描整个案例/研究仓库')
    sources={};skipped=[];total=0
    for folder,dirs,files in os.walk(root,followlinks=False):
        keep=[]
        for name in sorted(dirs):
            path=Path(folder)/name;rel=path.relative_to(root).as_posix()
            if path.is_symlink():skipped.append(dict(path=rel,reason='symlink_directory'))
            elif name in EXCLUDED or name.startswith('.'):skipped.append(dict(path=rel,reason='excluded_directory'))
            else:keep.append(name)
        dirs[:]=keep
        for name in sorted(files):
            path=Path(folder)/name;rel=path.relative_to(root).as_posix()
            if name.startswith('.'):continue
            if path.is_symlink():skipped.append(dict(path=rel,reason='symlink_file'));continue
            if path.suffix.lower() not in CODE_EXT:continue
            if path.stat().st_size>MAX_FILE:skipped.append(dict(path=rel,reason='file_size_limit'));continue
            total+=path.stat().st_size
            if total>MAX_TOTAL or len(sources)>=1000:raise EvidenceError('候选源码超过本工具范围（1000 文件 / 25 MiB）')
            raw=path.read_bytes()
            try:sources[rel]=raw.decode('utf-8')
            except UnicodeDecodeError:skipped.append(dict(path=rel,reason='non_utf8_source'))
    return sources,sorted(skipped,key=lambda x:(x['path'],x['reason']))


def js_analyze(sources,node=None):
    executable=node or shutil.which('node')
    if not executable:return [],dict(status='unavailable',reason='Node.js not found; npm ci --prefix tools/temporal-contract-analyzer required for JS/TS/Vue')
    try:
        p=subprocess.run([executable,str(ROOT/'tools/temporal-contract-analyzer/parse.cjs')],input=canonical({'files':[dict(path=p,text=t) for p,t in sorted(sources.items())]}),text=True,capture_output=True,timeout=45)
        if p.returncode:return [],dict(status='unavailable',reason='JS parser failed; run npm ci --prefix tools/temporal-contract-analyzer',detail=p.stderr[-1500:])
        data=json.loads(p.stdout)
        metadata=dict(status='available',parser=data['parser'],version=data['version'],library_sha256=data['library_sha256'],node=data['node'])
        if 'sfc_parser' in data:metadata['sfc_parser']=data['sfc_parser']
        return data['files'],metadata
    except (OSError,subprocess.TimeoutExpired,ValueError) as e:return [],dict(status='unavailable',reason=type(e).__name__)


def enrich(files):
    for file in files:
        for f in file['functions']:
            f['local_id']=f['id'];f['id']=file['path']+'::'+f['id'];f['path']=file['path']
        for e in file['events']:
            e['id']=file['path']+'::'+e['id'];e['path']=file['path'];e['tags']=[]
            if e['kind']=='call':
                tail=e['callee'].rsplit('.',1)[-1]
                e['tags']=[tag for tag,names in CALL_TAGS.items() if tail in names]
                e['api_basis']='name_clue_only' if e['tags'] else 'unmodeled_call'
            elif e['kind'] in {'await','yield','resource_scope','guard','async_iteration'}:e['tags']=[e['kind']]
    by_path={f['path']:f for f in files};links=[]
    for file in files:
        scopes={f['local_id']:f for f in file['functions']}
        def ancestry(scope):
            while scope:
                if scope in scopes:yield scope
                scope=scopes.get(scope,{}).get('parent',scope.rsplit('/',1)[0] if '/' in scope else None)
        for e in file['events']:
            if e['kind']!='call':continue
            callee=e['callee'];parts=callee.split('.');e['binding']='unresolved';target=None
            for scope in ancestry(e['scope']):
                f=scopes.get(scope,{})
                if parts[0] in f.get('parameters',[]):
                    e['binding']='parameter_callback' if len(parts)==1 else 'parameter_member'
                    if len(parts)==1:e['tags'].append('parameter_callback')
                    break
                bindings=[b for b in file['bindings'] if b['scope']==scope and b['name']==parts[0]]
                writes=[w for w in file['events'] if w['kind']=='write' and w['scope']==scope and w.get('target')==parts[0]]
                imports=[i for i in file['imports'] if i['scope']==scope and i['local']==parts[0]]
                if bindings:
                    if len(parts)==1 and len(bindings)==1 and not writes:target=file['path']+'::'+bindings[0]['target'];e['binding']='lexical_declaration_candidate'
                    else:e['binding']='ambiguous_or_reassigned'
                    break
                if writes:e['binding']='local_value_unresolved';break
                if imports:
                    if len(imports)!=1:e['binding']='ambiguous_import';break
                    imp=imports[0];e['binding']='import_binding_candidate'
                    qualified=imp['module']+('' if imp['symbol']=='*' else '.'+imp['symbol'])+('.'+'.'.join(parts[1:]) if len(parts)>1 else '')
                    e['import_name']=qualified
                    module=imp['module']
                    if module.startswith('.') and imp['symbol'] not in {'*','default'} and len(parts)==1:
                        if file['language']=='python':
                            levels=len(module)-len(module.lstrip('.'));base=PurePosixPath(file['path']).parent
                            for _ in range(levels-1):base=base.parent
                            rel=str(base/module.lstrip('.').replace('.','/'));candidates=[rel+'.py',rel+'/__init__.py']
                        else:
                            import posixpath
                            rel=posixpath.normpath(str(PurePosixPath(file['path']).parent/module));candidates=[rel] if PurePosixPath(rel).suffix else [rel+x for x in ('.js','.ts','.mjs','.cjs','/index.js')]
                        matches=[by_path[p] for p in candidates if p in by_path]
                        if len(matches)==1:
                            other=matches[0];export=other['exports'].get(imp['symbol'])
                            defs=[b for b in other['bindings'] if b['scope']=='<module>' and b['name']==export]
                            if len(defs)==1:target=other['path']+'::'+defs[0]['target']
                    break
            if target:links.append(dict(kind='candidate_call_target',call=e['id'],target=target,basis=e['binding'],qualification='Lexical/import binding candidate only; execution, reassignment timing and arguments not proven.'))
    return links


def patterns(files):
    findings=[];relations=[]
    def finding(rule,file,events,message,condition,question):
        findings.append(dict(rule=rule,path=file['path'],scope=events[0]['scope'],evidence=[e['id'] for e in events],message=message,condition=condition,review_question=question,classification='review_hint_not_bug_verdict'))
    for file in files:
        es=file['events'];calls=[e for e in es if e['kind']=='call']
        groups=collections.defaultdict(list)
        for e in es:groups[(e['scope'],e['block'])].append(e)
        for group in groups.values():
            starts=[e for e in group if e['kind']=='call' and e['callee'].endswith('.connect')]
            listeners=[e for e in group if e['kind']=='call' and e['callee'].endswith('.addEventListener')]
            for start in starts:
                for listener in listeners:
                    receiver=listener['receiver'].removesuffix('.target') if hasattr(str,'removesuffix') else re.sub(r'\.target$','',listener['receiver'])
                    if not receiver or receiver!=start['receiver'] or start['statement']==listener['statement']:continue
                    first,second=sorted([start,listener],key=lambda e:e['statement'])
                    relations.append(dict(kind='lexical_before_same_block',before=first['id'],after=second['id'],qualification='Only if both statements execute on this path; not a whole-program happens-before proof.'))
                    early=first is listener
                    finding('listen-before-connect' if early else 'connect-before-listen',file,[first,second],
                            '同一语法块中监听注册位于连接调用之前。' if early else '同一语法块中连接调用位于监听注册之前。',
                            '接收者语法表达式相同；需确认对象类型、别名稳定性、同步通知与是否允许漏收。',
                            '提前监听可能激活同步回调：归属/清理信息是否先建立？' if early else '若 connect 同步发消息，这个消费者是否应接收初始消息？统计消费者可能有意忽略它。')
            waits=[e for e in group if e['kind']=='await']
            effects=[e for e in group if e['kind']=='call' and 'effect' in e['tags']]
            for wait in waits:
                after=next((e for e in effects if e['statement']>wait['statement']),None)
                if after:finding('effect-after-await',file,[wait,after],'同一语法块中，潜在等待点之后出现效果名称线索。','只表示源码顺序；效果语义、是否真的暂停及中间保护需人工核查。','结果完成后对象仍有效吗？这个效果应继续完成还是应失效？')
            for y in [e for e in group if e['kind']=='yield']:
                commit=next((e for e in group if e['kind']=='call' and e['callee'].endswith('.commit') and e['statement']>y['statement']),None)
                if commit:finding('commit-after-yield',file,[y,commit],'yield 之后的正常继续路径包含 commit 名称调用。','需确认生成器/上下文管理器协议和连接类型；异常路径不保证提交。','通知或外部副作用是否要求等事务提交成功？')
        for write in [e for e in es if e['kind']=='write' and e.get('rhs_callee') and e.get('operator')=='=']:
            nested=[e for e in calls if e['scope']==write['scope'] and e['callee']==write['rhs_callee'] and (e['line'],e['column'])>=(write['line'],write['column']) and (e['end_line'],e['end_column'])<=(write['end_line'],write['end_column'])]
            if not nested:continue
            call=nested[-1]
            relations.append(dict(kind='rhs_before_assignment',before=call['id'],after=write['id'],qualification='Assignment occurs after successful RHS evaluation; call return alone does not imply asynchronous work completion.'))
            if re.search(r'(release|cleanup|unsubscribe|dispose)',write['target'],re.I):
                finding('cleanup-handle-after-call',file,[call,write],'清理句柄名称的赋值发生在右侧调用成功求值之后。','若调用内可能执行用户回调，须另查回调是否重入；本条不声称重入已发生。','回调先切换/关闭时，旧操作返回后会覆盖新清理句柄吗？')
        continuations=[e for e in calls if 'continuation' in e['tags']]
        removals=[e for e in calls if e['callee'].endswith('.removeEventListener')]
        for continuation in continuations:
            removal=next((e for e in removals if file['language']!='vue' or e['scope'].split('/')[0]==continuation['scope'].split('/')[0]),None)
            if removal:
                finding('continuation-and-listener-removal',file,[continuation,removal],'同一文件中同时存在完成回调登记和监听移除。','仅是共现线索；需追踪是否属于同一工作、同一生命周期。','若二者相关，移除监听后，已开始的工作完成时是否还有有效性检查？')
                break
        for e in es:
            if e['kind']=='return' and any(c.startswith('AsyncFor path') for c in e['conditions']):
                finding('early-return-from-async-iteration',file,[e],'异步迭代体内存在提前返回。','需确认迭代器所有权、上下文管理和调用者协议；不直接判断是否必须由此函数关闭。','若此函数拥有资源，提前返回前是否完成必要关闭？')
        for e in calls:
            if any('finally path'==c for c in e['conditions']) and ('cleanup_or_cancel' in e['tags'] or e['callee'].endswith('.pop')):
                finding('cleanup-in-finally',file,[e],'finally 路径包含清理名称线索。','不证明所有退出路径、清理完成时间或清理异常均正确。','该路径是否等待必要清理完成？清理中断时如何处理？')
            if e.get('import_name')=='asyncio.shield':
                finding('asyncio-shield-call',file,[e],'存在通过导入名称定位的 asyncio.shield 调用。','基于导入绑定候选；未验证运行时替换或参数实际归属。','这里是否用于区分等待者取消与共享任务生命周期？')
    findings.extend(lifecycle_patterns(files))
    reentrant_findings, reentrant_relations = reentrancy_patterns(files)
    findings.extend(reentrant_findings)
    relations.extend(reentrant_relations)
    for i,f in enumerate(findings):f['id']='hint-'+str(i+1)
    return findings,relations


def analyze_sources(sources,node=None,skipped=None):
    # This API also supports already-frozen candidate text. Refuse obvious evaluator paths.
    for path,text in sources.items():
        p=PurePosixPath(path)
        if p.is_absolute() or '..' in p.parts or any(x in EXCLUDED or x.startswith('.') for x in p.parts):raise EvidenceError('禁止的输入路径: '+path)
        if not isinstance(text,str):raise EvidenceError('源码必须是 UTF-8 文本')
    files=[];js={};adapters={'python':dict(parser='stdlib.ast',version=sys.version.split()[0])}
    for path,text in sorted(sources.items()):
        ext=PurePosixPath(path).suffix.lower()
        if ext=='.py':files.append(python_analyze(path,text))
        elif ext in JS_EXT or ext=='.vue':js[path]=text
        else:files.append(dict(path=path,language=ext.lstrip('.'),status='unsupported_language',functions=[],events=[],imports=[],exports={},bindings=[]))
    if js:
        parsed,metadata=js_analyze(js,node);adapters['javascript_typescript']=metadata;files+=parsed
        if not parsed:
            for path in js:files.append(dict(path=path,language='vue' if PurePosixPath(path).suffix.lower()=='.vue' else 'javascript/typescript',status='parser_unavailable',functions=[],events=[],imports=[],exports={},bindings=[]))
    files.sort(key=lambda f:f['path'])
    for file in files:file['sha256']=sha(sources[file['path']].encode())
    links=enrich(files);findings,relations=patterns(files)
    inputs=[dict(path=p,sha256=sha(t.encode())) for p,t in sorted(sources.items())]
    tool_files=['temporal_contract_analyzer/__init__.py','temporal_contract_analyzer/__main__.py','temporal_contract_analyzer/cli.py','temporal_contract_analyzer/review_packet.py','temporal_contract_analyzer/core.py','temporal_contract_analyzer/lifecycle.py','temporal_contract_analyzer/reentrancy.py','temporal_contract_analyzer/python_adapter.py','temporal_contract_analyzer/report.py','tools/temporal-contract-analyzer/parse.cjs','tools/temporal-contract-analyzer/package.json','tools/temporal-contract-analyzer/package-lock.json']
    tool_hash=sha(canonical({p:sha((ROOT/p).read_bytes()) for p in tool_files if (ROOT/p).is_file()}).encode())
    incomplete=any(f['status']!='parsed' for f in files) or any(s['reason']!='excluded_directory' for s in skipped or [])
    report=dict(schema_version='temporal-contract-analysis-1',tool_version=VERSION,tool_sha256=tool_hash,input_sha256=sha(canonical(inputs).encode()),adapters=adapters,
                scope='candidate-source-only; no oracle, model outputs, profile labels or candidate execution',
                status='partial' if incomplete else 'parsed' if files else 'empty',inputs=inputs,skipped=skipped or [],limitations=LIMITS,files=files,call_links=links,relations=relations,findings=findings,
                summary=dict(files=len(files),parsed_files=sum(f['status']=='parsed' for f in files),events=sum(len(f['events']) for f in files),candidate_call_links=len(links),review_hints=len(findings)))
    if any(f['language']=='vue' for f in files):
        report['limitations']=LIMITS+['Vue 仅分析内联 <script>/<script setup> 的 JS/TS/JSX/TSX 语法；不分析模板表达式、样式、自定义块转换、生成代码或 Vue 运行时调度。两个脚本块独立分析，跨块绑定与组件实例方法派发保持未知。parsed 表示上述范围内的解析完成，不是整个组件行为已被验证。']
    return report


def scan(directory,node=None):
    sources,skipped=collect(directory);return analyze_sources(sources,node,skipped)


def compare(before,after):
    def facts(report):
        values={};events={e['id']:e for f in report['files'] for e in f['events']}
        def event_key(e):return [e['path'],e['scope'],e['kind'],normalize(e.get('callee') or e.get('target') or e.get('expression') or e['text']),e.get('operator',''),e.get('awaited',False),[normalize(c) for c in e['conditions']]]
        for f in report['findings']:
            signature=canonical([f['rule'],f['path'],f['scope'],[event_key(events[e]) for e in f['evidence']]])
            values.setdefault(signature,[]).append(f)
        return values
    left,right=facts(before),facts(after)
    comparable=before['status']=='parsed' and after['status']=='parsed' and before['adapters']==after['adapters'] and before['tool_sha256']==after['tool_sha256']
    added=[];removed=[]
    for key in sorted(set(left)|set(right)):
        a,b=left.get(key,[]),right.get(key,[])
        added+=b[min(len(a),len(b)):];removed+=a[min(len(a),len(b)):]
    files_before={f['path']:f['sha256'] for f in before['files']};files_after={f['path']:f['sha256'] for f in after['files']}
    return dict(schema_version='temporal-contract-analysis-comparison-1',before=before,after=after,
                changed_files=[p for p in sorted(set(files_before)|set(files_after)) if files_before.get(p)!=files_after.get(p)],
                added_hints=added if comparable else [],removed_hints=removed if comparable else [],delta_status='computed' if comparable else 'not_computed_due_to_incomplete_or_different_analysis',
                interpretation='变化仅表示规则命中的语法结构变化；不是已验证的 bug 引入/修复，也不证明未变化路径安全。',
                comparable=comparable)
