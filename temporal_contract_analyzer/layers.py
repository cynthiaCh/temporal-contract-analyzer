"""Frozen, source-bound intervention inputs. No models or candidate execution.

The shared selection is deliberately rule-selected: locations is an intervention,
not a neutral repository listing. Facts contain only whitelisted syntax fields.
"""
import json
from pathlib import Path, PurePosixPath
import re
import shutil

from .core import EvidenceError, canonical, sha


SCHEMA = 'temporal-contract-analysis-bundle-1'
LEGACY_LAYER_SCHEMA = 'temporal-contract-analysis-layers-1'
OPEN_LAYER_SCHEMA = 'temporal-contract-analysis-layers-2'
LAYER_SCHEMA = 'temporal-contract-analysis-layers-3'
LEGACY_CONDITIONS = ('none', 'locations', 'facts', 'review')
OPEN_CONDITIONS = (*LEGACY_CONDITIONS, 'audit', 'risk')
CONDITIONS = (*OPEN_CONDITIONS, 'audit_review')
LAYER_FILES = {'none': None, **{c: c + '.md' for c in CONDITIONS if c != 'none'}}
# Frozen wording shared by both open-review arms. Keep case-specific evidence out.
AUDIT_PROMPT = (
    '# Temporal-risk audit\n\n'
    'Before editing, inspect the candidate-visible repository for evidence that code\n'
    'being removed, replaced, or reordered may incidentally delay, sequence, cancel,\n'
    'invalidate, or wait for another operation. Consider at least two feasible event\n'
    'orders and preserve every evidence-supported behavior and authorization\n'
    'boundary. Do not assume that such a coupling exists, and do not invent a\n'
    'requirement without repository evidence. Then complete the maintenance task.\n'
)
INCOMPLETE_REVIEW_NOTICE = (
    '## Incomplete source-derived review aid\n\n'
    'Treat the D-style locations, syntax facts, interpretations, and questions below as\n'
    'incomplete by default. They are heuristic leads, not a complete repository inventory\n'
    'or a closed causal path. Do not limit inspection to the listed locations. Independently\n'
    'inspect the maintenance target, its call entries and consumers, synchronous callbacks,\n'
    'identity or capability capture, and final persistent and visible effects. Resolve the\n'
    'required behavior from repository evidence before editing.\n'
)
LIMITATIONS = [
    'Locations are selected by frozen heuristic rules, not a neutral file list.',
    'All nonempty layers share the same selected source ranges; no truncation is performed.',
    'Facts are syntax observations and limited binding candidates, not execution or contract proofs.',
    'Review adds rule-authored interpretations, conditions and questions; it is not an oracle.',
    'Candidate-source provenance must be checked by the experiment runner; hashes do not establish semantic correctness.',
    'Report lengths are UTF-8 bytes and Unicode characters, not tokenizer estimates.',
]
OPEN_LIMITATIONS = [
    'Locations/facts/review share selected source ranges; audit/risk disclose no locations or rule details.',
    'Audit is a fixed process reminder. Risk adds only a source-screening signal to the identical reminder.',
    'The signal is present iff a complete scan has at least one rule finding; no detection does not establish safety.',
    'Screening is not calibrated severity, difficulty, defect probability or proof of a temporal obligation.',
]
COMBINED_LIMITATION = (
    'Audit_review presents the audit first and then the review, explicitly treating the review as incomplete by default.'
)


def _conditions(layer_schema):
    if layer_schema == LEGACY_LAYER_SCHEMA:
        return LEGACY_CONDITIONS
    if layer_schema == OPEN_LAYER_SCHEMA:
        return OPEN_CONDITIONS
    if layer_schema == LAYER_SCHEMA:
        return CONDITIONS
    raise EvidenceError('Unsupported layer schema')


def screening_signal(report):
    return dict(policy='any-source-finding-v1',
                status='detected' if report['findings'] else 'not_detected')


def _risk_prompt(report):
    detected = bool(report['findings'])
    signal = ('Candidate-source screening detected temporal-related clues that require review.' if detected else
              'Candidate-source screening did not detect temporal-related clues with its current rules. '
              'This does not establish that temporal risks are absent.')
    return AUDIT_PROMPT + '\n## Candidate-source screening signal\n\n' + signal + (
        '\nThis is a source-based screening cue, not a confirmed defect or a calibrated risk level. '
        'Determine the applicable obligations from repository evidence.\n')


FACT_FIELDS = ('kind', 'callee', 'receiver', 'arguments', 'target', 'operator',
               'rhs_callee', 'awaited', 'expression', 'optional', 'construct',
               'asynchronous', 'conditions', 'block', 'statement', 'name',
               'references', 'argument_references', 'value_references', 'rhs_kind',
               'loop_bindings', 'object_target', 'target_scope', 'argument_index',
               'declared_names', 'assigned_names', 'write_roots', 'binding_kind', 'rhs_text', 'immediate_target_scope',
               'branch_path', 'linear_block', 'guard_key', 'early_return_identifier',
               'condition_path_supported', 'then_path_block', 'else_path_block',
               'condition_identifier', 'condition_truthy', 'null_return_identifier', 'conditional_path', 'object_binding_source', 'object_bindings',
               'reflective_branch_linear', 'countdown_guard', 'countdown_cleanup', 'update_prefix', 'update_standalone',
               'null_throw_identifier', 'listener_method', 'argument_cache_guard', 'return_identifier')
RELATIONS = {
    'callback_before_listener_detach': 'A matching local listener is detached after its user callback on the selected straight wrapper path; runtime dispatch is unproven.',
    'listener_detach_before_callback': 'A matching local listener is detached before its user callback; this is a bounded order fact, not a safety verdict.',
    'cache_key_before_compute': 'A closure cache key is assigned before candidate result computation; cache-hit and exception semantics require review.',
    'compute_before_cache_result': 'The cached-result assignment follows successful RHS evaluation; a thrown RHS skips this write.',
    'numeric_budget_guard_before_call': 'A candidate callback on the positive numeric countdown branch; budget type and meaning are unproven.',
    'external_call_before_conditional_callback_clear': 'If its later numeric condition is true, the callback clear follows the call; the clear itself is not a defect verdict.',
    'external_call_before_callback_clear': 'A direct parameter call precedes its same-frame simple null/undefined clear; the clear itself is not a defect verdict.',
    'receiver_capture_before_reflective_call': 'A this-value capture precedes a candidate Reflect invocation; callable type and native identity remain unresolved.',
    'local_alias_snapshot_before_call': 'A simple local copy of a parameter value precedes its candidate invocation; runtime types and indirect mutation remain unresolved.',
    'state_write_before_external_call': 'Bounded JS evaluation prefix: shared-state write before a candidate external call; value meaning and protection remain unproven.',
    'external_call_before_state_write': 'Bounded JS evaluation prefix: candidate external call before shared-state write; reentry remains a condition to verify.',
    'lexical_before_same_block': 'Source statement order within the same syntax block; execution is not established.',
    'rhs_before_assignment': 'Assignment follows successful RHS evaluation; asynchronous completion is not established.',
    'lexical_write_before_direct_call': 'Source order within one function; execution, callback identity and synchronous reentry are not established.',
    'lexical_capture_before_consumer': 'Local variable/member references and source order; runtime dataflow, ownership and immutability are not established.',
}


def _digest(value, label):
    if not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{64}', value):
        raise EvidenceError('Invalid SHA-256: ' + label)
    return value


def _path(value):
    if not isinstance(value, str) or not value or '\\' in value:
        raise EvidenceError('Invalid frozen source path')
    p = PurePosixPath(value)
    if p.is_absolute() or '..' in p.parts or str(p) != value:
        raise EvidenceError('Invalid frozen source path: ' + value)


def _prepare_checked(report):
    if not isinstance(report, dict):
        raise EvidenceError('Expected a scan report object')
    if report.get('schema_version') != 'temporal-contract-analysis-1' or report.get('status') != 'parsed':
        reasons=[]
        for file in report.get('files', []):
            if file.get('status') != 'parsed':
                error=file.get('error', {})
                detail=error.get('message', '') if isinstance(error, dict) else str(error)
                reasons.append('%s: %s%s' % (file.get('path', '?'), file.get('status', 'unknown'), ' — '+detail if detail else ''))
        for adapter in report.get('adapters', {}).values():
            if adapter.get('status') == 'unavailable':
                reasons.append(adapter.get('reason', 'Parser unavailable'))
        raise EvidenceError('Experiment bundles require a complete parsed scan report'+(': '+'; '.join(reasons) if reasons else ''))
    _digest(report.get('tool_sha256'), 'tool_sha256')
    _digest(report.get('input_sha256'), 'input_sha256')
    files = report.get('files')
    if not isinstance(files, list) or not files or any(f.get('status') != 'parsed' for f in files):
        raise EvidenceError('Experiment bundles require parsed source files')
    if any(s.get('reason') != 'excluded_directory' for s in report.get('skipped', [])):
        raise EvidenceError('Experiment bundles reject incomplete source coverage')
    paths = [f['path'] for f in files]
    if len(set(paths)) != len(paths):
        raise EvidenceError('Duplicate source file in report')
    for f in files:
        _path(f['path']); _digest(f.get('sha256'), f['path'])
    inputs = sorted([{'path': f['path'], 'sha256': f['sha256']} for f in files], key=lambda x: x['path'])
    if report.get('inputs') != inputs or sha(canonical(inputs).encode('utf-8')) != report['input_sha256']:
        raise EvidenceError('Frozen report input inventory/hash does not match source files')
    events = {}
    units = {f['path']: f.get('column_unit', 'unknown') for f in files}
    for f in files:
        for event in f['events']:
            if event['id'] in events or event.get('path') != f['path']:
                raise EvidenceError('Invalid or duplicate source event')
            for field in ('line', 'column', 'end_line', 'end_column'):
                if type(event.get(field)) is not int or event[field] < (1 if 'line' in field else 0):
                    raise EvidenceError('Invalid source event range')
            if (event['end_line'], event['end_column']) < (event['line'], event['column']):
                raise EvidenceError('Invalid source event range order')
            events[event['id']] = event
    selected = set()
    for finding in report['findings']:
        if not finding.get('evidence') or any(e not in events for e in finding['evidence']):
            raise EvidenceError('Finding refers to missing source evidence')
        selected.update(finding['evidence'])
    def key(eid):
        e = events[eid]
        return (e['path'], e['scope'], e['line'], e['column'], e['end_line'], e['end_column'])
    grouped = {}
    for eid in sorted(selected, key=lambda eid: (key(eid), eid)):
        grouped.setdefault(key(eid), []).append(eid)
    locations = []
    for i, (k, ids) in enumerate(grouped.items(), 1):
        path, scope, line, column, end_line, end_column = k
        locations.append(dict(id='L%04d' % i, path=path, scope=scope,
                              start=dict(line=line, column=column),
                              end=dict(line=end_line, column=end_column),
                              column_unit=units[path], evidence_ids=ids))
    return events, locations


def _prepare(report):
    try:
        return _prepare_checked(report)
    except (KeyError, TypeError, AttributeError) as e:
        raise EvidenceError('Malformed scan report: ' + str(e)) from e


def _json_block(value):
    # A fence longer than any source backtick sequence preserves literal snippets.
    content = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)
    longest = max([len(x) for x in re.findall(r'`+', content)] or [0])
    fence = '`' * max(3, longest + 1)
    return fence + 'json\n' + content + '\n' + fence


def _location_lines(locations):
    public = [{k: v for k, v in loc.items() if k != 'evidence_ids'} for loc in locations]
    return ['# Selected candidate-source locations', '',
            'This list is selected by fixed tool rules, not a complete repository inventory.', '',
            _json_block(public), '']


def render_layers(report, layer_schema=LAYER_SCHEMA):
    """Render source reports and open-review inputs; retain legacy bundle bytes."""
    _conditions(layer_schema)
    events, locations = _prepare(report)
    common = _location_lines(locations)
    if any(f.get('language') == 'vue' for f in report['files']):
        common += ['## Vue analysis scope', '',
                   'Only inline script/script setup syntax is analyzed, in separate scopes. Template expressions, generated code, cross-block bindings and Vue runtime behavior are outside this report.', '']
    references = {eid: loc['id'] for loc in locations for eid in loc['evidence_ids']}
    facts = common + ['## Syntax observations at the selected locations', '',
                      'These observations do not establish runtime behavior or business obligations.', '']
    for loc in locations:
        observations = []
        for eid in loc['evidence_ids']:
            e = events[eid]
            observations.append(dict(source=e['text'], syntax={k: e[k] for k in FACT_FIELDS if k in e}))
        facts += ['### ' + loc['id'], '', _json_block(observations), '']
    relations = []
    for r in report.get('relations', []):
        if r.get('kind') in RELATIONS and r.get('before') in references and r.get('after') in references:
            relations.append(dict(kind=r['kind'], before=references[r['before']], after=references[r['after']],
                                  qualification=RELATIONS[r['kind']]))
    scopes = {(loc['path'], loc['scope']) for loc in locations}
    for link in report.get('call_links', []):
        target = link.get('target', '')
        pair = tuple(target.split('::', 1))
        if link.get('call') in references and pair in scopes:
            relations.append(dict(kind='candidate_call_target', call=references[link['call']],
                                  target_scope=target, basis=link.get('basis'),
                                  qualification='Lexical/import binding candidate only; dynamic dispatch and execution are unresolved.'))
    relations = [json.loads(x) for x in sorted(set(canonical(r) for r in relations))]
    facts += ['## Limited relations between selected locations/scopes', '', _json_block(relations), '']
    review = facts + ['## Heuristic interpretations and review questions', '',
                      'The following text is rule-authored guidance, not a defect verdict or an oracle.', '']
    for finding in report['findings']:
        review += [_json_block(dict(rule=finding['rule'], locations=sorted(set(references[e] for e in finding['evidence'])),
                                    interpretation=finding['message'], condition=finding['condition'],
                                    review_question=finding['review_question'], classification='heuristic_review_hint',
                                    **({key: finding[key] for key in ('state_publication', 'listener_detach', 'cache_publication')
                                        if key in finding}))), '']
    layers = {'none': '', 'locations': '\n'.join(common), 'facts': '\n'.join(facts), 'review': '\n'.join(review)}
    if layer_schema in (OPEN_LAYER_SCHEMA, LAYER_SCHEMA):
        layers.update(audit=AUDIT_PROMPT, risk=_risk_prompt(report))
    if layer_schema == LAYER_SCHEMA:
        layers['audit_review'] = AUDIT_PROMPT + '\n' + INCOMPLETE_REVIEW_NOTICE + '\n' + layers['review']
    return layers


def coverage_summary(report, max_chars=60000):
    """Preflight counts from exactly the selection/rendering used by bundles."""
    _, locations = _prepare(report)
    layers = render_layers(report)
    return dict(status=report['status'], tool_version=report['tool_version'],
                input_sha256=report['input_sha256'], tool_sha256=report['tool_sha256'],
                **report['summary'], selected_locations=len(locations),
                has_substantive_report=bool(locations),
                screening_signal=screening_signal(report),
                open_review_inputs={c: layers[c] for c in ('audit', 'risk', 'audit_review')},
                rules={rule: sum(f['rule'] == rule for f in report['findings'])
                       for rule in sorted({f['rule'] for f in report['findings']})},
                layers={c: dict(chars=len(t), bytes=len(t.encode('utf-8'))) for c, t in layers.items()},
                max_chars=max_chars,
                within_limit=max_chars is None or all(len(t) <= max_chars for t in layers.values()))


def _descriptor(path, text):
    raw = text.encode('utf-8')
    return dict(path=path, sha256=sha(raw), bytes=len(raw), chars=len(text))


def _report_text(report):
    return json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + '\n'


def _manifest(report, layers, generator_hash, max_chars, layer_schema=LAYER_SCHEMA):
    _, locations = _prepare(report)
    if max_chars is not None:
        if type(max_chars) is not int or max_chars <= 0:
            raise EvidenceError('max_chars must be a positive integer or None')
        over = [condition for condition, text in layers.items() if len(text) > max_chars]
        if over:
            raise EvidenceError('Report character limit exceeded (no truncation): ' + ', '.join(over))
    conditions = _conditions(layer_schema)
    legacy = layer_schema == LEGACY_LAYER_SCHEMA
    limitations = (LIMITATIONS if legacy else
                   [LIMITATIONS[0], *OPEN_LIMITATIONS,
                    *([] if layer_schema == OPEN_LAYER_SCHEMA else [COMBINED_LIMITATION]),
                    *LIMITATIONS[2:]])
    return dict(schema_version=SCHEMA, layer_schema_version=layer_schema,
                input_sha256=report['input_sha256'], tool_sha256=report['tool_sha256'],
                tool_version=report['tool_version'], generator_sha256=generator_hash,
                adapters=report['adapters'], report=_descriptor('report.json', _report_text(report)),
                layers={c: _descriptor(LAYER_FILES[c], layers[c]) for c in conditions},
                selected_locations=locations, selection_sha256=sha(canonical(locations).encode('utf-8')),
                max_chars=max_chars, truncation='none',
                limitations=limitations,
                **({} if legacy else {'screening_signal': screening_signal(report)}))


def freeze_bundle(report, directory, max_chars=None, layer_schema=LAYER_SCHEMA):
    """Write a new immutable-by-convention bundle; refuse partial/oversize inputs.

    Callers with access to a candidate root must enforce output outside that root.
    Nothing is executed, and no existing directory/file is overwritten.
    """
    layers = render_layers(report, layer_schema=layer_schema)
    manifest = _manifest(report, layers, sha(Path(__file__).read_bytes()), max_chars, layer_schema)
    dest = Path(directory)
    if dest.exists() or dest.is_symlink():
        raise EvidenceError('Bundle directory already exists; choose a new output directory')
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.mkdir()
    try:
        (dest/'report.json').write_text(_report_text(report), encoding='utf-8')
        for condition in _conditions(layer_schema):
            filename = LAYER_FILES[condition]
            if filename:
                (dest/filename).write_text(layers[condition], encoding='utf-8')
        (dest/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2)+'\n', encoding='utf-8')
    except BaseException:
        shutil.rmtree(dest)
        raise
    return manifest


def verify_bundle(directory, expected_input_sha256=None):
    """Verify bytes, lengths, source binding and deterministic rendering.

    The frozen generator hash is recorded, not equated with the current tool.
    This is consistency verification, not cryptographic provenance or correctness.
    """
    root = Path(directory)
    if not root.is_dir() or root.is_symlink():
        raise EvidenceError('Bundle must be a real directory')
    manifest_path = root/'manifest.json'
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise EvidenceError('Frozen manifest must be a regular file')
    try:
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, ValueError) as e:
        raise EvidenceError('Invalid frozen manifest: ' + str(e)) from e
    if not isinstance(manifest, dict):
        raise EvidenceError('Expected a frozen manifest object')
    layer_schema = manifest.get('layer_schema_version')
    if manifest.get('schema_version') != SCHEMA or layer_schema not in (
            LEGACY_LAYER_SCHEMA, OPEN_LAYER_SCHEMA, LAYER_SCHEMA):
        raise EvidenceError('Unsupported bundle/layer schema')
    conditions = _conditions(layer_schema)
    names = {'manifest.json', 'report.json'} | {LAYER_FILES[c] for c in conditions if LAYER_FILES[c]}
    if set(p.name for p in root.iterdir()) != names:
        raise EvidenceError('Unexpected or missing files in frozen bundle')
    if any((root/n).is_symlink() or not (root/n).is_file() for n in names):
        raise EvidenceError('Frozen bundle files must be regular files, not symbolic links')
    try:
        report = json.loads((root/'report.json').read_text(encoding='utf-8'))
        _digest(manifest.get('generator_sha256'), 'generator_sha256')
        rendered = render_layers(report, layer_schema=layer_schema)
        expected = _manifest(report, rendered, manifest['generator_sha256'], manifest.get('max_chars'), layer_schema)
        if manifest != expected:
            raise EvidenceError('Manifest does not match the frozen report and rendered layer descriptors')
        if expected_input_sha256 is not None and expected_input_sha256 != manifest['input_sha256']:
            raise EvidenceError('Bundle does not match expected candidate-source input hash')
        for desc in [manifest['report']] + list(manifest['layers'].values()):
            raw = b'' if desc['path'] is None else (root/desc['path']).read_bytes()
            text = raw.decode('utf-8')
            if _descriptor(desc['path'], text) != desc:
                raise EvidenceError('Frozen report file changed: ' + str(desc['path']))
        return manifest
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as e:
        if isinstance(e, EvidenceError):
            raise
        raise EvidenceError('Invalid frozen bundle: ' + str(e)) from e
