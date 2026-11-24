"""Read-only temporal guidance packs for everyday agents, not experiment snapshots."""
import json
import os
from pathlib import Path

from .core import EvidenceError
from .personal_memory import terms

VERSION = 'tempoevo-general-experience-v1'
SECTIONS = ('applicability', 'event_relation', 'preservation', 'exclusion', 'verification')
DEFAULT_PACK = Path(__file__).parent/'data'/'temporal-experience.json'


def export_pack(store, version):
    """Copy current accepted guidance/Abstracts verbatim, omitting research traces."""
    from . import compact_experience as compact, experience_approval as approval
    if not version.strip():
        raise EvidenceError('A readable guidance pack version is required')
    approved = {entry['bundle']['id'] for entry in approval.approved(store)}
    summaries = compact.reviewed_summaries(store)
    entries = []
    for _, document in compact.documents(store):
        for item in document['experiences']:
            if item['id'] not in approved:
                continue
            if item['id'] not in summaries:
                raise EvidenceError('Current accepted Abstract required for '+item['id'])
            review = compact.review_for(document, item)
            entries.append(dict(experience_id=item['id'], title=item['title'],
                                summary=summaries[item['id']]['text'], labels=item['labels'],
                                requires=item['requires'], excludes=item['excludes'],
                                reviewed_by=review['reviewer'], reviewed_at=review['at'],
                                **{key: item[key] for key in SECTIONS}))
    return dict(schema_version=VERSION, version=version, domain='temporal_contracts',
                entries=sorted(entries, key=lambda row: row['experience_id']))


class GeneralMemory:
    def __init__(self, pack=None):
        self.path = Path(pack or os.environ.get('TCA_GENERAL_MEMORY') or DEFAULT_PACK).expanduser().resolve()

    def recall(self, query):
        value = json.loads(self.path.read_text(encoding='utf-8'))
        if (not isinstance(value, dict) or value.get('schema_version') != VERSION
                or value.get('domain') != 'temporal_contracts'
                or not isinstance(value.get('version'), str) or not value['version'].strip()
                or not isinstance(value.get('entries'), list)):
            raise EvidenceError('Invalid general experience pack')
        needles = terms(query)
        matches, seen = [], set()
        for entry in value['entries']:
            if not isinstance(entry, dict):
                raise EvidenceError('Invalid general experience entry')
            for key in ('experience_id', 'title', 'summary', 'reviewed_by', 'reviewed_at')+SECTIONS:
                if not isinstance(entry.get(key), str) or not entry[key].strip():
                    raise EvidenceError('Incomplete general experience entry: '+key)
            for key in ('labels', 'requires', 'excludes'):
                if not isinstance(entry.get(key), list) or any(not isinstance(x, str) for x in entry[key]):
                    raise EvidenceError('Invalid general experience '+key)
            code = entry['experience_id']
            if code in seen:
                raise EvidenceError('Duplicate general experience ID')
            seen.add(code)
            text = ' '.join(entry[key] for key in ('title', 'summary')+SECTIONS)
            score = len(needles & terms(text))
            if needles and not score:
                continue
            matches.append(dict(entry, source='general', scope='applicability_conditions',
                                domain=value['domain'], version=value['version'], read_only=True, score=score))
        matches.sort(key=lambda row: (-row['score'], row['experience_id']))
        return dict(items=matches, version=value['version'], bank_count=len(seen))


def recall_combined(personal, general, project, query, limit=5, offset=0, source='all'):
    """Interleave candidates so neither source monopolizes the first page."""
    if source not in ('all', 'personal', 'general'):
        raise EvidenceError('Unknown experience source')
    # Personal recall also validates/canonicalizes the current project path.
    own = personal.recall(project, query, limit=None) if source != 'general' else None
    if own is None:
        from .personal_memory import project_path
        project_path(project)
        personal_items = []
    else:
        personal_items = own['items']
    shared = general.recall(query) if source != 'personal' else dict(items=[], version=None, bank_count=0)
    pools = [personal_items, shared['items']]
    items = []
    for index in range(max(map(len, pools))):
        for pool in pools:
            if index < len(pool):
                items.append(pool[index])
    return dict(items=items[offset:offset+limit], total=len(items),
                next_offset=offset+limit if offset+limit < len(items) else None,
                sources=dict(personal=dict(matches=len(personal_items)),
                             general=dict(matches=len(shared['items']), bank_count=shared['bank_count'],
                                          version=shared['version'])),
                selection_guidance='Candidates only. Read full applicability and exclusions against current task/source; '
                    'select at most 3 useful nonredundant entries and allow no match. Current explicit requirements take '
                    'precedence; project corrections specialize general advice only within their stated scope. '
                    'Do not guess unresolved business conflicts or treat lexical relevance as applicability. '
                    'General guidance is read-only; record corrections in personal memory.',
                qualification='Everyday recall is not the frozen experimental retrieval protocol or evidence of memory use.')
