"""Provider-balance guard for a sequential, bounded DeepSeek experiment.

Only the explicit fetch function performs network I/O. Credentials are read from
the environment at call time and never enter receipts. Balance movements are an
account observation, not a provider invoice attributable to this experiment.
Other account debits count conservatively; increases never enlarge authorization.
Enforcement is at stage boundaries, with a reserve for in-flight/late billing.
"""
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import urllib.error
import urllib.request


VERSION = 'deepseek-live-budget-v1'
BALANCE_URL = 'https://api.deepseek.com/user/balance'
PRICING = dict(input_usd_per_million='0.3', cached_input_usd_per_million='0.006',
               output_usd_per_million='1.2', usd_to_cny_reserve='8',
               checked_date='2026-11-15', source='https://api-docs.deepseek.com/quick_start/pricing/')


class BudgetError(ValueError):
    """Invalid or modified budget configuration/receipt; contains no credentials."""


class BalanceUnavailable(RuntimeError):
    def __init__(self, reason):
        known = {'credential_unavailable', 'invalid_balance_response', 'unique_cny_balance_required',
                 'invalid_cny_balance', 'balance_http_error', 'oversized_balance_response'}
        safe = isinstance(reason, str) and (reason in known or re.fullmatch(
            r'balance_http_[0-9]{3}|balance_transport_[A-Za-z_][A-Za-z_0-9]{0,60}', reason))
        self.reason = reason if safe else 'balance_unavailable'
        super().__init__(self.reason)


def _decimal(value):
    if isinstance(value, bool):
        raise BudgetError('Budget amount must be a finite nonnegative number')
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise BudgetError('Budget amount must be a finite nonnegative number') from None
    if not result.is_finite() or result < 0:
        raise BudgetError('Budget amount must be a finite nonnegative number')
    return result


def _number(value):
    value = _decimal(value)
    return format(value.normalize(), 'f') if value else '0'


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def _digest(value):
    return hashlib.sha256(_canonical(value)).hexdigest()


def cny_balance(response):
    """Validate only documented fields and retain no raw provider response."""
    if not isinstance(response, dict) or type(response.get('is_available')) is not bool:
        raise BalanceUnavailable('invalid_balance_response')
    rows = response.get('balance_infos')
    if not isinstance(rows, list):
        raise BalanceUnavailable('invalid_balance_response')
    rows = [row for row in rows if isinstance(row, dict) and row.get('currency') == 'CNY']
    if len(rows) != 1:
        raise BalanceUnavailable('unique_cny_balance_required')
    try:
        amount = _decimal(rows[0]['total_balance'])
    except (KeyError, BudgetError):
        raise BalanceUnavailable('invalid_cny_balance') from None
    return response['is_available'], amount


def fetch_provider_balance(*, timeout=20, opener=None):
    """Explicit read-only GET; never include token/headers/error bodies in output."""
    if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or not 0 < timeout <= 20:
        raise BudgetError('Balance timeout must be at most 20 seconds')
    key = os.environ.get('DEEPSEEK_API_KEY')
    if not key:
        raise BalanceUnavailable('credential_unavailable')
    request = urllib.request.Request(BALANCE_URL, headers={'Authorization': 'Bearer ' + key})
    try:
        with (opener or urllib.request.urlopen)(request, timeout=timeout) as response:
            if response.status != 200:
                raise BalanceUnavailable('balance_http_error')
            raw = response.read(65537)
            if len(raw) > 65536:
                raise BalanceUnavailable('oversized_balance_response')
            value = json.loads(raw)
        cny_balance(value)
        return value
    except BalanceUnavailable:
        raise
    except urllib.error.HTTPError as error:
        raise BalanceUnavailable('balance_http_' + str(error.code)) from None
    except Exception as error:
        # Do not preserve repr(error): transports can embed headers or bodies.
        raise BalanceUnavailable('balance_transport_' + type(error).__name__) from None


def estimate_tokens_cny(tokens, *, pricing=None):
    """Peak, cache-aware audit estimate. Reasoning is already in output_tokens."""
    if not isinstance(tokens, dict):
        raise BudgetError('Complete token usage is required')
    required = ['input_tokens', 'output_tokens']
    if any(type(tokens.get(k)) is not int or tokens[k] < 0 for k in required):
        raise BudgetError('Complete token usage is required')
    cached = tokens.get('cached_input_tokens', 0)
    if cached is None:
        cached = 0  # Unknown cache use is conservatively priced as a miss.
    if type(cached) is not int or not 0 <= cached <= tokens['input_tokens']:
        raise BudgetError('Invalid cached token usage')
    reasoning = tokens.get('reasoning_output_tokens')
    if reasoning is not None and (type(reasoning) is not int or not 0 <= reasoning <= tokens['output_tokens']):
        raise BudgetError('Invalid reasoning token usage')
    prices = pricing or PRICING
    try:
        miss, hit, output, reserve = [_decimal(prices[k]) for k in
            ['input_usd_per_million', 'cached_input_usd_per_million', 'output_usd_per_million', 'usd_to_cny_reserve']]
    except KeyError:
        raise BudgetError('Incomplete audit prices') from None
    if min(miss, output, reserve) <= 0 or hit > miss:
        raise BudgetError('Invalid audit prices')
    return ((tokens['input_tokens'] - cached) * miss + cached * hit +
            tokens['output_tokens'] * output) * reserve / Decimal(1000000)


class LiveBudget:
    def __init__(self, path, *, authorized_total_cny=250, prior_spend_cny=0,
                 reserve_cny=10, fetcher=None, clock=None):
        self.path = Path(path)
        total, prior, reserve = map(_decimal, [authorized_total_cny, prior_spend_cny, reserve_cny])
        if not 0 < total <= 250 or prior > total:
            raise BudgetError('Authorization must be at most 250 CNY, including prior spend')
        self.policy = dict(authorized_total_cny=_number(total), prior_spend_cny=_number(prior),
                           reserve_cny=_number(reserve), currency='CNY', pricing=dict(PRICING),
                           prior_spend_basis='caller_supplied_debit_or_conservative_upper_bound',
                           balance_source=BALANCE_URL,
                           enforcement='stage_boundary_with_reserve_not_provider_hard_cap')
        self.fetcher = fetcher or fetch_provider_balance
        self.clock = clock or (lambda: datetime.now(timezone.utc).isoformat())

    def _now(self):
        value = self.clock()
        if isinstance(value, datetime):
            value = value.astimezone(timezone.utc).isoformat()
        if not isinstance(value, str) or not value:
            raise BudgetError('Clock must return a nonempty timestamp')
        return value

    def _fresh(self):
        return dict(schema_version=VERSION, policy=deepcopy(self.policy), created_at=self._now(),
                    status='uninitialized', stop_reason=None, baseline_balance_cny=None,
                    last_balance_cny=None, allocated_new_cny=None, observed_decrease_cny='0',
                    observed_increase_cny='0', audit_peak_cache_aware_cny='0', requests=0,
                    input_tokens=0, cached_input_tokens=0, output_tokens=0,
                    incomplete_usage=False, observations=[], stages=[])

    def _load(self):
        try:
            value = json.loads(self.path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            raise BudgetError('Live budget receipt cannot be read') from None
        if not isinstance(value, dict):
            raise BudgetError('Live budget receipt must be an object')
        digest = value.pop('sha256', None)
        if digest != _digest(value) or value.get('schema_version') != VERSION or value.get('policy') != self.policy:
            raise BudgetError('Live budget receipt or authorization changed')
        return value

    def _save(self, value):
        value = deepcopy(value)
        value.pop('sha256', None)
        value['sha256'] = _digest(value)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix='.live-budget-', dir=self.path.parent)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as stream:
                json.dump(value, stream, ensure_ascii=False, indent=2)
                stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return value

    def _refresh(self, value):
        observation = dict(captured_at=self._now())
        try:
            available, balance = cny_balance(self.fetcher())
        except Exception as error:
            reason = error.reason if isinstance(error, BalanceUnavailable) else 'balance_fetch_failed_' + type(error).__name__
            observation.update(valid=False, reason=reason)
            value['observations'].append(observation)
            value.update(status='stopped', stop_reason=reason)
            return False
        observation.update(valid=True, is_available=available, balance_cny=_number(balance))
        if value['baseline_balance_cny'] is None:
            allocation = min(_decimal(self.policy['authorized_total_cny']) - _decimal(self.policy['prior_spend_cny']),
                             max(balance - _decimal(self.policy['reserve_cny']), Decimal(0)))
            value.update(baseline_balance_cny=_number(balance), allocated_new_cny=_number(allocation))
        else:
            change = _decimal(value['last_balance_cny']) - balance
            field = 'observed_decrease_cny' if change >= 0 else 'observed_increase_cny'
            value[field] = _number(_decimal(value[field]) + abs(change))
            observation.update(decrease_cny=_number(max(change, Decimal(0))),
                               increase_cny=_number(max(-change, Decimal(0))))
        value['last_balance_cny'] = _number(balance)
        value['observations'].append(observation)
        if not available:
            value.update(status='stopped', stop_reason='provider_balance_unavailable')
            return False
        remaining = min(_decimal(value['allocated_new_cny']) - _decimal(value['observed_decrease_cny']),
                        balance - _decimal(self.policy['reserve_cny']))
        if remaining <= 0:
            value.update(status='stopped', stop_reason='live_spend_limit')
            return False
        value.update(status='active', stop_reason=None)
        return True

    def initialize(self):
        """Establish a baseline once. Existing receipts are never silently reset."""
        if self.path.exists():
            value = self._load()
            return dict(value, sha256=_digest(value))
        value = self._fresh()
        self._refresh(value)
        return self._save(value)

    def before_stage(self, stage_id=None):
        """Poll immediately before a paid stage; return an explicit allow/stop result."""
        if self.path.exists():
            value = self._load()
            fresh = False
        else:
            value = self.initialize(); value.pop('sha256', None)
            fresh = True
        if value['incomplete_usage']:
            value.update(status='stopped', stop_reason='incomplete_model_usage')
            allowed = False
        elif stage_id is not None and any(row['stage_id'] == str(stage_id) for row in value['stages']):
            value.update(status='stopped', stop_reason='stage_already_accounted')
            allowed = False
        else:
            allowed = value['status'] == 'active' if fresh else self._refresh(value)
        receipt = self._save(value)
        return dict(allowed=allowed, reason=receipt['stop_reason'], ledger=receipt)

    def observe(self, result, stage_id=None):
        """Record returned request/token usage; no network call, no fabricated zeros."""
        value = self._load()
        if value['baseline_balance_cny'] is None:
            raise BudgetError('A provider baseline must precede model usage')
        if not isinstance(result, dict):
            result = {}
        requests, tokens = result.get('requests'), result.get('tokens')
        identifier = str(stage_id) if stage_id is not None else 'stage-' + str(len(value['stages']) + 1)
        evidence = dict(requests=requests, tokens=tokens, usage_incomplete=result.get('usage_incomplete', False))
        digest = _digest(evidence)
        prior = next((row for row in value['stages'] if row['stage_id'] == identifier), None)
        if prior:
            if prior['evidence_sha256'] != digest:
                raise BudgetError('A stage cannot be re-accounted with changed usage')
            return self._save(value)
        complete = type(requests) is int and requests >= 0 and not evidence['usage_incomplete']
        cost = Decimal(0)
        if complete and requests == 0 and tokens is None:
            pass
        elif complete:
            try:
                cost = estimate_tokens_cny(tokens, pricing=self.policy['pricing'])
                if requests == 0 and (tokens['input_tokens'] or tokens['output_tokens']):
                    complete = False
            except BudgetError:
                complete = False
        row = dict(stage_id=identifier, observed_at=self._now(), requests=requests,
                   complete=complete, evidence_sha256=digest,
                   audit_peak_cache_aware_cny=_number(cost) if complete else None)
        if type(requests) is int and requests >= 0:
            value['requests'] += requests
        if complete:
            value['audit_peak_cache_aware_cny'] = _number(_decimal(value['audit_peak_cache_aware_cny']) + cost)
            if tokens:
                value['input_tokens'] += tokens['input_tokens']
                value['output_tokens'] += tokens['output_tokens']
                value['cached_input_tokens'] += tokens.get('cached_input_tokens') or 0
        else:
            value.update(incomplete_usage=True, status='stopped', stop_reason='incomplete_model_usage')
        value['stages'].append(row)
        return self._save(value)

    def summary(self):
        value = self._load()
        remaining = None if value['allocated_new_cny'] is None else _number(max(
            _decimal(value['allocated_new_cny']) - _decimal(value['observed_decrease_cny']), Decimal(0)))
        return dict(status=value['status'], reason=value['stop_reason'], requests=value['requests'],
                    authorized_total_cny=self.policy['authorized_total_cny'],
                    prior_spend_cny=self.policy['prior_spend_cny'], reserve_cny=self.policy['reserve_cny'],
                    allocated_new_cny=value['allocated_new_cny'], remaining_authorization_cny=remaining,
                    observed_decrease_cny=value['observed_decrease_cny'],
                    audit_peak_cache_aware_cny=value['audit_peak_cache_aware_cny'],
                    incomplete_usage=value['incomplete_usage'])
