"""Read-only compatibility view for frozen MeasurementBench 0.6 reports.

The adapter does not rerun the Paper 1 validator and does not reinterpret its
profile.  It preserves the original report digest and already-derived labels
beside a new analyzer report.  Source equivalence is deliberately not claimed
because the two repositories use different snapshot recipes.
"""
from pathlib import Path
import json

from .core import EvidenceError, sha


SCHEMA = 'temporal-contract-measurement-v06-import-1'
APPLICATION_COUNTS = (
    'necessary_unit_count', 'semantic_role_count', 'dependency_hops',
    'invalidation_boundary_count', 'affected_commit_site_count',
)


def _require(value, message):
    if not value:
        raise EvidenceError(message)


def _json_object(pairs):
    value = {}
    for key, item in pairs:
        _require(key not in value, 'MeasurementBench report contains duplicate key: ' + key)
        value[key] = item
    return value


def read_report(path):
    path = Path(path)
    try:
        raw = path.read_bytes()
        value = json.loads(raw, object_pairs_hook=_json_object)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise EvidenceError('Cannot read MeasurementBench 0.6 report: ' + str(error)) from error
    _require(isinstance(value, dict) and value.get('schema_version') == '0.6',
             'Expected a MeasurementBench 0.6 report')
    _require(value.get('mechanical_valid') is True, 'MeasurementBench report is not mechanically valid')
    _require(isinstance(value.get('case_id'), str) and isinstance(value.get('conditions'), list),
             'Malformed MeasurementBench 0.6 report')
    return raw, value


def import_report(path, report_id, input_sha256):
    raw, source = read_report(path)
    conditions = []
    for condition in source['conditions']:
        _require(isinstance(condition, dict) and isinstance(condition.get('id'), str),
                 'Malformed MeasurementBench condition')
        _require(condition.get('H') is None or type(condition.get('H')) is int and condition['H'] in (0, 1, 2),
                 'Malformed MeasurementBench H label')
        rows = []
        for row in condition.get('measurements', []):
            _require(isinstance(row.get('obligation_id'), str) and row['obligation_id'],
                     'Malformed MeasurementBench obligation ID')
            labels = row.get('labels')
            _require(isinstance(labels, dict) and set(labels) == {'E', 'T', 'L'},
                     'Malformed MeasurementBench labels')
            _require(all(labels[axis] is None or type(labels[axis]) is int and labels[axis] in (0, 1, 2)
                         for axis in ('E', 'T')) and
                     (labels['L'] in (None, 'N/A') or type(labels['L']) is int and labels['L'] in (0, 1, 2)),
                     'Invalid MeasurementBench ordinal label')
            application = row.get('application', {})
            chains = []
            for chain in application.get('chains', []):
                _require(all(key in chain for key in ('id',) + APPLICATION_COUNTS),
                         'Malformed MeasurementBench application chain')
                _require(isinstance(chain['id'], str) and chain['id'] and
                         all(type(chain[key]) is int and chain[key] >= 0 for key in APPLICATION_COUNTS),
                         'Invalid MeasurementBench application count')
                chains.append({'id': chain['id'], **{key: chain[key] for key in APPLICATION_COUNTS}})
            rows.append({'obligation_id': row.get('obligation_id'), 'labels': dict(labels),
                         'application': {'status': application.get('status'), 'chains': chains}})
        conditions.append({'id': condition['id'], 'variant': condition.get('variant'),
                           'H': condition.get('H'), 'measurements': rows})
    return {
        'schema_version': SCHEMA,
        'source_binding': {'report_id': report_id, 'input_sha256': input_sha256,
                           'alignment': 'not_verified_across_snapshot_recipes'},
        'origin': {'format': 'measurementbench-0.6-report', 'sha256': sha(raw),
                   'case_id': source['case_id'],
                   'profile_sha256': source.get('profile_sha256'),
                   'tool_sha256': source.get('tool_sha256'),
                   'standard_sha256': source.get('standard_sha256')},
        'conditions': conditions,
        'review': source.get('review'),
        'qualification': (
            'Read-only compatibility view. The original validator result is preserved, '
            'but equivalence between its benchmark snapshot and this analyzer snapshot is not verified.'
        ),
    }
