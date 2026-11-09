"""Summarize every fixed slot, complete behavior vectors, separate old/new costs."""
import json
import subprocess
import hashlib
import time
from pathlib import Path
from archive import save, sha
from feedback import feedback

A = Path(__file__).resolve().parent
REPO = A.parent.parent
FIELDS = ['input_tokens', 'cached_input_tokens', 'cache_write_input_tokens',
          'output_tokens', 'reasoning_output_tokens', 'total_tokens']
TARGETS = ['cached-paused-background', 'cached-later-consumption']


def read(path, default=None):
    return json.loads(Path(path).read_text()) if Path(path).exists() else default


def aggregate(rows):
    if not rows:
        return {'sessions_started': 0, 'requests_started': 0, 'tool_attempts': 0,
                'known_usage_subtotal': {k: 0 for k in FIELDS},
                'unknown_usage_requests': 0, 'total_usage': {k: 0 for k in FIELDS},
                'seconds': 0, 'money': None}
    usages = [row.get('usage') for row in rows]
    known = {}
    for key in FIELDS:
        values = [(u.get('observed_usage_subtotal') or {}).get(key) for u in usages if isinstance(u, dict)]
        values = [v for v in values if type(v) in (int, float)]
        known[key] = sum(values) if values else None
    counts = [u.get('requests_started') if isinstance(u, dict) else None for u in usages]
    unknowns = [u.get('usage_unknown_requests') if isinstance(u, dict) else None for u in usages]
    times = [r.get('seconds') for r in rows]
    tools = [u.get('tool_hook_attempts') if isinstance(u, dict) else None for u in usages]
    incomplete = any(not isinstance(u, dict) or u.get('usage_incomplete', True) for u in usages)
    return {'sessions_started': len(rows),
            'requests_started': sum(counts) if all(type(v) is int for v in counts) else None,
            'tool_attempts': sum(tools) if all(type(v) is int for v in tools) else None,
            'known_usage_subtotal': known,
            'unknown_usage_requests': sum(unknowns) if all(type(v) is int for v in unknowns) else None,
            'total_usage': None if incomplete else known,
            'seconds': sum(times) if all(type(v) in (int, float) for v in times) else None,
            'money': None}


def row(root, label, original, standards):
    record = read(root / 'receipt.json', {})
    score = read(root / 'score/stdout.json')
    valid = (record.get('scoring_admissible') is True
             and record.get('scoring_status') == 'COLLECTED'
             and record.get('scored_candidate_unchanged') is True
             and record.get('score_result', {}).get('score_valid') is True)
    if not valid:
        score = None
    relation = feedback(original, [score], standards)['runs'][0] if score else None
    return {'label': label, 'archive': str(root.relative_to(A)), 'slot': record.get('slot'),
            'valid_score': valid, 'verdict': score.get('verdict') if score else None,
            'whole_task_pass': score['verdict'] == 'PASS' if score else None,
            'behavior_vector': score.get('observed_effects') if score else None,
            'target_behaviors': {k: score['observed_effects'].get(k) if score else None for k in TARGETS},
            'satisfied_count': len(relation['actual_successes']) if relation else None,
            'original_successes_lost': [r['effect'] for r in relation['regressions']] if relation else None,
            'improvements_over_original': [r['effect'] for r in relation['improvements']] if relation else None,
            'failed_checks': relation['failed_checks'] if relation else None,
            'usage': read(root / 'usage.json'), 'seconds': record.get('seconds'),
            'scoring_status': record.get('scoring_status'), 'infrastructure_valid': record.get('infrastructure_valid')}


