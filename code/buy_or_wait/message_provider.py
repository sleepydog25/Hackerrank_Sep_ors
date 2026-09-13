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
    upstream: str = 'OpenAI'
    reasoning_enabled: bool | None = None

    def __post_init__(self):
        if not self.model or self.provider not in ('openai','openrouter'):raise ValueError('Configure MESSAGE_MODEL and MESSAGE_PROVIDER=openai or openrouter')
        if not self.upstream or (self.reasoning_enabled is not None and type(self.reasoning_enabled) is not bool):raise ValueError('invalid routing configuration')
        if not 1<=self.timeout<=60 or not 1<=self.max_attempts<=3 or not 256<=self.max_output_tokens<=8000:
            raise ValueError('invalid bounded provider configuration')
        for value in (self.input_per_million,self.output_per_million,self.cached_input_per_million):
            if value is not None and (not isinstance(value,Decimal) or not value.is_finite() or value<0):raise ValueError('invalid price')

    @classmethod
    def from_env(cls):
        def price(name):return Decimal(os.environ[name]) if os.environ.get(name) else None
        reasoning=os.environ.get('MESSAGE_REASONING','')
        if reasoning not in ('','enabled','disabled'):raise ValueError('invalid MESSAGE_REASONING')
        return cls(model=os.environ.get('MESSAGE_MODEL',''),provider=os.environ.get('MESSAGE_PROVIDER','openai'),
                   api_key=os.environ.get('OPENROUTER_API_KEY' if os.environ.get('MESSAGE_PROVIDER')=='openrouter' else 'OPENAI_API_KEY',''),timeout=int(os.environ.get('MESSAGE_TIMEOUT','45')),
                   max_attempts=int(os.environ.get('MESSAGE_MAX_ATTEMPTS','2')),
                   max_output_tokens=int(os.environ.get('MESSAGE_MAX_OUTPUT_TOKENS','3000')),
                   input_per_million=price('MESSAGE_INPUT_USD_PER_MILLION'),
                   output_per_million=price('MESSAGE_OUTPUT_USD_PER_MILLION'),
                   cached_input_per_million=price('MESSAGE_CACHED_INPUT_USD_PER_MILLION'),
                   upstream=os.environ.get('MESSAGE_UPSTREAM','OpenAI'),
                   reasoning_enabled=None if not reasoning else reasoning=='enabled')

@dataclass(frozen=True)
class ProviderReply:
    text: str = ''
    error: str | None = None
    retryable: bool = False
    usage: dict | None = None
    actual_model: str | None = None
    reported_cost_usd: str | None = None
    upstream_provider: str | None = None
    http_status: int | None = None

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
        if self.config.provider=='openrouter':
            payload=dict(model=self.config.model,temperature=0,max_tokens=self.config.max_output_tokens,
                        messages=[{'role':'system','content':SYSTEM_INSTRUCTION},
                                  {'role':'user','content':canonical(task.model_input())}],
                        provider={'only':[self.config.upstream],'allow_fallbacks':False,'require_parameters':True},
                        response_format={'type':'json_schema','json_schema':{'name':'message_evidence','strict':True,'schema':output_schema()}})
            if self.config.reasoning_enabled is not None:payload['reasoning']={'enabled':self.config.reasoning_enabled}
            if self.config.model.endswith(':free'):payload['provider']['max_price']={'prompt':0,'completion':0}
            return payload
        return dict(model=self.config.model,store=False,max_output_tokens=self.config.max_output_tokens,
                    input=[{'role':'system','content':SYSTEM_INSTRUCTION},
                           {'role':'user','content':canonical(task.model_input())}],
                    text={'format':{'type':'json_schema','name':'message_evidence','strict':True,'schema':output_schema()}})

    def call(self,task):
        if not self.config.api_key:raise ValueError('Provider API key is not configured')
        endpoint='https://openrouter.ai/api/v1/chat/completions' if self.config.provider=='openrouter' else 'https://api.openai.com/v1/responses'
        req=Request(endpoint,data=canonical(self.payload(task)).encode('utf-8'),
                    headers={'Authorization':'Bearer '+self.config.api_key,'Content-Type':'application/json'},method='POST')
        try:
            with urlopen(req,timeout=self.config.timeout) as response:
                body=response.read(262145)
            if len(body)>262144:return ProviderReply(error='OUTPUT_TRUNCATED')
            raw=json.loads(body,parse_float=Decimal)
        except HTTPError as exc:
            # Never retain provider error bodies/headers; they may echo input or credentials.
            return ProviderReply(error='MODEL_RATE_LIMIT' if exc.code==429 else 'MODEL_PROVIDER_ERROR',
                                 retryable=exc.code in (408,429,500,502,503,504),http_status=exc.code)
        except (TimeoutError,socket.timeout):return ProviderReply(error='MODEL_TIMEOUT',retryable=True)
        except URLError as exc:
            return ProviderReply(error='MODEL_TIMEOUT' if isinstance(exc.reason,(TimeoutError,socket.timeout)) else 'MODEL_PROVIDER_ERROR',retryable=True)
        except (ValueError,UnicodeError):return ProviderReply(error='INVALID_STRUCTURED_OUTPUT')
        if not isinstance(raw,dict):return ProviderReply(error='INVALID_STRUCTURED_OUTPUT')
        if self.config.provider=='openrouter':return self.parse_openrouter(raw)
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

    @staticmethod
    def parse_openrouter(raw):
        u=raw.get('usage') if isinstance(raw.get('usage'),dict) else {}
        details=u.get('prompt_tokens_details')
        usage=usage_fields(dict(input_tokens=u.get('prompt_tokens'),output_tokens=u.get('completion_tokens'),
                                total_tokens=u.get('total_tokens'),input_tokens_details=details))
        cost=u.get('cost')
        cost=str(cost) if isinstance(cost,(Decimal,int)) and not isinstance(cost,bool) and Decimal(cost).is_finite() and cost>=0 else None
        meta=dict(usage=usage,actual_model=raw.get('model') if isinstance(raw.get('model'),str) else None,
                  reported_cost_usd=cost,upstream_provider=raw.get('provider') if isinstance(raw.get('provider'),str) else None)
        choices=raw.get('choices')
        if not isinstance(choices,list) or len(choices)!=1 or not isinstance(choices[0],dict):return ProviderReply(error='INVALID_STRUCTURED_OUTPUT',**meta)
        choice=choices[0];message=choice.get('message')
        if choice.get('finish_reason')=='length':return ProviderReply(error='OUTPUT_TRUNCATED',**meta)
        if choice.get('finish_reason')!='stop' or not isinstance(message,dict):return ProviderReply(error='UNSUPPORTED_CONTENT',**meta)
        if message.get('refusal'):return ProviderReply(error='UNSUPPORTED_CONTENT',**meta)
        content=message.get('content')
        if not isinstance(content,str):return ProviderReply(error='INVALID_STRUCTURED_OUTPUT',**meta)
        return ProviderReply(text=content,**meta)
