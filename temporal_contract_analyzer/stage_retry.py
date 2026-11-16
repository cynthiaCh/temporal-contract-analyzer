"""Explicit transient-failure classification and null-safe per-stage accounting."""
import re
from pathlib import PurePosixPath

TOKEN_FIELDS = ('input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens','total_tokens')


def contract_write_denial(result, kind, sources):
    """A stopped Contract session may correct one attempted patch to public files."""
    receipt = result.get('native_receipt') or {}
    denial = result.get('policy_denial') or {}
    if kind != 'contract' or result.get('failure_type') != 'tool_policy_denied' \
            or receipt.get('archive_failure_requires_stop') is not False \
            or receipt.get('transport_cleanup_error') or not receipt.get('native', {}).get('blocked_tools') \
            or receipt.get('patch_delivered') is not False or receipt.get('preanalysis_error') \
            or denial.get('tool_name') != 'apply_patch':
        return False
    patch = denial.get('command')
    if not isinstance(patch, str) or not patch.startswith('*** Begin Patch\n') or not patch.rstrip().endswith('*** End Patch'):
        return False
    paths = re.findall(r'^\*\*\* (?:Update File|Add File|Delete File|Move to): (.+)$', patch, re.M)
    if not paths:
        return False
    for text in paths:
        path = PurePosixPath(text)
        if '..' in path.parts:
            return False
        if path.is_absolute():
            try:path = path.relative_to('/workspace')
            except ValueError:return False
        if str(path) not in sources:
            return False
    return True


def restart_counts(stage):
    executions = stage.get('executions', [])
    corrections = sum(e.get('restart_reason') == 'contract_write_recovery' for e in executions)
    return dict(transport_retries=max(len(executions)-1-corrections, 0), tool_policy_recoveries=corrections)


def transient_transport(result, message):
    """Only restart a fully stopped, archived session with a transport failure."""
    receipt = result.get('receipt') or {}
    text = str(message or '').lower()
    if receipt.get('failure_class') != 'model_or_cli_abnormal_exit' or receipt.get('archive_failure_requires_stop') is not False:
        return False
    if receipt.get('transport_cleanup_error') or receipt.get('native',{}).get('blocked_tools'):
        return False
    if re.search(r'\b(400|401|403|404|422)\b|bad request|unauthoriz|authentication|invalid api|unsupported|quota|context length', text):
        return False
    return any(x in text for x in ('connection failed','error sending request','stream disconnected','connection reset','connection refused','remote closed','temporary failure in name resolution'))


def aggregate(results):
    def sum_known(values):
        return sum(values) if all(type(v) in (int,float) and v>=0 for v in values) else None
    requests = sum_known([r.get('requests') for r in results])
    observed = {}
    for key in TOKEN_FIELDS:
        vals = [(r.get('observed_tokens') or r.get('tokens') or {}).get(key) for r in results]
        observed[key] = sum(v for v in vals if type(v) in (int,float)) if any(type(v) in (int,float) for v in vals) else None
    totals = {k: sum_known([(r.get('tokens') or {}).get(k) for r in results]) for k in TOKEN_FIELDS}
    incomplete = any(r.get('usage_incomplete') or r.get('tokens') is None for r in results)
    unknown = sum_known([r.get('unknown_usage_requests',0) for r in results])
    return dict(requests=requests, tokens=None if incomplete else totals, observed_tokens=observed,
                usage_incomplete=incomplete, unknown_usage_requests=unknown)
