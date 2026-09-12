"""V1 modeling choices, not fitted to solved labels. See docs/financial-core.md."""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class ForecastPolicy:
    horizon_days: int = 90  # day 0 through day 90 inclusive
    history_days: int = 180
    minimum_observations: int = 3
    monthly_day_tolerance: int = 3
    interval_tolerance_days: int = 2
    maximum_interval_days: int = 35
    stale_income_cycles: Decimal = Decimal('1.5')
    amount_stability_ratio: Decimal = Decimal('1.25')
    variable_quantile: Decimal = Decimal('0.75')
    variable_categories: frozenset[str] = frozenset({'groceries', 'transport', 'dining'})
    cent: Decimal = Decimal('0.01')


DEFAULT_POLICY = ForecastPolicy()
# These are semantic exclusions, not case IDs or exact dataset descriptions.
NONRECURRING_WORDS = ('bonus', 'commission', 'arrears', 'refund', 'reimbursement',
                     'prize', 'lottery', 'windfall', 'internal transfer', 'own account', 'valuation',
                     'sale proceeds', 'one-off', 'one time', 'one-time', 'authorization')
ENDED_INCOME_WORDS = ('final employer', 'final payroll', 'final salary', 'termination', 'employment ended')
