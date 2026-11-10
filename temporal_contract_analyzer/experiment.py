"""Frozen source-report interventions; never executes candidate code or a model."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

from .core import ROOT, canonical
from .layers import CONDITIONS

ARMS = CONDITIONS
SCHEMA = 'tool-report-experiment-1'
ASSISTANCE_SCHEMA = 'tool-report-assistance-1'


def digest_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def implementation_hashes():
    paths = list((ROOT / 'temporal_contract_analyzer').glob('*.py'))
    paths += [ROOT / 'temporal_contract_analyzer/javascript' / name
              for name in ('parse.cjs', 'package.json', 'package-lock.json')]
    return {str(p.relative_to(ROOT)): digest_bytes(p.read_bytes()) for p in sorted(paths)}


def append_report(original, report, arm, condition='latent-maintenance'):
    if arm not in ARMS:
        raise ValueError('Unknown tool report arm')
    if arm == 'none':
        if report:
            raise ValueError('Unassisted arm must have an empty report')
        return original
    if condition == 'open-recovery':
        # Preserve the frozen report bodies, while keeping this task read-only.
        return original + b'\n\n' + (
            '--- Supplementary aid for read-only contract recovery ---\n'
            'The task remains repository inspection and contract recovery only.\n'
            'Interpret maintenance/editing language below as context for analysis, not permission to modify files.\n\n'
        ).encode('utf-8') + report + (
            '\n--- End supplementary recovery aid ---\n'
            'Remain read-only. Recover obligations, cite repository evidence, and describe event orders; '
            'do not implement the maintenance change.\n'
        ).encode('utf-8')
    if arm in ('audit', 'risk', 'audit_review'):
        # Same neutral wrapper: these conditions lead with the generic audit.
        return original + b'\n\n' + (
            '--- Supplementary temporal review aid ---\n'
            'Use the original maintenance task to decide the required behavior.\n\n'
        ).encode('utf-8') + report + b'\n--- End supplementary review aid ---\n'
    # Preserve the original B/C/D wrapper exactly for archived experiments.
    return original + b'\n\n' + (
        '--- Supplementary candidate-source inspection report ---\n'
        'This material is generated from the initial candidate source. '
        'Use the original maintenance task to decide the required behavior.\n\n'
    ).encode('utf-8') + report + b'\n--- End supplementary report ---\n'


def assistance(bundle_dir, bundle_path, manifest, arm, candidate_hash, original, condition='latent-maintenance'):
    descriptor = manifest['layers'][arm]
    report = (Path(bundle_dir) / descriptor['path']).read_bytes() if descriptor['path'] else b''
    final = append_report(original, report, arm, condition)
    suffix = final[len(original):]
    record = {
        'schema_version': ASSISTANCE_SCHEMA, 'arm': arm,
        'bundle_path': bundle_path,
        'bundle_manifest_sha256': digest_bytes((Path(bundle_dir) / 'manifest.json').read_bytes()),
        'report_sha256': digest_bytes(report),
        'input_sha256': manifest['input_sha256'], 'tool_sha256': manifest['tool_sha256'],
        'layer_generator_sha256': manifest['generator_sha256'],
        'selected_locations_sha256': manifest['selection_sha256'],
        'candidate_tree_sha256': candidate_hash,
        'original_prompt_sha256': digest_bytes(original), 'final_prompt_sha256': digest_bytes(final),
        'report_bytes': len(report), 'report_characters': len(report.decode('utf-8')),
        'appended_bytes': len(suffix), 'appended_characters': len(suffix.decode('utf-8')),
        'prompt_bytes': len(final), 'prompt_characters': len(final.decode('utf-8')),
        'report_tokens': None, 'truncation': 'none',
    }
    return final, record


def input_receipt(plan_path, data, job):
    """Retained even if the agent or scorer never produces a terminal run receipt."""
    return {
        'schema_version': 'tool-report-job-input-1',
        'plan_sha256': digest_bytes(Path(plan_path).read_bytes()),
        'job_id': job['id'], 'case_id': job['case_id'], 'replicate': job['replicate'],
        'condition': job['condition'], 'tool_report': job['tool_report'],
        'tool_assistance': job['tool_assistance'],
        'model': data['config']['model'], 'reasoning_effort': data['config']['reasoning_effort'],
        'timeout_seconds': data['config']['timeout_seconds'],
        'final_prompt_path': 'prompts/' + job['id'] + '.md',
        'delivery_status': 'frozen_input_verified; model_delivery_not_yet_confirmed',
    }


def resources(folder, status):
    """Observed terminal usage only. Byte/character lengths are not token estimates."""
    import costbench
    folder = Path(folder)
    fields = (*costbench.TOKEN_FIELDS, 'total_tokens', 'input_tokens_excluding_cache_read')
    result = {key: None for key in fields}
    result.update(usage_status='missing_terminal_usage', agent_seconds=None,
                  agent_clock='utc_agent', resource_warnings=[])
    path = folder / 'agent/run.json'
    if not path.is_file():
        return result
    try:
        raw = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(raw, dict):
            raise ValueError('Agent receipt is not an object')
    except (OSError, UnicodeError, ValueError) as error:
        result['usage_status'] = 'invalid_usage_receipt'
        result['resource_warnings'].append(str(error))
        return result
    try:
        start = raw.get('agent_started_at_utc') or raw.get('started_at_utc')
        end = raw.get('agent_completed_at_utc') or raw.get('completed_at_utc')
        seconds = (datetime.fromisoformat(end.replace('Z', '+00:00')) -
                   datetime.fromisoformat(start.replace('Z', '+00:00'))).total_seconds()
        if seconds >= 0:
            result['agent_seconds'] = seconds
    except (AttributeError, TypeError, ValueError):
        pass
    if status in ('RUNNING', 'RUNNER_ERROR', 'RUNNER_TIMEOUT', 'INTERRUPTED'):
        result['usage_status'] = 'scheduler_' + status.lower()
        return result
    events_path = folder / 'agent/events.jsonl'
    if not events_path.is_file():
        return result
    try:
        events, warnings = costbench.parse_events(events_path.read_bytes(), raw.get('agent_exit_code') != 0)
        usage = costbench.extract_usage(events, status, raw.get('agent_exit_code'))
        result.update({key: usage.get(key) for key in fields})
        result.update(usage_status=usage['accounting_status'], resource_warnings=warnings)
    except (ValueError, TypeError, KeyError) as error:
        result['usage_status'] = 'invalid_usage_receipt'
        result['resource_warnings'].append(str(error))
    return result
