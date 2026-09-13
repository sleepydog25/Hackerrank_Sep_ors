"""Typed evidence adapter. The existing engine alone computes balances and FX."""
from dataclasses import dataclass, replace
from .evidence import EvidenceSource, SourceType, ValidationStatus, Reason
from .evidence_validation import EvidenceContext
from .evidence_reconciliation import reconcile_evidence
from .evidence_state import NormalizedEvidenceState
from .models import ForecastResult
from .forecast import forecast
from .fx import RateBook


@dataclass(frozen=True)
class EvidenceForecastResult:
    forecast: ForecastResult
    normalized: NormalizedEvidenceState
    source_issues: tuple[str, ...]


def forecast_with_evidence(profile,request,events,rates,sources,batches):
    sources=tuple(sources); batches=tuple(batches)
    key=lambda s:(s.source_type,s.source_id)
    if len({key(s) for s in sources})!=len(sources):raise ValueError('duplicate canonical evidence source')
    if len({key(b.source) for b in batches})!=len(batches):raise ValueError('duplicate evidence batch')
    issues=[]; candidates=[]
    for batch in batches:
        if batch.source not in sources or any(c.source!=batch.source for c in batch.candidates):
            issues.append(f'{batch.source.source_id}: {Reason.SOURCE_MISMATCH}')
            continue
        candidates.extend(batch.candidates)
    state=reconcile_evidence(candidates,EvidenceContext(request,tuple(events),sources))
    for s in sources:
        if s.user_id!=request.user_id or s.request_id not in (None,request.request_id):continue
        if s.observed_at and s.observed_at.date()>request.request_date:continue
        batch=next((b for b in batches if b.source==s),None)
        if batch is None or not batch.exhaustive:
            issues.append(f'{s.source_id}: {Reason.SOURCE_NOT_EXHAUSTED}')
        if batch is not None and not batch.candidates:issues.append(f'{s.source_id}: {Reason.NO_CANDIDATES}')
    for decision in state.decisions:
        if decision.status==ValidationStatus.UNRESOLVED:
            issues.append(f'{decision.candidate.source.source_id} -> {decision.candidate.fact_id}: {decision.reason}')
    result=forecast(profile,request,state.events,rates,normalized_state=state)
    notes=tuple(f'{d.candidate.source.source_id} -> {d.candidate.fact_id}: {d.status}: {d.reason}; label={d.candidate.original_label}' for d in state.decisions)
    result=replace(result,issues=tuple(dict.fromkeys((*result.issues,*issues))),
                   reconciliation_notes=(*result.reconciliation_notes,*notes))
    return EvidenceForecastResult(result,state,tuple(issues))


def dataset_sources(dataset,request):
    sources=[]
    for m in dataset.messages_by_user.get(request.user_id,()):
        if m.request_id in (None,request.request_id):
            sources.append(EvidenceSource(SourceType.MESSAGE,m.message_id,m.user_id,m.request_id,m.related_event_id,m.sent_at))
    for i in dataset.images_by_user.get(request.user_id,()):
        if i.request_id in (None,request.request_id):
            sources.append(EvidenceSource(SourceType.IMAGE,i.image_id,i.user_id,i.request_id,i.related_event_id))
    return tuple(sources)


def forecast_dataset_evidence(dataset,request,batches):
    return forecast_with_evidence(dataset.profiles[request.user_id],request,dataset.events_by_user.get(request.user_id,()),
                                  RateBook(dataset.rates),dataset_sources(dataset,request),batches)
