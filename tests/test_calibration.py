"""Financial invariants for calibration; entirely synthetic evidence."""
import random
import unittest
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal as D
from test_core import START, event, history, profile, request, run
from buy_or_wait.forecast import simulate
from buy_or_wait.income import supplement, EvidenceStrength as E
from buy_or_wait.policy import DEFAULT_POLICY, ForecastPolicy
from buy_or_wait.recurrence import infer_series
from buy_or_wait.spending import estimate
from evaluation.experiments import replay_capacity


def payroll(id, day, amount='500', description='Payroll', status='settled'):
    return event(id, amount, day, status, 'credit', 'salary', description, event_type='income')


def groceries():
    return tuple(event(str(n), '70', START-timedelta(days=28-7*n), 'settled',
                       category='groceries', description='Neighborhood market') for n in range(4))


class IncomeEvidenceTests(unittest.TestCase):
    def test_first_prorated_salary_and_confirmed_next(self):
        first=payroll('first',date(2026,3,15),'200','First prorated salary')
        next_pay=payroll('next',date(2026,4,15),'500','Next confirmed salary','scheduled')
        result=run([first,next_pay])
        self.assertEqual([(f.date,f.amount) for f in result.cash_flows],
                         [(date(2026,m,15),D(500)) for m in (4,5,6)])
        self.assertEqual(sum(not f.inferred for f in result.cash_flows),1)
        self.assertTrue(any('SUPPORTED_RECURRING' in n for n in result.reconciliation_notes))

    def test_one_payroll_without_confirmation_insufficient(self):
        rows=[payroll('one',date(2026,3,15))]
        added,evidence=supplement(rows,[],[],START,DEFAULT_POLICY)
        self.assertFalse(added)
        self.assertEqual(evidence[0].state,E.INSUFFICIENT)
        self.assertFalse(run(rows).cash_flows)

    def test_equal_payrolls_from_different_named_sources_do_not_bridge(self):
        rows=[payroll('old',date(2026,3,15),'500','Acme payroll'),
              payroll('new',date(2026,4,15),'500','Beta confirmed payroll','scheduled')]
        self.assertFalse(any(f.inferred for f in run(rows).cash_flows))

    def test_period_label_change_does_not_split_payroll(self):
        rows=[payroll(str(m),date(2026,m,15),'500',f'Acme payroll 2026-0{m}') for m in (1,2,3)]
        self.assertEqual(sum(f.amount for f in run(rows).cash_flows),D(1500))

    def test_two_equal_payrolls_are_separate_experimental_policy(self):
        rows=[payroll(str(m),date(2026,m,15)) for m in (2,3)]
        self.assertFalse(run(rows).cash_flows)
        result=run(rows,policy=replace(DEFAULT_POLICY,income_policy='two_payrolls'))
        self.assertEqual(sum(f.amount for f in result.cash_flows),D(1500))

    def test_stable_three_payrolls_supported(self):
        rows=history('salary','credit','Payroll','500')
        series=infer_series(rows,START)
        _,evidence=supplement(rows,[],series,START,DEFAULT_POLICY)
        self.assertTrue(all(e.state==E.SUPPORTED_RECURRING for e in evidence))

    def test_confirmation_does_not_prove_wrong_month_or_amount(self):
        for next_date,next_amount in [(date(2026,5,15),'500'),(date(2026,4,15),'1500'),(date(2026,4,15),'0')]:
            with self.subTest(next_date=next_date,amount=next_amount):
                result=run([payroll('old',date(2026,3,15)),
                            payroll('next',next_date,next_amount,'Next salary','scheduled')])
                self.assertFalse(any(f.inferred for f in result.cash_flows))

    def test_final_payroll_blocks_continuation_but_confirmed_credit_remains(self):
        rows=[payroll('last',date(2026,3,15),'500','Final payroll')]
        next_pay=payroll('next',date(2026,4,15),'500','Next salary','scheduled')
        result=run([*rows,next_pay])
        self.assertEqual(len(result.cash_flows),1)
        self.assertFalse(result.cash_flows[0].inferred)
        _,evidence=supplement(rows,[next_pay],[],START,DEFAULT_POLICY)
        self.assertEqual([e.state for e in evidence],[E.TERMINATED,E.CONFIRMED])

    def test_freelance_history_does_not_confirm_future_work(self):
        rows=[payroll(str(m),date(2026,m,15),'500','Freelance contract invoice') for m in (1,2,3)]
        self.assertFalse(run(rows).cash_flows)
        self.assertTrue(run(rows,policy=replace(DEFAULT_POLICY,income_policy='freelance')).cash_flows)

    def test_bonus_commission_reimbursement_one_off(self):
        for description in ['Salary bonus','Sales commission','Work reimbursement']:
            rows=[payroll(str(m),date(2026,m,15),'500',description) for m in (1,2,3)]
            _,evidence=supplement(rows,[],[],START,DEFAULT_POLICY)
            self.assertTrue(all(e.state==E.ONE_OFF for e in evidence))
            self.assertFalse(run(rows).cash_flows)


class SpendingTests(unittest.TestCase):
    def test_all_estimators_on_constant_weekly_budget(self):
        daily={e.settlement_date:e.amount for e in groceries()}
        for method in ['p75_daily','mean_daily','trimmed_daily','median_daily','weekly_p75','cadence']:
            amount,cadence,gap,_=estimate(daily,START,replace(DEFAULT_POLICY,variable_estimator=method))
            self.assertEqual(amount,D(70 if method=='cadence' else 10))
            self.assertEqual(cadence,'interval' if method=='cadence' else 'daily')
            self.assertEqual(gap,7)

    def test_mean_is_observed_total_over_covered_calendar_days(self):
        daily={START-timedelta(days=d):D(a) for d,a in [(28,70),(20,140),(7,70)]}
        amount,_,_,reason=estimate(daily,START,DEFAULT_POLICY)
        self.assertEqual(amount,D(10))
        self.assertIn('exposure=28',reason)

    def test_outlier_is_not_discarded_without_evidence(self):
        daily={START-timedelta(days=7*(n+1)):D(700 if n==0 else 70) for n in range(10)}
        mean=estimate(daily,START,DEFAULT_POLICY)[0]
        trimmed=estimate(daily,START,replace(DEFAULT_POLICY,variable_estimator='trimmed_daily'))[0]
        median=estimate(daily,START,replace(DEFAULT_POLICY,variable_estimator='median_daily'))[0]
        self.assertEqual(mean,D(19))
        self.assertEqual(trimmed,D(10))
        self.assertEqual(median,D(10))

    def test_sparse_history_does_not_create_spending_series(self):
        self.assertFalse(infer_series(groceries()[:2],START))

    def test_history_excludes_today_future_and_old_outlier(self):
        base=groceries()
        extra=[event('today','10000',START,'settled',category='groceries'),
               event('future','10000',START+timedelta(days=1),'settled',category='groceries'),
               event('old','10000',START-timedelta(days=181),'settled',category='groceries')]
        self.assertEqual(infer_series(base,START),infer_series(base+tuple(extra),START))

    def test_occurrence_projection_does_not_accrue_each_day(self):
        result=run(groceries(),policy=replace(DEFAULT_POLICY,variable_estimator='cadence'))
        self.assertEqual(result.cash_flows[0].date,START)
        self.assertEqual(result.cash_flows[1].date,START+timedelta(days=7))
        self.assertEqual(result.cash_flows[0].amount,D(70))


class OverlapAndGroupingTests(unittest.TestCase):
    def hold(self,**kw):
        args=dict(id='hold',amount='70',day=START+timedelta(days=2),status='pending',category='groceries',description='Neighborhood market')
        args.update(kw)
        return event(**args)

    def test_identified_nearby_pending_occurrence_substitutes_budget(self):
        rows=[*groceries(),self.hold()]
        before=run(rows,policy=replace(DEFAULT_POLICY,pending_overlap=False))
        after=run(rows)
        self.assertEqual(sum(f.amount for f in before.cash_flows)-sum(f.amount for f in after.cash_flows),D(70))
        self.assertEqual(sum(f.amount for f in after.cash_flows if f.source=='hold'),D(70))
        self.assertEqual(sum(f.amount for f in after.cash_flows if f.inferred),D(840))

    def test_category_alone_large_or_distant_charge_not_offset(self):
        for hold in [self.hold(description='Generic card authorization'),self.hold(amount='700'),self.hold(day=START+timedelta(days=20))]:
            with self.subTest(hold=hold):
                self.assertEqual(sum(f.amount for f in run([*groceries(),hold]).cash_flows if f.inferred),D(910))

    def test_superseded_hold_cannot_offset_budget(self):
        hold=self.hold(description='Neighborhood market authorization',linked='0')
        posted=self.hold(id='posted',linked='hold',status='settled')
        result=run([*groceries(),hold,posted])
        self.assertFalse(any(f.source=='hold' for f in result.cash_flows))
        self.assertEqual(sum(f.amount for f in result.cash_flows if f.inferred),D(910))

    def test_multiple_holds_cannot_make_category_budget_negative(self):
        result=run([*groceries(),self.hold(),self.hold(id='second')])
        self.assertTrue(all(f.amount>=0 for f in result.cash_flows))
        self.assertEqual(sum(f.amount for f in result.cash_flows if not f.inferred),D(140))

    def test_period_labels_do_not_false_split_same_obligation(self):
        rows=[replace(e,description=f'Flat A rent 2026-0{n}') for n,e in enumerate(history(),1)]
        self.assertEqual(len(infer_series(rows,START)),1)
        self.assertFalse(infer_series(rows,START,ForecastPolicy()))

    def test_distinct_accounts_do_not_false_merge(self):
        rows=[replace(e,event_id=e.event_id+account,description='Loan account '+account) for account in ('17','28') for e in history(category='debt')]
        result=run(rows)
        self.assertEqual(len(result.series),2)
        self.assertEqual(sum(f.amount for f in result.cash_flows),D(600))

    def test_variable_merchants_share_one_category_budget(self):
        rows=[replace(e,description='Shop '+e.event_id) for e in groceries()]
        result=run(rows)
        self.assertEqual(len(result.series),1)
        self.assertEqual(sum(f.amount for f in result.cash_flows),D(910))

    def test_settled_today_fixed_occurrence_not_reintroduced(self):
        start=date(2026,4,5)
        rows=[*history(),event('paid','100',start,'settled')]
        result=run(rows,q=request(start=start))
        self.assertFalse(any(f.date==start for f in result.cash_flows))
        self.assertEqual(sum(f.amount for f in result.cash_flows),D(200))


class CapacityInvariants(unittest.TestCase):
    def test_generated_ledgers_direct_formula_equals_payment_replay(self):
        rng=random.Random(2701)
        for n in range(100):
            rows=[]
            for k in range(8):
                credit=rng.choice([True,False])
                rows.append(event(str(k),str(rng.randrange(0,50000)/100),START+timedelta(days=rng.randrange(91)),
                                  direction='credit' if credit else 'debit',category='salary' if credit else 'rent',
                                  description='Salary' if credit else 'Bill',event_type='income' if credit else 'expense'))
            for timing in ['before_credit','after_credit']:
                q=request(str(rng.randrange(1,200000)/100))
                result=run(rows,p=profile(str(rng.randrange(100,200000)/100),'1'),q=q,
                           policy=replace(DEFAULT_POLICY,candidate_timing=timing))
                self.assertEqual(result.amount_safe_to_pay,replay_capacity(result,q.requested_amount,timing),(n,timing))

    def test_boundary_only_changes_cash_on_removed_day(self):
        rows=[event('last','300',START+timedelta(days=90))]
        self.assertEqual(run(rows,q=request('900')).amount_safe_to_pay,D(600))
        self.assertEqual(run(rows,q=request('900'),policy=replace(DEFAULT_POLICY,horizon_days=89)).amount_safe_to_pay,D(900))

    def test_candidate_order_changes_capacity_without_hiding_debit_breach(self):
        rows=[payroll('salary',START,'500','Next salary','scheduled')]
        after=run(rows,p=profile('200'),q=request('500'))
        before=run(rows,p=profile('200'),q=request('500'),policy=replace(DEFAULT_POLICY,candidate_timing='before_credit'))
        self.assertEqual(after.amount_safe_to_pay,D(500))
        self.assertEqual(before.amount_safe_to_pay,D(100))
        self.assertEqual(before.earliest_date_for_full_payment,START+timedelta(days=1))
