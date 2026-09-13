import io
import json
import unittest
from decimal import Decimal
from unittest.mock import patch
from urllib.error import HTTPError
from test_message_cache import reply
from test_message_extraction_contract import task,response
from buy_or_wait.message_provider import ModelConfig,OpenAIMessageProvider
from buy_or_wait.message_usage import summarize

class MessageProviderTests(unittest.TestCase):
    def setUp(self):self.provider=OpenAIMessageProvider(ModelConfig('fake-model',api_key='synthetic-only'))

    def raw(self,**changes):
        r=dict(status='completed',model='fake-model',output=[dict(type='message',content=[dict(type='output_text',text=response())])],
               usage=dict(input_tokens=100,output_tokens=20,total_tokens=120,input_tokens_details=dict(cached_tokens=0)))
        r.update(changes);return r

    def call_raw(self,raw):
        with patch('buy_or_wait.message_provider.urlopen',return_value=io.BytesIO(json.dumps(raw).encode())):
            return self.provider.call(task())

    def test_response_transport_collects_usage(self):
        r=self.call_raw(self.raw())
        self.assertIsNone(r.error);self.assertEqual(r.usage['total_tokens'],120)
        self.assertEqual(r.text,response())

    def test_refusal_and_truncation_are_failures_with_usage(self):
        for raw,reason in [(self.raw(status='incomplete'),'OUTPUT_TRUNCATED'),
                           (self.raw(output=[dict(type='message',content=[dict(type='refusal',refusal='No')])]),'UNSUPPORTED_CONTENT')]:
            r=self.call_raw(raw);self.assertEqual(r.error,reason);self.assertEqual(r.usage['total_tokens'],120)

    def test_invalid_provider_envelope_does_not_crash(self):
        for output in (None,{},[None],[dict(type='message',content=[None])],[dict(type='message',content=None)]):
            self.assertEqual(self.call_raw(self.raw(output=output)).error,'INVALID_STRUCTURED_OUTPUT')

    def test_transport_failure_classification(self):
        for exc,code,retry in [(TimeoutError(),'MODEL_TIMEOUT',True),
                               (HTTPError('https://api.openai.com',429,'limited',None,None),'MODEL_RATE_LIMIT',True),
                               (HTTPError('https://api.openai.com',401,'secret error text',None,None),'MODEL_PROVIDER_ERROR',False)]:
            with patch('buy_or_wait.message_provider.urlopen',side_effect=exc):r=self.provider.call(task())
            self.assertEqual(r.error,code);self.assertEqual(r.retryable,retry)
            self.assertNotIn('secret',repr(r))

    def test_unknown_usage_totals_cannot_be_reported_as_zero(self):
        r=dict(external_call=True,cache_hit=False,attempt=1,status='MODEL_TIMEOUT',provider='openai',model='fake',
               input_tokens=None,output_tokens=None,total_tokens=None,cached_input_tokens=None,estimated_cost_usd=None)
        result=summarize([r]);self.assertIsNone(result['total_tokens']);self.assertIsNone(result['estimated_cost_usd'])
        self.assertEqual(result['external_attempts'],1)

    def test_config_does_not_accept_unbounded_retries_or_invalid_price(self):
        for kwargs in (dict(max_attempts=100),dict(timeout=0),dict(input_per_million=Decimal('NaN'))):
            with self.assertRaises(ValueError):ModelConfig('fake',**kwargs)
