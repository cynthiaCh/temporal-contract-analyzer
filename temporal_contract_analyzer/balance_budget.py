"""Cross-process balance admission for at most two bounded native model stages.

The official balance, not token estimates, controls CNY admission. Balance
movements remain account observations, not per-request invoices. Reservations
and a cash reserve reduce in-flight/late-billing exposure; this is a stage
boundary guard, not a provider-enforced hard spending limit. Unknown token
usage is retained and never replaced with zero.
"""
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

from .live_budget import (BalanceUnavailable, BudgetError, BALANCE_URL,
                          _decimal, _number, _digest, cny_balance,
                          fetch_provider_balance)
from .stage_retry import TOKEN_FIELDS

VERSION='deepseek-shared-balance-budget-v1'
REQUEST_RESERVATION=24  # Frozen Native Action maximum, including continuations.


def _integer(value, minimum=0, maximum=None):
    return type(value) is int and value>=minimum and (maximum is None or value<=maximum)


def _hash(value):return isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value) is not None


def _timestamp(value):
    if not isinstance(value,str):return False
    try:parsed=datetime.fromisoformat(value.replace('Z','+00:00'))
    except ValueError:return False
    return parsed.tzinfo is not None


def _clean_stop(result):
    receipt=result.get('native_receipt')
    if not isinstance(receipt,dict):return False
    archive=receipt.get('archive_status') or {}
    if not isinstance(archive,dict):return False
    return (receipt.get('archive_failure_requires_stop') is False
        and archive.get('status')=='OK' and archive.get('errors')==[]
        and type(receipt.get('exit_code')) is int
        and not receipt.get('transport_cleanup_error')
        and not result.get('bridge_error') and not result.get('cleanup_error'))


def _tokens(value):
    if not isinstance(value,dict):return None
    return {key:value[key] if _integer(value.get(key)) else None for key in TOKEN_FIELDS}


class BalanceBudget:
    def __init__(self,path,*,authorized_total_cny=250,prior_account_debit_cny=0,
                 reserve_cny=10,inflight_reservation_cny=10,max_inflight_stages=2,
                 max_consecutive_infra_failures=3,max_requests=30000,
                 recovery_receipt=None,fetcher=None,clock=None):
        self.path=Path(path).resolve()
        total=None if authorized_total_cny is None else _decimal(authorized_total_cny)
        prior,reserve,reservation=map(_decimal,[prior_account_debit_cny,reserve_cny,inflight_reservation_cny])
        if (total is not None and (not 0<total<=250 or prior>total)) or (total is None and prior!=0) or reserve<10 or reservation<10:
            raise BudgetError('Authorization must include prior debit, with at least10 CNY cash and stage reserves')
        if (not _integer(max_inflight_stages,1,4) or max_consecutive_infra_failures!=3
                or type(max_consecutive_infra_failures) is not int or not _integer(max_requests,1,30000)):
            raise BudgetError('Invalid shared concurrency, circuit or request ceiling')
        recovery=self._recovery(recovery_receipt,prior)
        if recovery and recovery.get('previous_requests',0)>max_requests:
            raise BudgetError('Historical requests exceed the global request ceiling')
        self.policy=dict(authorized_total_cny=None if total is None else _number(total),prior_account_debit_cny=_number(prior),
            reserve_cny=_number(reserve),inflight_reservation_cny=_number(reservation),
            max_inflight_stages=max_inflight_stages,max_consecutive_infra_failures=3,
            max_requests=max_requests,requests_per_stage_reservation=REQUEST_RESERVATION,
            recovery_receipt=recovery,currency='CNY',balance_source=BALANCE_URL,
            enforcement='locked_stage_boundary_with_inflight_reserve_not_provider_hard_cap')
        self.fetcher=fetcher or fetch_provider_balance
        self.clock=clock or (lambda:datetime.now(timezone.utc).isoformat())

    @staticmethod
    def _recovery(value,prior):
        if value is None:return None
        required={'previous_ledger_path','previous_ledger_file_sha256','previous_unknown_requests',
                  'reconciled_balance_cny','reconciled_at','balance_receipt_sha256'}
        if (not isinstance(value,dict) or not required<=set(value)
                or set(value)-required-{'previous_requests'}):
            raise BudgetError('Explicit historical reconciliation receipt is required')
        if (not isinstance(value['previous_ledger_path'],str) or not value['previous_ledger_path']
                or not _hash(value['previous_ledger_file_sha256']) or not _hash(value['balance_receipt_sha256'])
                or not _integer(value['previous_unknown_requests'],1)
                or not _integer(value.get('previous_requests',0)) or not _timestamp(value['reconciled_at'])):
            raise BudgetError('Invalid historical reconciliation metadata')
        receipt=deepcopy(value)
        receipt['previous_ledger_path']=str(Path(receipt['previous_ledger_path']).resolve())
        receipt['reconciled_balance_cny']=_number(receipt['reconciled_balance_cny'])
        # The caller supplies a verified total account debit, never a token estimate.
        if prior<=0:raise BudgetError('Historical reconciliation requires an explicit positive prior account debit')
        return receipt

    def _now(self):
        value=self.clock()
        if isinstance(value,datetime):value=value.astimezone(timezone.utc).isoformat()
        if not _timestamp(value):raise BudgetError('Clock must return a timezone-aware timestamp')
        return value

    @contextmanager
    def _lock(self):
        # Every process/thread opens its own descriptor; replacement of the JSON
        # cannot replace this separate lock inode. Model execution is outside it.
        import fcntl
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.path.with_suffix(self.path.suffix+'.lock').open('a+b') as stream:
            fcntl.flock(stream.fileno(),fcntl.LOCK_EX)
            try:yield
            finally:fcntl.flock(stream.fileno(),fcntl.LOCK_UN)

    def _verify_history(self):
        receipt=self.policy['recovery_receipt']
        if receipt is None:return
        try:
            raw=Path(receipt['previous_ledger_path']).read_bytes()
            value=json.loads(raw)
        except (OSError,ValueError):raise BudgetError('Historical ledger cannot be verified') from None
        if hashlib.sha256(raw).hexdigest()!=receipt['previous_ledger_file_sha256'] or not isinstance(value,dict):
            raise BudgetError('Historical ledger file changed')
        sealed=value.pop('sha256',None)
        if (sealed!=_digest(value) or value.get('schema_version')!='deepseek-live-budget-v1'
                or value.get('incomplete_usage') is not True):
            raise BudgetError('Historical incomplete-usage receipt is not sealed')

    def _fresh(self):
        recovery=self.policy['recovery_receipt'] or {}
        return dict(schema_version=VERSION,policy=deepcopy(self.policy),policy_sha256=_digest(self.policy),
            created_at=self._now(),status='uninitialized',stop_reason=None,
            baseline_balance_cny=None,last_balance_cny=None,allocated_new_cny=None,
            observed_decrease_cny='0',observed_increase_cny='0',observations=[],stages=[],
            historical_unknown_requests=recovery.get('previous_unknown_requests',0),
            historical_requests=recovery.get('previous_requests',0),
            consecutive_infrastructure_failures=0,consecutive_balance_failures=0,
            circuit_open=False,permanent_stop_reason=None,reconciliation=None)

    def _load(self):
        self._verify_history()
        try:value=json.loads(self.path.read_text(encoding='utf8'))
        except (OSError,ValueError):raise BudgetError('Shared budget ledger cannot be read') from None
        if not isinstance(value,dict):raise BudgetError('Shared budget ledger must be an object')
        sealed=value.pop('sha256',None)
        if (sealed!=_digest(value) or value.get('schema_version')!=VERSION or value.get('policy')!=self.policy
                or value.get('policy_sha256')!=_digest(self.policy)):
            raise BudgetError('Shared budget ledger or authorization changed')
        return value

    def _save(self,value):
        self._totals(value)
        value=deepcopy(value);value.pop('sha256',None);value['sha256']=_digest(value)
        fd,temporary=tempfile.mkstemp(prefix='.balance-budget-',dir=self.path.parent)
        try:
            with os.fdopen(fd,'w',encoding='utf8',newline='\n') as stream:
                json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False)
                stream.write('\n');stream.flush();os.fsync(stream.fileno())
            os.replace(temporary,self.path)
            directory=os.open(self.path.parent,os.O_RDONLY)
            try:os.fsync(directory)
            finally:os.close(directory)
        finally:
            if os.path.exists(temporary):os.unlink(temporary)
        return value

    def _totals(self,value):
        rows=[row for row in value['stages'] if row.get('result_sha256') is not None]
        incomplete=value['historical_unknown_requests']>0 or any(row['usage_incomplete'] for row in rows)
        observed={key:None for key in TOKEN_FIELDS};exact={key:0 for key in TOKEN_FIELDS}
        for row in rows:
            for key in TOKEN_FIELDS:
                known=(row.get('observed_tokens') or {}).get(key)
                if not _integer(known):known=(row.get('tokens') or {}).get(key)
                if _integer(known):observed[key]=(observed[key] or 0)+known
                token=(row.get('tokens') or {}).get(key)
                if exact[key] is not None and _integer(token):exact[key]+=token
                else:exact[key]=None
        if value['historical_unknown_requests']:
            exact={key:None for key in TOKEN_FIELDS}
        value.update(incomplete_usage=incomplete,tokens=None if incomplete else exact,observed_tokens=observed,
            known_requests_subtotal=value['historical_requests']+sum(row['requests'] for row in rows if _integer(row.get('requests'))),
            unknown_request_count=value['historical_unknown_requests']+sum(row['unknown_request_count'] for row in rows),
            unknown_request_count_is_lower_bound=any(row.get('unknown_request_count_is_lower_bound') for row in rows),
            pending_stage_count=sum(row['state'] in ('started','observed_balance_pending','observed_cleanup_unconfirmed') for row in value['stages']))
        value['requests']=None if any(row.get('requests') is None for row in rows) else value['known_requests_subtotal']
        value['request_count_upper_bound']=value['historical_requests']+sum(
            row.get('requests') if _integer(row.get('requests')) else row['reserved_requests']
            for row in value['stages'])
        value['reserved_cny']=_number(sum((_decimal(row['reserved_cny']) for row in value['stages']
            if row['state'] in ('started','observed_balance_pending','observed_cleanup_unconfirmed')),Decimal(0)))

    def _refresh(self,value):
        observation=dict(captured_at=self._now())
        try:available,balance=cny_balance(self.fetcher())
        except Exception as error:
            reason=error.reason if isinstance(error,BalanceUnavailable) else 'balance_fetch_failed_'+type(error).__name__
            value['observations'].append(dict(observation,valid=False,reason=reason))
            value['consecutive_balance_failures']+=1
            value.update(status='stopped',stop_reason=reason)
            return False
        value['consecutive_balance_failures']=0
        observation.update(valid=True,is_available=available,balance_cny=_number(balance))
        if value['baseline_balance_cny'] is None:
            allocation=(min(_decimal(self.policy['authorized_total_cny'])-_decimal(self.policy['prior_account_debit_cny']),
                           max(balance-_decimal(self.policy['reserve_cny']),Decimal(0)))
                        if self.policy['authorized_total_cny'] is not None else None)
            value.update(baseline_balance_cny=_number(balance),allocated_new_cny=None if allocation is None else _number(allocation))
            if self.policy['recovery_receipt']:
                value['reconciliation']=dict(previous_ledger_file_sha256=self.policy['recovery_receipt']['previous_ledger_file_sha256'],
                    previous_unknown_requests=value['historical_unknown_requests'],observed_at=observation['captured_at'],
                    fresh_balance_cny=_number(balance),prior_account_debit_cny=self.policy['prior_account_debit_cny'],
                    basis='explicit historical receipt plus fresh official CNY balance; unknown tokens remain unknown')
        else:
            change=_decimal(value['last_balance_cny'])-balance
            field='observed_decrease_cny' if change>=0 else 'observed_increase_cny'
            value[field]=_number(_decimal(value[field])+abs(change))
            observation.update(decrease_cny=_number(max(change,Decimal(0))),increase_cny=_number(max(-change,Decimal(0))))
        value['last_balance_cny']=_number(balance);value['observations'].append(observation)
        if not available:
            value.update(status='stopped',stop_reason='provider_balance_unavailable');return False
        # A new successful observation can settle already stopped/clean actors.
        for row in value['stages']:
            if row['state']=='observed_balance_pending' and row.get('clean_stop_verified'):
                row.update(state='settled',balance_confirmed_at=observation['captured_at'],
                           balance_observation_index=len(value['observations'])-1)
        return True

    def _reason(self,value,*,admission=False):
        self._totals(value)
        if value['permanent_stop_reason']:return value['permanent_stop_reason']
        if value['circuit_open']:return 'infrastructure_circuit_open'
        if (self.path.parent/'STOP_REQUESTED').exists():return 'run_stop_requested'
        if any(row['state']=='observed_cleanup_unconfirmed' for row in value['stages']):return 'native_cleanup_unconfirmed'
        if value['baseline_balance_cny'] is None:return 'balance_baseline_unavailable'
        cash=_decimal(value['last_balance_cny'])-_decimal(self.policy['reserve_cny'])
        remaining=cash if self.policy['authorized_total_cny'] is None else _decimal(value['allocated_new_cny'])-_decimal(value['observed_decrease_cny'])
        if min(cash,remaining)<=0:return 'live_spend_limit'
        if admission:
            if value['pending_stage_count']>=self.policy['max_inflight_stages']:return 'inflight_stage_limit'
            if min(cash,remaining)-_decimal(value['reserved_cny'])<_decimal(self.policy['inflight_reservation_cny']):
                return 'inflight_reserve_unavailable'
        if value['request_count_upper_bound']+REQUEST_RESERVATION>self.policy['max_requests']:
            return 'global_request_limit'
        return None

    def _initial_locked(self):
        if self.path.exists():return self._load()
        self._verify_history();value=self._fresh();ok=self._refresh(value)
        if ok:
            reason=self._reason(value);value.update(status='stopped' if reason else 'active',stop_reason=reason)
        self._save(value)
        return value

    def initialize(self):
        with self._lock():return self._save(self._initial_locked())

    def audit_balance(self):
        """Refresh currency evidence without inventing or reserving a model stage."""
        with self._lock():
            value=self._initial_locked()
            if not self._refresh(value):
                return dict(allowed=False,reason=value['stop_reason'],ledger=self._save(value))
            reason=self._reason(value)
            value.update(status='stopped' if reason else 'active',stop_reason=reason)
            return dict(allowed=reason is None,reason=reason,ledger=self._save(value))

    @staticmethod
    def _identifier(stage_id):
        if not isinstance(stage_id,str) or not stage_id or len(stage_id)>2048 or any(ord(c)<32 for c in stage_id):
            raise BudgetError('Stage identifier must be a nonempty immutable text identifier')
        return stage_id

    def before_stage(self,stage_id):
        identifier=self._identifier(stage_id)
        with self._lock():
            value=self._initial_locked()
            if any(row['stage_id']==identifier for row in value['stages']):
                return dict(allowed=False,reason='stage_already_registered',ledger=self._save(value))
            if (self.path.parent/'STOP_REQUESTED').exists():
                value.update(status='stopped',stop_reason='run_stop_requested')
                return dict(allowed=False,reason='run_stop_requested',ledger=self._save(value))
            if not self._refresh(value):return dict(allowed=False,reason=value['stop_reason'],ledger=self._save(value))
            reason=self._reason(value,admission=True)
            if reason:
                value.update(status='stopped',stop_reason=reason)
                return dict(allowed=False,reason=reason,ledger=self._save(value))
            value['stages'].append(dict(stage_id=identifier,state='started',started_at=self._now(),
                reserved_cny=self.policy['inflight_reservation_cny'],reserved_requests=REQUEST_RESERVATION,
                result_sha256=None,requests=None,tokens=None,observed_tokens=None,
                usage_incomplete=None,unknown_request_count=None,clean_stop_verified=False))
            value.update(status='active',stop_reason=None)
            return dict(allowed=True,reason=None,ledger=self._save(value))

    def observe(self,result,stage_id):
        identifier=self._identifier(stage_id)
        if not isinstance(result,dict):raise BudgetError('A model result object is required')
        try:evidence=_digest(result)
        except (ValueError,TypeError):raise BudgetError('Model result must be JSON serializable') from None
        with self._lock():
            value=self._load();row=next((row for row in value['stages'] if row['stage_id']==identifier),None)
            if row is None:raise BudgetError('Observe requires a previously admitted stage')
            if row.get('abandoned_proof') is not None:raise BudgetError('An abandoned stage cannot be observed or redispatched')
            if row['result_sha256'] is not None:
                if row['result_sha256']!=evidence:raise BudgetError('A stage cannot be re-accounted with changed evidence')
            else:
                requests=result.get('requests');requests=requests if _integer(requests) else None
                token=_tokens(result.get('tokens'));observed=_tokens(result.get('observed_tokens'))
                complete=(requests is not None and result.get('usage_incomplete') is False
                    and result.get('unknown_usage_requests',0)==0 and token is not None
                    and all(_integer(token[key]) for key in TOKEN_FIELDS))
                if complete and (token['cached_input_tokens']>token['input_tokens']
                        or token['reasoning_output_tokens']>token['output_tokens']
                        or requests==0 and any(token.values())):complete=False
                unknown=result.get('unknown_usage_requests')
                unknown_exact=_integer(unknown)
                unknown=unknown if unknown_exact else (0 if complete else 1)
                if not complete and unknown==0:unknown=1;unknown_exact=False
                reported_requests=requests
                if requests is not None and unknown>requests:
                    requests=None  # Contradictory counters cannot reduce the reserved upper bound.
                clean=_clean_stop(result);receipt=result.get('native_receipt') or {}
                if not isinstance(receipt,dict):receipt={}
                failure=result.get('failure_type')
                infra=(not complete or not clean or receipt.get('infrastructure_valid') is False
                    or bool(receipt.get('failure_class')) or failure in
                    ('timeout','infrastructure_error','transient_transport_error','accounting_incomplete'))
                row.update(observed_at=self._now(),result_sha256=evidence,requests=requests,reported_requests=reported_requests,tokens=token,
                    observed_tokens=observed,usage_incomplete=not complete,unknown_request_count=unknown,
                    unknown_request_count_is_lower_bound=not unknown_exact,clean_stop_verified=clean,
                    infrastructure_failure=infra,state='observed_balance_pending' if clean else 'observed_cleanup_unconfirmed')
                value['consecutive_infrastructure_failures']=value['consecutive_infrastructure_failures']+1 if infra else 0
                if value['consecutive_infrastructure_failures']>=3:value['circuit_open']=True
                if requests is not None and requests>row['reserved_requests']:
                    value['permanent_stop_reason']='stage_request_reservation_exceeded'
            ok=self._refresh(value)
            if ok:
                reason=self._reason(value);value.update(status='stopped' if reason else 'active',stop_reason=reason)
            return self._save(value)

    def reconcile_abandoned(self,stage_id,proof):
        identifier=self._identifier(stage_id)
        required={'no_live_processes','native_cleanup_confirmed','evidence_sha256','checked_at'}
        if (not isinstance(proof,dict) or set(proof)!=required or proof.get('no_live_processes') is not True
                or proof.get('native_cleanup_confirmed') is not True or not _hash(proof.get('evidence_sha256'))
                or not _timestamp(proof.get('checked_at'))):
            raise BudgetError('Explicit verified-stop evidence is required to reconcile an abandoned stage')
        with self._lock():
            value=self._load();row=next((row for row in value['stages'] if row['stage_id']==identifier),None)
            if row is None or row['state']=='settled':raise BudgetError('Only a pending registered stage may be reconciled')
            if row.get('abandoned_proof') is not None and row['abandoned_proof']!=proof:
                raise BudgetError('Abandoned-stage stop evidence cannot change')
            if row['result_sha256'] is None:
                row.update(result_sha256=_digest(dict(abandoned=True,proof=proof)),observed_at=self._now(),
                    requests=None,tokens=None,observed_tokens=None,usage_incomplete=True,
                    unknown_request_count=1,unknown_request_count_is_lower_bound=True,infrastructure_failure=True)
                value['consecutive_infrastructure_failures']+=1
                if value['consecutive_infrastructure_failures']>=3:value['circuit_open']=True
            row.update(abandoned_proof=deepcopy(proof),clean_stop_verified=True,state='observed_balance_pending')
            ok=self._refresh(value)
            if ok:
                reason=self._reason(value);value.update(status='stopped' if reason else 'active',stop_reason=reason)
            return self._save(value)

    def summary(self):
        with self._lock():
            value=self._load();self._totals(value)
            remaining=(_number(max(Decimal(0),_decimal(value['last_balance_cny'])-_decimal(self.policy['reserve_cny'])))
                if self.policy['authorized_total_cny'] is None and value['last_balance_cny'] is not None else
                None if value['allocated_new_cny'] is None else _number(max(Decimal(0),min(
                _decimal(value['allocated_new_cny'])-_decimal(value['observed_decrease_cny']),
                _decimal(value['last_balance_cny'])-_decimal(self.policy['reserve_cny'])))))
            return dict(status=value['status'],reason=value['stop_reason'],requests=value['requests'],
                known_requests_subtotal=value['known_requests_subtotal'],request_count_upper_bound=value['request_count_upper_bound'],
                max_requests=self.policy['max_requests'],incomplete_usage=value['incomplete_usage'],
                unknown_request_count=value['unknown_request_count'],
                unknown_request_count_is_lower_bound=value['unknown_request_count_is_lower_bound'],
                tokens=deepcopy(value['tokens']),observed_tokens=deepcopy(value['observed_tokens']),
                authorized_total_cny=self.policy['authorized_total_cny'],prior_account_debit_cny=self.policy['prior_account_debit_cny'],
                reserve_cny=self.policy['reserve_cny'],allocated_new_cny=value['allocated_new_cny'],
                last_balance_cny=value['last_balance_cny'],observed_decrease_cny=value['observed_decrease_cny'],
                remaining_authorization_cny=remaining,reserved_cny=value['reserved_cny'],pending_stage_count=value['pending_stage_count'],
                circuit_open=value['circuit_open'],consecutive_infrastructure_failures=value['consecutive_infrastructure_failures'],
                balance_observation_caveat='Last observed account balance; not a per-request invoice or provider hard cap')
