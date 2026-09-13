"""Small Responses API transport; standard library, no implicit retries or tools."""
from dataclasses import dataclass, field
from decimal import Decimal
import json
import os
import socket
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from .message_extraction import SYSTEM_INSTRUCTION, output_schema, canonical

@dataclass(frozen=True)
class ModelConfig:
    model: str
    provider: str = 'openai'
    api_key: str = field(default='',repr=False,compare=False)
    timeout: int = 45
    max_attempts: int = 2
    max_output_tokens: int = 3000
    input_per_million: Decimal | None = None
    output_per_million: Decimal | None = None
    cached_input_per_million: Decimal | None = None

    def __post_init__(self):
        if not self.model or self.provider!='openai':raise ValueError('Configure MESSAGE_MODEL and supported MESSAGE_PROVIDER=openai')
        if not 1<=self.timeout<=60 or not 1<=self.max_attempts<=3 or not 256<=self.max_output_tokens<=8000:
            raise ValueError('invalid bounded provider configuration')
        for value in (self.input_per_million,self.output_per_million,self.cached_input_per_million):
            if value is not None and (not isinstance(value,Decimal) or not value.is_finite() or value<0):raise ValueError('invalid price')

    @classmethod
    def from_env(cls):
        def price(name):return Decimal(os.environ[name]) if os.environ.get(name) else None
        return cls(model=os.environ.get('MESSAGE_MODEL',''),provider=os.environ.get('MESSAGE_PROVIDER','openai'),
                   api_key=os.environ.get('OPENAI_API_KEY',''),timeout=int(os.environ.get('MESSAGE_TIMEOUT','45')),
                   max_attempts=int(os.environ.get('MESSAGE_MAX_ATTEMPTS','2')),
                   max_output_tokens=int(os.environ.get('MESSAGE_MAX_OUTPUT_TOKENS','3000')),
                   input_per_million=price('MESSAGE_INPUT_USD_PER_MILLION'),
                   output_per_million=price('MESSAGE_OUTPUT_USD_PER_MILLION'),
                   cached_input_per_million=price('MESSAGE_CACHED_INPUT_USD_PER_MILLION'))

@dataclass(frozen=True)
class ProviderReply:
    text: str = ''
    error: str | None = None
    retryable: bool = False
    usage: dict | None = None
    actual_model: str | None = None

def usage_fields(raw):
    raw=raw if isinstance(raw,dict) else {}
    def count(v):return v if type(v) is int and v>=0 else None
    details=raw.get('input_tokens_details') or {}
    if not isinstance(details,dict):details={}
    return dict(input_tokens=count(raw.get('input_tokens')),output_tokens=count(raw.get('output_tokens')),
                total_tokens=count(raw.get('total_tokens')),cached_input_tokens=count(details.get('cached_tokens')))

def estimated_cost(usage,config):
    i,o,c=(usage.get(k) for k in ('input_tokens','output_tokens','cached_input_tokens'))
    if i is None or o is None or config.input_per_million is None or config.output_per_million is None:return None
    if c is None or (c and config.cached_input_per_million is None) or (c is not None and c>i):return None
    return str(((i-c)*config.input_per_million+o*config.output_per_million+c*(config.cached_input_per_million or Decimal(0)))/Decimal(1000000))

class OpenAIMessageProvider:
    def __init__(self,config):self.config=config

    def payload(self,task):
        return dict(model=self.config.model,store=False,max_output_tokens=self.config.max_output_tokens,
                    input=[{'role':'system','content':SYSTEM_INSTRUCTION},
                           {'role':'user','content':canonical(task.model_input())}],
                    text={'format':{'type':'json_schema','name':'message_evidence','strict':True,'schema':output_schema()}})

    def call(self,task):
        if not self.config.api_key:raise ValueError('OPENAI_API_KEY is not configured')
        req=Request('https://api.openai.com/v1/responses',data=canonical(self.payload(task)).encode('utf-8'),
                    headers={'Authorization':'Bearer '+self.config.api_key,'Content-Type':'application/json'},method='POST')
        try:
            with urlopen(req,timeout=self.config.timeout) as response:
                body=response.read(262145)
            if len(body)>262144:return ProviderReply(error='OUTPUT_TRUNCATED')
            raw=json.loads(body)
        except HTTPError as exc:
            # Never retain provider error bodies/headers; they may echo input or credentials.
            return ProviderReply(error='MODEL_RATE_LIMIT' if exc.code==429 else 'MODEL_PROVIDER_ERROR',
                                 retryable=exc.code in (408,429,500,502,503,504))
        except (TimeoutError,socket.timeout):return ProviderReply(error='MODEL_TIMEOUT',retryable=True)
        except URLError as exc:
            return ProviderReply(error='MODEL_TIMEOUT' if isinstance(exc.reason,(TimeoutError,socket.timeout)) else 'MODEL_PROVIDER_ERROR',retryable=True)
        except (ValueError,UnicodeError):return ProviderReply(error='INVALID_STRUCTURED_OUTPUT')
        if not isinstance(raw,dict):return ProviderReply(error='INVALID_STRUCTURED_OUTPUT')
        usage=usage_fields(raw.get('usage'))
        model=raw.get('model') if isinstance(raw.get('model'),str) else None
        if raw.get('status')=='incomplete':return ProviderReply(error='OUTPUT_TRUNCATED',usage=usage,actual_model=model)
        if raw.get('status')!='completed':return ProviderReply(error='MODEL_PROVIDER_ERROR',usage=usage,actual_model=model)
        texts=[]
        output=raw.get('output',[])
        if not isinstance(output,list):return ProviderReply(error='INVALID_STRUCTURED_OUTPUT',usage=usage,actual_model=model)
        for item in output:
            if not isinstance(item,dict):return ProviderReply(error='INVALID_STRUCTURED_OUTPUT',usage=usage,actual_model=model)
            if item.get('type')=='message':
                content=item.get('content',[])
                if not isinstance(content,list):return ProviderReply(error='INVALID_STRUCTURED_OUTPUT',usage=usage,actual_model=model)
                for part in content:
                    if not isinstance(part,dict):return ProviderReply(error='INVALID_STRUCTURED_OUTPUT',usage=usage,actual_model=model)
                    if part.get('type')=='refusal':return ProviderReply(error='UNSUPPORTED_CONTENT',usage=usage,actual_model=model)
                    if part.get('type')=='output_text':texts.append(part.get('text',''))
        if len(texts)!=1 or not isinstance(texts[0],str):return ProviderReply(error='INVALID_STRUCTURED_OUTPUT',usage=usage,actual_model=model)
        return ProviderReply(text=texts[0],usage=usage,actual_model=model)
