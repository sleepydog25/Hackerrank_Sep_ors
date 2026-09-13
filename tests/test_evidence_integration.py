import unittest
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal as D
from test_core import START, event, history, profile, request, run
from test_calibration import payroll
from test_evidence import source,candidate
from buy_or_wait.evidence import *
from buy_or_wait.evidence_integration import forecast_with_evidence
from buy_or_wait.fx import RateBook


def integrate(c,events=(),extra_sources=(),exhaustive=True):
    sources=tuple(dict.fromkeys([c.source,*extra_sources]))
    return forecast_with_evidence(profile(),request(),tuple(events),RateBook(()),sources,
                                  [EvidenceBatch(c.source,(c,),exhaustive)])


def salary_rows():
    return (*history('salary','credit','Payroll','400'),payroll('salary',date(2026,4,15),'400','Next salary','scheduled'))


class EvidenceIntegrationTests(unittest.TestCase):
    def test_ongoing_salary_amends_all_supported_future_occurrences(self):
        c=candidate(scope=Scope.ONGOING,payment_date=date(2026,4,15),explicit_amendment=True)
        r=integrate(c,salary_rows()).forecast
        self.assertTrue(r.complete,r.issues)
        self.assertEqual([f.amount for f in r.cash_flows],[D(500)]*3)
        self.assertEqual(r.ledger[-1].balance,D(2500))

    def test_next_pay_change_does_not_retrain_income_recurrence(self):
        c=candidate(payment_date=date(2026,4,15),explicit_amendment=True)
        r=integrate(c,salary_rows()).forecast
        self.assertEqual([f.amount for f in r.cash_flows],[D(500),D(400),D(400)])

    def test_salary_delay_across_month_preserves_following_cycle(self):
        c=candidate(fact_type=FactType.RESCHEDULE,amount=None,payment_date=date(2026,5,5))
        r=integrate(c,salary_rows()).forecast
        self.assertEqual([f.date for f in r.cash_flows],[date(2026,5,5),date(2026,5,5),date(2026,6,5)])
        # Historical payroll fixture is the fifth, not the fifteenth.
        self.assertEqual(sum(f.amount for f in r.cash_flows),D(1200))

    def test_final_payroll_settles_once_and_ends_inferred_continuation(self):
        c=candidate(fact_type=FactType.FINAL_PAYROLL,payment_date=date(2026,4,15),amount=D(400))
        r=integrate(c,salary_rows()).forecast
        self.assertTrue(r.complete,r.issues)
        self.assertEqual([(f.date,f.amount) for f in r.cash_flows],[(date(2026,4,15),D(400))])

    def test_hypothetical_is_resolved_without_money(self):
        r=integrate(candidate(certainty=Certainty.HYPOTHETICAL),[payroll('salary',date(2026,4,15),'400','Next salary','scheduled')]).forecast
        self.assertTrue(r.complete,r.issues)
        self.assertEqual(sum(f.amount for f in r.cash_flows),D(400))

    def test_valuation_is_resolved_non_cash(self):
        c=candidate(source=source(None),fact_type=FactType.INVESTMENT_VALUE,amount_meaning=AmountMeaning.VALUATION)
        r=integrate(c).forecast
        self.assertTrue(r.complete,r.issues)
        self.assertEqual(r.low_water_mark,D(1000))

    def test_refund_sale_and_approved_invoice_are_single_confirmed_future_credits(self):
        for fact,meaning in [(FactType.REFUND,AmountMeaning.AMOUNT_RECEIVED),(FactType.INVESTMENT_SALE,AmountMeaning.SALE_PROCEEDS),
                             (FactType.INVOICE_APPROVED,AmountMeaning.INVOICE_AMOUNT),(FactType.REIMBURSEMENT,AmountMeaning.AMOUNT_RECEIVED)]:
            c=candidate(source=source(None),fact_type=fact,amount_meaning=meaning,scope=Scope.ONE_OFF,
                         category='one_off_income',obligation_key='document-reference',payment_date=START+timedelta(days=3))
            r=integrate(c).forecast
            self.assertTrue(r.complete,r.issues)
            self.assertEqual(len(r.cash_flows),1)
            self.assertEqual(r.ledger[-1].balance,D(1500))
            self.assertFalse(r.cash_flows[0].inferred)

    def test_invoice_balance_resolves_missing_image_amount(self):
        s=replace(source('bill'),source_type=SourceType.IMAGE)
        c=candidate(source=s,fact_type=FactType.EXPENSE,amount_meaning=AmountMeaning.BALANCE_DUE,amount=D(100))
        r=integrate(c,[event('bill',amount=None)]).forecast
        self.assertTrue(r.complete,r.issues)
        self.assertEqual(r.ledger[-1].balance,D(900))

    def test_ambiguous_cropped_image_stays_provisional(self):
        s=replace(source('bill'),source_type=SourceType.IMAGE)
        c=candidate(source=s,fact_type=FactType.EXPENSE,amount_meaning=AmountMeaning.UNKNOWN)
        r=integrate(c,[event('bill',amount=None)],exhaustive=False).forecast
        self.assertFalse(r.complete)
        self.assertTrue(any('AMBIGUOUS_AMOUNT_MEANING' in issue for issue in r.issues))

    def test_unprocessed_source_keeps_request_provisional(self):
        c=candidate(certainty=Certainty.HYPOTHETICAL)
        r=integrate(c,[payroll('salary',START)],extra_sources=[source(None,id='unread')]).forecast
        self.assertFalse(r.complete)
        self.assertTrue(any('unread' in issue for issue in r.issues))

    def test_cancelled_missing_bill_does_not_require_an_amount(self):
        c=candidate(source=source('bill'),fact_type=FactType.CANCELLATION,amount=None)
        r=integrate(c,[event('bill',amount=None)]).forecast
        self.assertTrue(r.complete,r.issues)
        self.assertFalse(r.cash_flows)

    def test_cancelled_recurring_occurrence_does_not_reappear(self):
        c=candidate(source=source('bill'),fact_type=FactType.CANCELLATION,amount=None)
        r=integrate(c,[*history(),event('bill','100',date(2026,4,5))]).forecast
        self.assertEqual([f.date for f in r.cash_flows],[date(2026,5,5),date(2026,6,5)])

    def test_provenance_reaches_cash_flow_and_decision_trace(self):
        c=candidate(payment_date=date(2026,4,15),explicit_amendment=True)
        r=integrate(c,salary_rows())
        self.assertIn('message -> fact',r.forecast.cash_flows[0].reason)
        self.assertEqual(r.normalized.amendments[0].original_label,'net salary')

    def test_no_evidence_adapter_matches_frozen_numeric_baseline(self):
        events=salary_rows()
        actual=forecast_with_evidence(profile(),request(),events,RateBook(()),(),()).forecast
        expected=run(events)
        self.assertEqual(actual,expected)
