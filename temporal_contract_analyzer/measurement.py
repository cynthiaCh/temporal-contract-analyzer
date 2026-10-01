"""Human-reviewed temporal-obligation measurements bound to archived source.

The syntax analyzer may nominate locations, but it never fills this schema.
All semantic claims are authored explicitly and labels are derived only from
those claims.  Candidate source, condition material, behavioral witnesses and
review records remain separate evidence classes.
"""
import copy
from pathlib import PurePosixPath

from .core import EvidenceError, canonical, sha


SCHEMA = 'temporal-contract-measurement-1'
REVIEW_SCHEMA = 'temporal-contract-measurement-review-1'
REVIEW_CHECKS = (
    'evidence_sufficiency', 'evidence_minimality', 'semantic_normalization',
    'temporal_relations', 'ownership_and_policy', 'application_chains',
    'condition_equivalence', 'witness_alignment',
)
RESPONSIBILITIES = {'creator', 'lifetime', 'cancellation', 'validity', 'commit', 'handoff'}
APPLICATION_COUNTS = (
    'necessary_unit_count', 'semantic_role_count', 'dependency_hops',
    'invalidation_boundary_count', 'affected_commit_site_count',
)


def _require(value, message):
    if not value:
        raise EvidenceError(message)


def _keys(value, fields, context):
    expected = set(fields.split())
    _require(isinstance(value, dict) and set(value) == expected,
             context + ': fields must be ' + ' '.join(sorted(expected)))
    return value


def _text(value, context, empty=False):
    _require(isinstance(value, str) and (empty or value.strip()), context + ': expected text')
    return value


def _choice(value, choices, context):
    _require(value in choices, context + ': invalid value')
    return value


def _list(value, context, minimum=0):
    _require(isinstance(value, list) and len(value) >= minimum, context + ': expected list')
    return value


def _strings(value, context, minimum=0):
    _list(value, context, minimum)
    for item in value:
        _text(item, context)
    _require(len(value) == len(set(value)), context + ': duplicate value')
    return value


def _index(value, context, field='id', minimum=0):
    result = {}
    for row in _list(value, context, minimum):
        _require(isinstance(row, dict) and field in row, context + ': missing ' + field)
        identity = _text(row[field], context + '.' + field)
        _require(identity not in result, context + ': duplicate ' + field + ' ' + identity)
        result[identity] = row
    return result


def _digest(value):
    return sha(canonical(value).encode('utf-8'))


def _graph_depth(nodes, edges, context):
    graph = {node: set() for node in nodes}
    for edge in _list(edges, context):
        _require(isinstance(edge, list) and len(edge) == 2 and all(x in graph for x in edge),
                 context + ': invalid dependency edge')
        left, right = edge
        _require(left != right and right not in graph[left], context + ': duplicate or self edge')
        graph[left].add(right)
    visiting, depths = set(), {}

    def visit(node):
        _require(node not in visiting, context + ': dependency cycle')
        if node not in depths:
            visiting.add(node)
            depths[node] = max((visit(child) + 1 for child in graph[node]), default=0)
            visiting.remove(node)
        return depths[node]

    depth = max((visit(node) for node in graph), default=0)
    for left, right in edges:
        pending, seen = [left], set()
        while pending:
            node = pending.pop()
            _require(node != right, context + ': redundant transitive edge')
            if node not in seen:
                seen.add(node)
                pending.extend(child for child in graph[node] if (node, child) != (left, right))
    return depth


def _ordinal(value, context, allow_na=False):
    _require(value is None or (type(value) is int and value in (0, 1, 2)) or
             (allow_na and value == 'N/A'), context + ': invalid ordinal')


def template(report_id, store=None, finding_id=None):
    """Create a draft; an optional finding contributes clues, never obligations."""
    from . import archive
    data = archive.read_report(report_id, store)
    meta = data['metadata']
    _require(data['report'] is not None, 'A failed scan cannot start a measurement')
    evidence_units = []
    if finding_id is not None:
        findings = {row['id']: row for row in data['report']['findings']}
        _require(finding_id in findings, 'Unknown finding for measurement draft')
        events = {event['id']: event for file in data['report']['files'] for event in file['events']}
        sources = archive.read_sources(report_id, store)
        finding = findings[finding_id]
        for position, event_id in enumerate(dict.fromkeys(finding['evidence']), 1):
            event = events.get(event_id)
            _require(event is not None and event['path'] in sources, 'Finding evidence is absent from snapshot')
            anchor = _text(event.get('text'), 'finding event text')
            text = sources[event['path']]
            _require(anchor in text, 'Finding event anchor is absent from snapshot')
            evidence_units.append({
                'id': 'candidate-' + finding_id + '-' + str(position),
                'semantic_key': 'candidate.' + finding['rule'] + '.' + str(position),
                'role': 'candidate-syntax-clue',
                'fact': ('Analyzer observed ' + event['kind'] + ' at ' + event['path'] + ':' + str(event['line']) +
                         '; its contract relevance remains unreviewed.'),
                'sources': [{'kind': 'candidate', 'path': event['path'], 'anchor': anchor,
                             'sha256': sha(text.encode('utf-8')), 'conditions': ['source-only']}],
            })
    return {
        'schema_version': SCHEMA,
        'workflow_status': 'draft',
        'source_binding': {'report_id': report_id, 'input_sha256': meta['input_sha256']},
        'authorship': {'authors': [], 'target_outcomes_seen': None, 'note': ''},
        'conditions': [{
            'id': 'source-only', 'label': 'Archived candidate source only', 'variant': 'ungranted',
            'materials': [],
            'policy': {'classification': 'unknown', 'rationale': '', 'consumers': [], 'contrasts': []},
        }],
        'evidence_units': evidence_units,
        'sites': [],
        'witness_artifacts': [],
        'obligations': [],
    }


def validate(document, report_id=None, store=None):
    """Validate a native document and derive labels without executing code."""
    from . import archive
    root = _keys(document, 'schema_version workflow_status source_binding authorship conditions evidence_units sites witness_artifacts obligations', 'measurement')
    _require(root['schema_version'] == SCHEMA, 'measurement: unsupported schema')
    final = _choice(root['workflow_status'], {'draft', 'final'}, 'workflow_status') == 'final'
    binding = _keys(root['source_binding'], 'report_id input_sha256', 'source_binding')
    bound_id = _text(binding['report_id'], 'source_binding.report_id')
    if report_id is not None:
        _require(bound_id == report_id, 'measurement is bound to another report')
    data = archive.read_report(bound_id, store)
    _require(data['report'] is not None, 'measurement source report has no analysis result')
    _require(binding['input_sha256'] == data['metadata']['input_sha256'],
             'source snapshot changed or measurement is stale')
    source_text = archive.read_sources(bound_id, store)
    snapshot = {path: {'path': path, 'text': text, 'sha256': sha(text.encode('utf-8'))}
                for path, text in source_text.items()}

    authorship = _keys(root['authorship'], 'authors target_outcomes_seen note', 'authorship')
    _strings(authorship['authors'], 'authorship.authors', 1 if final else 0)
    _require(authorship['target_outcomes_seen'] is None or type(authorship['target_outcomes_seen']) is bool,
             'authorship.target_outcomes_seen: expected boolean or null')
    if final:
        _require(type(authorship['target_outcomes_seen']) is bool,
                 'final measurement must declare target_outcomes_seen')
        _text(authorship['note'], 'authorship.note')
    else:
        _text(authorship['note'], 'authorship.note', empty=True)

    conditions = _index(root['conditions'], 'conditions', minimum=1)
    materials = {}
    for cid, condition in conditions.items():
        _keys(condition, 'id label variant materials policy', 'condition/' + cid)
        _text(condition['label'], cid + '.label')
        _choice(condition['variant'], {'ungranted', 'granted', 'observational'}, cid + '.variant')
        for material in _index(condition['materials'], cid + '.materials').values():
            _keys(material, 'id kind text sha256', cid + '.material')
            _choice(material['kind'], {'prompt', 'specification', 'other'}, cid + '.material.kind')
            _text(material['text'], cid + '.material.text', empty=True)
            _require(material['sha256'] == sha(material['text'].encode('utf-8')), cid + '.material: stale SHA-256')
            materials[(cid, material['id'])] = material

    units = _index(root['evidence_units'], 'evidence_units', minimum=1 if final else 0)
    semantic_keys, facts, visible = set(), set(), {cid: set() for cid in conditions}
    for uid, unit in units.items():
        _keys(unit, 'id semantic_key role fact sources', 'evidence/' + uid)
        for field in ('semantic_key', 'role', 'fact'):
            _text(unit[field], uid + '.' + field)
        normalized = ' '.join(unit['fact'].split()).casefold()
        _require(unit['semantic_key'] not in semantic_keys and normalized not in facts,
                 uid + ': duplicate semantic key or fact')
        semantic_keys.add(unit['semantic_key']); facts.add(normalized)
        seen_sources = set()
        for source in _list(unit['sources'], uid + '.sources', 1):
            kind = source.get('kind') if isinstance(source, dict) else None
            if kind == 'candidate':
                _keys(source, 'kind path anchor sha256 conditions', uid + '.source')
                path = _text(source['path'], uid + '.source.path')
                pure = PurePosixPath(path)
                _require(not pure.is_absolute() and '..' not in pure.parts and str(pure) == path,
                         uid + ': unsafe source path')
                _require(path in snapshot, uid + ': source is absent from archived snapshot')
                content, actual = snapshot[path]['text'], snapshot[path]['sha256']
                coordinate = (kind, path, source['anchor'])
            elif kind == 'condition':
                _keys(source, 'kind material_id anchor sha256 conditions', uid + '.source')
                listed = _strings(source['conditions'], uid + '.source.conditions', 1)
                _require(len(listed) == 1, uid + ': condition material source must name one condition')
                material = materials.get((listed[0], source['material_id']))
                _require(material is not None, uid + ': unknown condition material')
                content, actual = material['text'], material['sha256']
                coordinate = (kind, listed[0], source['material_id'], source['anchor'])
            else:
                raise EvidenceError(uid + '.source: invalid kind')
            listed = _strings(source['conditions'], uid + '.source.conditions', 1)
            _require(set(listed) <= set(conditions), uid + ': unknown condition')
            _require(source['sha256'] == actual, uid + ': stale source SHA-256')
            _require(_text(source['anchor'], uid + '.source.anchor') in content, uid + ': anchor not found')
            _require(coordinate not in seen_sources, uid + ': duplicate source')
            seen_sources.add(coordinate)
            for cid in listed:
                visible[cid].add(uid)

    sites = _index(root['sites'], 'sites')
    site_coordinates = set()
    for sid, site in sites.items():
        _keys(site, 'id kind path anchor sha256 description', 'site/' + sid)
        _choice(site['kind'], {'invalidation_boundary', 'commit'}, sid + '.kind')
        path = _text(site['path'], sid + '.path')
        _require(path in snapshot, sid + ': site source absent from snapshot')
        _require(site['sha256'] == snapshot[path]['sha256'], sid + ': stale SHA-256')
        _require(_text(site['anchor'], sid + '.anchor') in snapshot[path]['text'], sid + ': anchor not found')
        _text(site['description'], sid + '.description')
        coordinate = (site['kind'], path, site['anchor'])
        _require(coordinate not in site_coordinates, sid + ': duplicate semantic site')
        site_coordinates.add(coordinate)

    witness_artifacts = _index(root['witness_artifacts'], 'witness_artifacts')
    for aid, artifact in witness_artifacts.items():
        _keys(artifact, 'id kind label content sha256', 'witness_artifact/' + aid)
        _choice(artifact['kind'], {'test-command', 'test-output', 'trace', 'review-note', 'other'}, aid + '.kind')
        _text(artifact['label'], aid + '.label')
        _text(artifact['content'], aid + '.content', empty=True)
        _require(artifact['sha256'] == sha(artifact['content'].encode('utf-8')), aid + ': stale SHA-256')

    obligations = _index(root['obligations'], 'obligations', minimum=1 if final else 0)
    measured_conditions = {cid: [] for cid in conditions}
    witness_summary = {'confirmed': 0, 'failed': 0, 'unknown': 0}
    all_witness_ids = set()
    for oid, obligation in obligations.items():
        _keys(obligation, 'id statement confirmation predicate witnesses measurements', 'obligation/' + oid)
        _text(obligation['statement'], oid + '.statement')
        confirmation = _keys(obligation['confirmation'], 'status actor note', oid + '.confirmation')
        _choice(confirmation['status'], {'draft', 'confirmed'}, oid + '.confirmation.status')
        _text(confirmation['actor'], oid + '.confirmation.actor', empty=not final)
        _text(confirmation['note'], oid + '.confirmation.note', empty=not final)
        if final:
            _require(confirmation['status'] == 'confirmed', oid + ': final measurement requires human confirmation')
        predicate = _keys(obligation['predicate'], 'activation identity deadline continuing_work forbidden_effects', oid + '.predicate')
        for field, value in predicate.items():
            _text(value, oid + '.predicate.' + field, empty=not final)
        witnesses = _index(obligation['witnesses'], oid + '.witnesses')
        duplicate_witnesses = all_witness_ids & set(witnesses)
        _require(not duplicate_witnesses, oid + ': witness IDs must be document-wide unique')
        all_witness_ids.update(witnesses)
        for wid, witness in witnesses.items():
            _keys(witness, 'id kind status reference artifact_ids assertions', oid + '.witness/' + wid)
            _choice(witness['kind'], {'test', 'trace', 'review'}, wid + '.kind')
            status = _choice(witness['status'], {'confirmed', 'failed', 'unknown'}, wid + '.status')
            witness_summary[status] += 1
            _text(witness['reference'], wid + '.reference')
            artifact_ids = _strings(witness['artifact_ids'], wid + '.artifact_ids')
            _require(set(artifact_ids) <= set(witness_artifacts), wid + ': unknown witness artifact')
            if status != 'unknown':
                _require(artifact_ids, wid + ': confirmed/failed witness requires a byte-bound artifact')
            _strings(witness['assertions'], wid + '.assertions')
        measurements = _index(obligation['measurements'], oid + '.measurements', field='condition_id')
        if final:
            _require(set(measurements) == set(conditions), oid + ': measurements must cover every condition')
        else:
            _require(set(measurements) <= set(conditions), oid + ': unknown condition measurement')
        for cid, item in measurements.items():
            measured_conditions[cid].append(_measure(item, oid, cid, units, visible[cid], sites, witnesses))

    condition_rows = []
    for cid, condition in conditions.items():
        policy = _policy(condition['policy'], cid, units, visible[cid], all_witness_ids)
        condition_rows.append({'id': cid, 'label': condition['label'], 'variant': condition['variant'],
                               'H': policy['H'], 'policy': policy, 'measurements': measured_conditions[cid]})
    if final:
        _require(all(len(row['measurements']) == len(obligations) for row in condition_rows),
                 'final measurement has incomplete condition-by-obligation coverage')
    report = {
        'schema_version': SCHEMA,
        'workflow_status': root['workflow_status'],
        'mechanical_valid': True,
        'measurement_sha256': _digest(document),
        'source_binding': copy.deepcopy(binding),
        'authorship': copy.deepcopy(authorship),
        'conditions': condition_rows,
        'obligation_count': len(obligations),
        'evidence_unit_count': len(units),
        'witness_artifact_count': len(witness_artifacts),
        'witness_summary': witness_summary,
        'review': {'status': 'pending', 'required_agreeing_reviewers': 2,
                   'eligible_agreeing_reviewers': 0, 'gate_passed': False, 'records': []},
        'semantic_limits': list(REVIEW_CHECKS),
        'qualification': 'Mechanical derivation from human-authored claims; not automatic contract inference or correctness proof.',
    }
    return report


def _evidence_set(item, context, units, visible, sites=None, witnesses=None, application=False):
    fields = 'id units dependencies sufficiency necessity'
    if application:
        fields += ' invalidation_boundaries affected_commit_sites witness_ids'
    _keys(item, fields, context)
    refs = _strings(item['units'], context + '.units', 1)
    _require(set(refs) <= visible, context + ': evidence unavailable in this condition')
    depth = _graph_depth(refs, item['dependencies'], context + '.dependencies')
    _text(item['sufficiency'], context + '.sufficiency')
    _require(isinstance(item['necessity'], dict) and set(item['necessity']) == set(refs),
             context + ': necessity must cover every selected unit')
    for reason in item['necessity'].values():
        _text(reason, context + '.necessity')
    result = {'id': item['id'], 'necessary_unit_count': len(refs),
              'semantic_role_count': len({units[uid]['role'] for uid in refs}),
              'dependency_hops': depth}
    if application:
        for field, kind, output in (
                ('invalidation_boundaries', 'invalidation_boundary', 'invalidation_boundary_count'),
                ('affected_commit_sites', 'commit', 'affected_commit_site_count')):
            refs2 = _strings(item[field], context + '.' + field)
            _require(all(sid in sites and sites[sid]['kind'] == kind for sid in refs2),
                     context + ': wrong semantic site kind')
            result[output] = len(refs2)
        _require(item['affected_commit_sites'], context + ': application requires a commit site')
        _require(set(_strings(item['witness_ids'], context + '.witness_ids')) <= set(witnesses),
                 context + ': unknown witness')
    else:
        result['E'] = (0 if len(refs) == 1 else 2 if len(refs) >= 4 or
                       result['semantic_role_count'] >= 3 or depth >= 2 else 1)
    return result


def _measure(item, oid, cid, units, visible, sites, witnesses):
    context = cid + '/' + oid
    _keys(item, 'condition_id rule_evidence temporal ownership application', context)
    rule = _keys(item['rule_evidence'], 'status sets', context + '.rule_evidence')
    _choice(rule['status'], {'provisional', 'unknown'}, context + '.rule_evidence.status')
    sets = _index(rule['sets'], context + '.rule_evidence.sets')
    _require(bool(sets) == (rule['status'] == 'provisional'), context + ': rule evidence status disagrees with sets')
    rule_stats = [_evidence_set(row, context + '/set/' + sid, units, visible) for sid, row in sets.items()]
    fingerprints = [frozenset(row['units']) for row in sets.values()]
    _require(len(fingerprints) == len(set(fingerprints)), context + ': duplicate evidence alternative')
    _require(not any(a < b for a in fingerprints for b in fingerprints), context + ': non-minimal evidence alternative')
    e_level = min((row['E'] for row in rule_stats), default=None)

    temporal = _keys(item['temporal'], 'status relations interactions', context + '.temporal')
    _choice(temporal['status'], {'provisional', 'unknown'}, context + '.temporal.status')
    relations = _index(temporal['relations'], context + '.relations')
    _require(bool(relations) == (temporal['status'] == 'provisional'), context + ': temporal status disagrees with relations')
    counts = {'explicit': 0, 'partial': 0, 'implicit': 0}
    semantic_keys = set()
    for rid, relation in relations.items():
        _keys(relation, 'id semantic_key from_event to_event scope predicate kind explicitness evidence enforcement witness_ids', context + '/relation/' + rid)
        for field in ('semantic_key', 'from_event', 'to_event', 'scope', 'predicate'):
            _text(relation[field], context + '.relation.' + field)
        _require(relation['semantic_key'] not in semantic_keys, context + ': duplicate relation semantic key')
        semantic_keys.add(relation['semantic_key'])
        _choice(relation['kind'], {'before', 'ready', 'invalidate-before-commit', 'same-generation', 'reentrant-handoff', 'exactly-once'}, context + '.relation.kind')
        counts[_choice(relation['explicitness'], counts, context + '.relation.explicitness')] += 1
        _require(set(_strings(relation['evidence'], context + '.relation.evidence', 1)) <= visible,
                 context + ': unavailable relation evidence')
        enforcement = _keys(relation['enforcement'], 'baseline maintenance', context + '.relation.enforcement')
        _text(enforcement['baseline'], context + '.enforcement.baseline')
        _text(enforcement['maintenance'], context + '.enforcement.maintenance')
        _require(set(_strings(relation['witness_ids'], context + '.relation.witness_ids')) <= set(witnesses),
                 context + ': unknown witness')
    interaction_pairs, interacting_implicit = set(), False
    for interaction in _list(temporal['interactions'], context + '.interactions'):
        _keys(interaction, 'relations rationale witness_ids', context + '.interaction')
        pair = _strings(interaction['relations'], context + '.interaction.relations', 2)
        _require(len(pair) == 2 and set(pair) <= set(relations), context + ': invalid interaction pair')
        frozen = frozenset(pair)
        _require(frozen not in interaction_pairs, context + ': duplicate interaction')
        interaction_pairs.add(frozen)
        _text(interaction['rationale'], context + '.interaction.rationale')
        _require(set(_strings(interaction['witness_ids'], context + '.interaction.witness_ids')) <= set(witnesses),
                 context + ': unknown witness')
        interacting_implicit |= all(relations[rid]['explicitness'] != 'explicit' for rid in pair)
    t_level = None if temporal['status'] == 'unknown' else 0 if not counts['partial'] + counts['implicit'] else 2 if interacting_implicit else 1

    ownership = _keys(item['ownership'], 'resolution responsibilities rationale competing_owners', context + '.ownership')
    resolution = _choice(ownership['resolution'], {'explicit', 'local', 'cross-context', 'not-applicable', 'unknown'}, context + '.ownership.resolution')
    _text(ownership['rationale'], context + '.ownership.rationale')
    _strings(ownership['competing_owners'], context + '.ownership.competing_owners')
    responsibilities = _index(ownership['responsibilities'], context + '.responsibilities', field='role')
    if resolution not in {'unknown', 'not-applicable'}:
        _require(set(responsibilities) == RESPONSIBILITIES, context + ': incomplete ownership responsibilities')
    else:
        _require(not responsibilities and not ownership['competing_owners'], context + ': unknown/N/A ownership must be empty')
    if resolution == 'cross-context':
        _require(len(ownership['competing_owners']) >= 2, context + ': cross-context ownership needs competing owners')
    for responsibility in responsibilities.values():
        _keys(responsibility, 'role owner evidence', context + '.responsibility')
        _text(responsibility['owner'], context + '.responsibility.owner')
        _require(set(_strings(responsibility['evidence'], context + '.responsibility.evidence', 1)) <= visible,
                 context + ': unavailable ownership evidence')
    l_level = {'explicit': 0, 'local': 1, 'cross-context': 2, 'not-applicable': 'N/A', 'unknown': None}[resolution]

    application = _keys(item['application'], 'status rationale chains', context + '.application')
    _choice(application['status'], {'annotated', 'not-applicable', 'unknown'}, context + '.application.status')
    _text(application['rationale'], context + '.application.rationale')
    chains = _index(application['chains'], context + '.application.chains')
    _require(bool(chains) == (application['status'] == 'annotated'), context + ': application status disagrees with chains')
    chain_stats = [_evidence_set(row, context + '/chain/' + chain_id, units, visible, sites, witnesses, True)
                   for chain_id, row in chains.items()]
    return {'obligation_id': oid, 'labels': {'E': e_level, 'T': t_level, 'L': l_level},
            'rule_sets': rule_stats, 'temporal_status': temporal['status'],
            'temporal_counts': counts if temporal['status'] != 'unknown' else None,
            'interaction_count': len(interaction_pairs) if temporal['status'] != 'unknown' else None,
            'application': {'status': application['status'], 'chains': chain_stats}}


def _policy(policy, cid, units, visible, witnesses):
    _keys(policy, 'classification rationale consumers contrasts', cid + '.policy')
    classification = _choice(policy['classification'], {'same', 'compatible', 'conflicting', 'unknown'}, cid + '.policy.classification')
    _text(policy['rationale'], cid + '.policy.rationale', empty=classification == 'unknown')
    consumers = _index(policy['consumers'], cid + '.policy.consumers')
    _require(bool(consumers) == (classification != 'unknown'), cid + ': policy classification disagrees with consumers')
    for consumer in consumers.values():
        _keys(consumer, 'id name policy evidence', cid + '.consumer')
        _text(consumer['name'], cid + '.consumer.name'); _text(consumer['policy'], cid + '.consumer.policy')
        _require(set(_strings(consumer['evidence'], cid + '.consumer.evidence', 1)) <= visible,
                 cid + ': unavailable policy evidence')
    contrasts = _list(policy['contrasts'], cid + '.policy.contrasts')
    if classification in {'compatible', 'conflicting'}:
        _require(len(consumers) >= 2 and contrasts, cid + ': policy difference requires a contrast')
    if classification == 'unknown':
        _require(not contrasts, cid + ': unknown policy cannot assert contrasts')
    seen = set()
    for contrast in contrasts:
        _keys(contrast, 'left right scope shared_change left_required right_required evidence witness_ids', cid + '.contrast')
        _require(contrast['left'] != contrast['right'] and contrast['left'] in consumers and contrast['right'] in consumers,
                 cid + ': invalid policy contrast')
        for field in ('scope', 'shared_change', 'left_required', 'right_required'):
            _text(contrast[field], cid + '.contrast.' + field)
        key = (frozenset((contrast['left'], contrast['right'])), contrast['scope'])
        _require(key not in seen, cid + ': duplicate policy contrast'); seen.add(key)
        _require(set(_strings(contrast['evidence'], cid + '.contrast.evidence', 1)) <= visible,
                 cid + ': unavailable contrast evidence')
        _require(set(_strings(contrast['witness_ids'], cid + '.contrast.witness_ids')) <= witnesses,
                 cid + ': unknown contrast witness')
    return {'classification': classification, 'rationale': policy['rationale'],
            'H': {'same': 0, 'compatible': 1, 'conflicting': 2, 'unknown': None}[classification],
            'consumer_count': len(consumers), 'contrast_count': len(contrasts)}


def review_template(measurement_report, reviewer_id):
    _text(reviewer_id, 'reviewer_id')
    rows = []
    for condition in measurement_report['conditions']:
        rows.append({'id': condition['id'], 'H': None,
                     'measurements': [{'obligation_id': row['obligation_id'],
                                      'labels': {'E': None, 'T': None, 'L': None},
                                      'application': {'status': None, 'chains': [
                                          {'id': chain['id'], **{key: None for key in APPLICATION_COUNTS}}
                                          for chain in row['application']['chains']]}}
                                     for row in condition['measurements']]})
    return {'schema_version': REVIEW_SCHEMA, 'measurement_sha256': measurement_report['measurement_sha256'],
            'reviewer_id': reviewer_id, 'independent_of_author': None, 'outcome_blinded': None,
            'checks': {name: None for name in REVIEW_CHECKS}, 'conditions': rows, 'findings': [], 'note': ''}


def check_review(measurement_report, review):
    _keys(review, 'schema_version measurement_sha256 reviewer_id independent_of_author outcome_blinded checks conditions findings note', 'review')
    _require(review['schema_version'] == REVIEW_SCHEMA, 'review: unsupported schema')
    _require(review['measurement_sha256'] == measurement_report['measurement_sha256'], 'review: stale measurement binding')
    reviewer = _text(review['reviewer_id'], 'reviewer_id')
    for field in ('independent_of_author', 'outcome_blinded'):
        _require(review[field] is None or type(review[field]) is bool, 'review.' + field + ': expected boolean or null')
    _keys(review['checks'], ' '.join(REVIEW_CHECKS), 'review.checks')
    _require(all(value is None or type(value) is bool for value in review['checks'].values()), 'review check must be boolean or null')
    _strings(review['findings'], 'review.findings'); _text(review['note'], 'review.note', empty=True)
    expected_conditions = {row['id']: row for row in measurement_report['conditions']}
    actual_conditions = _index(review['conditions'], 'review.conditions', minimum=1)
    _require(set(actual_conditions) == set(expected_conditions), 'review: condition coverage mismatch')
    disagreements, incomplete = [], []
    for cid, expected in expected_conditions.items():
        actual = _keys(actual_conditions[cid], 'id H measurements', 'review/' + cid)
        _ordinal(actual['H'], 'review.H')
        if actual['H'] is None: incomplete.append(cid + '/H')
        if actual['H'] != expected['H']: disagreements.append(cid + '/H')
        expected_rows = {row['obligation_id']: row for row in expected['measurements']}
        actual_rows = _index(actual['measurements'], 'review.measurements', field='obligation_id')
        _require(set(actual_rows) == set(expected_rows), 'review: obligation coverage mismatch')
        for oid, expected_row in expected_rows.items():
            actual_row = _keys(actual_rows[oid], 'obligation_id labels application', 'review/' + cid + '/' + oid)
            labels = _keys(actual_row['labels'], 'E T L', 'review.labels')
            for axis, value in labels.items():
                _ordinal(value, 'review.' + axis, allow_na=axis == 'L')
                if value is None: incomplete.append(cid + '/' + oid + '/' + axis)
                if value != expected_row['labels'][axis]: disagreements.append(cid + '/' + oid + '/' + axis)
            application = _keys(actual_row['application'], 'status chains', 'review.application')
            _require(application['status'] in {None, 'annotated', 'not-applicable', 'unknown'}, 'review: invalid application status')
            chains = _index(application['chains'], 'review.application.chains')
            expected_chains = {chain['id']: chain for chain in expected_row['application']['chains']}
            if application['status'] is None: incomplete.append(cid + '/' + oid + '/application')
            if application['status'] != expected_row['application']['status'] or set(chains) != set(expected_chains):
                disagreements.append(cid + '/' + oid + '/application')
            for chain_id, chain in chains.items():
                _keys(chain, 'id ' + ' '.join(APPLICATION_COUNTS), 'review.application.chain')
                for key in APPLICATION_COUNTS:
                    value = chain[key]
                    _require(value is None or (type(value) is int and value >= 0), 'review: invalid application count')
                    if value is None: incomplete.append(cid + '/' + oid + '/application/' + chain_id + '/' + key)
                    elif chain_id in expected_chains and value != expected_chains[chain_id][key]:
                        disagreements.append(cid + '/' + oid + '/application/' + chain_id + '/' + key)
    pending = [key for key, value in review['checks'].items() if value is not True]
    independent = review['independent_of_author'] is True and reviewer not in measurement_report['authorship']['authors']
    eligible = independent and review['outcome_blinded'] is True and not pending and not incomplete and not disagreements and not review['findings']
    return {'reviewer_id': reviewer, 'independence_declared_and_distinct_from_author': independent,
            'outcome_blinded_declared': review['outcome_blinded'], 'pending_checks': pending,
            'incomplete_labels': sorted(set(incomplete)), 'disagreements': sorted(set(disagreements)),
            'findings': list(review['findings']), 'eligible_agreement': eligible,
            'identity_and_independence_are_self_reported': True}


def review_gate(measurement_report, review_records):
    checked, seen = [], set()
    for record in review_records:
        result = check_review(measurement_report, record)
        _require(result['reviewer_id'] not in seen, 'review: duplicate reviewer_id')
        seen.add(result['reviewer_id']); checked.append(result)
    eligible = sum(row['eligible_agreement'] for row in checked)
    passed = eligible >= 2 and all(row['eligible_agreement'] for row in checked)
    return {'status': 'declared_agreement' if passed else 'pending' if not checked else 'unresolved',
            'required_agreeing_reviewers': 2, 'eligible_agreeing_reviewers': eligible,
            'gate_passed': passed, 'records': checked,
            'identity_and_independence_are_self_reported': True}
