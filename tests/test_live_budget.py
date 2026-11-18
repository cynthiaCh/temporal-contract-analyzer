"""Balance guards use injected provider receipts; these tests never contact a service."""
from copy import deepcopy
from decimal import Decimal
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from temporal_contract_analyzer.live_budget import (
    BalanceUnavailable, BudgetError, LiveBudget, cny_balance,
    estimate_tokens_cny, fetch_provider_balance)


def balance(amount='249', available=True):
    return dict(is_available=available, balance_infos=[dict(currency='CNY', total_balance=amount)])


class LiveBudgetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)/'budget.json'
        self.fetch = Mock(return_value=balance())
        self.guard = LiveBudget(self.path, prior_spend_cny='5.4210576', fetcher=self.fetch,
                                clock=lambda: '2026-11-15T02:00:00+00:00')

    def test_initial_allocation_reserves_balance_and_prior_spend(self):
        ledger = self.guard.initialize()
        self.assertEqual(ledger['allocated_new_cny'], '239')
        self.assertTrue(self.guard.before_stage('first')['allowed'])
        other = LiveBudget(Path(self.temp.name)/'second.json', prior_spend_cny='20', fetcher=self.fetch)
        self.assertEqual(other.initialize()['allocated_new_cny'], '230')

    def test_balance_increase_never_increases_authorized_run_allocation(self):
        self.guard.initialize()
        self.fetch.return_value = balance('200')
        self.assertTrue(self.guard.before_stage('a')['allowed'])
        self.fetch.return_value = balance('300')
        self.assertTrue(self.guard.before_stage('b')['allowed'])
        summary = self.guard.summary()
        self.assertEqual(summary['allocated_new_cny'], '239')
        self.assertEqual(summary['observed_decrease_cny'], '49')
        self.assertEqual(summary['remaining_authorization_cny'], '190')
        self.fetch.return_value = balance('109')
        denied = self.guard.before_stage('c')
        self.assertFalse(denied['allowed'])
        self.assertEqual(denied['reason'], 'live_spend_limit')

    def test_reserve_stops_even_when_provider_says_account_available(self):
        self.guard.initialize(); self.fetch.return_value = balance('10')
        self.assertEqual(self.guard.before_stage('a')['reason'], 'live_spend_limit')

    def test_provider_unavailable_and_malformed_currency_fail_closed(self):
        self.guard.initialize(); self.fetch.return_value = balance('200', False)
        self.assertEqual(self.guard.before_stage('a')['reason'], 'provider_balance_unavailable')
        self.fetch.return_value = dict(is_available=True, balance_infos=[dict(currency='USD', total_balance='50')])
        self.assertEqual(self.guard.before_stage('a')['reason'], 'unique_cny_balance_required')

    def test_transport_errors_do_not_expose_exception_or_secret(self):
        self.guard.initialize(); self.fetch.side_effect = RuntimeError('sk-DO-NOT-LOG-THIS')
        denied = self.guard.before_stage('a')
        self.assertFalse(denied['allowed'])
        self.assertNotIn('sk-DO-NOT-LOG-THIS', self.path.read_text())
        self.assertEqual(denied['reason'], 'balance_fetch_failed_RuntimeError')

    def test_failed_initial_balance_can_recover_without_resetting_any_spend(self):
        self.fetch.side_effect = BalanceUnavailable('network_unavailable')
        self.assertFalse(self.guard.before_stage('a')['allowed'])
        self.fetch.side_effect = None
        self.assertTrue(self.guard.before_stage('a')['allowed'])
        self.assertEqual(self.guard.summary()['allocated_new_cny'], '239')

    def test_incomplete_usage_blocks_future_calls_without_querying_provider(self):
        self.guard.initialize()
        self.guard.observe(dict(requests=1, tokens=None), 'a')
        before = self.fetch.call_count
        self.assertFalse(self.guard.before_stage('b')['allowed'])
        self.assertEqual(self.fetch.call_count, before)
        self.assertTrue(self.guard.summary()['incomplete_usage'])

    def test_usage_is_idempotent_but_changed_reaccounting_is_rejected(self):
        self.guard.initialize()
        usage = dict(requests=2, tokens=dict(input_tokens=1000000, cached_input_tokens=800000,
                                           output_tokens=100000, reasoning_output_tokens=90000))
        one = self.guard.observe(usage, 'a'); two = self.guard.observe(usage, 'a')
        self.assertEqual(one['requests'], two['requests'])
        self.assertEqual(two['audit_peak_cache_aware_cny'], '1.4784')
        changed = deepcopy(usage); changed['requests'] = 3
        with self.assertRaisesRegex(BudgetError, 're-accounted'):
            self.guard.observe(changed, 'a')
        self.assertEqual(self.guard.before_stage('a')['reason'], 'stage_already_accounted')

    def test_zero_dispatch_does_not_fabricate_token_usage(self):
        self.guard.initialize()
        value = self.guard.observe(dict(requests=0, tokens=None), 'blocked-before-dispatch')
        self.assertFalse(value['incomplete_usage']); self.assertEqual(value['requests'], 0)

    def test_positive_tokens_without_a_request_are_unknown_usage(self):
        self.guard.initialize()
        value = self.guard.observe(dict(requests=0, tokens=dict(input_tokens=1, output_tokens=1)), 'contradiction')
        self.assertTrue(value['incomplete_usage'])

    def test_untrusted_balance_error_reason_is_not_written_to_receipt(self):
        self.guard.initialize(); self.fetch.side_effect = BalanceUnavailable('sk-DO-NOT-LOG-THIS')
        denied = self.guard.before_stage('a')
        self.assertEqual(denied['reason'], 'balance_unavailable')
        self.assertNotIn('sk-DO-NOT-LOG-THIS', self.path.read_text())

    def test_cached_input_and_reasoning_are_not_double_charged(self):
        tokens = dict(input_tokens=1000000, cached_input_tokens=1000000,
                      output_tokens=1000000, reasoning_output_tokens=800000)
        self.assertEqual(estimate_tokens_cny(tokens), Decimal('9.648'))
        tokens.pop('cached_input_tokens')
        self.assertEqual(estimate_tokens_cny(tokens), Decimal('12'))
        tokens['cached_input_tokens'] = 1000001
        with self.assertRaises(BudgetError):estimate_tokens_cny(tokens)

    def test_modified_receipt_and_policy_drift_are_rejected(self):
        self.guard.initialize()
        with self.assertRaisesRegex(BudgetError, 'authorization changed'):
            LiveBudget(self.path, prior_spend_cny=0, fetcher=self.fetch).initialize()
        value = json.loads(self.path.read_text()); value['allocated_new_cny'] = '999'
        self.path.write_text(json.dumps(value))
        with self.assertRaisesRegex(BudgetError, 'receipt or authorization changed'):
            self.guard.summary()

    def test_invalid_money_and_duplicate_currency_are_rejected(self):
        for amount in ['NaN', '-1', 'Infinity', True, 'not-money']:
            with self.subTest(amount=amount), self.assertRaises(BudgetError):
                LiveBudget(self.path, authorized_total_cny=amount)
        for response in [balance('NaN'), dict(is_available=True, balance_infos=balance()['balance_infos']*2)]:
            with self.assertRaises(BalanceUnavailable):cny_balance(response)

    def test_default_fetch_uses_env_auth_without_returning_it(self):
        response = Mock(); response.status = 200; response.read.return_value = json.dumps(balance()).encode()
        opener = Mock(); opener.return_value.__enter__ = Mock(return_value=response)
        opener.return_value.__exit__ = Mock(return_value=False)
        with patch.dict(os.environ, DEEPSEEK_API_KEY='SYNTHETIC_TEST_SECRET'):
            result = fetch_provider_balance(opener=opener)
        request = opener.call_args.args[0]
        self.assertEqual(request.get_header('Authorization'), 'Bearer SYNTHETIC_TEST_SECRET')
        self.assertNotIn('SYNTHETIC_TEST_SECRET', json.dumps(result))
        self.assertEqual(opener.call_args.kwargs['timeout'], 20)


if __name__ == '__main__':unittest.main()
