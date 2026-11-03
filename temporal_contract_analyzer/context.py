"""Opt-in, snapshot-only source context. Never part of a frozen scan layer."""
import json
from collections import deque
from pathlib import PurePosixPath
import posixpath
import re
import shutil
import subprocess

from . import archive
from .core import EvidenceError, ROOT, canonical, sha


def build_context(report_id, store=None, finding_id=None, depth=1, max_chars=12000,
                  aliases=None, node=None):
    if type(depth) is not int or not 0 <= depth <= 5:
        raise EvidenceError('Context depth must be an integer from 0 to 5')
    if type(max_chars) is not int or not 1 <= max_chars <= 100000:
        raise EvidenceError('Context max_chars must be an integer from 1 to 100000')
    if aliases is not None and (not isinstance(aliases, dict) or any(
            not isinstance(k, str) or not k or not isinstance(v, str)
            for k, v in aliases.items())):
        raise EvidenceError('Context aliases must map nonempty prefixes to relative directories')
    aliases = aliases or {}
    for prefix, directory in aliases.items():
        if '\\' in prefix or '\\' in directory or PurePosixPath(directory).is_absolute() or '..' in PurePosixPath(directory).parts:
            raise EvidenceError('Context aliases must stay within the snapshot')
    report = json.loads(archive.artifact(report_id, 'report.json', store))
    sources = archive.read_sources(report_id, store)
    findings = [f for f in report['findings'] if finding_id is None or f['id'] == finding_id]
    if finding_id is not None and not findings:
        raise EvidenceError('Unknown finding: ' + str(finding_id))
    events = {e['id']: e for file in report['files'] for e in file['events']}
    snippets = []
    for finding in findings:
        for eid in finding['evidence']:
            event = events[eid]
            end = event['end_line'] - (event.get('end_column') == 0 and event['end_line'] > event['line'])
            snippets.append(dict(file=event['path'], start_line=event['line'], end_line=end,
                                 kind='seed', reasons=[dict(kind='finding-evidence', finding_id=finding['id'], evidence_id=eid)]))
    snippets = merge_ranges(snippets, sources)
    used = sum(len(s['code']) for s in snippets)
    if used > max_chars:
        raise EvidenceError('Seed code exceeds max_chars; select one finding or increase the context budget')
    parsed, parser_info = parse_sources(sources, node or archive.configuration().get('node')) if snippets else ({}, {'status': 'not-needed'})
    snippets, unresolved = expand(snippets, sources, parsed, depth, max_chars, aliases)
    used = sum(len(s['code']) for s in snippets)
    return dict(schema_version='temporal-context-1', report_id=report_id,
                input_sha256=report['input_sha256'], finding_ids=[f['id'] for f in findings],
                scan_status=report['status'], aliases=aliases, parser=parser_info,
                generator=dict(version=1, implementation_sha256=sha(canonical({
                    path: sha((ROOT/path).read_bytes()) for path in (
                        'temporal_contract_analyzer/context.py', 'tools/temporal-contract-analyzer/context.cjs')}).encode())),
                qualification='Incomplete syntactic context; not proven behavior, complete dependencies or a defect verdict.',
                limitations=['只补充可识别的词法引用与导入所指向的候选定义，未解析项不覆盖所有未知关系。',
                             '未建模对象成员派发、运行时重赋值、完整调用方、数据流和控制流。',
                             '仅使用归档扫描范围内的源码，不会从当前工作区读取缺失文件。',
                             '完整行和声明片段可能含有无关代码；预算只计源码字符，不含说明文字，也不是 token 限制。'],
                limits=dict(max_depth=depth, max_code_chars=max_chars), snippets=snippets,
                unresolved=unresolved,
                usage=dict(code_chars=used, snippets=len(snippets),
                           seeds=sum(s['kind']=='seed' for s in snippets),
                           definitions=sum(any(r['kind'] in {'local-definition','import-definition'} for r in s['reasons']) for s in snippets)))


def parse_sources(sources, node=None):
    executable = node or shutil.which('node')
    if not executable:
        return {}, dict(status='unavailable', reason='Node.js not found')
    try:
        process = subprocess.run([executable, str(ROOT/'tools/temporal-contract-analyzer/context.cjs')],
                                 input=canonical(dict(files=[dict(path=p, text=t) for p,t in sorted(sources.items())])),
                                 capture_output=True, text=True, timeout=45)
        if process.returncode:
            return {}, dict(status='unavailable', reason=process.stderr.strip()[:2000])
        value = json.loads(process.stdout)
        return {f['path']: f for f in value.pop('files')}, dict(value, status='available')
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        return {}, dict(status='unavailable', reason=str(error))


def resolve_module(source, module, sources, aliases):
    if module.startswith('.'):
        base = posixpath.normpath(posixpath.join(posixpath.dirname(source), module))
    else:
        prefix = next((k for k in sorted(aliases, key=lambda k: (-len(k), k)) if module==k or module.startswith(k+'/')), None)
        if prefix is None:
            return None, 'external-or-unmapped-module'
        base = posixpath.normpath(posixpath.join(aliases[prefix], module[len(prefix):].lstrip('/')))
    if base.startswith('/') or '..' in PurePosixPath(base).parts or '\\' in base:
        return None, 'outside-snapshot'
    candidates = [base] if PurePosixPath(base).suffix else [base+ext for ext in (
        '.js', '.mjs', '.cjs', '.jsx', '.ts', '.tsx', '.vue', '/index.js', '/index.mjs', '/index.ts', '/index.tsx')]
    matches = [p for p in candidates if p in sources]
    if len(matches)>1:
        return None, 'ambiguous-module'
    return (matches[0], None) if matches else (None, 'module-not-in-snapshot')


def expand(seeds, sources, parsed, depth, max_chars, aliases):
    snippets = seeds
    queue = deque((s, 0) for s in seeds)
    visited, unresolved = set(), []

    def gap(item):
        if item not in unresolved:
            unresolved.append(item)

    while queue:
        snippet, level = queue.popleft()
        key = (snippet['file'], snippet['start_line'], snippet['end_line'])
        if key in visited:
            continue
        visited.add(key)
        module = parsed.get(snippet['file'])
        if not module or module['status']!='parsed':
            gap(dict(from_file=snippet['file'], start_line=snippet['start_line'], end_line=snippet['end_line'],
                     reason=module['status'] if module else 'parser-unavailable', detail=module.get('error','') if module else ''))
            continue
        overlaps = lambda r: r['start_line']<=snippet['end_line'] and r['end_line']>=snippet['start_line']
        for item in module['gaps']:
            if overlaps(item):
                gap(dict(from_file=snippet['file'], **item))
        for ref in module['references']:
            if not overlaps(ref):
                continue
            binding = ref['binding']
            reason = dict(binding, from_file=snippet['file'], reference_line=ref['start_line'])
            target = snippet['file']
            definition = binding
            if binding['kind']=='import-definition':
                if binding['symbol']=='*':
                    gap(dict(reason, reason='namespace-import-not-supported'))
                    continue
                target, error = resolve_module(target, binding['module'], sources, aliases)
                if error:
                    gap(dict(reason, reason=error))
                    continue
                other = parsed.get(target)
                if not other or other['status']!='parsed':
                    gap(dict(reason, target_file=target, reason=other['status'] if other else 'parser-unavailable'))
                    continue
                definition = other['exports'].get(binding['symbol'])
                if not definition or 'reason' in definition or definition.get('kind')!='local-definition':
                    gap(dict(reason, target_file=target, reason=(definition or {}).get('reason','export-not-supported-or-missing')))
                    continue
            item = dict(file=target, start_line=definition['start_line'], end_line=definition['end_line'],
                        kind='definition', reasons=[reason])
            covered = next((s for s in snippets if s['file']==target and s['start_line']<=item['start_line'] and s['end_line']>=item['end_line']), None)
            if covered:
                if reason not in covered['reasons']:
                    covered['reasons'].append(reason)
                continue
            if level>=depth:
                gap(dict(reason, target_file=target, reason='depth-limit'))
                continue
            proposed = merge_ranges(snippets+[item], sources)
            if sum(len(s['code']) for s in proposed)>max_chars:
                gap(dict(reason, target_file=target, reason='budget-limit'))
                continue
            snippets = proposed
            item['code'] = ''.join(sources[target].splitlines(keepends=True)[item['start_line']-1:item['end_line']])
            queue.append((item, level+1))
    return snippets, unresolved


def markdown(packet):
    metadata = {k:packet[k] for k in ('schema_version','report_id','input_sha256','scan_status',
                                     'finding_ids','generator','parser','aliases','limits','usage')}
    def fenced(text, language=''):
        fence = '`'*max(3, max((len(part) for part in re.findall(r'`+', text)), default=0)+1)
        return [fence+language, text.rstrip('\r\n'), fence, '']
    lines = ['# 分析线索与源码上下文', '',
             '报告：'+packet['report_id'], '', packet['qualification'], '',
             '仅使用归档源码快照；补充定义不证明实际调用、完整依赖或缺陷成立。', '',
             '代码字符数：'+str(packet['usage']['code_chars'])+'；最大展开深度：'+str(packet['limits']['max_depth']), '',
             '## 来源与生成参数', '', *fenced(json.dumps(metadata, ensure_ascii=False, indent=2), 'json')]
    for item in packet['snippets']:
        lines += ['## '+item['file']+':'+str(item['start_line'])+'–'+str(item['end_line'])+' · '+item['kind'], '',
                  '补充依据：'+json.dumps(item['reasons'], ensure_ascii=False), '']
        lines += fenced(item['code'])
    if not packet['snippets']:
        lines += ['没有选中的分析线索；不会自动进行全仓库检索，也不代表程序安全。', '']
    lines += ['## 未解析项', '', *fenced(json.dumps(packet['unresolved'], ensure_ascii=False, indent=2), 'json'),
              '## 范围限制', '', *['- '+s for s in packet['limitations']], '']
    return '\n'.join(lines)


def merge_ranges(items, sources):
    merged = []
    for item in sorted(items, key=lambda s: (s['file'], s['start_line'], s['end_line'])):
        item = dict(item, reasons=list(item['reasons']))
        if merged and merged[-1]['file'] == item['file'] and item['start_line'] <= merged[-1]['end_line'] + 1:
            previous = merged[-1]
            previous['end_line'] = max(previous['end_line'], item['end_line'])
            if item['kind'] == 'seed':
                previous['kind'] = 'seed'
            for reason in item['reasons']:
                if reason not in previous['reasons']:
                    previous['reasons'].append(reason)
        else:
            merged.append(item)
    for item in merged:
        item['code'] = ''.join(sources[item['file']].splitlines(keepends=True)[item['start_line']-1:item['end_line']])
    return merged
