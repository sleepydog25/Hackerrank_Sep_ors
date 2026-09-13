import unittest
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal as D
from test_core import START, request, event
from test_calibration import payroll
from test_evidence import candidate, source
from buy_or_wait.evidence import *
from buy_or_wait.evidence_validation import validate, EvidenceContext
from buy_or_wait.evidence_reconciliation import reconcile_evidence
from buy_or_wait.evidence_state import SeriesAction


def context(events=None,sources=None):
    return EvidenceContext(request(),tuple(events if events is not None else [payroll('salary',START,'400','Next salary','scheduled')]),tuple(sources or [source()]))


class EvidenceValidationTests(unittest.TestCase):
    def test_invalid_money_and_missing_currency(self):
        for c,reason in [(candidate(amount=D(0)),Reason.INVALID_AMOUNT),(candidate(amount=D(-1)),Reason.INVALID_AMOUNT),
                         (candidate(amount=D('NaN')),Reason.INVALID_AMOUNT),(candidate(currency=None),Reason.MISSING_CURRENCY),
                         (candidate(currency='XYZ'),Reason.INVALID_CURRENCY)]:
            self.assertEqual(validate(c,context()).reason,reason)

    def test_confidence_never_overrides_hypothetical(self):
        c=candidate(certainty=Certainty.HYPOTHETICAL,confidence=D(1))
        self.assertEqual(validate(c,context()).status,ValidationStatus.REJECTED)
        self.assertFalse(reconcile_evidence([c],context()).amendments)

    def test_source_and_event_ownership_must_match(self):
        for s in [replace(source(),user_id='other'),replace(source(),request_id='different'),replace(source(),related_event_id='missing')]:
            self.assertEqual(validate(candidate(source=s),context()).status,ValidationStatus.UNRESOLVED)

    def test_future_source_is_not_available(self):
        s=replace(source(),observed_at=source().observed_at+timedelta(days=5))
        self.assertEqual(validate(candidate(source=s),context(sources=[s])).reason,Reason.FUTURE_EVIDENCE)

    def test_invalid_scope_and_date_ranges(self):
        c=candidate(scope=Scope.UNTIL_DATE,period_end=START-timedelta(days=1))
        self.assertEqual(validate(c,context()).reason,Reason.INVALID_DATES)

    def test_pending_confirmation_is_not_settlement(self):
        ctx=context([payroll('salary',START,'400','Salary','pending')])
        self.assertEqual(validate(candidate(),ctx).reason,Reason.UNCONFIRMED_SETTLEMENT)


class EvidenceReconciliationTests(unittest.TestCase):
    def test_salary_replaces_exact_record(self):
        state=reconcile_evidence([candidate(explicit_amendment=True)],context())
        self.assertEqual(len(state.events),1)
        self.assertEqual(state.events[0].amount,D(500))
        self.assertEqual(state.events[0].event_id,'salary')
        self.assertEqual(state.amendments[0].source,source())

    def test_next_pay_has_no_ongoing_directive(self):
        self.assertFalse(reconcile_evidence([candidate(explicit_amendment=True)],context()).series_amendments)

    def test_ongoing_scope_has_explicit_series_amendment(self):
        state=reconcile_evidence([candidate(scope=Scope.ONGOING,explicit_amendment=True)],context())
        self.assertEqual(state.series_amendments[0].action,SeriesAction.AMOUNT)

    def test_delay_moves_record_not_duplicate(self):
        c=candidate(fact_type=FactType.RESCHEDULE,payment_date=START+timedelta(days=5),amount=None)
        state=reconcile_evidence([c],context())
        self.assertEqual(len(state.events),1)
        self.assertEqual(state.events[0].settlement_date,START+timedelta(days=5))

    def test_cancellation_only_linked_event(self):
        s=source('bill'); c=candidate(source=s,fact_type=FactType.CANCELLATION,amount=None)
        state=reconcile_evidence([c],context([event('bill'),event('other')],[s]))
        self.assertEqual([e.status for e in state.events],['cancelled','scheduled'])

    def test_balance_due_fills_missing_without_adding_invoice_total(self):
        s=source('bill'); c=candidate(source=s,fact_type=FactType.EXPENSE,amount_meaning=AmountMeaning.BALANCE_DUE,amount=D(100))
        state=reconcile_evidence([c],context([event('bill',amount=None)],[s]))
        self.assertEqual(len(state.events),1)
        self.assertEqual(state.events[0].amount,D(100))
        ambiguous=replace(c,amount_meaning=AmountMeaning.TOTAL)
        self.assertEqual(validate(ambiguous,context([event('bill',amount=None)],[s])).status,ValidationStatus.UNRESOLVED)

    def test_paid_bill_is_in_snapshot_not_charged_again(self):
        s=source('bill'); c=candidate(source=s,fact_type=FactType.PAYMENT_RECEIVED,certainty=Certainty.SETTLED,
                                     amount_meaning=AmountMeaning.AMOUNT_PAID,amount=D(200))
        state=reconcile_evidence([c],context([event('bill')],[s]))
        self.assertEqual(state.events[0].status,'settled')
        self.assertEqual(state.events[0].settlement_date,START)

    def test_conflicting_sources_leave_original_unchanged(self):
        a=candidate(explicit_amendment=True)
        s=source(id='other',publisher='another-employer')
        b=candidate(fact_id='otherfact',source=s,amount=D(600),explicit_amendment=True)
        state=reconcile_evidence([a,b],context(sources=[source(),s]))
        self.assertFalse(state.amendments)
        self.assertTrue(all(d.reason==Reason.CONFLICTING_EVIDENCE for d in state.decisions))

    def test_later_same_publisher_explicit_amendment_supersedes(self):
        a=candidate(explicit_amendment=True)
        s=replace(source(id='later'),observed_at=source().observed_at+timedelta(hours=1))
        b=candidate(fact_id='new',source=s,amount=D(600),explicit_amendment=True)
        state=reconcile_evidence([b,a],context(sources=[source(),s]))
        self.assertEqual(state.events[0].amount,D(600))
        self.assertEqual(len(state.amendments),1)

    def test_generic_salary_without_event_link_cannot_overwrite(self):
        s=source(None); c=candidate(source=s)
        self.assertEqual(validate(c,context(sources=[s])).reason,Reason.MISSING_LINK)

    def test_valuation_never_becomes_cash(self):
        c=candidate(fact_type=FactType.INVESTMENT_VALUE,amount_meaning=AmountMeaning.VALUATION)
        state=reconcile_evidence([c],context())
        self.assertFalse(state.amendments)
        self.assertEqual(state.decisions[0].reason,Reason.VALUATION_NOT_CASH)

    def test_new_refund_and_sale_are_one_off_typed_credits(self):
        for fact,meaning in [(FactType.REFUND,AmountMeaning.AMOUNT_RECEIVED),(FactType.INVESTMENT_SALE,AmountMeaning.SALE_PROCEEDS)]:
            s=source(None)
            c=candidate(source=s,fact_type=fact,amount_meaning=meaning,scope=Scope.ONE_OFF,
                         category='refund',obligation_key='external-reference')
            state=reconcile_evidence([c],context([], [s]))
            self.assertEqual(len(state.events),1)
            self.assertEqual(state.events[0].direction,'credit')
            self.assertFalse(state.series_amendments)
            self.assertIn(state.events[0].event_id,state.confirmed_credit_ids)

    def test_exact_compatible_facts_do_not_duplicate(self):
        a=candidate(explicit_amendment=True); b=replace(a,fact_id='copy')
        state=reconcile_evidence([a,b],context())
        self.assertEqual(len(state.amendments),1)
        self.assertEqual(len(state.events),1)

    def test_final_historical_payroll_ends_continuation_without_replay(self):
        c=candidate(fact_type=FactType.FINAL_PAYROLL,amount=D(400))
        state=reconcile_evidence([c],context([payroll('salary',START,'400')]))
        self.assertEqual(state.series_amendments[0].action,SeriesAction.END)
        self.assertEqual(state.events[0].status,'settled')
