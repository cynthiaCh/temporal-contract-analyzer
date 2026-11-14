"""Local research experience memory. No model or experiment execution path."""
import json
from collections import Counter
import math
from pathlib import Path
import re

from .core import EvidenceError, canonical, sha
from . import taxonomy

STORE_VERSION = 'research-experience-memory-v1'
BUNDLE_VERSION = 'experience-bundle-v1'
BUNDLE_VERSION_V2 = 'experience-bundle-v2'
LEGACY_TAXONOMY = 'legacy-toolflow-t1-t4-v1'
CATEGORIES = {'applicability': 'Applicability', 'event_relation': 'Event relation',
              'preservation': 'Preservation', 'exclusion': 'Exclusion', 'verification': 'Verification'}
FIELDS = {'schema_version', 'id', 'version', 'parent_sha256', 'taxonomy_version',
          'labels', 'requires', 'excludes', 'rules', 'review', 'audit'}


def digest(value):
    return sha(value.encode('utf-8'))


def text(value):
    return isinstance(value, str) and bool(value.strip())


def object_fields(value, fields, name):
    if not isinstance(value, dict) or set(value) != set(fields):
        raise EvidenceError('Invalid fields: '+name)


def strings(value, name, allowed=None, nonempty=False):
    if not isinstance(value, list) or (nonempty and not value) or any(not text(v) for v in value) \
            or len(set(value)) != len(value) or (allowed is not None and any(v not in allowed for v in value)):
        raise EvidenceError('Invalid strings: '+name)


def render(bundle):
    """Deterministic repair text, without source paths, evidence IDs or scores."""
    return '\n\n'.join(f"{rule['id']} [{CATEGORIES[rule['category']]}]\n{rule['body']}"
                       for rule in bundle['rules'])+'\n'


def seal(payload):
    """Derive digests for a new unsealed payload; never repairs an existing digest."""
    object_fields(payload, FIELDS, 'unsealed bundle')
    try:
        body = render(payload)
    except (KeyError, TypeError) as error:
        raise EvidenceError('Malformed rule list; refusing to render') from error
    result = dict(payload, body_sha256=digest(body))
    result['sha256'] = digest(canonical(result))
    return result


def json_pointer(raw, pointer):
    if pointer == '':
        return raw
    if not isinstance(pointer, str) or not pointer.startswith('/'):
        raise EvidenceError('Invalid evidence JSON pointer')
    try:
        value = json.loads(raw)
        for token in pointer.split('/')[1:]:
            token = token.replace('~1', '/').replace('~0', '~')
            if isinstance(value, list):
                if not token.isdigit():
                    raise ValueError('Non-index token')
                value = value[int(token)]
            else:
                value = value[token]
        return value
    except (ValueError, KeyError, TypeError, IndexError) as error:
        raise EvidenceError('Evidence pointer does not resolve: '+pointer) from error


def _validate(bundle, blobs):
    object_fields(bundle, FIELDS | {'body_sha256', 'sha256'}, 'bundle')
    if bundle['schema_version'] not in (BUNDLE_VERSION, BUNDLE_VERSION_V2):
        raise EvidenceError('Wrong experience schema version')
    for field in ('id', 'version'):
        if not isinstance(bundle[field], str) or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9._-]{0,159}', bundle[field]):
            raise EvidenceError('Invalid experience '+field)
    if bundle['parent_sha256'] is not None and (not isinstance(bundle['parent_sha256'], str)
            or not re.fullmatch('[a-f0-9]{64}', bundle['parent_sha256'])):
        raise EvidenceError('Invalid parent digest')
    namespace = bundle['taxonomy_version']
    if namespace not in (taxonomy.VERSION, LEGACY_TAXONOMY):
        raise EvidenceError('Unsupported taxonomy; explicit recoding is required')
    strings(bundle['labels'], 'labels', taxonomy.CODES if namespace == taxonomy.VERSION
            else ('T1', 'T2', 'T3', 'T4'), nonempty=True)
    predicates = taxonomy.definition()['mechanism_predicates']
    for field in ('requires', 'excludes'):
        strings(bundle[field], field, predicates, nonempty=field == 'requires')
    if set(bundle['requires']) & set(bundle['excludes']):
        raise EvidenceError('Conflicting applicability predicates')
    if not isinstance(bundle['rules'], list) or not bundle['rules']:
        raise EvidenceError('Missing rules')
    categories = set()
    for index, rule in enumerate(bundle['rules'], 1):
        object_fields(rule, {'id', 'category', 'body'}, 'rule')
        if rule['id'] != f'R{index:02d}' or not isinstance(rule['category'], str) \
                or rule['category'] not in CATEGORIES or not text(rule['body']):
            raise EvidenceError('Invalid rule number, category or body')
        categories.add(rule['category'])
    if bundle['schema_version'] == BUNDLE_VERSION and categories != set(CATEGORIES):
        raise EvidenceError('Bundle must retain applicability, relations, preservation, exclusions and verification')
    review = bundle['review']
    object_fields(review, {'status', 'kind', 'source_sha256', 'limitations'}, 'review')
    if review['status'] not in ('candidate', 'research_admitted', 'rejected') \
            or review['kind'] not in ('ai_assisted_historical', 'ai_assisted', 'human', 'synthetic'):
        raise EvidenceError('Invalid review status or kind')
    strings(review['limitations'], 'review limitations')
    audit = bundle['audit']
    object_fields(audit, {'sources', 'rule_links', 'notes', 'outcome_refs'}, 'audit')
    strings(audit['notes'], 'audit notes')
    if not isinstance(audit['sources'], list) or not audit['sources']:
        raise EvidenceError('Missing provenance')
    available = set()
    for item in audit['sources']:
        object_fields(item, {'path', 'sha256'}, 'provenance source')
        if not text(item['path']) or not isinstance(item['sha256'], str) \
                or not re.fullmatch('[a-f0-9]{64}', item['sha256']):
            raise EvidenceError('Invalid provenance source')
        raw = blobs(item['sha256'])
        if sha(raw) != item['sha256']:
            raise EvidenceError('Provenance digest mismatch')
        available.add(item['sha256'])
    if review['source_sha256'] not in available:
        raise EvidenceError('Review must reference a preserved source')
    if not isinstance(audit['rule_links'], list) or not isinstance(audit['outcome_refs'], list):
        raise EvidenceError('Invalid evidence links')
    covered = set()
    for link in audit['rule_links']:
        object_fields(link, {'rule_id', 'source_sha256', 'pointer'}, 'rule evidence link')
        if link['rule_id'] not in {r['id'] for r in bundle['rules']} or link['source_sha256'] not in available:
            raise EvidenceError('Unknown rule or source in evidence link')
        json_pointer(blobs(link['source_sha256']), link['pointer'])
        covered.add(link['rule_id'])
    for link in audit['outcome_refs']:
        object_fields(link, {'source_sha256', 'pointer'}, 'outcome reference')
        if link['source_sha256'] not in available:
            raise EvidenceError('Unknown outcome source')
        json_pointer(blobs(link['source_sha256']), link['pointer'])
    if review['status'] == 'research_admitted' and covered != {r['id'] for r in bundle['rules']}:
        raise EvidenceError('Admitted bundle needs an evidence link for every rule')
    if bundle['body_sha256'] != digest(render(bundle)) or bundle['sha256'] != digest(
            canonical({k: v for k, v in bundle.items() if k != 'sha256'})):
        raise EvidenceError('Experience digest mismatch')
    return bundle


def validate(bundle, blobs):
    try:
        return _validate(bundle, blobs)
    except (KeyError, TypeError, IndexError) as error:
        raise EvidenceError('Malformed experience fields') from error


def initialize(store):
    store = Path(store)
    if store.exists():
        raise EvidenceError('Memory path exists; use an existing store or a new path')
    store.mkdir(parents=True)
    (store/'records').mkdir()
    (store/'sources').mkdir()
    (store/'memory.json').write_text(json.dumps(dict(schema_version=STORE_VERSION,
        scope='research_only', automatic_evolution=False), indent=2)+'\n', encoding='utf-8')
    from .experience_approval import empty_index
    from .archive import atomic_json
    atomic_json(store/'active.json', empty_index())
    return dict(initialized=True, scope='research_only')


def records(store):
    store = Path(store)
    if store.is_file():
        from .compact_experience import materialize
        return materialize(store)[0]
    if json.loads((store/'memory.json').read_text(encoding='utf-8')) != dict(
            schema_version=STORE_VERSION, scope='research_only', automatic_evolution=False):
        raise EvidenceError('Invalid research memory header')
    if not (store/'records').is_dir() or not (store/'sources').is_dir():
        raise EvidenceError('Incomplete memory store: records or sources directory is missing')
    result = []
    for path in sorted((store/'records').glob('*.json')):
        bundle = json.loads(path.read_text(encoding='utf-8'))
        validate(bundle, lambda code: (store/'sources'/code).read_bytes())
        if path.name != bundle['sha256']+'.json':
            raise EvidenceError('Record filename mismatch')
        result.append(bundle)
    identities = [(b['id'], b['version']) for b in result]
    if len(set(identities)) != len(identities):
        raise EvidenceError('Duplicate immutable experience version')
    by_hash = {b['sha256']: b for b in result}
    for bundle in result:
        parent = bundle['parent_sha256']
        if parent is not None and (parent not in by_hash or by_hash[parent]['id'] != bundle['id']):
            raise EvidenceError('Missing or unrelated parent version')
        visited = {bundle['sha256']}
        while parent is not None:
            if parent not in by_hash:
                raise EvidenceError('Missing ancestor version')
            if parent in visited:
                raise EvidenceError('Cyclic version lineage')
            visited.add(parent)
            parent = by_hash[parent]['parent_sha256']
    return result


def tips(bundles):
    parents = {b['parent_sha256'] for b in bundles}
    return [b for b in bundles if b['sha256'] not in parents]


def source_bytes(store, code):
    if Path(store).is_file():
        from .compact_experience import materialize
        blobs = materialize(store)[2]
        if code not in blobs:
            raise EvidenceError('Single-file experience content changed')
        return blobs[code]
    return (Path(store)/'sources'/code).read_bytes()


def add(store, payload, source_paths=()):
    store = Path(store)
    existing = records(store)
    if not isinstance(payload, dict):
        raise EvidenceError('Expected experience object')
    bundle = seal(payload) if set(payload) == FIELDS else payload
    pending = {}
    for path in source_paths:
        raw = Path(path).read_bytes()
        pending[sha(raw)] = raw
    def blob(code):
        return pending[code] if code in pending else (store/'sources'/code).read_bytes()
    validate(bundle, blob)
    for old in existing:
        if (old['id'], old['version']) == (bundle['id'], bundle['version']):
            raise EvidenceError('Experience version exists; create a new version')
    same_id = [b for b in existing if b['id'] == bundle['id']]
    parent = next((b for b in existing if b['sha256'] == bundle['parent_sha256']), None)
    if (same_id or bundle['parent_sha256'] is not None) and (parent is None or parent['id'] != bundle['id']):
        raise EvidenceError('New versions must reference an existing parent of the same experience')
    for code in {s['sha256'] for s in bundle['audit']['sources']}:
        raw = blob(code)
        target = store/'sources'/code
        if target.exists():
            if target.read_bytes() != raw:
                raise EvidenceError('Stored source digest mismatch')
        else:
            with target.open('xb') as stream:
                stream.write(raw)
    target = store/'records'/(bundle['sha256']+'.json')
    with target.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(bundle, ensure_ascii=False, indent=2)+'\n')
    return bundle


def snapshot(bundles):
    """All versions are pinned, including rejected/candidate records and lineage."""
    hashes = sorted(b['sha256'] for b in bundles)
    return dict(schema_version='experience-memory-snapshot-v1', record_sha256=hashes,
                sha256=digest(canonical(hashes)), scope='research_only')


def search_records(bundles, query, namespace=None, limit=8, include_all=False):
    if not text(query) or type(limit) is not int or not 1 <= limit <= 100:
        raise EvidenceError('Search requires nonempty text and a limit from 1 to 100')
    if namespace is not None and namespace not in (taxonomy.VERSION, LEGACY_TAXONOMY):
        raise EvidenceError('Unsupported search taxonomy')
    corpus = [b for b in (bundles if include_all else tips(bundles)) if namespace is None or b['taxonomy_version'] == namespace]
    # Audit provenance, outcome records, IDs and version names never enter the index.
    counts = [Counter(_terms(render(b)+'\n'+' '.join(b['requires']+b['excludes']))) for b in corpus]
    average = sum(sum(c.values()) for c in counts)/max(1, len(counts)) or 1
    frequencies = Counter(token for c in counts for token in c)
    query_terms = set(_terms(query))
    ranked = []
    for bundle, bag in zip(corpus, counts):
        score = 0.0
        for token in sorted(query_terms):
            tf = bag[token]
            if tf:
                idf = math.log(1+(len(corpus)-frequencies[token]+0.5)/(frequencies[token]+0.5))
                score += idf*tf*2.5/(tf+1.5*(0.25+0.75*sum(bag.values())/average))
        if score > 0:
            ranked.append(dict(id=bundle['id'], version=bundle['version'], sha256=bundle['sha256'],
                taxonomy_version=bundle['taxonomy_version'], labels=bundle['labels'],
                admission_status=bundle['review']['status'], score=score,
                body_sha256=bundle['body_sha256'], text=render(bundle)))
    ranked.sort(key=lambda row: (-row['score'], row['sha256']))
    return dict(schema_version='experience-search-v1', purpose='discovery_only_not_delivery_or_semantic_admission',
                memory_sha256=snapshot(bundles)['sha256'], taxonomy_filter=namespace,
                results=ranked[:limit])


def _terms(text):
    stop = set('a an the to of and or in on with for is be by from that this it as'.split())
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text).replace('_', ' ')
    return [s for s in re.findall(r'[a-z][a-z0-9]*|[\u4e00-\u9fff]', text.lower()) if s not in stop]


def search(store, query, namespace=None, limit=8, required_labels=None):
    from . import experience_approval as approval
    bundles=records(store)
    requested=taxonomy.labels([] if required_labels is None else required_labels)
    active_hashes={row['bundle']['sha256'] for row in approval.active(store)}
    parent_hashes={b['parent_sha256'] for b in bundles}
    # Discovery includes active parents as well as new candidate tips. The index
    # still excludes audit data; this flag is display metadata, not a rank feature.
    visible=[b for b in bundles if (b['sha256'] in active_hashes or b['sha256'] not in parent_hashes)
             and set(requested)<=set(b['labels'])]
    result=search_records(visible,query,namespace,limit,include_all=True)
    result['memory_sha256']=snapshot(bundles)['sha256']
    result['label_filter']=requested
    for row in result['results']:row['expert_active']=row['sha256'] in active_hashes
    return result


def legacy_payload(entry, identifier, registry_path, review_path, extra_sources=(),
                   admitted=False, notes=(), rule_links=None, outcome_refs=None):
    """Deterministic import adapter, not recoding or a new semantic review."""
    object_fields(entry, {'requires', 'excludes', 'version', 'primary_class', 'text',
                          'text_sha256', 'sha256'}, 'historical frozen entry')
    if not text(entry['text']) or not text(entry['version']) or not isinstance(entry['primary_class'], str):
        raise EvidenceError('Malformed historical text, version or class')
    if entry['text_sha256'] != digest(entry['text']) or entry['sha256'] != digest(
            canonical({k:v for k,v in entry.items() if k != 'sha256'})):
        raise EvidenceError('Historical entry digest mismatch')
    headers = list(re.finditer(r'^R([0-9]{2}) \[([^\]\n]+)\]\n', entry['text'], re.MULTILINE))
    reverse = {v:k for k,v in CATEGORIES.items()}
    rules = []
    for index, match in enumerate(headers):
        end = headers[index+1].start()-2 if index+1 < len(headers) else len(entry['text'])-1
        category = reverse.get(match.group(2))
        if category is None:
            raise EvidenceError('Unknown historical rule category; no automatic rewrite')
        rules.append(dict(id='R'+match.group(1), category=category, body=entry['text'][match.end():end]))
    if not rules or render(dict(rules=rules)) != entry['text']:
        raise EvidenceError('Historical text does not round-trip exactly; do not silently normalize')
    paths = list(dict.fromkeys([str(registry_path), str(review_path)]+[str(p) for p in extra_sources]))
    sources = [dict(path=p, sha256=sha(Path(p).read_bytes())) for p in paths]
    review_code = sha(Path(review_path).read_bytes())
    links = rule_links if rule_links is not None else [dict(rule_id=r['id'], source_sha256=review_code,
            pointer=f'/rules/{i}') for i, r in enumerate(rules)]
    return dict(schema_version=BUNDLE_VERSION, id=identifier, version=entry['version'], parent_sha256=None,
        taxonomy_version=LEGACY_TAXONOMY, labels=[entry['primary_class']], requires=entry['requires'],
        excludes=entry['excludes'], rules=rules,
        review=dict(status='research_admitted' if admitted else 'candidate', kind='ai_assisted_historical',
                    source_sha256=review_code,
                    limitations=['Historical review retained; import is not a fresh semantic review or production admission.',
                                 'Historical labels are retained; delivery uses reviewed applicability predicates.']),
        audit=dict(sources=sources, rule_links=links, outcome_refs=[] if outcome_refs is None else outcome_refs,
                   notes=list(notes)+['Exact historical body and applicability retained; no new model output.']))


def delivery_entries(bundles):
    """Historical labels stay unchanged; reviewed predicates decide applicability."""
    from . import experience_routing as routing
    return [(routing.freeze_entry(render(b), b['labels'] if b['taxonomy_version'] == taxonomy.VERSION
                                  else list(taxonomy.CODES), b['requires'], b['excludes'], b['version']), b)
            for b in bundles]


def route_records(visible, bundles, *, max_experiences=5):
    """Shared routing for repair delivery and prospective/evaluation views."""
    from . import experience_routing as routing
    routing.delivery_limit(max_experiences)
    entries = delivery_entries(bundles)
    # Prefer the latest reviewed applicable revision within the same experience.
    # An inapplicable revision cannot hide an applicable approved predecessor.
    applicable = {}
    for entry, bundle in entries:
        trial = routing.route(visible['analysis'], visible['sources'], [entry],
                              task=visible['task'], review=visible.get('review'))
        if trial['selected'] is not None:
            applicable[bundle['id']] = (entry, bundle)
    if applicable:
        entries = list(applicable.values())
    decision = routing.route(visible['analysis'], visible['sources'], [entry for entry, _ in entries],
                             task=visible['task'], review=visible.get('review'), max_experiences=max(1,len(entries)))
    chosen = {row['sha256']: row for row in decision['selected_entries']}
    codes=[r['code'] for r in visible['analysis']['obligation_labels']] if decision['condition']=='ROUTED' else []
    entries.sort(key=lambda pair:(routing.match_rank(pair[0],codes),pair[1]['sha256']))
    matched=[]
    for entry, bundle in entries:
        if entry['sha256'] not in chosen:
            continue
        if digest(render(bundle)) != chosen[entry['sha256']]['text_sha256']:
            raise EvidenceError('Selected body digest mismatch')
        matched.append((entry,bundle))
    selected=[bundle for _,bundle in matched[:max_experiences]]
    selected_entries=[dict(version=e['version'],obligation_labels=e['obligation_labels'],sha256=e['sha256'],text_sha256=e['text_sha256']) for e,_ in matched[:max_experiences]]
    decision.update(selected_entries=selected_entries,selected=selected_entries[0] if len(selected_entries)==1 else None,
        matched_count=len(matched),max_experiences=max_experiences,truncated_count=max(0,len(matched)-max_experiences),
        ranking='label_jaccard_then_overlap_then_digest',
        omitted_memory_sha256s=[b['sha256'] for _,b in matched[max_experiences:]])
    return decision, selected


def delivery_text(bundles):
    if not bundles:
        return None
    if len(bundles)==1:
        return render(bundles[0])
    sections=[]
    for bundle in bundles:
        rules=[dict(r,id=bundle['sha256']+':'+r['id']) for r in bundle['rules']]
        sections.append('Matched experience '+bundle['sha256']+'\n'+render(dict(rules=rules)))
    return ('Use the matched guidance together where supported by the current task and source. '
            'If advice conflicts, resolve it against the concrete requirements and explain the choice; '
            'do not combine incompatible obligations.\n\n'+'\n\n'.join(sections))


def retrieve(store, visible, expected_snapshot=None, frozen_snapshot=None, *, max_experiences=5):
    """Route approved guidance against the current task evidence."""
    from . import experience_routing as routing
    from . import experience_approval as approval
    if not isinstance(visible, dict) or not {'task', 'sources', 'analysis'} <= set(visible) \
            or set(visible) - {'task', 'sources', 'analysis', 'review'}:
        raise EvidenceError('Only task, candidate sources, analysis and optional visible-input review are allowed')
    routing.source_inputs(visible['task'], visible['sources'])
    state = approval.freeze(store) if frozen_snapshot is None else approval.validate_snapshot(store, frozen_snapshot)
    bundles = [entry['bundle'] for entry in state['entries']]
    if expected_snapshot is not None and expected_snapshot != state['sha256']:
        raise EvidenceError('Frozen experience memory changed')
    decision, selected = route_records(visible, bundles, max_experiences=max_experiences)
    if decision['reason'] == 'empty_or_inapplicable_library' and not bundles:
        decision['reason'] = 'no_expert_approved_experience'
    return dict(schema_version='experience-delivery-v1', memory_snapshot=state, route=decision,
                selected_memory_record=None if len(selected)!=1 else dict(id=selected[0]['id'],
                    version=selected[0]['version'], sha256=selected[0]['sha256'], body_sha256=selected[0]['body_sha256']),
                selected_memory_records=[dict(id=b['id'],version=b['version'],sha256=b['sha256'],body_sha256=b['body_sha256']) for b in selected],
                experience_text=delivery_text(selected),
                qualification='Research guidance only. Pass experience_text alone as optional repair guidance; '
                              'route and provenance are separate audit material. No repair benefit is established.')
