from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from statistics import median
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.classification import EmailClassification
from app.models.contract import Contract
from app.models.email import Email
from app.models.email_thread_link import EmailThreadLink
from app.models.stakeholder import Stakeholder
from app.schemas.advanced_analytics import (
    Anomaly,
    AnomalyList,
    BottleneckPrediction,
    CompletionPrediction,
    ContractInsights,
    EscalationPattern,
    ProcessImprovement,
    RiskAlert,
    RiskFactor,
    RiskFactors,
    RiskMatrix,
    RiskMatrixPoint,
    RiskTrend,
    RiskTrendPoint,
    SentimentByEntity,
    SentimentPoint,
    SentimentTimeline,
    WeeklyInsights,
    WhatIfResult,
    WorkloadForecast,
)
from app.services.ai_service import get_ai_service
from app.services.cache_service import cache_get, cache_set

settings = get_settings()


def _parse_dt(val) -> datetime | None:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    try:
        return datetime.fromisoformat(str(val).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _stage_name(val) -> str | None:
    STAGES = [
        "Request", "Legal Review", "Finance Review",
        "Procurement/Compliance", "Redline Negotiation",
        "Leadership Sign-off", "Repository & Obligation Tracking",
    ]
    if val is None:
        return None
    if isinstance(val, int) and 1 <= val <= len(STAGES):
        return STAGES[val - 1]
    return str(val)


# ── Sentiment Analytics ──────────────────────────────────────────────────────

async def get_sentiment_timeline(db: AsyncSession, contract_id: UUID) -> SentimentTimeline:
    contract = await db.get(Contract, contract_id)
    if contract is None:
        return SentimentTimeline(contract_id=str(contract_id), points=[])

    if not contract.thread_id:
        return SentimentTimeline(contract_id=str(contract_id), points=[])

    email_rows = await db.execute(
        select(Email, EmailClassification)
        .join(EmailThreadLink, EmailThreadLink.email_id == Email.id)
        .outerjoin(EmailClassification, EmailClassification.email_id == Email.id)
        .where(EmailThreadLink.thread_id == contract.thread_id)
        .order_by(Email.date.asc())
    )
    rows = email_rows.all()

    history = contract.stage_history or []

    def _current_stage(dt: datetime | None) -> str | None:
        if dt is None:
            return None
        aware_dt = dt if dt.tzinfo else dt.replace(tzinfo=UTC)
        for i, entry in enumerate(history):
            entered = _parse_dt(entry.get("date"))
            exited = _parse_dt(history[i + 1].get("date")) if i + 1 < len(history) else None
            if entered and entered <= aware_dt and (exited is None or aware_dt < exited):
                return _stage_name(entry.get("stage"))
        return None

    sentiment_scores = {"positive": 1.0, "neutral": 0.5, "negative": 0.0}
    points = []
    for email, classification in rows:
        if classification is None:
            continue
        sentiment = classification.sentiment or "neutral"
        score = sentiment_scores.get(sentiment.lower(), 0.5)
        points.append(
            SentimentPoint(
                date=email.date,
                stage=_current_stage(email.date),
                sentiment=sentiment,
                score=score,
                email_id=str(email.id),
            )
        )
    return SentimentTimeline(contract_id=str(contract_id), points=points)


async def get_sentiment_by_stakeholder(db: AsyncSession) -> list[SentimentByEntity]:
    rows = list(
        (
            await db.execute(
                select(Email.from_address, EmailClassification.sentiment)
                .join(EmailClassification, EmailClassification.email_id == Email.id)
            )
        ).all()
    )
    data: dict[str, list[str]] = defaultdict(list)
    for addr, sentiment in rows:
        data[addr].append(sentiment or "neutral")

    result = []
    for addr, sentiments in data.items():
        counts = Counter(sentiments)
        total = len(sentiments)
        scores = {"positive": 1.0, "neutral": 0.5, "negative": 0.0}
        avg = sum(scores.get(s.lower(), 0.5) for s in sentiments) / total
        result.append(
            SentimentByEntity(
                entity=addr,
                entity_type="stakeholder",
                avg_sentiment_score=round(avg, 3),
                positive_count=counts.get("positive", 0),
                neutral_count=counts.get("neutral", 0),
                negative_count=counts.get("negative", 0),
            )
        )
    return result


async def get_sentiment_by_stage(db: AsyncSession) -> list[SentimentByEntity]:
    contracts = list((await db.execute(select(Contract))).scalars().all())
    stage_sentiments: dict[str, list[str]] = defaultdict(list)

    for contract in contracts:
        if not contract.thread_id:
            continue
        history = contract.stage_history or []
        email_rows = await db.execute(
            select(Email, EmailClassification)
            .join(EmailThreadLink, EmailThreadLink.email_id == Email.id)
            .outerjoin(EmailClassification, EmailClassification.email_id == Email.id)
            .where(EmailThreadLink.thread_id == contract.thread_id)
            .order_by(Email.date.asc())
        )
        for email, cls in email_rows.all():
            if cls is None or not email.date:
                continue
            email_dt = email.date if email.date.tzinfo else email.date.replace(tzinfo=UTC)
            for i, entry in enumerate(history):
                entered = _parse_dt(entry.get("date"))
                exited = _parse_dt(history[i + 1].get("date")) if i + 1 < len(history) else None
                if entered and entered <= email_dt and (exited is None or email_dt < exited):
                    stage = _stage_name(entry.get("stage")) or "Unknown"
                    stage_sentiments[stage].append(cls.sentiment or "neutral")
                    break

    result = []
    scores_map = {"positive": 1.0, "neutral": 0.5, "negative": 0.0}
    for stage, sentiments in stage_sentiments.items():
        counts = Counter(sentiments)
        total = len(sentiments)
        avg = sum(scores_map.get(s.lower(), 0.5) for s in sentiments) / total
        result.append(
            SentimentByEntity(
                entity=stage,
                entity_type="stage",
                avg_sentiment_score=round(avg, 3),
                positive_count=counts.get("positive", 0),
                neutral_count=counts.get("neutral", 0),
                negative_count=counts.get("negative", 0),
            )
        )
    return result


async def get_escalation_patterns(db: AsyncSession) -> list[EscalationPattern]:
    contracts = list((await db.execute(select(Contract))).scalars().all())
    neg_sequences: list[float] = []

    for contract in contracts:
        if not contract.thread_id:
            continue
        email_rows = await db.execute(
            select(Email, EmailClassification)
            .join(EmailThreadLink, EmailThreadLink.email_id == Email.id)
            .outerjoin(EmailClassification, EmailClassification.email_id == Email.id)
            .where(EmailThreadLink.thread_id == contract.thread_id)
            .order_by(Email.date.asc())
        )
        rows = email_rows.all()
        for i in range(1, len(rows)):
            _, prev_cls = rows[i - 1]
            email, curr_cls = rows[i]
            if (
                prev_cls and curr_cls
                and prev_cls.sentiment == "negative"
                and curr_cls.sentiment == "negative"
                and email.date
            ):
                neg_sequences.append(1.0)

    return [
        EscalationPattern(
            pattern_type="consecutive_negative",
            description="Two or more consecutive negative-sentiment emails, indicating escalation",
            frequency=len(neg_sequences),
            avg_lead_time_hours=24.0,
            examples=[],
        )
    ]


async def get_sentiment_correlation(db: AsyncSession) -> dict:
    """Correlate avg sentiment score with cycle time."""
    contracts = list((await db.execute(select(Contract))).scalars().all())
    data_points = []
    for contract in contracts:
        if not contract.thread_id:
            continue
        history = contract.stage_history or []
        if not history:
            continue
        first = _parse_dt(history[0].get("date"))
        last = _parse_dt(history[-1].get("date"))
        if not first or not last:
            continue
        cycle_days = (last - first).total_seconds() / 86400

        email_rows = await db.execute(
            select(EmailClassification.sentiment)
            .join(Email, Email.id == EmailClassification.email_id)
            .join(EmailThreadLink, EmailThreadLink.email_id == Email.id)
            .where(EmailThreadLink.thread_id == contract.thread_id)
        )
        sentiments = [r[0] or "neutral" for r in email_rows.all()]
        if not sentiments:
            continue
        scores = {"positive": 1.0, "neutral": 0.5, "negative": 0.0}
        avg_score = sum(scores.get(s.lower(), 0.5) for s in sentiments) / len(sentiments)
        data_points.append((avg_score, cycle_days))

    if len(data_points) < 2:
        return {"correlation": None, "description": "Insufficient data"}

    xs = [p[0] for p in data_points]
    ys = [p[1] for p in data_points]
    n = len(data_points)
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in data_points)
    dx = (sum((x - mx) ** 2 for x in xs)) ** 0.5
    dy = (sum((y - my) ** 2 for y in ys)) ** 0.5
    corr = round(num / (dx * dy), 3) if dx * dy > 0 else None
    return {
        "correlation": corr,
        "description": "Negative correlation: more negative sentiment → longer cycle time",
        "sample_count": n,
    }


# ── Risk Scoring ─────────────────────────────────────────────────────────────

async def get_risk_matrix(db: AsyncSession) -> RiskMatrix:
    contracts = list((await db.execute(select(Contract))).scalars().all())
    points = []
    for c in contracts:
        if c.risk_score is None:
            continue
        history = c.stage_history or []
        cycle_days = 0.0
        if history:
            first = _parse_dt(history[0].get("date"))
            last = _parse_dt(history[-1].get("date"))
            if first and last:
                cycle_days = (last - first).total_seconds() / 86400
        points.append(
            RiskMatrixPoint(
                contract_id=str(c.id),
                agreement_name=c.agreement_name,
                risk_score=c.risk_score,
                cycle_time_days=round(cycle_days, 2),
                current_stage=c.current_stage,
            )
        )
    return RiskMatrix(points=points)


async def get_risk_factors_breakdown(db: AsyncSession, contract_id: UUID) -> RiskFactors:
    contract = await db.get(Contract, contract_id)
    if contract is None:
        return RiskFactors(contract_id=str(contract_id), overall_risk_score=0.0, factors=[])

    factors = []
    overall = contract.risk_score or 0.0

    # SLA breach factor
    if contract.sla_breached:
        factors.append(RiskFactor(factor="SLA Breach", weight=0.3, description="Contract has breached SLA"))

    # Key clause issues
    clauses = contract.key_clauses or []
    risky_clauses = [c for c in clauses if isinstance(c, dict) and c.get("risk_flag")]
    if risky_clauses:
        factors.append(
            RiskFactor(
                factor="Clause Issues",
                weight=0.25,
                description=f"{len(risky_clauses)} risky clauses detected",
            )
        )

    # Complexity
    if contract.complexity_score and contract.complexity_score > 0.7:
        factors.append(
            RiskFactor(
                factor="High Complexity",
                weight=0.2,
                description=f"Complexity score: {contract.complexity_score:.2f}",
            )
        )

    # Delay reasons
    delay_reasons = contract.delay_reasons or []
    if delay_reasons:
        factors.append(
            RiskFactor(
                factor="Delay History",
                weight=0.15,
                description=f"{len(delay_reasons)} delay reasons recorded",
            )
        )

    if not factors:
        factors.append(RiskFactor(factor="General Risk", weight=1.0, description="Overall risk assessment"))

    return RiskFactors(contract_id=str(contract_id), overall_risk_score=overall, factors=factors)


async def get_risk_trend(db: AsyncSession) -> RiskTrend:
    contracts = list((await db.execute(select(Contract))).scalars().all())
    buckets: dict[str, list[float]] = defaultdict(list)
    for c in contracts:
        if c.risk_score is None or not c.created_at:
            continue
        key = c.created_at.strftime("%Y-%m")
        buckets[key].append(c.risk_score)

    points = [
        RiskTrendPoint(
            period=k,
            avg_risk_score=round(sum(v) / len(v), 3),
            high_risk_count=sum(1 for s in v if s > 0.7),
        )
        for k, v in sorted(buckets.items())
    ]
    return RiskTrend(points=points)


async def get_high_risk_alerts(db: AsyncSession, threshold: float = 0.7) -> list[RiskAlert]:
    contracts = list(
        (
            await db.execute(
                select(Contract)
                .where(Contract.risk_score >= threshold)
                .order_by(Contract.risk_score.desc())
            )
        ).scalars().all()
    )
    alerts = []
    for c in contracts:
        reasons = []
        if c.sla_breached:
            reasons.append("SLA breached")
        if c.delay_reasons:
            reasons.extend(str(r) for r in (c.delay_reasons or [])[:3])
        if not reasons:
            reasons.append(f"Risk score {c.risk_score:.2f}")
        alerts.append(
            RiskAlert(
                contract_id=str(c.id),
                agreement_name=c.agreement_name,
                risk_score=c.risk_score or 0.0,
                reasons=reasons,
                current_stage=c.current_stage,
                detected_at=datetime.now(UTC),
            )
        )
    return alerts


# ── Predictive Analytics ─────────────────────────────────────────────────────

async def predict_contract_completion(db: AsyncSession, contract_id: UUID) -> CompletionPrediction:
    cache_key = f"analytics:predict:completion:{contract_id}"
    cached = await cache_get(cache_key)
    if cached:
        return CompletionPrediction(**cached)

    contract = await db.get(Contract, contract_id)
    if contract is None:
        return CompletionPrediction(
            contract_id=str(contract_id),
            predicted_completion_date=None,
            sla_breach_probability=0.0,
            confidence=0.0,
            reasoning="Contract not found",
        )

    # Use stored predicted_completion if available
    if contract.predicted_completion:
        breach_prob = 0.8 if contract.sla_breached else 0.1
        result = CompletionPrediction(
            contract_id=str(contract_id),
            predicted_completion_date=contract.predicted_completion,
            sla_breach_probability=breach_prob,
            confidence=0.7,
            reasoning=f"Based on current stage: {contract.current_stage}",
        )
        await cache_set(cache_key, result.model_dump(mode="json"), ttl_seconds=3600)
        return result

    # Estimate from stage history
    now = datetime.now(UTC)
    history = contract.stage_history or []
    STAGE_AVG_HOURS = {
        "Request": 24, "Legal Review": 48, "Finance Review": 36,
        "Procurement/Compliance": 96, "Redline Negotiation": 168,
        "Leadership Sign-off": 24, "Repository & Obligation Tracking": 12,
    }
    STAGES = list(STAGE_AVG_HOURS.keys())
    current_idx = 0
    if contract.current_stage and contract.current_stage in STAGES:
        current_idx = STAGES.index(contract.current_stage)
    remaining_hours = sum(list(STAGE_AVG_HOURS.values())[current_idx:])
    predicted = now + timedelta(hours=remaining_hours)
    sla_days = 15
    history_first = _parse_dt(history[0].get("date")) if history else now
    projected_total = (predicted - history_first).total_seconds() / 86400 if history_first else remaining_hours / 24
    breach_prob = min(1.0, max(0.0, (projected_total - sla_days) / sla_days))

    result = CompletionPrediction(
        contract_id=str(contract_id),
        predicted_completion_date=predicted,
        sla_breach_probability=round(breach_prob, 2),
        confidence=0.5,
        reasoning=f"Estimated {remaining_hours:.0f}h remaining based on historical stage averages",
    )
    await cache_set(cache_key, result.model_dump(mode="json"), ttl_seconds=3600)
    return result


async def predict_bottleneck(db: AsyncSession, contract_id: UUID) -> BottleneckPrediction:
    cache_key = f"analytics:predict:bottleneck:{contract_id}"
    cached = await cache_get(cache_key)
    if cached:
        return BottleneckPrediction(**cached)

    contract = await db.get(Contract, contract_id)
    if contract is None:
        return BottleneckPrediction(
            contract_id=str(contract_id),
            predicted_bottleneck_stage="Unknown",
            probability=0.0,
            reasoning="Contract not found",
        )

    # Historical bottleneck analysis
    all_contracts = list((await db.execute(select(Contract))).scalars().all())
    stage_delay_freq: dict[str, int] = defaultdict(int)
    yellow_mins = settings.slr_yellow_minutes
    for c in all_contracts:
        history = c.stage_history or []
        for i, entry in enumerate(history):
            entered = _parse_dt(entry.get("date"))
            exited = _parse_dt(history[i + 1].get("date")) if i + 1 < len(history) else None
            if entered and exited:
                mins = (exited - entered).total_seconds() / 60
                if mins > yellow_mins:
                    stage = _stage_name(entry.get("stage")) or "Unknown"
                    stage_delay_freq[stage] += 1

    if stage_delay_freq:
        top_stage = max(stage_delay_freq, key=lambda k: stage_delay_freq[k])
        total = sum(stage_delay_freq.values())
        prob = round(stage_delay_freq[top_stage] / max(total, 1), 2)
    else:
        top_stage = "Redline Negotiation"
        prob = 0.33

    result = BottleneckPrediction(
        contract_id=str(contract_id),
        predicted_bottleneck_stage=top_stage,
        probability=prob,
        reasoning=f"'{top_stage}' is historically the most frequent bottleneck stage",
    )
    await cache_set(cache_key, result.model_dump(mode="json"), ttl_seconds=3600)
    return result


async def predict_workload(db: AsyncSession, department: str, period: str = "month") -> WorkloadForecast:
    contracts = list((await db.execute(select(Contract))).scalars().all())
    stakeholders = list(
        (
            await db.execute(
                select(Stakeholder).where(Stakeholder.department == department)
            )
        ).scalars().all()
    )
    dept_addrs = {s.email_address for s in stakeholders}
    dept_addrs.update(s.name for s in stakeholders if s.name)

    active = sum(
        1 for c in contracts
        if c.current_stage and c.current_stage != "Repository & Obligation Tracking"
        and any(
            e.get("actor") in dept_addrs
            for e in (c.stage_history or [])
        )
    )
    # Simple forecast: assume similar volume next period
    trend = "stable"
    return WorkloadForecast(
        department=department,
        period=period,
        forecast_count=active,
        trend=trend,
    )


async def get_what_if_analysis(db: AsyncSession, contract_id: UUID, scenario: str) -> WhatIfResult:
    cache_key = f"analytics:what_if:{contract_id}:{hash(scenario)}"
    cached = await cache_get(cache_key)
    if cached:
        return WhatIfResult(**cached)

    ai_service = get_ai_service()
    contract = await db.get(Contract, contract_id)
    if contract is None:
        return WhatIfResult(
            contract_id=str(contract_id),
            scenario=scenario,
            original_completion=None,
            new_completion=None,
            time_saved_days=0.0,
            reasoning="Contract not found",
        )

    completion = await predict_contract_completion(db, contract_id)
    prompt_data = {
        "contract": {
            "name": contract.agreement_name,
            "current_stage": contract.current_stage,
            "sla_breached": contract.sla_breached,
            "predicted_completion": completion.predicted_completion_date,
        },
        "scenario": scenario,
    }
    result = await ai_service.complete(
        system_prompt=(
            "You are a contract process analyst. Given a contract and a scenario, estimate the new completion "
            "date and time saved. Return JSON: {\"new_completion_days_offset\": 5, \"time_saved_days\": 3, \"reasoning\": \"...\"}"
        ),
        user_prompt=json.dumps(prompt_data, default=str),
        max_tokens=500,
    )
    offset_days = result.get("new_completion_days_offset", 0)
    saved = result.get("time_saved_days", 0.0)
    new_completion = (
        completion.predicted_completion_date - timedelta(days=float(saved))
        if completion.predicted_completion_date
        else None
    )

    what_if = WhatIfResult(
        contract_id=str(contract_id),
        scenario=scenario,
        original_completion=completion.predicted_completion_date,
        new_completion=new_completion,
        time_saved_days=float(saved),
        reasoning=result.get("reasoning", ""),
    )
    await cache_set(cache_key, what_if.model_dump(mode="json"), ttl_seconds=1800)
    return what_if


# ── Anomaly Detection ────────────────────────────────────────────────────────

async def detect_anomalies(db: AsyncSession) -> AnomalyList:
    anomalies: list[Anomaly] = []
    now = datetime.now(UTC)
    # Anomaly threshold: 10x the SLR yellow threshold (both in minutes)
    anomaly_threshold_mins = settings.slr_yellow_minutes * 10

    contracts = list((await db.execute(select(Contract))).scalars().all())
    for contract in contracts:
        history = contract.stage_history or []
        for i, entry in enumerate(history):
            entered = _parse_dt(entry.get("date"))
            exited = _parse_dt(history[i + 1].get("date")) if i + 1 < len(history) else now
            if entered and exited:
                mins = (exited - entered).total_seconds() / 60
                if mins > anomaly_threshold_mins:
                    anomalies.append(
                        Anomaly(
                            anomaly_type="long_stage_duration",
                            severity="high",
                            entity_id=str(contract.id),
                            entity_type="contract",
                            description=(
                                f"Contract '{contract.agreement_name}' spent {mins/60:.1f}h in "
                                f"stage '{_stage_name(entry.get('stage'))}' (abnormally long)"
                            ),
                            detected_at=now,
                            recommendation="Review and expedite this contract stage",
                        )
                    )

        # Detect backward transitions
        stage_indices = []
        STAGES = [
            "Request", "Legal Review", "Finance Review",
            "Procurement/Compliance", "Redline Negotiation",
            "Leadership Sign-off", "Repository & Obligation Tracking",
        ]
        for entry in history:
            sn = _stage_name(entry.get("stage"))
            if sn in STAGES:
                stage_indices.append(STAGES.index(sn))
        for i in range(1, len(stage_indices)):
            if stage_indices[i] < stage_indices[i - 1]:
                anomalies.append(
                    Anomaly(
                        anomaly_type="backward_stage_transition",
                        severity="medium",
                        entity_id=str(contract.id),
                        entity_type="contract",
                        description=f"Contract '{contract.agreement_name}' moved backward in lifecycle",
                        detected_at=now,
                        recommendation="Investigate reason for re-review",
                    )
                )
                break

    # Stakeholder response time anomalies
    stakeholders = list((await db.execute(select(Stakeholder))).scalars().all())
    avg_rt_global = 0.0
    rt_values = [s.avg_response_time for s in stakeholders if s.avg_response_time]
    if rt_values:
        avg_rt_global = sum(rt_values) / len(rt_values)
    for s in stakeholders:
        if s.avg_response_time and avg_rt_global > 0:
            if s.avg_response_time > avg_rt_global * 3:
                anomalies.append(
                    Anomaly(
                        anomaly_type="high_response_time",
                        severity="medium",
                        entity_id=str(s.id),
                        entity_type="stakeholder",
                        description=(
                            f"Stakeholder '{s.name}' has avg response time "
                            f"{s.avg_response_time:.1f}h vs global avg {avg_rt_global:.1f}h"
                        ),
                        detected_at=now,
                        recommendation="Check if stakeholder is overloaded or has availability issues",
                    )
                )

    return AnomalyList(anomalies=anomalies, total=len(anomalies))


# ── AI Insights Engine ───────────────────────────────────────────────────────

async def generate_weekly_insights(db: AsyncSession) -> WeeklyInsights:
    cache_key = "analytics:insights:weekly"
    cached = await cache_get(cache_key)
    if cached:
        return WeeklyInsights(**cached)

    now = datetime.now(UTC)
    week_start = now - timedelta(days=7)

    contracts = list((await db.execute(select(Contract))).scalars().all())
    recent_completed = [
        c for c in contracts
        if c.updated_at and c.updated_at >= week_start
        and c.current_stage == "Repository & Obligation Tracking"
    ]
    breached = [c for c in contracts if c.sla_breached and c.updated_at and c.updated_at >= week_start]
    high_risk = [c for c in contracts if c.risk_score and c.risk_score > 0.7]

    prompt_data = {
        "completed_contracts": len(recent_completed),
        "sla_breaches_this_week": len(breached),
        "high_risk_active": len(high_risk),
        "total_active": sum(1 for c in contracts if c.current_stage and c.current_stage != "Repository & Obligation Tracking"),
    }

    ai_service = get_ai_service()
    result = await ai_service.complete(
        system_prompt=(
            "You are a contract management AI. Generate a weekly insights report. "
            "Return JSON: {\"accomplishments\": [], \"current_risks\": [], "
            "\"bottleneck_trends\": [], \"recommendations\": [], \"stakeholder_highlights\": []}"
        ),
        user_prompt=json.dumps(prompt_data, default=str),
        max_tokens=800,
    )

    insights = WeeklyInsights(
        week_start=week_start,
        week_end=now,
        accomplishments=result.get("accomplishments") or [f"{len(recent_completed)} contracts completed this week"],
        current_risks=result.get("current_risks") or [f"{len(breached)} SLA breaches this week"],
        bottleneck_trends=result.get("bottleneck_trends") or ["Redline Negotiation remains top bottleneck"],
        recommendations=result.get("recommendations") or ["Consider expediting high-risk contracts"],
        stakeholder_highlights=result.get("stakeholder_highlights") or [],
        generated_at=now,
    )
    await cache_set(cache_key, insights.model_dump(mode="json"), ttl_seconds=3600)
    return insights


async def generate_contract_insights(db: AsyncSession, contract_id: UUID) -> ContractInsights:
    cache_key = f"analytics:insights:contract:{contract_id}"
    cached = await cache_get(cache_key)
    if cached:
        return ContractInsights(**cached)

    contract = await db.get(Contract, contract_id)
    if contract is None:
        return ContractInsights(
            contract_id=str(contract_id),
            insights=[],
            risk_flags=[],
            recommendations=[],
            generated_at=datetime.now(UTC),
        )

    ai_service = get_ai_service()
    prompt_data = {
        "contract": {
            "name": contract.agreement_name,
            "type": contract.agreement_type,
            "stage": contract.current_stage,
            "sla_breached": contract.sla_breached,
            "risk_score": contract.risk_score,
            "complexity_score": contract.complexity_score,
            "delay_reasons": contract.delay_reasons,
            "key_clauses": contract.key_clauses,
        }
    }
    result = await ai_service.complete(
        system_prompt=(
            "You are a contract analyst. Analyze this contract and return insights. "
            "Return JSON: {\"insights\": [], \"risk_flags\": [], \"recommendations\": []}"
        ),
        user_prompt=json.dumps(prompt_data, default=str),
        max_tokens=800,
    )

    insights = ContractInsights(
        contract_id=str(contract_id),
        insights=result.get("insights") or [contract.ai_summary or "No AI summary available"],
        risk_flags=result.get("risk_flags") or (["SLA breached"] if contract.sla_breached else []),
        recommendations=result.get("recommendations") or [],
        generated_at=datetime.now(UTC),
    )
    await cache_set(cache_key, insights.model_dump(mode="json"), ttl_seconds=3600)
    return insights


async def generate_process_improvement_suggestions(db: AsyncSession) -> list[ProcessImprovement]:
    cache_key = "analytics:insights:process_improvements"
    cached = await cache_get(cache_key)
    if cached:
        return [ProcessImprovement(**item) for item in cached]

    contracts = list((await db.execute(select(Contract))).scalars().all())
    breach_rate = sum(1 for c in contracts if c.sla_breached) / max(len(contracts), 1)

    ai_service = get_ai_service()
    prompt_data = {
        "total_contracts": len(contracts),
        "sla_breach_rate": round(breach_rate * 100, 2),
        "avg_risk": round(
            sum(c.risk_score for c in contracts if c.risk_score) / max(sum(1 for c in contracts if c.risk_score), 1),
            2,
        ),
    }
    result = await ai_service.complete(
        system_prompt=(
            "You are a process improvement consultant specializing in legal contract management. "
            "Based on analytics data, suggest process improvements. "
            "Return JSON: {\"improvements\": [{\"category\": \"...\", \"suggestion\": \"...\", "
            "\"estimated_impact\": \"...\", \"priority\": \"high|medium|low\"}]}"
        ),
        user_prompt=json.dumps(prompt_data, default=str),
        max_tokens=800,
    )
    raw = result.get("improvements") or []
    improvements = [ProcessImprovement(**item) for item in raw if isinstance(item, dict)]
    if not improvements:
        improvements = [
            ProcessImprovement(
                category="SLA Management",
                suggestion="Implement automated SLA alerts at 50% and 80% threshold",
                estimated_impact="Reduce SLA breach rate by ~30%",
                priority="high",
            ),
            ProcessImprovement(
                category="Negotiation",
                suggestion="Standardize liability clause templates to reduce negotiation rounds",
                estimated_impact="Save 2-3 days per contract",
                priority="high",
            ),
        ]
    await cache_set(cache_key, [i.model_dump(mode="json") for i in improvements], ttl_seconds=3600)
    return improvements
