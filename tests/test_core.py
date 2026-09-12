import sys
import unittest
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal as D
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'code'))
from buy_or_wait.models import FinancialProfile, FinancialEvent, FinanceRequest, ExchangeRate
from buy_or_wait.forecast import forecast
from buy_or_wait.fx import RateBook, MissingRate
from buy_or_wait.recurrence import infer_series
from buy_or_wait.policy import ForecastPolicy
from buy_or_wait.recurrence import monthly_date

START = date(2026, 4, 1)


def profile(balance='1000', minimum='100'):
    return FinancialProfile('person', 'USD', D(balance), D(minimum), frozenset(),
                            frozenset({'rent', 'groceries'}), frozenset(), frozenset(),
                            frozenset({'full_payment'}), None)


def request(amount='700', start=START):
    return FinanceRequest('question', 'person', start, 'purchase', D(amount),
                          start+timedelta(days=10), False, 'Synthetic purchase')


def event(id='bill', amount='200', day=START+timedelta(days=5), status='scheduled',
          direction='debit', category='rent', description='Monthly rent', linked=None,
          currency='USD', event_type='expense', settlement=None):
    return FinancialEvent(id, 'person', event_type, description, category, direction,
                          None if amount is None else D(amount), currency, day,
                          settlement or day, status, linked, 'fixed', None)


def history(category='rent', direction='debit', description='Monthly rent', amount='100'):
    return tuple(event(str(n), amount, date(2026, n, 5), 'settled', direction,
                       category, description, event_type='income' if direction=='credit' else 'expense')
                 for n in range(1, 4))


def run(events=(), p=None, q=None, rates=(), policy=None):
    kwargs={'policy':policy} if policy is not None else {}
    return forecast(p or profile(), q or request(), tuple(events), RateBook(tuple(rates)),**kwargs)


class CoreTests(unittest.TestCase):
    def test_opening_snapshot_not_replayed(self):
        result = run([event(day=START-timedelta(days=1), status='settled', amount='999')])
        self.assertEqual(result.low_water_mark, D('1000'))
        self.assertEqual(result.amount_safe_to_pay, D('700'))

    def test_pending_once_immediately(self):
        result = run([event(status='pending')], q=request('1000'))
        self.assertEqual(len(result.cash_flows), 1)
        self.assertEqual(result.cash_flows[0].date, START)
        self.assertEqual(result.ledger[-1].balance, D('800'))
        self.assertEqual(result.amount_safe_to_pay, D('700'))

    def test_duplicate_id_rejected_not_double_reserved(self):
        with self.assertRaises(ValueError):
            run([event(),event()])

    def test_month_end_and_leap_year_calendar(self):
        self.assertEqual(monthly_date(date(2024,1,31),1),date(2024,2,29))
        self.assertEqual(monthly_date(date(2024,1,31),2),date(2024,3,31))

    def test_pending_fx_uses_settlement_not_reservation_date(self):
        day=START+timedelta(days=5)
        result=run([event(currency='EUR',amount='100',status='pending',settlement=day)],
                   rates=[ExchangeRate(day,'EUR','USD',D('1.2'))])
        self.assertEqual(result.cash_flows[0].date,START)
        self.assertEqual(result.cash_flows[0].rate_date,day)
        self.assertEqual(result.ledger[-1].balance,D('880'))

    def test_pending_credit_excluded_even_salary(self):
        result = run([event(status='pending', direction='credit', category='salary',
                            description='Confirmed payroll', event_type='income')])
        self.assertFalse(result.cash_flows)

    def test_scheduled_confirmed_salary(self):
        result = run([event(direction='credit', category='salary', description='Next confirmed salary', event_type='income')])
        self.assertEqual(result.ledger[-1].balance, D('1200'))

    def test_scheduled_bonus_excluded(self):
        result = run([event(direction='credit', category='salary', description='Quarterly bonus', event_type='income')])
        self.assertFalse(result.cash_flows)

    def test_cancelled_failed_and_unrealized(self):
        result = run([event('a', status='cancelled'), event('b', status='failed'),
                      event('c', status='unrealized', direction='non_cash', event_type='investment_valuation')])
        self.assertFalse(result.cash_flows)

    def test_failed_attempt_with_linked_retry(self):
        result = run([event('failed', status='failed'), event('retry', linked='failed')])
        self.assertEqual(result.ledger[-1].balance, D('800'))

    def test_linked_reimbursement_is_distinct_cash(self):
        result = run([event('purchase', day=START-timedelta(days=2), status='settled'),
                      event('refund', status='settled', direction='credit', category='work_expense',
                            description='Reimbursement', event_type='refund', linked='purchase')])
        self.assertEqual(result.ledger[-1].balance, D('1200'))

    def test_possible_duplicate_without_reversal_reserved(self):
        result = run([event('original', day=START-timedelta(days=2), status='settled'),
                      event('disputed', status='pending', linked='original', description='Possible duplicate charge')])
        self.assertEqual(result.ledger[-1].balance, D('800'))

    def test_settled_authorization_replacement(self):
        result = run([event('hold', status='pending', description='Card authorization'),
                      event('posted', status='settled', linked='hold')])
        self.assertEqual(len(result.cash_flows), 1)
        self.assertEqual(result.ledger[-1].balance, D('800'))

    def test_monthly_rent(self):
        result = run(history())
        self.assertEqual([f.date for f in result.cash_flows], [date(2026, m, 5) for m in (4,5,6)])
        self.assertEqual(result.ledger[-1].balance, D('700'))

    def test_rent_paid_by_transfer_is_still_recurring(self):
        result = run(history(description='Apartment rent transfer'))
        self.assertEqual(result.ledger[-1].balance,D('700'))

    def test_final_payroll_ends_inferred_income(self):
        result = run([*history('salary','credit','Payroll','500'),
                      event('end','500',date(2026,3,20),'settled','credit','salary','Final employer payroll',event_type='income')])
        self.assertFalse(result.cash_flows)

    def test_monthly_salary(self):
        result = run(history('salary', 'credit', 'Payroll', '500'))
        self.assertEqual(result.ledger[-1].balance, D('2500'))
        self.assertTrue(all(f.inferred for f in result.cash_flows))

    def test_bonus_not_recurring(self):
        result = run(history('salary', 'credit', 'Monthly bonus', '500'))
        self.assertFalse(result.series)

    def test_single_purchase_not_recurring(self):
        result = run([event(day=START-timedelta(days=1), status='settled')])
        self.assertFalse(result.series)

    def test_variable_essential_category_and_outlier(self):
        rows = [event(str(n), str(amount), START-timedelta(days=28-7*n), 'settled',
                      category='groceries', description=f'Shop {n}')
                for n, amount in enumerate([70, 70, 70, 7000])]
        result = run(rows, p=profile('5000'),policy=ForecastPolicy())
        self.assertEqual(len(result.series), 1)
        self.assertEqual(result.series[0].amount, D('10'))
        self.assertEqual(sum(f.amount for f in result.cash_flows), D('910'))

    def test_explicit_salary_replaces_inferred_cycle(self):
        result = run([*history('salary','credit','Payroll','500'),
                      event('next', '500', date(2026,4,15), direction='credit', category='salary',
                            description='Next confirmed salary', event_type='income')])
        self.assertEqual(sum(f.amount for f in result.cash_flows), D('1500'))
        self.assertEqual(sum(f.date.month == 4 for f in result.cash_flows), 1)

    def test_fx_exact_settlement_date_direction(self):
        day = START+timedelta(days=5)
        result = run([event(currency='EUR', amount='100', day=START, settlement=day)],
                     rates=[ExchangeRate(day, 'EUR', 'USD', D('1.2345'))])
        self.assertEqual(result.cash_flows[0].amount, D('123.4500'))
        self.assertEqual(result.cash_flows[0].rate_date, day)
        self.assertEqual(result.cash_flows[0].rate, D('1.2345'))

    def test_fx_no_inverse_or_date_fallback(self):
        rates = RateBook((ExchangeRate(START,'USD','EUR',D('0.9')),))
        with self.assertRaises(MissingRate):
            rates.convert(D('100'),'EUR','USD',START)

    def test_missing_fx_is_explicit_issue(self):
        result = run([event(currency='EUR')])
        self.assertFalse(result.complete)
        self.assertIn('missing FX', result.issues[0])

    def test_future_bill_reduces_today_capacity(self):
        result = run([event(amount='650')], q=request('900'))
        self.assertEqual(result.amount_safe_to_pay, D('250'))
        self.assertEqual(result.low_water_mark-result.amount_safe_to_pay, D('100'))

    def test_minimum_breach_means_no_safe_payment(self):
        result = run([event(amount='950')])
        self.assertFalse(result.baseline_safe)
        self.assertEqual(result.amount_safe_to_pay, D(0))
        self.assertIsNone(result.earliest_date_for_full_payment)

    def test_same_day_debit_before_credit_and_candidate_after(self):
        rows = [event('credit', '500', START, direction='credit', category='salary',
                      description='Next salary', event_type='income'), event('debit','800',START)]
        result = run(rows, q=request('600'))
        self.assertEqual([f.direction for f in result.cash_flows], ['debit','credit'])
        self.assertEqual(result.low_water_mark, D('200'))
        self.assertEqual(result.amount_safe_to_pay,D('600'))
        self.assertEqual(result.earliest_date_for_full_payment,START)

    def test_intraday_breach_not_hidden_by_credit(self):
        rows = [event('debit','950',START), event('credit','2000',START,direction='credit',
                    category='salary',description='Next salary',event_type='income')]
        self.assertFalse(run(rows).baseline_safe)

    def test_earliest_ignores_preferences_and_deadline(self):
        day = START+timedelta(days=20)
        p = replace(profile('500'), payment_methods_user_will_consider=frozenset({'installments'}), max_installment_months=3)
        result = run([event('salary','1000',day,direction='credit', category='salary',
                            description='Next salary',event_type='income')],p=p)
        self.assertEqual(result.earliest_date_for_full_payment,day)

    def test_no_safe_full_date(self):
        self.assertIsNone(run(q=request('10000')).earliest_date_for_full_payment)

    def test_day_90_included_day_91_excluded(self):
        result = run([event('a','100',START+timedelta(days=90)),event('b','800',START+timedelta(days=91))])
        self.assertEqual(result.ledger[-1].balance,D('900'))

    def test_missing_amount_never_zero_filled(self):
        result = run([event(amount=None)])
        self.assertFalse(result.complete)
        self.assertTrue(any('missing amount' in x for x in result.issues))

    def test_safe_amount_rounds_down_to_cents(self):
        result = run(p=profile('1000.009'),q=request('9999'))
        self.assertEqual(result.amount_safe_to_pay,D('900.00'))

    def test_input_order_does_not_change_result(self):
        rows = [event('a','250'),event('b','100')]
        self.assertEqual(run(rows),run(rows[::-1]))

    def test_capacity_matches_independent_payment_replay(self):
        result = run([event('rent','600'),event('salary','300', START+timedelta(days=15),
                    direction='credit',category='salary',description='Salary',event_type='income')],q=request('1000'))
        after_close = False
        for row in result.ledger:
            if row.date == START and row.source == 'close':
                after_close = True
            adjusted = row.balance-result.amount_safe_to_pay if after_close else row.balance
            self.assertGreaterEqual(adjusted,result.minimum_balance)
        # One extra cent must fail at a future minimum checkpoint.
        self.assertTrue(any(r.balance-result.amount_safe_to_pay-D('.01') < result.minimum_balance
                            for r in result.ledger if r.date > START))


if __name__ == '__main__':
    unittest.main()
