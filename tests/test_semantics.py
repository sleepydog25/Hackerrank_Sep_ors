"""Contract tests: permissions do not change baseline cash; safety persists."""
import unittest
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal as D
from test_core import START, event, history, profile, request, run
from test_calibration import groceries, payroll


class ForecastSemanticsTests(unittest.TestCase):
    def test_both_day89_and_day90_debits_are_reserved(self):
        result=run([event('before','200',START+timedelta(days=89)),
                    event('endpoint','300',START+timedelta(days=90))],q=request('900'))
        self.assertEqual(result.amount_safe_to_pay,D(400))
        self.assertEqual(result.end,START+timedelta(days=90))
        self.assertEqual(sum(r.source=='close' for r in result.ledger),91)

    def test_full_payment_exactly_on_endpoint(self):
        endpoint=START+timedelta(days=90)
        rows=[payroll('salary',endpoint,'500','Confirmed salary','scheduled'),
              event('outside','1000',endpoint+timedelta(days=1))]
        result=run(rows,p=profile('200'),q=request('600'))
        self.assertEqual(result.earliest_date_for_full_payment,endpoint)
        self.assertEqual(result.amount_safe_to_pay,D(100))

    def test_income_outside_endpoint_cannot_create_date(self):
        result=run([payroll('late',START+timedelta(days=91),'500','Confirmed salary','scheduled')],
                   p=profile('200'),q=request('600'))
        self.assertIsNone(result.earliest_date_for_full_payment)

    def test_protected_variable_spending_keeps_full_budget(self):
        result=run(groceries(),p=profile('2000'),q=request('2000'))
        self.assertEqual(result.amount_safe_to_pay,D(990))

    def test_unprotected_variable_is_not_automatically_free(self):
        p=replace(profile('2000'),expense_categories_to_protect=frozenset())
        result=run(groceries(),p=p,q=request('2000'))
        self.assertEqual(result.amount_safe_to_pay,D(990))

    def test_reduce_permission_is_not_an_actual_reduction(self):
        p=replace(profile('2000'),expense_categories_to_protect=frozenset(),
                  expense_categories_user_is_willing_to_reduce=frozenset({'groceries'}))
        rows=[replace(e,flexibility='reducible',minimum_allowed_amount=D(7)) for e in groceries()]
        self.assertEqual(run(rows,p=p,q=request('2000')).amount_safe_to_pay,D(990))

    def test_stop_permission_is_not_a_cancellation(self):
        p=replace(profile(),expense_categories_user_is_willing_to_stop=frozenset({'streaming'}))
        rows=[replace(e,flexibility='stoppable') for e in history(category='streaming',description='Video service')]
        self.assertEqual(run(rows,p=p,q=request('900')).amount_safe_to_pay,D(600))

    def test_protect_permission_overlap_does_not_lower_baseline(self):
        p=replace(profile('2000'),expense_categories_user_is_willing_to_reduce=frozenset({'groceries'}),
                  expense_categories_user_is_willing_to_stop=frozenset({'groceries'}))
        self.assertEqual(run(groceries(),p=p,q=request('2000')).amount_safe_to_pay,D(990))

    def test_flexible_minimum_is_not_baseline_amount(self):
        rows=[replace(e,flexibility='reducible',minimum_allowed_amount=D(10)) for e in history(category='gym',description='Fitness membership')]
        result=run(rows,q=request('900'))
        self.assertEqual(sum(f.amount for f in result.cash_flows),D(300))
        self.assertEqual(result.amount_safe_to_pay,D(600))

    def test_mandatory_fixed_bill_reserved_without_profile_protection(self):
        p=replace(profile(),expense_categories_to_protect=frozenset())
        self.assertEqual(run([event(amount='400')],p=p,q=request('900')).amount_safe_to_pay,D(500))

    def test_earliest_waits_for_salary_after_essential_debit(self):
        bill=START+timedelta(days=10)
        payday=START+timedelta(days=20)
        result=run([event('essential','400',bill),payroll('salary',payday,'500','Confirmed salary','scheduled')])
        self.assertEqual(result.amount_safe_to_pay,D(500))
        self.assertEqual(result.earliest_date_for_full_payment,payday)
        # Instantaneous cash could fund 700 today; continuing safety cannot.
        self.assertGreaterEqual(result.opening_balance-D(700),result.minimum_balance)

    def test_later_salary_does_not_repair_prior_breach(self):
        result=run([event('essential','950',START+timedelta(days=10)),
                    payroll('salary',START+timedelta(days=20),'1000','Confirmed salary','scheduled')])
        self.assertFalse(result.baseline_safe)
        self.assertIsNone(result.earliest_date_for_full_payment)

    def test_same_day_debit_credit_then_payment_all_checked(self):
        rows=[event('essential','800',START),payroll('salary',START,'500','Confirmed salary','scheduled')]
        result=run(rows,q=request('600'))
        actual=[r for r in result.ledger if r.source in ('essential','salary','close')][:3]
        self.assertEqual([r.source for r in actual],['essential','salary','close'])
        self.assertEqual(result.amount_safe_to_pay,D(600))
        self.assertEqual(result.earliest_date_for_full_payment,START)

    def test_optional_permissions_change_neither_amount_nor_date(self):
        rows=[event('essential','400',START+timedelta(days=10)),
              payroll('salary',START+timedelta(days=20),'500','Confirmed salary','scheduled')]
        base=run(rows)
        p=replace(profile(),expense_categories_user_is_willing_to_reduce=frozenset({'rent'}),
                  expense_categories_user_is_willing_to_stop=frozenset({'rent'}))
        alternative=run(rows,p=p)
        self.assertEqual(base.amount_safe_to_pay,alternative.amount_safe_to_pay)
        self.assertEqual(base.earliest_date_for_full_payment,alternative.earliest_date_for_full_payment)
