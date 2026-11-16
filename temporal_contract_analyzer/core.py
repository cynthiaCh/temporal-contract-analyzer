"""Collect sources, extract syntax evidence, and compare review hints.

No benchmark/oracle imports or candidate execution.
"""
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
from .publication import publication_patterns

VERSION='0.6.10'
ROOT=Path(__file__).resolve().parents[1]
JS_EXT={'.js','.mjs','.cjs','.jsx','.ts','.tsx'}
CODE_EXT=JS_EXT|{'.py','.vue','.go','.java','.rs','.c','.h','.cpp','.cs','.rb','.php'}
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
 'Syntax facts, candidate call links and review hints are not verified contracts, bugs, severity or difficulty scores.',
 'API names are clues. Types, aliases, control flow, dynamic dispatch and callback targets are not fully resolved.',
 'Local order is lexical order within a block; branches, exceptions, loops, short-circuiting and execution remain unchecked.',
 'await may suspend; cancellation does not imply completed work or cleanup. Listener removal does not cancel work already started.',
 'if/try/finally syntax does not prove adequate protection. The absence of hints does not imply safety.',
 'No hidden scorers, reference patches, model results or human profiles are read. Operators must verify input provenance.',
]


class EvidenceError(ValueError): pass

def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def sha(raw):return hashlib.sha256(raw).hexdigest()
def normalize(value):return re.sub(r'\s+',' ',value).strip()


def collect(directory):
    root=Path(directory).expanduser()
    if not root.is_dir() or root.is_symlink():raise EvidenceError('Use a candidate source directory, not a symlink')
    root=root.resolve()
    if root.name in EXCLUDED or any(part in {'oracle','reference','references','mutants','negative-controls'} for part in root.parts):raise EvidenceError('Scorers, results, references and dependencies cannot be scan roots')
    if (root/'case.json').is_file() or (root/'case-clusters').is_dir():raise EvidenceError('Scan the candidate base/ or patched project, not the case or benchmark root')
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
            if total>MAX_TOTAL or len(sources)>=1000:raise EvidenceError('Source limit exceeded: 1,000 files / 25 MiB')
            raw=path.read_bytes()
            try:sources[rel]=raw.decode('utf-8')
            except UnicodeDecodeError:skipped.append(dict(path=rel,reason='non_utf8_source'))
    return sources,sorted(skipped,key=lambda x:(x['path'],x['reason']))


def js_analyze(sources,node=None):
    executable=node or shutil.which('node')
    if not executable:return [],dict(status='unavailable',reason='Node.js not found; npm ci --prefix temporal_contract_analyzer/javascript required for JS/TS/Vue')
    try:
        p=subprocess.run([executable,str(ROOT/'temporal_contract_analyzer/javascript/parse.cjs')],input=canonical({'files':[dict(path=p,text=t) for p,t in sorted(sources.items())]}),text=True,capture_output=True,timeout=45)
        if p.returncode:return [],dict(status='unavailable',reason='JS parser failed; run npm ci --prefix temporal_contract_analyzer/javascript',detail=p.stderr[-1500:])
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
                            'Listener registration precedes connect in the same block.' if early else 'Connect precedes listener registration in the same block.',
                            'Receiver expressions match; verify types, aliases, synchronous notifications and whether missed messages are allowed.',
                            'If registration invokes a callback synchronously, are ownership and cleanup ready?' if early else 'Should this consumer receive synchronous initial messages from connect? Statistics consumers may intentionally skip them.')
            waits=[e for e in group if e['kind']=='await']
            effects=[e for e in group if e['kind']=='call' and 'effect' in e['tags']]
            for wait in waits:
                after=next((e for e in effects if e['statement']>wait['statement']),None)
                if after:finding('effect-after-await',file,[wait,after],'An effect-like call follows await in the same block.','Lexical order only; verify effect semantics, suspension and intervening guards.','Is the owner still valid after completion? Should the effect proceed or be discarded?')
            for y in [e for e in group if e['kind']=='yield']:
                commit=next((e for e in group if e['kind']=='call' and e['callee'].endswith('.commit') and e['statement']>y['statement']),None)
                if commit:finding('commit-after-yield',file,[y,commit],'A commit-named call follows yield on normal continuation.','Verify generator/context-manager protocols and connection type; exceptional paths may not commit.','Must notifications or external effects wait for a successful commit?')
        for write in [e for e in es if e['kind']=='write' and e.get('rhs_callee') and e.get('operator')=='=']:
            nested=[e for e in calls if e['scope']==write['scope'] and e['callee']==write['rhs_callee'] and (e['line'],e['column'])>=(write['line'],write['column']) and (e['end_line'],e['end_column'])<=(write['end_line'],write['end_column'])]
            if not nested:continue
            call=nested[-1]
            relations.append(dict(kind='rhs_before_assignment',before=call['id'],after=write['id'],qualification='Assignment occurs after successful RHS evaluation; call return alone does not imply asynchronous work completion.'))
            if re.search(r'(release|cleanup|unsubscribe|dispose)',write['target'],re.I):
                finding('cleanup-handle-after-call',file,[call,write],'A cleanup-like handle is assigned after the right-hand call returns.','Check whether user callbacks can reenter the caller; reentry is not established.','If a callback switches or closes the owner, can the old return overwrite a newer cleanup handle?')
        continuations=[e for e in calls if 'continuation' in e['tags']]
        removals=[e for e in calls if e['callee'].endswith('.removeEventListener')]
        for continuation in continuations:
            removal=next((e for e in removals if file['language']!='vue' or e['scope'].split('/')[0]==continuation['scope'].split('/')[0]),None)
            if removal:
                finding('continuation-and-listener-removal',file,[continuation,removal],'Completion callback registration and listener removal coexist in this file.','Co-occurrence only; verify that both concern the same work and lifecycle.','If related, is validity checked when in-flight work completes after listener removal?')
                break
        for e in es:
            if e['kind']=='return' and any(c.startswith('AsyncFor path') for c in e['conditions']):
                finding('early-return-from-async-iteration',file,[e],'An async iteration body returns early.','Verify iterator ownership and context/caller protocols before assigning cleanup responsibility.','If this function owns the resource, does early return perform the required close?')
        for e in calls:
            if any('finally path'==c for c in e['conditions']) and ('cleanup_or_cancel' in e['tags'] or e['callee'].endswith('.pop')):
                finding('cleanup-in-finally',file,[e],'A cleanup-like call occurs in a finally path.','Exit coverage, cleanup completion and exception handling are not proven.','Does this path await required cleanup? What happens if cleanup is interrupted?')
            if e.get('import_name')=='asyncio.shield':
                finding('asyncio-shield-call',file,[e],'An import-bound candidate calls asyncio.shield.','Runtime replacement and argument ownership remain unchecked.','Does shielding separate waiter cancellation from the shared task lifecycle?')
    findings.extend(lifecycle_patterns(files))
    reentrant_findings, reentrant_relations = reentrancy_patterns(files)
    findings.extend(reentrant_findings)
    relations.extend(reentrant_relations)
    publication_findings, publication_relations = publication_patterns(files)
    findings.extend(publication_findings)
    relations.extend(publication_relations)
    for i,f in enumerate(findings):f['id']='hint-'+str(i+1)
    return findings,relations


def analyze_sources(sources,node=None,skipped=None):
    # This API also supports already-frozen candidate text. Refuse obvious evaluator paths.
    for path,text in sources.items():
        p=PurePosixPath(path)
        if p.is_absolute() or '..' in p.parts or any(x in EXCLUDED or x.startswith('.') for x in p.parts):raise EvidenceError('Disallowed input path: '+path)
        if not isinstance(text,str):raise EvidenceError('Source must be UTF-8 text')
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
    tool_files=['temporal_contract_analyzer/__init__.py','temporal_contract_analyzer/__main__.py','temporal_contract_analyzer/cli.py','temporal_contract_analyzer/core.py','temporal_contract_analyzer/lifecycle.py','temporal_contract_analyzer/reentrancy.py','temporal_contract_analyzer/publication.py','temporal_contract_analyzer/reflective.py','temporal_contract_analyzer/countdown.py','temporal_contract_analyzer/protocols.py','temporal_contract_analyzer/python_adapter.py','temporal_contract_analyzer/report.py','temporal_contract_analyzer/review.py','temporal_contract_analyzer/javascript/parse.cjs','temporal_contract_analyzer/javascript/package.json','temporal_contract_analyzer/javascript/package-lock.json']
    tool_hash=sha(canonical({p:sha((ROOT/p).read_bytes()) for p in tool_files if (ROOT/p).is_file()}).encode())
    incomplete=any(f['status']!='parsed' for f in files) or any(s['reason']!='excluded_directory' for s in skipped or [])
    report=dict(schema_version='temporal-contract-analysis-1',tool_version=VERSION,tool_sha256=tool_hash,input_sha256=sha(canonical(inputs).encode()),adapters=adapters,
                scope='candidate-source-only; no oracle, model outputs, profile labels or candidate execution',
                status='partial' if incomplete else 'parsed' if files else 'empty',inputs=inputs,skipped=skipped or [],limitations=LIMITS,files=files,call_links=links,relations=relations,findings=findings,
                summary=dict(files=len(files),parsed_files=sum(f['status']=='parsed' for f in files),events=sum(len(f['events']) for f in files),candidate_call_links=len(links),review_hints=len(findings)))
    if any(f['language']=='vue' for f in files):
        report['limitations']=LIMITS+[
            'Vue analysis covers inline <script>/<script setup> in JS/TS/JSX/TSX only. '
            'Templates, styles, custom-block transforms, generated code and runtime scheduling are excluded. '
            'Script blocks are independent; cross-block bindings and instance dispatch remain unresolved. '
            'parsed means script parsing succeeded, not component behaviour was verified.']
    return report


def scan(directory,node=None):
    sources,skipped=collect(directory);return analyze_sources(sources,node,skipped)


def compare(before,after):
    def facts(report):
        values={};events={e['id']:e for f in report['files'] for e in f['events']}
        def event_key(e):return [e['path'],e['scope'],e['kind'],normalize(e.get('callee') or e.get('target') or e.get('expression') or e['text']),e.get('operator',''),e.get('awaited',False),[normalize(c) for c in e['conditions']]]
        for f in report['findings']:
            parts=[f['rule'],f['path'],f['scope'],[event_key(events[e]) for e in f['evidence']]]
            if 'state_publication' in f:
                publication=f['state_publication']
                parts.append([publication['status'],publication.get('write_value')])
            for key in ('listener_detach', 'cache_publication'):
                if key in f:
                    parts.append([key, f[key].get('status')])
            signature=canonical(parts)
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
                interpretation='Hint changes reflect matched syntax, not verified bug introductions or fixes; unchanged paths are not proven safe.',
                comparable=comparable)
