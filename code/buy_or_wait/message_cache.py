"""Transactional persistent cache and per-attempt development usage journal."""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
import json
import sqlite3
import time
import uuid
from . import message_extraction as contract
from .message_provider import usage_fields, estimated_cost

SUCCESS={'SUCCESS','NON_ACTIONABLE_SUCCESS','UNRESOLVED_SUCCESS'}
CACHEABLE=SUCCESS|{'PERMANENT_PARSE_FAILURE','PERMANENT_PROVIDER_FAILURE'}

def identity(task,config):
    source=asdict(task.source); source['observed_at']=task.source.observed_at.isoformat()
    return dict(content_hash=contract.digest(task.text),context_hash=contract.digest(task.context),
                source=source,provider=config.provider,model=config.model,
                schema_version=contract.SCHEMA_VERSION,prompt_version=contract.PROMPT_VERSION,
                extractor_version=contract.EXTRACTOR_VERSION,schema_hash=contract.digest(contract.output_schema()),
                prompt_hash=contract.digest(contract.SYSTEM_INSTRUCTION),max_output_tokens=config.max_output_tokens)

@dataclass(frozen=True)
class ExtractionResult:
    key: str
    status: str
    batch: object | None
    cache_hit: bool
    error: str | None = None

class ExtractionStore:
    def __init__(self,path):
        Path(path).parent.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(path,timeout=10)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.executescript('''
          CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, metadata TEXT NOT NULL,
            status TEXT NOT NULL, output TEXT, error TEXT, created_at TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS usage (id TEXT PRIMARY KEY, key TEXT NOT NULL, run_id TEXT NOT NULL,
            state TEXT NOT NULL, record TEXT NOT NULL);
          CREATE UNIQUE INDEX IF NOT EXISTS one_inflight ON usage(key) WHERE state='IN_FLIGHT';
        ''')
        self.db.commit()

    def close(self):self.db.close()

    def entries(self,run_id=None):
        rows=self.db.execute('SELECT record FROM usage'+(' WHERE run_id=?' if run_id else ''),(run_id,) if run_id else ())
        return [json.loads(row[0]) for row in rows]

    def release_interrupted(self,key):
        """Explicit operator action: preserve unknown usage, then allow retry."""
        row=self.db.execute("SELECT id,record FROM usage WHERE key=? AND state='IN_FLIGHT'",(key,)).fetchone()
        if row:
            record=json.loads(row[1]);record['status']='UNKNOWN_PROVIDER_OUTCOME'
            with self.db:self.db.execute('UPDATE usage SET state=?,record=? WHERE id=?',
                                        ('UNKNOWN_PROVIDER_OUTCOME',contract.canonical(record),row[0]))

    def extract(self,task,config,provider,run_id,refresh=False,cache_only=False,sleep=time.sleep):
        metadata=identity(task,config); key=contract.digest(metadata)
        row=self.db.execute('SELECT status,output,error FROM cache WHERE key=?',(key,)).fetchone()
        if row and row[0] in CACHEABLE and not refresh:
            batch=contract.parse_output(row[1],task) if row[0] in SUCCESS else None
            record=dict(metadata,external_call=False,cache_hit=True,attempt=0,status=row[0],error=row[2],
                        input_tokens=0,output_tokens=0,total_tokens=0,cached_input_tokens=0,estimated_cost_usd='0',
                        timestamp=datetime.now(timezone.utc).isoformat())
            with self.db:self.db.execute('INSERT INTO usage VALUES (?,?,?,?,?)',(str(uuid.uuid4()),key,run_id,'CACHE_HIT',contract.canonical(record)))
            return ExtractionResult(key,row[0],batch,True,row[2])
        if cache_only:return ExtractionResult(key,'NOT_RUN',None,False,'CACHE_MISS')
        if not config.api_key:return ExtractionResult(key,'NOT_RUN',None,False,'CONFIGURATION_MISSING')
        if self.db.execute("SELECT 1 FROM usage WHERE key=? AND state='IN_FLIGHT'",(key,)).fetchone():
            return ExtractionResult(key,'INTERRUPTED_ATTEMPT',None,False,'REVIEW_IN_FLIGHT_ATTEMPT')
        for attempt in range(1,config.max_attempts+1):
            attempt_id=str(uuid.uuid4())
            record=dict(metadata,external_call=True,cache_hit=False,attempt=attempt,status='IN_FLIGHT',
                        input_tokens=None,output_tokens=None,total_tokens=None,cached_input_tokens=None,
                        estimated_cost_usd=None,timestamp=datetime.now(timezone.utc).isoformat())
            # Record dispatch intent before I/O. A crash cannot silently lose a call.
            try:
                with self.db:
                    self.db.execute('BEGIN IMMEDIATE')
                    latest=self.db.execute('SELECT status FROM cache WHERE key=?',(key,)).fetchone()
                    already_cached=latest and latest[0] in CACHEABLE and not refresh
                    if not already_cached:
                        self.db.execute('INSERT INTO usage VALUES (?,?,?,?,?)',(attempt_id,key,run_id,'IN_FLIGHT',contract.canonical(record)))
            except sqlite3.IntegrityError:
                return ExtractionResult(key,'INTERRUPTED_ATTEMPT',None,False,'CONCURRENT_ATTEMPT')
            if already_cached:
                return self.extract(task,config,provider,run_id,cache_only=True,sleep=sleep)
            reply=provider.call(task)
            usage=reply.usage or usage_fields(None)
            error=reply.error; batch=None; output=None
            if error:
                status='RETRYABLE_FAILURE' if reply.retryable else 'PERMANENT_PROVIDER_FAILURE'
            else:
                try:
                    batch=contract.parse_output(reply.text,task)
                    parsed=contract.strict_json(reply.text)
                    output=contract.canonical(parsed)
                    status={'FACTS':'SUCCESS','NO_FACT':'NON_ACTIONABLE_SUCCESS','UNRESOLVED':'UNRESOLVED_SUCCESS'}[parsed['outcome']]
                except (ValueError,TypeError,KeyError,OverflowError,RecursionError,UnicodeError):
                    status='PERMANENT_PARSE_FAILURE'; error='SCHEMA_VALIDATION_FAILED'
            record.update(usage,status=status,error=error,actual_model=reply.actual_model,
                          reported_cost_usd=reply.reported_cost_usd,upstream_provider=reply.upstream_provider,
                          estimated_cost_usd=estimated_cost(usage,config),
                          price_basis={k:str(getattr(config,k)) if getattr(config,k) is not None else None
                                       for k in ('input_per_million','output_per_million','cached_input_per_million')})
            with self.db:
                self.db.execute('UPDATE usage SET state=?,record=? WHERE id=?',(status,contract.canonical(record),attempt_id))
                self.db.execute('INSERT OR REPLACE INTO cache VALUES (?,?,?,?,?,?)',
                                (key,contract.canonical(metadata),status,output,error,datetime.now(timezone.utc).isoformat()))
            if not reply.retryable or attempt==config.max_attempts:
                return ExtractionResult(key,status,batch,False,error)
            sleep(min(2**(attempt-1),4))
        raise AssertionError('bounded attempts exhausted without result')
