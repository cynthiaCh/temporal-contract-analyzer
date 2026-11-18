"""Shared spending controls use injected official-shaped receipts, never a service."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import Mock

from temporal_contract_analyzer.balance_budget import BalanceBudget, BudgetError
from temporal_contract_analyzer.live_budget import _digest


STAMP='2026-11-15T03:00:00+00:00'


def balance(amount='100'):
    return dict(is_available=True,balance_infos=[dict(currency='CNY',total_balance=amount)])


def usage(requests=1,**overrides):
    value=dict(valid=True,requests=requests,tokens=dict(input_tokens=100,cached_input_tokens=50,
        cache_write_input_tokens=0,output_tokens=20,reasoning_output_tokens=10,total_tokens=120),
        usage_incomplete=False,unknown_usage_requests=0,
        native_receipt=dict(exit_code=0,infrastructure_valid=True,turn_complete=True,
            archive_failure_requires_stop=False,archive_status=dict(status='OK',errors=[])))
    value.update(overrides)
    return value


def worker(path,stage,barrier,queue):
    try:
        guard=BalanceBudget(path,prior_account_debit_cny=20,fetcher=balance,clock=lambda:STAMP)
        admitted=guard.before_stage(stage)
        barrier.wait(timeout=10)
        if admitted['allowed']:guard.observe(usage(2),stage)
        queue.put(dict(allowed=admitted['allowed']))
    except Exception as error:queue.put(dict(error=type(error).__name__))


@unittest.skipIf(os.name=='nt','production ledger uses Linux fcntl shared-file locks')
class BalanceBudgetTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name);self.path=self.root/'balance-budget.json'
        self.fetch=Mock(return_value=balance())
        self.guard=BalanceBudget(self.path,prior_account_debit_cny=20,fetcher=self.fetch,clock=lambda:STAMP)

    def register(self,stage='one'):
        result=self.guard.before_stage(stage)
        self.assertTrue(result['allowed'],result['reason'])
        return result

    def test_initial_reserve_and_immutable_admission_prevent_replay(self):
        ledger=self.guard.initialize()
        self.assertEqual(ledger['allocated_new_cny'],'90')
        self.register()
        self.assertEqual(self.guard.summary()['reserved_cny'],'10')
        self.assertEqual(self.guard.before_stage('one')['reason'],'stage_already_registered')
        self.guard.observe(usage(),'one')
        self.assertEqual(self.guard.summary()['reserved_cny'],'0')
        self.assertFalse(self.guard.before_stage('one')['allowed'])
        self.guard.observe(usage(),'one')
        self.assertEqual(self.guard.summary()['requests'],1)
        changed=usage();changed['tokens']['output_tokens']=21
        with self.assertRaisesRegex(BudgetError,'changed evidence'):self.guard.observe(changed,'one')

    def test_two_threads_admit_and_account_without_lost_updates(self):
        self.guard.initialize();barrier=threading.Barrier(2)
        def run(index):
            admitted=self.guard.before_stage('thread-'+str(index));barrier.wait(timeout=10)
            if admitted['allowed']:self.guard.observe(usage(2),'thread-'+str(index))
            return admitted['allowed']
        with ThreadPoolExecutor(max_workers=2) as pool:self.assertEqual(list(pool.map(run,[1,2])),[True,True])
        summary=self.guard.summary()
        self.assertEqual(summary['requests'],4)
        self.assertEqual(summary['tokens']['input_tokens'],200)
        self.assertEqual(summary['pending_stage_count'],0)
        self.assertEqual(len(json.loads(self.path.read_text())['stages']),2)

    def test_two_processes_share_the_same_lock_and_ledger(self):
        self.guard.initialize();context=multiprocessing.get_context('fork')
        barrier=context.Barrier(2);queue=context.Queue()
        jobs=[context.Process(target=worker,args=(str(self.path),'process-'+str(i),barrier,queue)) for i in [1,2]]
        for job in jobs:job.start()
        for job in jobs:job.join(timeout=15);self.assertFalse(job.is_alive());self.assertEqual(job.exitcode,0)
        self.assertEqual([queue.get(timeout=2) for _ in jobs],[dict(allowed=True),dict(allowed=True)])
        summary=self.guard.summary()
        self.assertEqual(summary['requests'],4)
        self.assertEqual(summary['observed_tokens']['output_tokens'],40)
        self.assertEqual(summary['reserved_cny'],'0')

    def test_unknown_usage_remains_null_but_fresh_balance_after_clean_stop_allows_next_stage(self):
        self.register()
        unknown=usage(valid=False,tokens=None,observed_tokens=dict(input_tokens=42,output_tokens=None),
            usage_incomplete=True,unknown_usage_requests=1,failure_type='transient_transport_error')
        unknown['native_receipt'].update(exit_code=1,infrastructure_valid=False,turn_complete=False,
            failure_class='model_or_cli_abnormal_exit')
        self.fetch.return_value=balance('99.8')
        ledger=self.guard.observe(unknown,'one')
        self.assertEqual(ledger['stages'][0]['state'],'settled')
        self.assertIsNone(ledger['stages'][0]['tokens'])
        self.assertTrue(ledger['incomplete_usage'])
        self.assertEqual(ledger['unknown_request_count'],1)
        self.assertEqual(ledger['observed_tokens']['input_tokens'],42)
        self.assertIsNone(ledger['observed_tokens']['output_tokens'])
        self.assertIsNone(ledger['tokens'])
        self.assertEqual(ledger['observed_decrease_cny'],'0.2')
        self.assertTrue(self.guard.before_stage('different-stage')['allowed'])

    def test_partial_known_tokens_are_preserved_without_claiming_complete_usage(self):
        self.register()
        partial=usage(tokens=dict(input_tokens=100,output_tokens=None),usage_incomplete=True,unknown_usage_requests=1)
        ledger=self.guard.observe(partial,'one')
        self.assertEqual(ledger['stages'][0]['tokens']['input_tokens'],100)
        self.assertIsNone(ledger['stages'][0]['tokens']['output_tokens'])
        self.assertEqual(ledger['observed_tokens']['input_tokens'],100)
        self.assertIsNone(ledger['tokens'])

    def test_balance_fetch_failure_stops_dispatch_and_idempotent_observe_can_reconcile(self):
        self.register();self.fetch.side_effect=RuntimeError('SYNTHETIC_SECRET_MUST_NOT_BE_LOGGED')
        ledger=self.guard.observe(usage(),'one')
        self.assertEqual(ledger['stages'][0]['state'],'observed_balance_pending')
        self.assertFalse(self.guard.before_stage('two')['allowed'])
        self.assertNotIn('SYNTHETIC_SECRET',self.path.read_text())
        self.fetch.side_effect=None
        self.guard.observe(usage(),'one')
        self.assertEqual(self.guard.summary()['requests'],1)
        self.assertTrue(self.guard.before_stage('two')['allowed'])

    def test_three_consecutive_infrastructure_failures_open_the_circuit(self):
        broken=usage(valid=False,tokens=None,usage_incomplete=True,unknown_usage_requests=1,failure_type='timeout')
        broken['native_receipt'].update(exit_code=1,infrastructure_valid=False)
        for index in range(3):
            stage='broken-'+str(index);self.register(stage);self.guard.observe(broken,stage)
        self.assertTrue(self.guard.summary()['circuit_open'])
        self.assertEqual(self.guard.before_stage('four')['reason'],'infrastructure_circuit_open')

    def test_completed_json_error_resets_infrastructure_circuit_without_hiding_unknowns(self):
        unknown=usage(valid=False,tokens=None,usage_incomplete=True,unknown_usage_requests=1)
        self.register('unknown');self.guard.observe(unknown,'unknown')
        self.register('schema');self.guard.observe(usage(valid=False,failure_type='structured_output_invalid'),'schema')
        self.assertEqual(self.guard.summary()['consecutive_infrastructure_failures'],0)
        self.assertTrue(self.guard.summary()['incomplete_usage'])
        self.assertEqual(self.guard.summary()['unknown_request_count'],1)

    def test_unconfirmed_cleanup_requires_explicit_abandoned_stage_reconciliation(self):
        self.register();broken=usage();broken['native_receipt']['transport_cleanup_error']='unconfirmed'
        self.guard.observe(broken,'one')
        self.assertEqual(self.guard.before_stage('two')['reason'],'native_cleanup_unconfirmed')
        with self.assertRaisesRegex(BudgetError,'verified-stop'):self.guard.reconcile_abandoned('one',dict(no_live_processes=True))
        proof=dict(no_live_processes=True,native_cleanup_confirmed=True,evidence_sha256='a'*64,checked_at=STAMP)
        self.guard.reconcile_abandoned('one',proof)
        self.assertTrue(self.guard.before_stage('two')['allowed'])
        self.assertFalse(self.guard.before_stage('one')['allowed'])

    def test_abandoned_pending_admission_never_becomes_a_zero_usage_or_replayed_stage(self):
        self.register();proof=dict(no_live_processes=True,native_cleanup_confirmed=True,evidence_sha256='a'*64,checked_at=STAMP)
        ledger=self.guard.reconcile_abandoned('one',proof)
        row=ledger['stages'][0]
        self.assertIsNone(row['requests']);self.assertIsNone(row['tokens'])
        self.assertTrue(ledger['incomplete_usage'])
        self.assertEqual(ledger['unknown_request_count'],1)
        self.assertTrue(ledger['unknown_request_count_is_lower_bound'])
        self.assertEqual(ledger['request_count_upper_bound'],24)
        self.assertFalse(self.guard.before_stage('one')['allowed'])
        with self.assertRaisesRegex(BudgetError,'abandoned'):self.guard.observe(usage(),'one')

    def test_inflight_cash_concurrency_and_global_request_reservations(self):
        self.fetch.return_value=balance('29')
        self.register('one')
        self.assertEqual(self.guard.before_stage('two')['reason'],'inflight_reserve_unavailable')
        self.guard.observe(usage(),'one');self.register('two')
        other=BalanceBudget(self.root/'limited.json',prior_account_debit_cny=20,fetcher=lambda:balance(),max_requests=48)
        self.assertTrue(other.before_stage('a')['allowed']);self.assertTrue(other.before_stage('b')['allowed'])
        self.assertEqual(other.before_stage('c')['reason'],'inflight_stage_limit')
        other.observe(usage(24),'a')
        self.assertEqual(other.before_stage('c')['reason'],'global_request_limit')
        self.assertFalse(other.audit_balance()['allowed'])
        self.assertEqual(other.summary()['reason'],'global_request_limit')

    def test_topups_never_expand_allocation_or_erase_previous_positive_debits(self):
        self.guard.initialize();self.fetch.return_value=balance('80');self.register('one')
        self.guard.observe(usage(),'one');self.fetch.return_value=balance('180');self.register('two')
        self.guard.observe(usage(),'two')
        summary=self.guard.summary()
        self.assertEqual(summary['allocated_new_cny'],'90')
        self.assertEqual(summary['observed_decrease_cny'],'20')
        self.assertEqual(summary['remaining_authorization_cny'],'70')
        self.fetch.return_value=balance('100')
        self.assertEqual(self.guard.before_stage('three')['reason'],'live_spend_limit')

    def test_policy_and_sealed_ledger_drift_fail_closed(self):
        self.guard.initialize()
        with self.assertRaisesRegex(BudgetError,'authorization changed'):
            BalanceBudget(self.path,prior_account_debit_cny=21,fetcher=self.fetch).initialize()
        value=json.loads(self.path.read_text());value['allocated_new_cny']='999';self.path.write_text(json.dumps(value))
        with self.assertRaisesRegex(BudgetError,'authorization changed'):self.guard.summary()

    def test_recovery_links_old_unknown_ledger_without_modifying_it(self):
        old=self.root/'old-v6-live-spending.json'
        previous=dict(schema_version='deepseek-live-budget-v1',incomplete_usage=True,stages=[dict(complete=False)])
        old.write_text(json.dumps(dict(previous,sha256=_digest(previous))),encoding='utf8');original=old.read_bytes()
        receipt=dict(previous_ledger_path=str(old),previous_ledger_file_sha256=hashlib.sha256(original).hexdigest(),
            previous_unknown_requests=1,previous_requests=518,reconciled_balance_cny='227.69',
            reconciled_at=STAMP,balance_receipt_sha256='b'*64)
        guard=BalanceBudget(self.root/'recovery.json',prior_account_debit_cny='22.31',
            recovery_receipt=receipt,fetcher=lambda:balance('227.69'),clock=lambda:STAMP)
        ledger=guard.initialize()
        self.assertEqual(ledger['allocated_new_cny'],'217.69')
        self.assertEqual(ledger['unknown_request_count'],1)
        self.assertTrue(ledger['incomplete_usage'])
        self.assertEqual(ledger['known_requests_subtotal'],518)
        self.assertIsNone(ledger['tokens'])
        self.assertEqual(ledger['reconciliation']['previous_ledger_file_sha256'],receipt['previous_ledger_file_sha256'])
        self.assertTrue(guard.before_stage('new-distinct-job')['allowed'])
        self.assertEqual(old.read_bytes(),original)
        old.write_bytes(original+b' ')
        with self.assertRaisesRegex(BudgetError,'Historical ledger file changed'):guard.summary()

    def test_operator_stop_is_checked_before_every_stage_without_poll_or_id_burn(self):
        self.guard.initialize();calls=self.fetch.call_count
        stop=self.root/'STOP_REQUESTED';stop.write_text('Synthetic operator stop',encoding='utf8')
        blocked=self.guard.before_stage('must-not-dispatch')
        self.assertFalse(blocked['allowed'])
        self.assertEqual(blocked['reason'],'run_stop_requested')
        self.assertEqual(self.fetch.call_count,calls)
        self.assertEqual(blocked['ledger']['stages'],[])
        self.assertFalse(self.guard.audit_balance()['allowed'])
        stop.unlink()
        self.assertTrue(self.guard.audit_balance()['allowed'])
        self.assertTrue(self.guard.before_stage('must-not-dispatch')['allowed'])

    def test_currency_only_audit_recovers_transient_fetch_failure_without_phantom_stage(self):
        self.guard.initialize();self.fetch.side_effect=RuntimeError('offline')
        blocked=self.guard.audit_balance()
        self.assertFalse(blocked['allowed'])
        self.assertEqual(blocked['ledger']['stages'],[])
        self.fetch.side_effect=None;self.fetch.return_value=balance('99')
        recovered=self.guard.audit_balance()
        self.assertTrue(recovered['allowed'])
        self.assertEqual(recovered['ledger']['observed_decrease_cny'],'1')
        self.assertEqual(recovered['ledger']['stages'],[])
        self.assertEqual(recovered['ledger']['requests'],0)
        self.assertEqual(recovered['ledger']['reserved_cny'],'0')

    def test_contradictory_request_counter_keeps_reserved_upper_bound_and_unknown_tokens(self):
        self.register()
        ledger=self.guard.observe(usage(requests=0,tokens=None,usage_incomplete=True,unknown_usage_requests=1),'one')
        self.assertIsNone(ledger['requests'])
        self.assertEqual(ledger['request_count_upper_bound'],24)
        self.assertEqual(ledger['stages'][0]['reported_requests'],0)
        self.assertIsNone(ledger['tokens'])
        self.assertEqual(ledger['unknown_request_count'],1)


if __name__=='__main__':unittest.main()
