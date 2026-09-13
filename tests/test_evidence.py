import unittest
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal as D
from test_core import START
from buy_or_wait.evidence import *


def source(event_id='salary',id='message',publisher='employer'):
    return EvidenceSource(SourceType.MESSAGE,id,'person','question',event_id,
                          datetime(2026,3,31,tzinfo=timezone.utc),publisher)


def candidate(**changes):
    base=EvidenceCandidate('fact',source(),FactType.SALARY,Certainty.CONFIRMED,
                           Scope.NEXT_OCCURRENCE_ONLY,AmountMeaning.NET_PAY,'net salary',
                           D(500),'USD',START,START)
    return replace(base,**changes)


class EvidenceContractTests(unittest.TestCase):
    def test_confirmed_and_hypothetical_are_different(self):
        a=candidate(); b=candidate(certainty=Certainty.HYPOTHETICAL)
        self.assertNotEqual(a,b)
        self.assertNotIsInstance(a,ValidatedEvidenceFact)

    def test_amount_meanings_are_not_interchangeable(self):
        for meaning in (AmountMeaning.BALANCE_DUE,AmountMeaning.TOTAL,AmountMeaning.AMOUNT_PAID):
            self.assertEqual(from_json(to_json(candidate(amount_meaning=meaning))).amount_meaning,meaning)

    def test_investment_valuation_and_sale_distinct(self):
        self.assertNotEqual(FactType.INVESTMENT_VALUE,FactType.INVESTMENT_SALE)
        self.assertNotEqual(AmountMeaning.VALUATION,AmountMeaning.SALE_PROCEEDS)

    def test_scope_and_dates_round_trip(self):
        a=candidate(scope=Scope.ONGOING,period_end=START,due_date=START)
        self.assertEqual(from_json(to_json(a)),a)
        self.assertNotEqual(a.scope,Scope.NEXT_OCCURRENCE_ONLY)

    def test_missing_currency_stays_missing(self):
        self.assertIsNone(from_json(to_json(candidate(currency=None))).currency)

    def test_provenance_survives_transport(self):
        self.assertEqual(from_json(to_json(candidate())).source,source())

    def test_invalid_nonpositive_amounts_are_only_candidates(self):
        for amount in (D(-1),D(0)):
            a=from_json(to_json(candidate(amount=amount)))
            self.assertEqual(a.amount,amount)
            self.assertNotIsInstance(a,ValidatedEvidenceFact)

    def test_no_float_or_unknown_fields(self):
        import json
        raw=json.loads(to_json(candidate())); raw['amount']=1.1
        with self.assertRaises(ValueError):from_json(json.dumps(raw))
        raw['amount']='500'; raw['balance_override']='999'
        with self.assertRaises(ValueError):from_json(json.dumps(raw))
