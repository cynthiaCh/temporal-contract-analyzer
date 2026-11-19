"""Standalone human-readable evidence, rendered without executing source text."""
import html
import json


def markdown(report, view="focused"):
    if view not in {"focused", "exploratory"}:
        raise ValueError("Unknown report view: " + view)
    if view == "focused":
        from .review import focused_markdown
        return focused_markdown(report)
    if report['schema_version']=='temporal-contract-analysis-comparison-1':
        lines=['# TempoEvo · Temporal source evidence: before and after','',report['interpretation'],'','Comparison status: '+report['delta_status'],'',
               'Same tool/parser and complete parsing on both sides: '+str(report['comparable']),'',
               'Changed files: '+', '.join(report['changed_files']),'',
               'Added hints: '+', '.join(x['rule']+' · '+x['path'] for x in report['added_hints']),
               'Removed hints: '+', '.join(x['rule']+' · '+x['path'] for x in report['removed_hints']),'',
               '## Before','',markdown(report['before'], view=view),'','## After','',markdown(report['after'], view=view)]
        return '\n'.join(lines)
    events={e['id']:e for f in report['files'] for e in f['events']}
    lines=['# TempoEvo · Temporal source evidence index','',
           '**Tool-generated review hints; not an oracle, defect verdict or difficulty score.**','',
           'Status: `'+report['status']+'`; tool version: `'+report['tool_version']+'`.',
           'Input digest: `'+report['input_sha256']+'`.',
           'Tool digest: `'+report['tool_sha256']+'`.','',
           '## Scope and limitations','']+['- '+x for x in report['limitations']]
    lines+=['','## Files and parsing coverage','', '| File | Status | SHA-256 |','|---|---|---|']
    for f in report['files']:lines.append('| '+f['path'].replace('|','\\|')+' | '+f['status']+' | '+f['sha256']+' |')
    for f in report['files']:
        if f.get('analysis_scope'):lines.append('- `'+f['path']+'` Analysis scope: '+f['analysis_scope'])
        if f.get('error'):lines.append('- `'+f['path']+'` Parsing note: '+str(f['error'].get('message','')).replace('\n',' '))
    for s in report['skipped']:lines.append('- Excluded/unread: `'+s['path']+'` · '+s['reason'])
    lines+=['','## Patterns to review','']
    if not report['findings']:lines.append('No pattern matched; safety is not established. Check parsing coverage and unmodeled calls.')
    for finding in report['findings']:
        lines+=['### '+finding['id']+' · '+finding['rule'],'',finding['message'],'','Conditions/limitations: '+finding['condition'],'','Review needed: '+finding['review_question'],'']
        for eid in finding['evidence']:
            e=events[eid];lines+=['`'+e['path']+':'+str(e['line'])+'` · '+e['scope'],'','```text',e['text'].replace('```','` ` `'),'```','']
    lines+=['## Candidate direct call links','', 'Only located lexical/import bindings are listed, not a complete call graph. Object methods, dynamic bindings and callback argument targets may remain unresolved.','']
    for link in report['call_links']:
        e=events[link['call']];lines.append('- `'+e['path']+':'+str(e['line'])+'` '+e['callee']+' → `'+link['target']+'`')
    lines+=['','## Guards and boundary locations (presence does not establish sufficiency)','']
    for file in report['files']:
        for e in file['events']:
            if e['kind'] in {'guard','await','yield','resource_scope'} or 'cleanup_or_cancel' in e['tags']:
                lines.append('- `'+e['path']+':'+str(e['line'])+'` · '+e['kind']+' · `'+e['text'].splitlines()[0].replace('`','\u2032')+'`')
    lines+=['','## Parsers','', '```json',json.dumps(report['adapters'],ensure_ascii=False,indent=2),'```','']
    return '\n'.join(lines)


def _focused_html(report):
    # Render only the generated structure; source lines are always escaped.
    parts = []
    in_code = False
    for line in markdown(report).splitlines():
        if line in {'```text', '```'}:
            parts.append('</pre>' if in_code else '<pre>')
            in_code = not in_code
        elif in_code:
            parts.append(html.escape(line, quote=True) + '\n')
        elif line.startswith('# '):
            parts.append('<h2>' + html.escape(line[2:], quote=True) + '</h2>')
        elif line.startswith('## '):
            parts.append('<h3>' + html.escape(line[3:], quote=True) + '</h3>')
        elif line:
            parts.append('<p>' + html.escape(line, quote=True) + '</p>')
    return ''.join(parts)


def html_report(report, view="focused"):
    if view not in {"focused", "exploratory"}:
        raise ValueError("Unknown report view: " + view)
    esc=lambda s:html.escape(str(s),quote=True)
    def card(r):
        es={e['id']:e for f in r['files'] for e in f['events']}
        hints=[]
        for f in r['findings']:
            snippets=''.join('<p><code>'+esc(es[x]['path'])+':'+str(es[x]['line'])+'</code> · '+esc(es[x]['scope'])+'</p><pre>'+esc(es[x]['text'])+'</pre>' for x in f['evidence'])
            hints.append('<details open><summary>'+esc(f['rule'])+' · '+esc(f['path'])+'</summary><p>'+esc(f['message'])+'</p><p class="muted">Condition: '+esc(f['condition'])+'</p><p><strong>Review question: </strong>'+esc(f['review_question'])+'</p>'+snippets+'</details>')
        files=''.join('<tr><td>'+esc(f['path'])+'</td><td>'+esc(f['status'])+
                      ('<br>'+esc(f['analysis_scope']) if f.get('analysis_scope') else '')+
                      ('<br>'+esc(f['error'].get('message','')) if f.get('error') else '')+
                      '</td><td><code>'+esc(f['sha256'][:16])+'</code></td></tr>' for f in r['files'])
        links=''.join('<li><code>'+esc(es[l['call']]['path'])+':'+str(es[l['call']]['line'])+'</code> → <code>'+esc(l['target'])+'</code></li>' for l in r['call_links'])
        events=''.join('<details><summary>'+esc(f['path'])+' · '+str(len(f['events']))+' syntax events</summary>'+''.join('<p><code>L'+str(e['line'])+' '+esc(e['kind'])+'</code> · '+esc(', '.join(e['tags']))+'</p><pre>'+esc(e['text'])+'</pre>' for e in f['events'])+'</details>' for f in r['files'])
        skipped=''.join('<li>'+esc(s['path'])+' · '+esc(s['reason'])+'</li>' for s in r['skipped'])
        return '<p>Parsing status: <strong>'+esc(r['status'])+'</strong> · '+str(r['summary']['parsed_files'])+'/'+str(r['summary']['files'])+' files parsed successfully</p><p class="digest">Input SHA-256: '+esc(r['input_sha256'])+'<br>Tool SHA-256: '+esc(r['tool_sha256'])+'</p><details><summary>Analysis scope and limitations</summary><ul>'+''.join('<li>'+esc(x)+'</li>' for x in r['limitations'])+'</ul><pre>'+esc(json.dumps(r['adapters'],ensure_ascii=False,indent=2))+'</pre></details><h2>File coverage</h2><table><tr><th>File</th><th>Status</th><th>Digest prefix</th></tr>'+files+'</table><ul>'+skipped+'</ul><h2>Review hints</h2>'+(''.join(hints) or '<p>No pattern matched; safety is not established.</p>')+'<h2>Candidate direct call links</h2><p>Unresolved dynamic calls remain unknown; these links are not complete execution paths.</p><ul>'+links+'</ul><h2>All syntax events</h2>'+events
    if view == 'focused':
        content = _focused_html(report)
    elif report['schema_version']=='temporal-contract-analysis-comparison-1':
        content='<p>Comparison status: '+esc(report['delta_status'])+'</p><p>'+esc(report['interpretation'])+'</p><p>Comparable parsing: '+esc(report['comparable'])+'</p><p>Added patterns: '+esc(', '.join(x['rule'] for x in report['added_hints']))+'</p><p>Removed patterns: '+esc(', '.join(x['rule'] for x in report['removed_hints']))+'</p><h2>Before</h2>'+card(report['before'])+'<h2>After</h2>'+card(report['after'])
    else:content=card(report)
    return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'"><title>TempoEvo · Temporal source evidence index</title><style>body{margin:0;background:#f7f8f3;color:#20372c;font:15px/1.8 system-ui,sans-serif}main{max-width:1000px;margin:auto;padding:36px 22px}h1{font-size:30px}h2{margin-top:36px;font-size:22px}details{padding:18px;margin:16px 0;background:white;border:1px solid #d8dfd3}summary{cursor:pointer;font-weight:600;overflow-wrap:anywhere}pre{padding:16px;background:#f0f3ed;white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px}code{overflow-wrap:anywhere;font-size:12px}.muted,.digest{color:#5d6e61}.digest{overflow-wrap:anywhere;font-size:11px}table{border-collapse:collapse;width:100%;font-size:12px}td,th{border-bottom:1px solid #d8dfd3;text-align:left;padding:10px;overflow-wrap:anywhere}.notice{border-left:4px solid #8e7139;padding:12px 18px;background:#faf1df}</style><main><h1>TempoEvo · Temporal source evidence index</h1><p class="notice">Deterministic syntax analysis · Review tool hints · No candidate code execution · No defect or difficulty scores</p>'+content+'</main></html>'
