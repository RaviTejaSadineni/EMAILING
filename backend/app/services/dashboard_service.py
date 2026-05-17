from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.classification import EmailClassification
from app.models.contract import Contract
from app.models.email import Email
from app.models.stakeholder import Stakeholder
from app.schemas.dashboard import (
    ActivityFeedItem,
    DashboardFilters,
    DashboardKPIs,
    DistributionItem,
    DistributionResponse,
    TopContract,
    TopStakeholder,
    TrendDataPoint,
    TrendResponse,
)
from app.services.cache_service import cache_get, cache_set


def _parse_dt(val) -> datetime | None:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    try:
        return datetime.fromisoformat(str(val).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


async def get_dashboard_kpis(db: AsyncSession, filters: DashboardFilters | None = None) -> DashboardKPIs:
    cache_key = "analytics:dashboard:kpis"
    cached = await cache_get(cache_key)
    if cached:
        return DashboardKPIs(**cached)

    # Contracts
    contracts = list((await db.execute(select(Contract))).scalars().all())
    total_contracts = len(contracts)
    FINAL_STAGE = "Repository & Obligation Tracking"
    active = sum(1 for c in contracts if c.current_stage and c.current_stage != FINAL_STAGE)
    completed = sum(1 for c in contracts if c.current_stage == FINAL_STAGE)
    stalled = sum(
        1 for c in contracts
        if c.current_stage and c.current_stage != FINAL_STAGE and c.sla_breached
    )

    # Emails
    total_emails = (await db.execute(select(func.count()).select_from(Email))).scalar_one() or 0
    now = datetime.now(UTC)
    week_start = now - timedelta(days=7)
    month_start = now - timedelta(days=30)
    emails_this_week = (
        await db.execute(
            select(func.count()).select_from(Email).where(Email.date >= week_start)
        )
    ).scalar_one() or 0
    emails_this_month = (
        await db.execute(
            select(func.count()).select_from(Email).where(Email.date >= month_start)
        )
    ).scalar_one() or 0

    # Avg cycle time
    cycle_days = []
    for c in contracts:
        history = c.stage_history or []
        if history:
            first = _parse_dt(history[0].get("date"))
            last = _parse_dt(history[-1].get("date"))
            if first and last:
                cycle_days.append((last - first).total_seconds() / 86400)
    avg_cycle_time = round(sum(cycle_days) / len(cycle_days), 2) if cycle_days else 0.0

    # SLA breach rate
    breached = sum(1 for c in contracts if c.sla_breached)
    sla_breach_rate = round(breached / max(total_contracts, 1) * 100, 2)

    # Active negotiations
    active_negotiations = sum(1 for c in contracts if c.current_stage == "Redline Negotiation")

    # Total stakeholders
    total_stakeholders = (await db.execute(select(func.count()).select_from(Stakeholder))).scalar_one() or 0

    # Most active contract type
    type_counts = Counter(c.agreement_type for c in contracts if c.agreement_type)
    most_active_type = type_counts.most_common(1)[0][0] if type_counts else None

    # Avg risk score
    risk_scores = [c.risk_score for c in contracts if c.risk_score is not None]
    avg_risk = round(sum(risk_scores) / len(risk_scores), 2) if risk_scores else 0.0

    kpis = DashboardKPIs(
        total_contracts=total_contracts,
        active_contracts=active,
        completed_contracts=completed,
        stalled_contracts=stalled,
        total_emails=int(total_emails),
        avg_cycle_time_days=avg_cycle_time,
        sla_breach_rate=sla_breach_rate,
        active_negotiations=active_negotiations,
        total_stakeholders=int(total_stakeholders),
        emails_this_week=int(emails_this_week),
        emails_this_month=int(emails_this_month),
        most_active_contract_type=most_active_type,
        avg_risk_score=avg_risk,
        ai_insights_count=0,
    )
    await cache_set(cache_key, kpis.model_dump(mode="json"), ttl_seconds=300)
    return kpis


def _period_key(dt: datetime, period: str) -> str:
    if period == "day":
        return dt.strftime("%Y-%m-%d")
    if period == "week":
        return dt.strftime("%Y-W%W")
    if period == "month":
        return dt.strftime("%Y-%m")
    return dt.strftime("%Y")


async def get_email_volume_trend(
    db: AsyncSession,
    period: str = "day",
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> TrendResponse:
    cache_key = f"analytics:trend:emails:{period}"
    cached = await cache_get(cache_key)
    if cached:
        return TrendResponse(**cached)

    query = select(Email.date)
    if date_from:
        query = query.where(Email.date >= date_from)
    if date_to:
        query = query.where(Email.date <= date_to)
    rows = (await db.execute(query)).all()

    buckets: dict[str, int] = defaultdict(int)
    for (dt,) in rows:
        if dt:
            buckets[_period_key(dt, period)] += 1

    data = [TrendDataPoint(period=k, value=float(v), count=v) for k, v in sorted(buckets.items())]
    result = TrendResponse(data=data, period=period, date_from=date_from, date_to=date_to)
    await cache_set(cache_key, result.model_dump(mode="json"), ttl_seconds=900)
    return result


async def get_contract_creation_trend(
    db: AsyncSession,
    period: str = "month",
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> TrendResponse:
    cache_key = f"analytics:trend:contracts:{period}"
    cached = await cache_get(cache_key)
    if cached:
        return TrendResponse(**cached)

    query = select(Contract.created_at)
    if date_from:
        query = query.where(Contract.created_at >= date_from)
    if date_to:
        query = query.where(Contract.created_at <= date_to)
    rows = (await db.execute(query)).all()

    buckets: dict[str, int] = defaultdict(int)
    for (dt,) in rows:
        if dt:
            buckets[_period_key(dt, period)] += 1

    data = [TrendDataPoint(period=k, value=float(v), count=v) for k, v in sorted(buckets.items())]
    result = TrendResponse(data=data, period=period, date_from=date_from, date_to=date_to)
    await cache_set(cache_key, result.model_dump(mode="json"), ttl_seconds=900)
    return result


async def get_sla_breach_trend(
    db: AsyncSession,
    period: str = "month",
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> TrendResponse:
    cache_key = f"analytics:trend:sla:{period}"
    cached = await cache_get(cache_key)
    if cached:
        return TrendResponse(**cached)

    contracts = list((await db.execute(select(Contract))).scalars().all())
    buckets: dict[str, dict] = defaultdict(lambda: {"total": 0, "breached": 0})
    for c in contracts:
        if not c.created_at:
            continue
        if date_from and c.created_at < date_from:
            continue
        if date_to and c.created_at > date_to:
            continue
        key = _period_key(c.created_at, period)
        buckets[key]["total"] += 1
        if c.sla_breached:
            buckets[key]["breached"] += 1

    data = [
        TrendDataPoint(
            period=k,
            value=round(v["breached"] / max(v["total"], 1) * 100, 2),
            count=v["breached"],
        )
        for k, v in sorted(buckets.items())
    ]
    result = TrendResponse(data=data, period=period, date_from=date_from, date_to=date_to)
    await cache_set(cache_key, result.model_dump(mode="json"), ttl_seconds=900)
    return result


async def get_avg_cycle_time_trend(
    db: AsyncSession,
    period: str = "month",
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> TrendResponse:
    cache_key = f"analytics:trend:cycle_time:{period}"
    cached = await cache_get(cache_key)
    if cached:
        return TrendResponse(**cached)

    contracts = list((await db.execute(select(Contract))).scalars().all())
    buckets: dict[str, list[float]] = defaultdict(list)
    for c in contracts:
        if not c.created_at:
            continue
        if date_from and c.created_at < date_from:
            continue
        if date_to and c.created_at > date_to:
            continue
        history = c.stage_history or []
        if history:
            first = _parse_dt(history[0].get("date"))
            last = _parse_dt(history[-1].get("date"))
            if first and last:
                days = (last - first).total_seconds() / 86400
                buckets[_period_key(c.created_at, period)].append(days)

    data = [
        TrendDataPoint(
            period=k,
            value=round(sum(v) / len(v), 2) if v else 0.0,
            count=len(v),
        )
        for k, v in sorted(buckets.items())
    ]
    result = TrendResponse(data=data, period=period, date_from=date_from, date_to=date_to)
    await cache_set(cache_key, result.model_dump(mode="json"), ttl_seconds=900)
    return result


async def _distribution(items: list[str]) -> DistributionResponse:
    counts = Counter(items)
    total = sum(counts.values())
    dist_items = [
        DistributionItem(label=label, count=count, percentage=round(count / max(total, 1) * 100, 2))
        for label, count in counts.most_common()
    ]
    return DistributionResponse(items=dist_items, total=total)


async def get_contract_type_distribution(db: AsyncSession) -> DistributionResponse:
    cache_key = "analytics:dist:contract_types"
    cached = await cache_get(cache_key)
    if cached:
        return DistributionResponse(**cached)
    contracts = list((await db.execute(select(Contract.agreement_type))).all())
    result = await _distribution([row[0] or "Unknown" for row in contracts])
    await cache_set(cache_key, result.model_dump(mode="json"), ttl_seconds=1800)
    return result


async def get_contract_stage_distribution(db: AsyncSession) -> DistributionResponse:
    cache_key = "analytics:dist:stages"
    cached = await cache_get(cache_key)
    if cached:
        return DistributionResponse(**cached)
    contracts = list((await db.execute(select(Contract.current_stage))).all())
    result = await _distribution([row[0] or "Unknown" for row in contracts])
    await cache_set(cache_key, result.model_dump(mode="json"), ttl_seconds=1800)
    return result


async def get_email_category_distribution(db: AsyncSession) -> DistributionResponse:
    cache_key = "analytics:dist:email_categories"
    cached = await cache_get(cache_key)
    if cached:
        return DistributionResponse(**cached)
    rows = list((await db.execute(select(EmailClassification.category))).all())
    result = await _distribution([r[0] or "Unknown" for r in rows])
    await cache_set(cache_key, result.model_dump(mode="json"), ttl_seconds=1800)
    return result


async def get_email_urgency_distribution(db: AsyncSession) -> DistributionResponse:
    cache_key = "analytics:dist:urgency"
    cached = await cache_get(cache_key)
    if cached:
        return DistributionResponse(**cached)
    rows = list((await db.execute(select(EmailClassification.urgency))).all())
    result = await _distribution([r[0] or "Unknown" for r in rows])
    await cache_set(cache_key, result.model_dump(mode="json"), ttl_seconds=1800)
    return result


async def get_email_sentiment_distribution(db: AsyncSession) -> DistributionResponse:
    cache_key = "analytics:dist:sentiment"
    cached = await cache_get(cache_key)
    if cached:
        return DistributionResponse(**cached)
    rows = list((await db.execute(select(EmailClassification.sentiment))).all())
    result = await _distribution([r[0] or "Unknown" for r in rows])
    await cache_set(cache_key, result.model_dump(mode="json"), ttl_seconds=1800)
    return result


async def get_department_distribution(db: AsyncSession) -> DistributionResponse:
    cache_key = "analytics:dist:departments"
    cached = await cache_get(cache_key)
    if cached:
        return DistributionResponse(**cached)
    rows = list((await db.execute(select(Stakeholder.department))).all())
    result = await _distribution([r[0] or "Unknown" for r in rows])
    await cache_set(cache_key, result.model_dump(mode="json"), ttl_seconds=1800)
    return result


async def get_risk_score_distribution(db: AsyncSession) -> DistributionResponse:
    cache_key = "analytics:dist:risk_scores"
    cached = await cache_get(cache_key)
    if cached:
        return DistributionResponse(**cached)
    contracts = list((await db.execute(select(Contract.risk_score))).all())
    bins = ["0.0-0.2", "0.2-0.4", "0.4-0.6", "0.6-0.8", "0.8-1.0"]
    bin_counts: dict[str, int] = {b: 0 for b in bins}
    for (score,) in contracts:
        if score is None:
            continue
        if score < 0.2:
            bin_counts["0.0-0.2"] += 1
        elif score < 0.4:
            bin_counts["0.2-0.4"] += 1
        elif score < 0.6:
            bin_counts["0.4-0.6"] += 1
        elif score < 0.8:
            bin_counts["0.6-0.8"] += 1
        else:
            bin_counts["0.8-1.0"] += 1
    total = sum(bin_counts.values())
    items = [
        DistributionItem(label=label, count=count, percentage=round(count / max(total, 1) * 100, 2))
        for label, count in bin_counts.items()
    ]
    result = DistributionResponse(items=items, total=total)
    await cache_set(cache_key, result.model_dump(mode="json"), ttl_seconds=1800)
    return result


async def get_clause_frequency_distribution(db: AsyncSession) -> DistributionResponse:
    cache_key = "analytics:dist:clauses"
    cached = await cache_get(cache_key)
    if cached:
        return DistributionResponse(**cached)
    contracts = list((await db.execute(select(Contract.key_clauses))).all())
    clause_list: list[str] = []
    for (clauses,) in contracts:
        if isinstance(clauses, list):
            for clause in clauses:
                if isinstance(clause, dict):
                    clause_list.append(clause.get("type") or "Unknown")
                elif isinstance(clause, str):
                    clause_list.append(clause)
    result = await _distribution(clause_list)
    await cache_set(cache_key, result.model_dump(mode="json"), ttl_seconds=1800)
    return result


async def get_top_bottleneck_contracts(db: AsyncSession, limit: int = 10) -> list[TopContract]:
    cache_key = f"analytics:top:bottlenecks:{limit}"
    cached = await cache_get(cache_key)
    if cached:
        return [TopContract(**item) for item in cached]

    contracts = list((await db.execute(select(Contract))).scalars().all())
    now = datetime.now(UTC)

    scored = []
    for c in contracts:
        if not c.current_stage or c.current_stage == "Repository & Obligation Tracking":
            continue
        history = c.stage_history or []
        days_stalled = 0.0
        if history:
            last_dt = _parse_dt(history[-1].get("date"))
            if last_dt:
                days_stalled = (now - last_dt).total_seconds() / 86400
        scored.append((days_stalled, c))

    scored.sort(key=lambda x: x[0], reverse=True)
    result = [
        TopContract(
            contract_id=str(c.id),
            agreement_name=c.agreement_name,
            counterparty_name=c.counterparty_name,
            current_stage=c.current_stage,
            days_stalled=round(days, 2),
            risk_score=c.risk_score,
            sla_breached=c.sla_breached,
        )
        for days, c in scored[:limit]
    ]
    await cache_set(cache_key, [r.model_dump(mode="json") for r in result], ttl_seconds=600)
    return result


async def get_top_risk_contracts(db: AsyncSession, limit: int = 10) -> list[TopContract]:
    cache_key = f"analytics:top:risks:{limit}"
    cached = await cache_get(cache_key)
    if cached:
        return [TopContract(**item) for item in cached]

    contracts = list(
        (
            await db.execute(
                select(Contract)
                .where(Contract.risk_score.is_not(None))
                .order_by(Contract.risk_score.desc())
                .limit(limit)
            )
        ).scalars().all()
    )
    result = [
        TopContract(
            contract_id=str(c.id),
            agreement_name=c.agreement_name,
            counterparty_name=c.counterparty_name,
            current_stage=c.current_stage,
            days_stalled=0.0,
            risk_score=c.risk_score,
            sla_breached=c.sla_breached,
        )
        for c in contracts
    ]
    await cache_set(cache_key, [r.model_dump(mode="json") for r in result], ttl_seconds=600)
    return result


async def get_top_active_stakeholders(db: AsyncSession, limit: int = 10) -> list[TopStakeholder]:
    cache_key = f"analytics:top:stakeholders:{limit}"
    cached = await cache_get(cache_key)
    if cached:
        return [TopStakeholder(**item) for item in cached]

    stakeholders = list(
        (
            await db.execute(
                select(Stakeholder)
                .order_by(Stakeholder.total_emails.desc())
                .limit(limit)
            )
        ).scalars().all()
    )
    result = [
        TopStakeholder(
            stakeholder_id=str(s.id),
            name=s.name,
            department=s.department,
            email_count=s.total_emails or 0,
            contract_count=s.total_contracts or 0,
            avg_response_time_hours=s.avg_response_time,
        )
        for s in stakeholders
    ]
    await cache_set(cache_key, [r.model_dump(mode="json") for r in result], ttl_seconds=600)
    return result


async def get_recent_activity(db: AsyncSession, limit: int = 20) -> list[ActivityFeedItem]:
    cache_key = f"analytics:recent_activity:{limit}"
    cached = await cache_get(cache_key)
    if cached:
        return [ActivityFeedItem(**item) for item in cached]

    activities: list[ActivityFeedItem] = []

    # Recent emails
    recent_emails = list(
        (
            await db.execute(
                select(Email).order_by(Email.date.desc()).limit(limit // 2)
            )
        ).scalars().all()
    )
    for email in recent_emails:
        activities.append(
            ActivityFeedItem(
                activity_type="email",
                entity_id=str(email.id),
                entity_type="email",
                title=email.subject or "(no subject)",
                description=f"From: {email.from_address}",
                timestamp=email.date or email.created_at,
                actor=email.from_address,
            )
        )

    # Recent contract updates
    recent_contracts = list(
        (
            await db.execute(
                select(Contract).order_by(Contract.updated_at.desc()).limit(limit // 2)
            )
        ).scalars().all()
    )
    for contract in recent_contracts:
        activities.append(
            ActivityFeedItem(
                activity_type="stage_transition" if contract.current_stage else "contract_created",
                entity_id=str(contract.id),
                entity_type="contract",
                title=contract.agreement_name or "Contract",
                description=f"Stage: {contract.current_stage or 'Unknown'}",
                timestamp=contract.updated_at or contract.created_at,
                actor=contract.counterparty_name,
            )
        )

    def _ts(dt: datetime | None) -> datetime:
        if dt is None:
            return datetime.min.replace(tzinfo=UTC)
        return dt if dt.tzinfo else dt.replace(tzinfo=UTC)

    activities.sort(key=lambda a: _ts(a.timestamp), reverse=True)
    result = activities[:limit]
    await cache_set(cache_key, [r.model_dump(mode="json") for r in result], ttl_seconds=600)
    return result
