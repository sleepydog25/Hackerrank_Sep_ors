"""Bind accepted scopes to supported history; ambiguity never chooses an amount."""
from dataclasses import replace
from datetime import date
from itertools import combinations
from .evidence import ValidationStatus, Reason
from .evidence_state import SeriesAction
from .income import supplement, payroll_source
from .policy import DEFAULT_POLICY
from .reconcile import reconcile, salary_event
from .recurrence import infer_series, series_description


def matches_series(series, target, all_series, policy=DEFAULT_POLICY):
    if (series.description=='*' or series.category!=target.category
            or series.currency!=target.currency or series.direction!=target.direction):
        return False
    if target.event_id in series.event_ids or target.linked_event_id in series.event_ids:
        return True
    if series_description(target.description,policy.robust_grouping)==series.description:
        return True
    if not salary_event(target):return False
    # A single known employer is not authority to modify a different named job.
    target_source=payroll_source(target.description)
    known_source=payroll_source(series.description)
    if target_source and known_source and target_source!=known_source:return False
    return sum(s.direction=='credit' and s.currency==series.currency for s in all_series)==1


def bind_series_amendments(state, start, policy=DEFAULT_POLICY):
    if not state.series_amendments:return state
    history=reconcile(state.original_events,start)
    series=infer_series(history.history,start,policy,[])
    added,_=supplement(history.history,history.obligations,series,start,policy)
    series+=tuple(added)
    groups={}; unresolved={}
    for rule in state.series_amendments:
        matches=[s for s in series if matches_series(s,rule.target,series,policy)]
        if len(matches)==1:groups.setdefault(matches[0].series_id,[]).append(rule)
        elif len(matches)>1 or rule.action!=SeriesAction.SKIP_OCCURRENCE:
            unresolved[rule.fact_id]=Reason.UNSUPPORTED_SCOPE
    for rules in groups.values():
        for a,b in combinations(rules,2):
            overlap=max(a.effective_date,b.effective_date)<=min(a.end_date or date.max,b.end_date or date.max)
            if overlap and a.action==b.action==SeriesAction.AMOUNT and a.amount!=b.amount:
                unresolved[a.fact_id]=unresolved[b.fact_id]=Reason.CONFLICTING_EVIDENCE
    # An ongoing rule must not overwrite a separately accepted next-pay value.
    # Different scoped facts need explicit precedence; retaining both silently
    # makes the final amount depend on which layer happens to run last.
    for s in series:
        for rule in groups.get(s.series_id,()):
            if rule.action!=SeriesAction.AMOUNT:continue
            for amendment in state.amendments:
                e=amendment.after
                if (amendment.fact_id==rule.fact_id or e is None or e.status=='settled'
                        or not matches_series(s,e,series,policy)):continue
                if (rule.effective_date<=e.settlement_date<=(rule.end_date or date.max)
                        and e.amount!=rule.amount):
                    unresolved[rule.fact_id]=unresolved[amendment.fact_id]=Reason.CONFLICTING_EVIDENCE
    if not unresolved:return state
    # Revert the entire affected fact, including its explicit event correction.
    # Do not leave a partly applied amendment when its recurring scope failed.
    rejected=[a for a in state.amendments if a.fact_id in unresolved]
    originals={a.after.event_id:a.before for a in rejected if a.after}
    events=tuple(originals.get(e.event_id,e) for e in state.events
                 if e.event_id not in originals or originals[e.event_id] is not None)
    decisions=tuple(replace(d,status=ValidationStatus.UNRESOLVED,reason=unresolved[d.candidate.fact_id],fact=None)
                    if d.candidate.fact_id in unresolved else d for d in state.decisions)
    return replace(state,events=events,decisions=decisions,
                   amendments=tuple(a for a in state.amendments if a.fact_id not in unresolved),
                   series_amendments=tuple(r for r in state.series_amendments if r.fact_id not in unresolved),
                   confirmed_credit_ids=state.confirmed_credit_ids-frozenset(originals))
