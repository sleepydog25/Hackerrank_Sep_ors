import csv
import sys
import tempfile
import unittest
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal as D
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'code'))
from test_core import profile, request, event, run, START
from buy_or_wait.models import Payment, PaymentOption
from buy_or_wait.recommendation import Candidate, select_candidate, rank, status
from buy_or_wait.plan_validation import validate_candidate
from buy_or_wait.submission import OUTPUT_COLUMNS, validate_output, write_output
from buy_or_wait.load import load_dataset


def offer(amount='350', fee='0', count=2, frequency=5, id='offer_a'):
    return PaymentOption(id, 'question', 'installments', D(amount), count, START,
                         frequency, D(fee), D(amount)*count)


class PlanTests(unittest.TestCase):
    def context(self, balance='1000', events=(), methods=('full_payment',), partial=False):
        p = replace(profile(balance), payment_methods_user_will_consider=frozenset(methods),
                    max_installment_months=3 if 'installments' in methods else None)
        q = replace(request(), allows_partial_payment=partial)
        return p, q, run(events, p, q)

    def salary(self, amount='1000', day=5):
        return event('salary', amount, START+timedelta(days=day), direction='credit',
                     category='salary', description='Next confirmed salary', event_type='income')

    def test_full_payment(self):
        p,q,b = self.context()
        c = select_candidate(p,q,b,())
        self.assertEqual(c.method, 'full_payment')
        self.assertEqual(status(c), 'affordable_now')

    def test_wait_contains_future_full_payment(self):
        p,q,b = self.context('500', (self.salary(),))
        c = select_candidate(p,q,b,())
        self.assertEqual(c.method, 'wait')
        self.assertEqual(c.payments, (Payment(START+timedelta(days=5),D('700')),))
        self.assertEqual(status(c), 'affordable_later')

    def test_partial_combined_plan(self):
        p,q,b = self.context('500',(self.salary(),),('full_payment','partial_payment'),True)
        c = select_candidate(p,q,b,())
        self.assertEqual(c.method, 'partial_payment')
        self.assertEqual([x.amount for x in c.payments], [D('400'),D('300')])
        self.assertEqual(status(c), 'affordable_with_plan')

    def test_partial_not_permitted(self):
        p,q,b = self.context('500',(self.salary(),),('partial_payment',),False)
        self.assertIsNone(select_candidate(p,q,b,()))

    def test_installment_exact_match(self):
        p,q,b = self.context(methods=('installments',))
        c = select_candidate(p,q,b,(offer(),))
        self.assertEqual(c.method, 'installments')
        self.assertTrue(validate_candidate(replace(c,payments=(Payment(START,D('349')),c.payments[1])),p,q,b,(offer(),)))

    def test_installment_financing_fee(self):
        p,q,b = self.context(methods=('installments',))
        o = offer('360','20')
        c = select_candidate(p,q,b,(o,))
        self.assertEqual(sum(x.amount for x in c.payments),D('720'))
        self.assertFalse(validate_candidate(c,p,q,b,(o,)))

    def test_deadline_rejection(self):
        p,q,b = self.context('500',(self.salary(day=11),))
        self.assertIsNone(select_candidate(p,q,b,()))
        self.assertEqual(b.earliest_date_for_full_payment,START+timedelta(days=11))

    def test_installment_deadline_and_duration(self):
        p,q,b = self.context(methods=('installments',))
        self.assertIsNone(select_candidate(p,q,b,(offer(frequency=11),)))
        q = replace(q, desired_completion_date=START+timedelta(days=90))
        p = replace(p,max_installment_months=1)
        self.assertIsNone(select_candidate(p,q,b,(offer(frequency=30),)))

    def test_method_preference_rejection_preserves_capacity(self):
        p,q,b = self.context(methods=('partial_payment',))
        self.assertIsNone(select_candidate(p,q,b,()))
        self.assertEqual(b.earliest_date_for_full_payment,START)

    def test_unsafe_future_balance(self):
        p,q,b = self.context(events=(event(amount='500',day=START+timedelta(days=40)),))
        c = Candidate('full_payment',(Payment(START,D('700')),),'USD')
        self.assertTrue(validate_candidate(c,p,q,b,()))
        self.assertIsNone(select_candidate(p,q,b,()))

    def test_combined_installments_not_independently_safe(self):
        p,q,b = self.context('700',methods=('installments',))
        self.assertGreaterEqual(b.amount_safe_to_pay,D('350'))
        self.assertIsNone(select_candidate(p,q,b,(offer(),)))

    def test_not_affordable(self):
        p,q,b = self.context('100')
        self.assertEqual(status(select_candidate(p,q,b,())), 'not_affordable')

    def test_amount_bounds(self):
        for balance in ('0','100','100.009','800','10000'):
            p,q,b = self.context(balance)
            self.assertGreaterEqual(b.amount_safe_to_pay,0)
            self.assertLessEqual(b.amount_safe_to_pay,q.requested_amount)

    def test_spending_change_legality_fails_closed(self):
        p,q,b = self.context()
        c = select_candidate(p,q,b,())
        for changes in [('stop:unknown',),('reduce_to:bill:0',),
                        ('stop:bill','reduce_to:bill:1'),tuple(f'stop:{n}' for n in range(4))]:
            self.assertTrue(validate_candidate(replace(c,changes=changes),p,q,b,()))

    def test_currency_nonfinite_and_chronology(self):
        p,q,b = self.context(methods=('installments',))
        c = select_candidate(p,q,b,(offer(),))
        for bad in (replace(c,currency='EUR'), replace(c,payments=c.payments[::-1]),
                    replace(c,payments=(Payment(START,D('NaN')),))):
            self.assertTrue(validate_candidate(bad,p,q,b,(offer(),)))

    def test_intraday_breach_cannot_be_hidden_by_salary(self):
        p,q,b = self.context('500',(event(amount='450'),self.salary()))
        self.assertIsNone(select_candidate(p,q,b,()))

    def test_missing_cash_amount_cannot_certify_plan(self):
        p,q,b = self.context(events=(event(amount=None),))
        self.assertIsNone(select_candidate(p,q,b,()))

    def test_ranking_cost_then_start_then_count_then_option(self):
        p,q,b = self.context(methods=('installments','full_payment'))
        self.assertEqual(select_candidate(p,q,b,(offer('360','20'),)).method,'full_payment')
        p = replace(p,payment_methods_user_will_consider=frozenset({'installments'}))
        self.assertEqual(select_candidate(p,q,b,(offer(id='offer_b'),offer())).option_id,'offer_a')


class OutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_dataset(Path(__file__).resolve().parents[1]/'dataset')

    def test_250_rows_schema_and_repeatability(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'output.csv'
            rows = write_output(self.data,path)
            self.assertEqual(len(rows),250)
            self.assertEqual(tuple(rows[0]),OUTPUT_COLUMNS)
            self.assertEqual(validate_output(self.data,path),rows)
            original = path.read_bytes()
            write_output(self.data,path)
            self.assertEqual(path.read_bytes(),original)

    def test_validator_rejects_corruption(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'output.csv'
            rows = write_output(self.data,path)
            for field,value in [('amount_safe_to_pay','NaN'),('request_id','absent'),
                                ('earliest_date_for_full_payment','2026-99-01'),
                                ('affordability_status','unknown'),('spending_changes_needed','stop:fake')]:
                bad = [dict(r) for r in rows]
                bad[0][field] = value
                with path.open('w',newline='',encoding='utf-8') as f:
                    writer = csv.DictWriter(f,fieldnames=OUTPUT_COLUMNS)
                    writer.writeheader(); writer.writerows(bad)
                with self.assertRaises(ValueError): validate_output(self.data,path)
            path.write_text('wrong,header\n',encoding='utf-8')
            with self.assertRaises(ValueError): validate_output(self.data,path)


if __name__ == '__main__':
    unittest.main()
