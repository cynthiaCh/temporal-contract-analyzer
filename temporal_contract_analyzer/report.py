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
        lines=['# TempoEvo · 时序源码证据：修改前后对照','',report['interpretation'],'','对照状态：'+report['delta_status'],'',
               '同工具/解析器且两侧均解析完整：'+str(report['comparable']),'',
               '变化文件：'+', '.join(report['changed_files']),'',
               '新增提示：'+', '.join(x['rule']+' · '+x['path'] for x in report['added_hints']),
               '消失提示：'+', '.join(x['rule']+' · '+x['path'] for x in report['removed_hints']),'',
               '## 修改前','',markdown(report['before'], view=view),'','## 修改后','',markdown(report['after'], view=view)]
        return '\n'.join(lines)
    events={e['id']:e for f in report['files'] for e in f['events']}
    lines=['# TempoEvo · 时序源码证据索引','',
           '**工具生成的待核查线索，不是 Oracle、缺陷结论或难度分。**','',
           '状态：`'+report['status']+'`；工具版本：`'+report['tool_version']+'`。',
           '输入摘要：`'+report['input_sha256']+'`。',
           '工具摘要：`'+report['tool_sha256']+'`。','',
           '## 范围与限制','']+['- '+x for x in report['limitations']]
    lines+=['','## 文件与解析覆盖','', '| 文件 | 状态 | SHA-256 |','|---|---|---|']
    for f in report['files']:lines.append('| '+f['path'].replace('|','\\|')+' | '+f['status']+' | '+f['sha256']+' |')
    for f in report['files']:
        if f.get('analysis_scope'):lines.append('- `'+f['path']+'` 分析范围：'+f['analysis_scope'])
        if f.get('error'):lines.append('- `'+f['path']+'` 解析说明：'+str(f['error'].get('message','')).replace('\n',' '))
    for s in report['skipped']:lines.append('- 排除/未读：`'+s['path']+'` · '+s['reason'])
    lines+=['','## 待核查模式','']
    if not report['findings']:lines.append('没有模式命中；不表示安全。请查看解析覆盖与未建模调用。')
    for finding in report['findings']:
        lines+=['### '+finding['id']+' · '+finding['rule'],'',finding['message'],'','成立条件/限制：'+finding['condition'],'','待核查：'+finding['review_question'],'']
        for eid in finding['evidence']:
            e=events[eid];lines+=['`'+e['path']+':'+str(e['line'])+'` · '+e['scope'],'','```text',e['text'].replace('```','` ` `'),'```','']
    lines+=['## 候选直接调用关系','', '只列可定位的词法/导入绑定，不等于完整调用图。对象方法、动态绑定和回调实参目标可能未解析。','']
    for link in report['call_links']:
        e=events[link['call']];lines.append('- `'+e['path']+':'+str(e['line'])+'` '+e['callee']+' → `'+link['target']+'`')
    lines+=['','## 保护与边界位置（存在不等于充分）','']
    for file in report['files']:
        for e in file['events']:
            if e['kind'] in {'guard','await','yield','resource_scope'} or 'cleanup_or_cancel' in e['tags']:
                lines.append('- `'+e['path']+':'+str(e['line'])+'` · '+e['kind']+' · `'+e['text'].splitlines()[0].replace('`','\u2032')+'`')
    lines+=['','## 解析器','', '```json',json.dumps(report['adapters'],ensure_ascii=False,indent=2),'```','']
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
            hints.append('<details open><summary>'+esc(f['rule'])+' · '+esc(f['path'])+'</summary><p>'+esc(f['message'])+'</p><p class="muted">条件：'+esc(f['condition'])+'</p><p><strong>核查问题：</strong>'+esc(f['review_question'])+'</p>'+snippets+'</details>')
        files=''.join('<tr><td>'+esc(f['path'])+'</td><td>'+esc(f['status'])+
                      ('<br>'+esc(f['analysis_scope']) if f.get('analysis_scope') else '')+
                      ('<br>'+esc(f['error'].get('message','')) if f.get('error') else '')+
                      '</td><td><code>'+esc(f['sha256'][:16])+'</code></td></tr>' for f in r['files'])
        links=''.join('<li><code>'+esc(es[l['call']]['path'])+':'+str(es[l['call']]['line'])+'</code> → <code>'+esc(l['target'])+'</code></li>' for l in r['call_links'])
        events=''.join('<details><summary>'+esc(f['path'])+' · '+str(len(f['events']))+' 个语法事件</summary>'+''.join('<p><code>L'+str(e['line'])+' '+esc(e['kind'])+'</code> · '+esc(', '.join(e['tags']))+'</p><pre>'+esc(e['text'])+'</pre>' for e in f['events'])+'</details>' for f in r['files'])
        skipped=''.join('<li>'+esc(s['path'])+' · '+esc(s['reason'])+'</li>' for s in r['skipped'])
        return '<p>解析状态：<strong>'+esc(r['status'])+'</strong> · '+str(r['summary']['parsed_files'])+'/'+str(r['summary']['files'])+' 个文件解析成功</p><p class="digest">输入 SHA-256：'+esc(r['input_sha256'])+'<br>工具 SHA-256：'+esc(r['tool_sha256'])+'</p><details><summary>分析范围与限制</summary><ul>'+''.join('<li>'+esc(x)+'</li>' for x in r['limitations'])+'</ul><pre>'+esc(json.dumps(r['adapters'],ensure_ascii=False,indent=2))+'</pre></details><h2>文件覆盖</h2><table><tr><th>文件</th><th>状态</th><th>摘要前缀</th></tr>'+files+'</table><ul>'+skipped+'</ul><h2>待核查线索</h2>'+(''.join(hints) or '<p>无模式命中，不表示安全。</p>')+'<h2>候选直接调用关系</h2><p>未解析的动态调用保持未知；不要把这些关系当作完整执行路径。</p><ul>'+links+'</ul><h2>全部语法事件</h2>'+events
    if view == 'focused':
        content = _focused_html(report)
    elif report['schema_version']=='temporal-contract-analysis-comparison-1':
        content='<p>对照状态：'+esc(report['delta_status'])+'</p><p>'+esc(report['interpretation'])+'</p><p>可比解析：'+esc(report['comparable'])+'</p><p>新增模式：'+esc(', '.join(x['rule'] for x in report['added_hints']))+'</p><p>消失模式：'+esc(', '.join(x['rule'] for x in report['removed_hints']))+'</p><h2>修改前</h2>'+card(report['before'])+'<h2>修改后</h2>'+card(report['after'])
    else:content=card(report)
    return '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'"><title>TempoEvo · 时序源码证据索引</title><style>body{margin:0;background:#f7f8f3;color:#20372c;font:15px/1.8 system-ui,sans-serif}main{max-width:1000px;margin:auto;padding:36px 22px}h1{font-size:30px}h2{margin-top:36px;font-size:22px}details{padding:18px;margin:16px 0;background:white;border:1px solid #d8dfd3}summary{cursor:pointer;font-weight:600;overflow-wrap:anywhere}pre{padding:16px;background:#f0f3ed;white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px}code{overflow-wrap:anywhere;font-size:12px}.muted,.digest{color:#5d6e61}.digest{overflow-wrap:anywhere;font-size:11px}table{border-collapse:collapse;width:100%;font-size:12px}td,th{border-bottom:1px solid #d8dfd3;text-align:left;padding:10px;overflow-wrap:anywhere}.notice{border-left:4px solid #8e7139;padding:12px 18px;background:#faf1df}</style><main><h1>TempoEvo · 时序源码证据索引</h1><p class="notice">确定性语法分析 · 工具线索需复核 · 不执行候选代码 · 不提供缺陷或难度评分</p>'+content+'</main></html>'
