"""Strict CSV parsing and indexed joins. Sample labels never enter domain objects."""
import csv
import re
import types
from collections import defaultdict
from dataclasses import dataclass, fields
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import get_args, get_origin, get_type_hints
from .models import (FinancialProfile, FinancialEvent, FinanceRequest, PaymentOption,
                     ExchangeRate, Message, ImageReference)


class DataError(ValueError):
    pass


OUTPUT_FIELDS = {'amount_safe_to_pay', 'affordability_status', 'recommended_payment_method',
                 'payment_plan', 'earliest_date_for_full_payment', 'spending_changes_needed',
                 'decision_explanation'}
CURRENCIES = {'INR', 'ZAR', 'IDR', 'USD', 'EUR'}
ENUMS = {
    'status': {'settled', 'pending', 'scheduled', 'cancelled', 'failed', 'unrealized'},
    'direction': {'credit', 'debit', 'non_cash'},
    'event_type': {'expense', 'income', 'subscription', 'debt_payment', 'refund',
                   'investment_purchase', 'investment_sale', 'investment_valuation'},
    'flexibility': {'fixed', 'reducible', 'stoppable', 'reducible_or_stoppable'},
    'request_type': {'purchase', 'travel', 'education', 'family_transfer', 'debt_repayment',
                     'investment', 'housing', 'emergency_expense', 'other'},
    'payment_method': {'full_payment', 'installments'},
    'source_type': {'bank', 'employer', 'financial_service', 'merchant', 'service_provider'},
}


def parse(value: str, kind):
    if get_origin(kind) is types.UnionType:
        if value == '':
            return None
        return parse(value, next(t for t in get_args(kind) if t is not type(None)))
    if get_origin(kind) is frozenset:
        if value == '':
            return frozenset()
        parts = value.split('|')
        if any(not p or p != p.strip() for p in parts) or len(parts) != len(set(parts)):
            raise DataError('invalid pipe-delimited set')
        return frozenset(parts)
    if value == '':
        raise DataError('missing required value')
    if kind is Decimal:
        try:
            result = Decimal(value)
        except InvalidOperation as exc:
            raise DataError('invalid decimal') from exc
        if not result.is_finite() or result < 0:
            raise DataError('amount/rate must be finite and nonnegative')
        return result
    if kind is date:
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
            raise DataError('date must be YYYY-MM-DD')
        return date.fromisoformat(value)
    if kind is datetime:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if result.tzinfo is None:
            raise DataError('timestamp needs timezone')
        return result
    if kind is bool:
        if value not in {'true', 'false'}:
            raise DataError('boolean must be true or false')
        return value == 'true'
    if kind is int:
        if not value.isdigit() or int(value) <= 0:
            raise DataError('integer must be positive')
        return int(value)
    return value


def read_table(path: Path, model, sample=False):
    hints = get_type_hints(model)
    names = [f.name for f in fields(model)]
    records = []
    with path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        header = reader.fieldnames or []
        extra = set(header) - set(names)
        if len(header) != len(set(header)) or set(names) - set(header) or extra - (OUTPUT_FIELDS if sample else set()):
            raise DataError(f'{path.name}: invalid schema')
        for line, row in enumerate(reader, 2):
            if None in row or any(v is None for v in row.values()):
                raise DataError(f'{path.name}:{line}: malformed CSV row')
            try:
                # Explicit projection excludes every solved-output column.
                record = model(**{name: parse(row[name], hints[name]) for name in names})
                validate_record(record)
            except ValueError as exc:
                raise DataError(f'{path.name}:{line}: {exc}') from exc
            records.append(record)
    return tuple(records)


def validate_record(record):
    for field in fields(record):
        value = getattr(record, field.name)
        if field.name in ENUMS and value not in ENUMS[field.name]:
            raise DataError(f'invalid {field.name}: {value}')
        if field.name in {'currency', 'home_currency', 'from_currency', 'to_currency'} and value not in CURRENCIES:
            raise DataError(f'invalid currency: {value}')
    if isinstance(record, FinancialProfile):
        methods = record.payment_methods_user_will_consider
        if not methods or not methods <= {'full_payment', 'partial_payment', 'installments'}:
            raise DataError('invalid payment preferences')
        if ('installments' in methods) != (record.max_installment_months is not None):
            raise DataError('installment preference/maximum mismatch')
    if isinstance(record, FinancialEvent):
        if record.direction != 'non_cash' and record.settlement_date is None:
            raise DataError('cash event needs settlement_date')
        if record.settlement_date and record.settlement_date < record.event_date:
            raise DataError('settlement before event date')
        if record.status == 'unrealized' and record.direction != 'non_cash':
            raise DataError('unrealized event must be non_cash')
    if isinstance(record, FinanceRequest) and record.desired_completion_date < record.request_date:
        raise DataError('deadline before request date')
    if isinstance(record, ExchangeRate) and record.rate <= 0:
        raise DataError('FX rate must be positive')
    if isinstance(record, PaymentOption):
        if record.payment_amount * record.number_of_payments != record.total_payable_amount:
            raise DataError('offer payments do not sum to total')
        if record.payment_method == 'installments' and (record.number_of_payments < 2 or record.payment_frequency_days is None):
            raise DataError('installment schedule incomplete')
        if record.payment_method == 'full_payment' and (record.number_of_payments != 1 or record.payment_frequency_days is not None):
            raise DataError('invalid full-payment schedule')


def unique(records, key):
    result = {}
    for r in records:
        k = key(r)
        if k in result:
            raise DataError(f'duplicate key: {k}')
        result[k] = r
    return result


def index(records, key):
    result = defaultdict(list)
    for r in records:
        result[key(r)].append(r)
    return {k: tuple(v) for k, v in result.items()}


@dataclass
class Dataset:
    profiles: dict[str, FinancialProfile]
    events: dict[str, FinancialEvent]
    requests: dict[str, FinanceRequest]
    selected_requests: tuple[FinanceRequest, ...]
    rates: tuple[ExchangeRate, ...]
    events_by_user: dict[str, tuple[FinancialEvent, ...]]
    messages_by_user: dict[str, tuple[Message, ...]]
    images_by_user: dict[str, tuple[ImageReference, ...]]
    options_by_request: dict[str, tuple[PaymentOption, ...]]
    missing_images: frozenset[str]


def load_dataset(root: Path, request_file: str = 'requests.csv') -> Dataset:
    if request_file not in {'requests.csv', 'sample_requests.csv'}:
        raise DataError('select requests.csv or sample_requests.csv')
    profiles = unique(read_table(root/'financial_profiles.csv', FinancialProfile), lambda r: r.user_id)
    events = unique(read_table(root/'financial_events.csv', FinancialEvent), lambda r: r.event_id)
    request_tables = {name: read_table(root/name, FinanceRequest, sample=name.startswith('sample_'))
                      for name in ('requests.csv', 'sample_requests.csv')}
    requests = unique(sum(request_tables.values(), ()), lambda r: r.request_id)
    rates = read_table(root/'exchange_rates.csv', ExchangeRate)
    unique(rates, lambda r: (r.rate_date, r.from_currency, r.to_currency))
    messages = read_table(root/'messages.csv', Message)
    images = read_table(root/'images.csv', ImageReference)
    options = read_table(root/'request_payment_options.csv', PaymentOption)
    for records, key in ((messages, 'message_id'), (images, 'image_id'), (options, 'payment_option_id')):
        unique(records, lambda r: getattr(r, key))
    for r in (*requests.values(), *events.values(), *messages, *images):
        if r.user_id not in profiles:
            raise DataError(f'unknown user {r.user_id}')
    for r in (*messages, *images, *options):
        if r.request_id:
            q = requests.get(r.request_id)
            if q is None or (hasattr(r, 'user_id') and r.user_id != q.user_id):
                raise DataError(f'invalid request join {r.request_id}')
    for r in (*messages, *images, *events.values()):
        target = getattr(r, 'related_event_id', None) or getattr(r, 'linked_event_id', None)
        if target:
            e = events.get(target)
            if e is None or e.user_id != r.user_id:
                raise DataError(f'invalid event join {target}')
    for e in events.values():
        seen = {e.event_id}
        parent = e.linked_event_id
        while parent:
            if parent in seen:
                raise DataError(f'cyclic event link {e.event_id}')
            seen.add(parent)
            if events[parent].event_date > e.event_date:
                raise DataError(f'link points to later event {e.event_id}')
            parent = events[parent].linked_event_id
    option_index = index(options, lambda r: r.request_id)
    for q in requests.values():
        offers = option_index.get(q.request_id, ())
        if not 2 <= len(offers) <= 4:
            raise DataError(f'{q.request_id}: expected 2-4 offers')
        for o in offers:
            if o.total_payable_amount != q.requested_amount + o.financing_fee or o.first_payment_date < q.request_date:
                raise DataError(f'{o.payment_option_id}: invalid offer amount/date')
    return Dataset(profiles, events, requests, request_tables[request_file], rates,
                   index(events.values(), lambda r: r.user_id), index(messages, lambda r: r.user_id),
                   index(images, lambda r: r.user_id), option_index,
                   frozenset(i.image_id for i in images if not (root/'media'/'images'/f'{i.image_id}.png').is_file()))
