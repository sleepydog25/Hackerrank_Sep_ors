"""Adversarial synthetic cases from the Checkpoint D read-only review."""
import unittest
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal as D
from test_core import START, event, history, profile, request, run
from test_calibration import payroll
from test_evidence import candidate, source
from test_evidence_integration import integrate, salary_rows
from test_evidence_reconciliation import context
from buy_or_wait.evidence import *
from buy_or_wait.evidence_integration import forecast_with_evidence
from buy_or_wait.evidence_reconciliation import reconcile_evidence
from buy_or_wait.evidence_validation import validate
from buy_or_wait.fx import RateBook


class EvidenceReviewTests(unittest.TestCase):
    def test_historical_rent_amendment_updates_explicit_and_inferred_occurrences(self):
        rows=(*history(),event('next','100',date(2026,4,5)))
        c=candidate(source=source(rows[0].event_id),fact_type=FactType.RENT,
                    amount_meaning=AmountMeaning.BALANCE_DUE,amount=D(150),
                    scope=Scope.ONGOING,payment_date=date(2026,4,5),explicit_amendment=True)
        result=integrate(c,rows)
        self.assertTrue(result.forecast.complete,result.forecast.issues)
        self.assertEqual([f.amount for f in result.forecast.cash_flows],[D(150)]*3)
        self.assertEqual(result.forecast.cash_flows[0].source,'next')
        self.assertEqual(result.forecast.ledger[-1].balance,D(550))
        self.assertTrue(all('message -> fact' in f.reason for f in result.forecast.cash_flows))

    def test_until_date_does_not_change_later_explicit_bill(self):
        rows=(*history(),event('april','100',date(2026,4,5)),event('may','100',date(2026,5,5)))
        c=candidate(source=source(rows[0].event_id),fact_type=FactType.RENT,
                    amount_meaning=AmountMeaning.BALANCE_DUE,amount=D(150),scope=Scope.UNTIL_DATE,
                    period_end=date(2026,4,30),payment_date=date(2026,4,5),explicit_amendment=True)
        r=integrate(c,rows).forecast
        self.assertTrue(r.complete,r.issues)
        self.assertEqual([f.amount for f in r.cash_flows],[D(150),D(100),D(100)])

    def test_cross_event_conflicting_series_amendments_are_atomic_and_order_independent(self):
        rows=history()
        a=candidate(source=source(rows[0].event_id),fact_type=FactType.RENT,
                    amount_meaning=AmountMeaning.BALANCE_DUE,amount=D(150),scope=Scope.ONGOING)
        b=replace(a,fact_id='second',source=source(rows[1].event_id,id='second',publisher='different'),amount=D(180))
        for facts in [(a,b),(b,a)]:
            r=forecast_with_evidence(profile(),request(),rows,RateBook(()),[a.source,b.source],
                                     [EvidenceBatch(c.source,(c,),True) for c in facts])
            self.assertFalse(r.forecast.complete)
            self.assertFalse(r.normalized.amendments)
            self.assertTrue(all(d.reason==Reason.CONFLICTING_EVIDENCE for d in r.normalized.decisions))
            self.assertEqual([f.amount for f in r.forecast.cash_flows],[D(100)]*3)

    def test_final_pay_at_another_employer_does_not_end_known_employer(self):
        rows=(*history('salary','credit','Acme Payroll','400'),payroll('salary',date(2026,4,15),'400','Beta Payroll','scheduled'))
        c=candidate(fact_type=FactType.FINAL_PAYROLL,amount=D(400),payment_date=date(2026,4,15))
        r=integrate(c,rows)
        self.assertFalse(r.forecast.complete)
        self.assertFalse(r.normalized.series_amendments)
        self.assertTrue(any(f.inferred and f.date.month==6 for f in r.forecast.cash_flows))

    def test_employment_end_requires_ongoing_scope(self):
        c=candidate(fact_type=FactType.EMPLOYMENT_ENDED,amount=None)
        self.assertEqual(validate(c,context()).reason,Reason.UNSUPPORTED_SCOPE)

    def test_employment_end_blocks_inference_but_keeps_final_confirmed_pay(self):
        c=candidate(fact_type=FactType.EMPLOYMENT_ENDED,amount=None,scope=Scope.FROM_DATE)
        r=integrate(c,salary_rows()).forecast
        self.assertTrue(r.complete,r.issues)
        self.assertEqual([(f.date,f.amount) for f in r.cash_flows],[(date(2026,4,15),D(400))])

    def test_reschedule_cannot_claim_ongoing_scope(self):
        c=candidate(fact_type=FactType.RESCHEDULE,amount=None,scope=Scope.ONE_OFF)
        self.assertEqual(validate(c,context()).reason,Reason.UNSUPPORTED_SCOPE)

    def test_cancellation_cannot_silently_override_settlement(self):
        s=source('bill'); other=source('bill',id='receipt',publisher='bank')
        cancel=candidate(source=s,fact_type=FactType.CANCELLATION,amount=None)
        paid=candidate(fact_id='paid',source=other,fact_type=FactType.PAYMENT_RECEIVED,
                        certainty=Certainty.SETTLED,amount_meaning=AmountMeaning.AMOUNT_PAID,amount=D(200))
        r=reconcile_evidence([cancel,paid],context([event('bill')],[s,other]))
        self.assertFalse(r.amendments)
        self.assertTrue(all(d.status==ValidationStatus.UNRESOLVED for d in r.decisions))

    def test_past_unsettled_unlinked_income_is_not_new_opening_cash(self):
        c=candidate(source=source(None),fact_type=FactType.INVOICE_APPROVED,
                    amount_meaning=AmountMeaning.INVOICE_AMOUNT,scope=Scope.ONE_OFF,
                    effective_date=None,payment_date=START-timedelta(days=1),category='contract',obligation_key='invoice')
        r=integrate(c)
        self.assertFalse(r.forecast.complete)
        self.assertEqual(r.forecast.ledger[-1].balance,D(1000))

    def test_empty_adapter_does_not_resolve_preexisting_missing_cancelled_amount(self):
        rows=(event('bill',amount=None,status='cancelled'),)
        actual=forecast_with_evidence(profile(),request(),rows,RateBook(()),(),()).forecast
        self.assertEqual(actual,run(rows))
        self.assertFalse(actual.complete)

    def test_exhaustive_flag_must_be_boolean(self):
        for invalid in ('false',1,None):
            with self.assertRaisesRegex(ValueError,'boolean'):
                integrate(candidate(certainty=Certainty.HYPOTHETICAL),exhaustive=invalid)

    def test_duplicate_json_amount_cannot_silently_choose_one_value(self):
        text=to_json(candidate())
        with self.assertRaisesRegex(ValueError,'duplicate JSON field'):
            from_json(text[:-1]+',"amount":"9000"}')

    def test_ongoing_rule_cannot_overwrite_separate_next_pay_amendment(self):
        rows=salary_rows()
        a=candidate(source=source(rows[0].event_id),scope=Scope.ONGOING)
        b=candidate(fact_id='next',source=source('salary',id='next'),amount=D(600),
                    payment_date=date(2026,4,15),explicit_amendment=True)
        r=forecast_with_evidence(profile(),request(),rows,RateBook(()),[a.source,b.source],
                                 [EvidenceBatch(c.source,(c,),True) for c in (a,b)])
        self.assertFalse(r.forecast.complete)
        self.assertFalse(r.normalized.amendments)
        self.assertEqual([f.amount for f in r.forecast.cash_flows],[D(400)]*3)

    def test_refund_cannot_relabel_salary_record(self):
        c=candidate(fact_type=FactType.REFUND,amount_meaning=AmountMeaning.AMOUNT_RECEIVED,
                    amount=D(400),explicit_amendment=True)
        self.assertEqual(validate(c,context()).reason,Reason.SOURCE_EVENT_MISMATCH)

    def test_confirmed_pending_debit_is_reserved_once(self):
        c=candidate(source=source('bill'),fact_type=FactType.EXPENSE,
                    amount_meaning=AmountMeaning.BALANCE_DUE,amount=D(200),payment_date=START+timedelta(days=5))
        r=integrate(c,[event('bill',status='pending')]).forecast
        self.assertTrue(r.complete,r.issues)
        self.assertEqual([(f.date,f.amount) for f in r.cash_flows],[(START,D(200))])

    def test_gross_salary_is_context_not_cash_even_with_high_confidence(self):
        c=candidate(amount_meaning=AmountMeaning.GROSS_PAY,amount=D(9000),confidence=D(1))
        r=integrate(c,salary_rows())
        self.assertTrue(r.forecast.complete,r.forecast.issues)
        self.assertFalse(r.normalized.amendments)
        self.assertEqual([f.amount for f in r.forecast.cash_flows],[D(400)]*3)

    def test_historical_receipt_fill_is_not_cash_or_recurrence_evidence(self):
        c=candidate(source=source('receipt'),fact_type=FactType.EXPENSE,certainty=Certainty.SETTLED,
                    amount_meaning=AmountMeaning.BALANCE_DUE,amount=D(5000),effective_date=None,
                    payment_date=START-timedelta(days=1))
        rows=[event('receipt',amount=None,day=START-timedelta(days=1),status='settled',category='groceries')]
        r=integrate(c,rows).forecast
        self.assertTrue(r.complete,r.issues)
        self.assertFalse(r.cash_flows)
        self.assertEqual(r.ledger[-1].balance,D(1000))
