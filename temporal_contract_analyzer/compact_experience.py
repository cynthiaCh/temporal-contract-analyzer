"""Single-file experience content and inline acceptance, without audit sidecars."""
from html import escape
import json
import os
from pathlib import Path
import tempfile

from . import experience_memory as memory, taxonomy
from .core import EvidenceError, canonical, sha
from . import archive

VERSION = 'experience-library-single-file-v1'
SECTIONS = [('applicability', '适用条件'), ('event_relation', '建议'),
            ('preservation', '需要保留'), ('exclusion', '不适用情况'),
            ('verification', '检查方法')]
STATES = {'pending': '待审核', 'accept': '已接受', 'revise': '需修改', 'reject': '已拒绝'}


def review_for(value, item):
    return item.get('review', value.get('review')) or dict(reviewer=None, decision='pending', at=None)


def validate_review(review):
    memory.object_fields(review, {'reviewer', 'decision', 'at'}, 'inline review')
    if review['decision'] not in STATES:
        raise EvidenceError('Invalid inline review')
    if review['decision']=='pending':
        if review['reviewer'] is not None or review['at'] is not None:
            raise EvidenceError('Pending experience must not claim a reviewer or review time')
    elif not memory.text(review['reviewer']) or not memory.text(review['at']):
        raise EvidenceError('A completed review requires reviewer and time')


def load(path):
    value = json.loads(Path(path).read_text(encoding='utf-8'))
    required = {'schema_version', 'experiences'}
    if isinstance(value, dict) and 'review' in value:
        required.add('review')
    memory.object_fields(value, required, 'experience file')
    if value['schema_version'] != VERSION:
        raise EvidenceError('Unknown single-file experience format')
    if 'review' in value:
        validate_review(value['review'])
    if not isinstance(value['experiences'], list) or not value['experiences']:
        raise EvidenceError('Experience list must not be empty')
    ids = set()
    for item in value['experiences']:
        fields = {'id', 'title', 'labels', 'requires', 'excludes'} | {key for key, _ in SECTIONS}
        if isinstance(item, dict) and 'review' in item:
            fields.add('review')
        memory.object_fields(item, fields, 'experience')
        if not memory.text(item['id']) or item['id'] in ids or not memory.text(item['title']) \
                or any(not memory.text(item[key]) for key, _ in SECTIONS):
            raise EvidenceError('Invalid or duplicate experience')
        ids.add(item['id'])
        validate_review(review_for(value, item))
    return value


def materialize(path):
    """Adapt the single source of truth to existing retrieval objects in memory only."""
    value = load(path)
    bundles, decisions, blobs = [], [], {}
    for index, item in enumerate(value['experiences'], 1):
        raw = canonical({k:v for k,v in item.items() if k!='review'}).encode('utf-8')
        code = sha(raw)
        blobs[code] = raw
        bundle = memory.seal(dict(schema_version=memory.BUNDLE_VERSION_V2,
            id=item['id'], version='single-file-v1', parent_sha256=None,
            taxonomy_version=taxonomy.VERSION, labels=item['labels'],
            requires=item['requires'], excludes=item['excludes'],
            rules=[dict(id=f'R{i:02d}', category=key, body=item[key])
                   for i, (key, _) in enumerate(SECTIONS, 1)],
            review=dict(status='candidate', kind='ai_assisted', source_sha256=code,
                        limitations=['Content acceptance does not establish cross-task effectiveness.']),
            audit=dict(sources=[dict(path=Path(path).name, sha256=code)],
                       rule_links=[], notes=[], outcome_refs=[])))
        memory.validate(bundle, blobs.__getitem__)
        bundles.append(bundle)
        review = review_for(value, item)
        if review['decision']=='pending':
            continue
        row = dict(review, reason='', scope='research', actor='named_operator',
                   schema_version='experience-expert-decision-v1',
                   candidate_sha256=bundle['sha256'], report_sha256=None, sequence=index,
                   rules=[dict(rule_id=r['id'], supported=review['decision']=='accept', reason='')
                          for r in bundle['rules']])
        row['sha256'] = memory.digest(canonical(row))
        decisions.append(row)
    return bundles, decisions, blobs


def save_review(path, request):
    """Caller serializes writes; only the selected item's review is changed."""
    memory.object_fields(request, {'id', 'expected_record', 'expected_review', 'reviewer', 'decision'}, 'review request')
    if not memory.text(request['reviewer']) or request['decision'] not in ('accept', 'revise', 'reject'):
        raise EvidenceError('请填写审核人并选择审核结论')
    value = load(path)
    bundles = materialize(path)[0]
    item = next((item for item in value['experiences'] if item['id']==request['id']), None)
    bundle = next((b for b in bundles if b['id']==request['id']), None)
    if item is None:
        raise EvidenceError('Experience not found')
    if bundle['sha256']!=request['expected_record'] or review_for(value, item)!=request['expected_review']:
        raise EvidenceError('经验或审核状态已变化，请刷新后重新审核')
    # Move existing whole-file acceptance onto its existing items before saving.
    if 'review' in value:
        for entry in value['experiences']:
            entry.setdefault('review', dict(value['review']))
        del value['review']
    item['review'] = dict(reviewer=request['reviewer'].strip(), decision=request['decision'], at=archive.now())
    # Preserve JSON field order so a review update does not reformat every entry.
    descriptor, temporary = tempfile.mkstemp(prefix='.write-', dir=Path(path).parent)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return dict(review=item['review'], record_sha256=bundle['sha256'])


def page(path):
    value = load(path)
    bundles = {b['id']:b for b in materialize(path)[0]}
    cards = []
    for item in value['experiences']:
        review = review_for(value, item)
        state = review['decision']
        status = STATES[state]
        saved = status if state=='pending' else f'{status} · {review["reviewer"]} · {review["at"]}'
        sections = ''.join(f'<dt>{label}</dt><dd>{escape(item[key])}</dd>'
                           for key, label in SECTIONS)
        cards.append(f'<article class="panel" data-state="{state}"><h2>{escape(item["title"])}</h2>'
                     f'<p class="compact-status">{escape(saved)}</p><dl>{sections}</dl>'
                     f'<form data-id="{escape(item["id"], quote=True)}" '
                     f'data-record="{bundles[item["id"]]["sha256"]}" '
                     f'data-review="{escape(canonical(review), quote=True)}">'
                     '<label>审核人<input name="reviewer" required '
                     f'value="{escape(review["reviewer"] or "", quote=True)}"></label>'
                     '<label>审核结论<select name="decision" required><option value="">请选择</option>'
                     '<option value="accept">接受</option><option value="revise">需修改</option>'
                     '<option value="reject">拒绝</option></select></label>'
                     '<button type="submit">保存审核</button></form></article>')
    html = ('<!doctype html><html lang="zh-CN"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>经验审核</title><link rel="stylesheet" href="/memory-review.css">'
            '<script src="/compact-review.js" defer></script><body class="compact-review"><main><section>'
            f'<h1>经验库 · {len(cards)} 条</h1><p id="compact-counts"></p>'
            f'<p>经验均保存在这个文件中，可直接编辑：<code>{escape(str(path))}</code></p>'
            '<p>阅读经验及适用边界后填写审核结论。结果写回同一文件，不生成独立审核文件。</p>'
            '<label>显示<select id="compact-filter"><option value="all">全部经验</option>'
            '<option value="pending">待审核</option><option value="accept">已接受</option>'
            '<option value="revise">需修改</option><option value="reject">已拒绝</option></select></label>'
            '<p id="compact-empty" hidden>此分类下没有经验。</p>'
            + ''.join(cards) + '</section></main><p id="message" role="status" aria-live="polite"></p></body></html>')
    return html.encode('utf-8')
