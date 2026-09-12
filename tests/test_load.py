import csv
import sys
import tempfile
import unittest
from pathlib import Path
from datetime import date
from decimal import Decimal
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'code'))
from buy_or_wait.load import parse, unique, read_table, load_dataset, DataError
from buy_or_wait.models import FinanceRequest
from dataclasses import replace
from unittest.mock import patch
from buy_or_wait.models import PaymentOption
from test_core import profile, request, event, START


class LoaderTests(unittest.TestCase):
    def fixture(self):
        q=request()
        return {'financial_profiles.csv':(profile(),), 'financial_events.csv':(event(),),
                'requests.csv':(q,), 'sample_requests.csv':(), 'exchange_rates.csv':(),
                'messages.csv':(), 'images.csv':(), 'request_payment_options.csv':(
                    PaymentOption('offer-a',q.request_id,'full_payment',q.requested_amount,1,START,None,Decimal(0),q.requested_amount),
                    PaymentOption('offer-b',q.request_id,'installments',q.requested_amount/2,2,START,30,Decimal(0),q.requested_amount))}

    def load_fixture(self,tables):
        with patch('buy_or_wait.load.read_table',side_effect=lambda path,*a,**kw: tables[path.name]):
            return load_dataset(Path('.'))

    def test_missing_user_join_rejected(self):
        tables=self.fixture()
        tables['financial_events.csv']=(replace(event(),user_id='unknown'),)
        with self.assertRaises(DataError):
            self.load_fixture(tables)

    def test_missing_event_join_rejected(self):
        tables=self.fixture()
        tables['financial_events.csv']=(replace(event(),linked_event_id='absent'),)
        with self.assertRaises(DataError):
            self.load_fixture(tables)

    def test_link_cycle_rejected(self):
        tables=self.fixture()
        tables['financial_events.csv']=(replace(event(),linked_event_id='bill'),)
        with self.assertRaises(DataError):
            self.load_fixture(tables)

    def test_missing_option_request_join_rejected(self):
        tables=self.fixture()
        offers=tables['request_payment_options.csv']
        tables['request_payment_options.csv']=(replace(offers[0],request_id='absent'),offers[1])
        with self.assertRaises(DataError):
            self.load_fixture(tables)

    def test_strict_scalar_parsing(self):
        self.assertEqual(parse('0',Decimal),Decimal(0))
        self.assertIsNone(parse('',Decimal|None))
        self.assertFalse(parse('false',bool))
        self.assertEqual(parse('rent|groceries',frozenset[str]),frozenset({'rent','groceries'}))
        for text, kind in [('NaN',Decimal),('Infinity',Decimal),('-1',Decimal),('yes',bool),('20260101',date)]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse(text,kind)

    def test_duplicate_keys(self):
        with self.assertRaises(DataError):
            unique(['same','same'],lambda x:x)

    def test_sample_labels_discarded(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'sample.csv'
            header=list(FinanceRequest.__dataclass_fields__)+['amount_safe_to_pay']
            with path.open('w',newline='') as out:
                writer=csv.writer(out)
                writer.writerow(header)
                writer.writerow(['q','u','2026-01-01','purchase','50','2026-02-01','false','Question','POISON'])
            q=read_table(path,FinanceRequest,sample=True)[0]
            self.assertFalse(hasattr(q,'amount_safe_to_pay'))
            self.assertEqual(q.requested_amount,Decimal(50))

    def test_real_dataset_both_request_sets(self):
        root=Path(__file__).resolve().parents[1]/'dataset'
        for name in ['requests.csv','sample_requests.csv']:
            data=load_dataset(root,name)
            self.assertTrue(data.selected_requests)
            self.assertFalse(data.missing_images)
            self.assertEqual(len(data.events),sum(map(len,data.events_by_user.values())))


if __name__ == '__main__':
    unittest.main()
