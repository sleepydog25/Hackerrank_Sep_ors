from datetime import date
from decimal import Decimal
from .models import ExchangeRate


class MissingRate(ValueError):
    pass


class RateBook:
    def __init__(self, rates: tuple[ExchangeRate, ...] = ()):
        self.rates = {}
        for r in rates:
            key = (r.rate_date, r.from_currency, r.to_currency)
            if key in self.rates:
                raise ValueError(f'duplicate FX key {key}')
            self.rates[key] = r.rate

    def convert(self, amount: Decimal, currency: str, home: str,
                settlement_date: date) -> tuple[Decimal, Decimal]:
        if currency == home:
            return amount, Decimal(1)
        key = (settlement_date, currency, home)
        if key not in self.rates:
            raise MissingRate(f'missing FX {settlement_date} {currency}->{home}')
        rate = self.rates[key]
        return amount * rate, rate
