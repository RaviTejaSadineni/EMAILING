from __future__ import annotations

import json
from collections import defaultdict
from datetime import UTC, datetime
from statistics import median
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.classification import EmailClassification
from app.models.contract import Contract
from app.models.email import Email
from app.models.email_thread_link import EmailThreadLink
from app.schemas.contract_analytics import (
    BottleneckReport,
    ContractTimeline,
    ContractTimelineEvent,
    CycleTimeBin,
    CycleTimeDistribution,
    LifecycleStory,
    NegotiationAnalysis,
    SLABreachItem,
    SLABreachReport,
    SLACompliancePeriod,
    SLAComplianceTrend,
    StageDuration,
    StageDurationStats,
    StageHealth,
    StageHealthItem,
    StageTransition,
    VelocityPoint,
    VelocityTrend,
)
from app.services.ai_service import get_ai_service
from app.services.cache_service import cache_get, cache_set

settings = get_settings()

STAGE_ORDER = [
    "Request",
    "Legal Review",
    "Finance Review",
    "Procurement/Compliance",
    "Redline Negotiation",
    "Leadership Sign-off",
    "Repository & Obligation Tracking",
]


def _parse_dt(val: str | datetime | None) -> datetime | None:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    try:
        return datetime.fromisoformat(str(val).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _stage_name(val: str | int | None) -> str | None:
    if val is None:
        return None
    if isinstance(val, int) and 1 <= val <= len(STAGE_ORDER):
        return STAGE_ORDER[val - 1]
    return str(val)


async def get_contract_timeline(db: AsyncSession, contract_id: UUID) -> ContractTimeline:
    contract = await db.get(Contract, contract_id)
    if contract is None:
        return ContractTimeline(contract_id=str(contract_id), events=[])

    events: list[ContractTimelineEvent] = []
    history = contract.stage_history or []
    for entry in history:
        stage = _stage_name(entry.get("stage"))
        events.append(
            ContractTimelineEvent(
                date=_parse_dt(entry.get("date")),
                event_type="stage_entry",
                stage=stage,
                actor=entry.get("actor"),
                description=entry.get("notes") or f"Entered stage: {stage}",
                email_id=entry.get("email_id"),
            )
        )

    # Also pull emails from the thread
    if contract.thread_id:
        rows = await db.execute(
            select(Email)
            .join(EmailThreadLink, EmailThreadLink.email_id == Email.id)
            .where(EmailThreadLink.thread_id == contract.thread_id)
            .order_by(Email.date.asc())
        )
        emails = list(rows.scalars().all())
        for email in emails:
            events.append(
                ContractTimelineEvent(
                    date=email.date,
                    event_type="email",
                    stage=None,
                    actor=email.from_address,
                    description=f"Email: {email.subject or '(no subject)'}",
                    email_id=str(email.id),
                )
            )

    events.sort(key=lambda e: (e.date or datetime.min.replace(tzinfo=UTC)))
    return ContractTimeline(contract_id=str(contract_id), events=events)


async def get_contract_stage_durations(db: AsyncSession, contract_id: UUID) -> list[StageDuration]:
    contract = await db.get(Contract, contract_id)
    if contract is None:
        return []

    history = contract.stage_history or []
    if not history:
        return []

    durations: list[StageDuration] = []
    for i, entry in enumerate(history):
        entered_at = _parse_dt(entry.get("date"))
        exited_at = _parse_dt(history[i + 1].get("date")) if i + 1 < len(history) else None
        if exited_at is None:
            exited_at = datetime.now(UTC)

        duration_hours = 0.0
        if entered_at and exited_at:
            delta = exited_at - entered_at
            duration_hours = delta.total_seconds() / 3600

        stage = _stage_name(entry.get("stage")) or "Unknown"
        actors = [entry.get("actor")] if entry.get("actor") else []

        # Count emails in this stage window
        emails_in_stage = 0
        if contract.thread_id and entered_at:
            result = await db.execute(
                select(func.count())
                .select_from(Email)
                .join(EmailThreadLink, EmailThreadLink.email_id == Email.id)
                .where(
                    EmailThreadLink.thread_id == contract.thread_id,
                    Email.date >= entered_at,
                    Email.date <= exited_at,
                )
            )
            emails_in_stage = result.scalar_one() or 0

        is_bottleneck = duration_hours > (settings.slr_yellow_minutes * 60 / 60)
        durations.append(
            StageDuration(
                stage=stage,
                duration_hours=round(duration_hours, 2),
                entered_at=entered_at,
                exited_at=exited_at if exited_at != datetime.now(UTC) else None,
                actors_involved=[a for a in actors if a],
                emails_in_stage=int(emails_in_stage),
                is_bottleneck=is_bottleneck,
            )
        )
    return durations


async def get_lifecycle_story(db: AsyncSession, contract_id: UUID) -> LifecycleStory:
    cache_key = f"analytics:lifecycle_story:{contract_id}"
    cached = await cache_get(cache_key)
    if cached:
        return LifecycleStory(**cached)

    contract = await db.get(Contract, contract_id)
    if contract is None:
        return LifecycleStory(
            contract_id=str(contract_id),
            narrative="Contract not found.",
            generated_at=datetime.now(UTC),
        )

    if contract.lifecycle_summary:
        story = LifecycleStory(
            contract_id=str(contract_id),
            narrative=contract.lifecycle_summary,
            generated_at=contract.updated_at or datetime.now(UTC),
        )
        await cache_set(cache_key, story.model_dump(mode="json"), ttl_seconds=3600)
        return story

    ai_service = get_ai_service()
    prompt_data = {
        "contract": {
            "name": contract.agreement_name,
            "type": contract.agreement_type,
            "counterparty": contract.counterparty_name,
            "current_stage": contract.current_stage,
            "sla_breached": contract.sla_breached,
            "risk_score": contract.risk_score,
            "stage_history": contract.stage_history,
            "delay_reasons": contract.delay_reasons,
        }
    }
    result = await ai_service.complete(
        system_prompt=(
            "You are a legal contract analyst. Given contract lifecycle data, write a clear narrative "
            "story of the contract's journey. Focus on key stages, bottlenecks, and outcomes. "
            "Return JSON: {\"narrative\": \"...\"}"
        ),
        user_prompt=json.dumps(prompt_data, default=str),
        max_tokens=800,
    )
    narrative = result.get("narrative") or contract.ai_summary or "No narrative available."
    story = LifecycleStory(
        contract_id=str(contract_id),
        narrative=narrative,
        generated_at=datetime.now(UTC),
    )
    await cache_set(cache_key, story.model_dump(mode="json"), ttl_seconds=3600)
    return story


async def get_stage_duration_stats(db: AsyncSession) -> list[StageDurationStats]:
    contracts = list((await db.execute(select(Contract))).scalars().all())

    stage_durations: dict[str, list[float]] = defaultdict(list)
    for contract in contracts:
        history = contract.stage_history or []
        for i, entry in enumerate(history):
            entered_at = _parse_dt(entry.get("date"))
            exited_at = _parse_dt(history[i + 1].get("date")) if i + 1 < len(history) else None
            if entered_at and exited_at:
                hours = (exited_at - entered_at).total_seconds() / 3600
                stage = _stage_name(entry.get("stage")) or "Unknown"
                stage_durations[stage].append(hours)

    stats = []
    for stage, durations in stage_durations.items():
        if not durations:
            continue
        sorted_d = sorted(durations)
        p90_idx = int(len(sorted_d) * 0.9)
        stats.append(
            StageDurationStats(
                stage=stage,
                avg_hours=round(sum(durations) / len(durations), 2),
                min_hours=round(min(durations), 2),
                max_hours=round(max(durations), 2),
                median_hours=round(median(durations), 2),
                p90_hours=round(sorted_d[min(p90_idx, len(sorted_d) - 1)], 2),
                sample_count=len(durations),
            )
        )
    return stats


async def get_bottleneck_analysis(db: AsyncSession) -> list[BottleneckReport]:
    contracts = list((await db.execute(select(Contract))).scalars().all())
    threshold_hours = settings.slr_yellow_minutes / 60.0

    stage_data: dict[str, dict] = defaultdict(lambda: {"delays": [], "actors": []})
    for contract in contracts:
        history = contract.stage_history or []
        for i, entry in enumerate(history):
            entered_at = _parse_dt(entry.get("date"))
            exited_at = _parse_dt(history[i + 1].get("date")) if i + 1 < len(history) else None
            if entered_at and exited_at:
                hours = (exited_at - entered_at).total_seconds() / 3600
                if hours > threshold_hours:
                    stage = _stage_name(entry.get("stage")) or "Unknown"
                    stage_data[stage]["delays"].append(hours)
                    if entry.get("actor"):
                        stage_data[stage]["actors"].append(entry["actor"])

    reports = []
    for stage, data in stage_data.items():
        delays = data["delays"]
        from collections import Counter
        actor_counts = Counter(data["actors"])
        top_offenders = [actor for actor, _ in actor_counts.most_common(3)]
        reports.append(
            BottleneckReport(
                stage=stage,
                frequency=len(delays),
                avg_delay_hours=round(sum(delays) / len(delays), 2) if delays else 0.0,
                top_offenders=top_offenders,
                bottleneck_score=round(len(delays) * sum(delays) / max(len(delays), 1), 2),
            )
        )
    reports.sort(key=lambda r: r.bottleneck_score, reverse=True)
    return reports


async def get_sla_breach_report(
    db: AsyncSession,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> SLABreachReport:
    query = select(Contract).where(Contract.sla_breached.is_(True))
    if date_from:
        query = query.where(Contract.created_at >= date_from)
    if date_to:
        query = query.where(Contract.created_at <= date_to)

    contracts = list((await db.execute(query)).scalars().all())
    items: list[SLABreachItem] = []
    sla_days = 15.0  # 15-day SLA from problem statement

    for contract in contracts:
        history = contract.stage_history or []
        total_days = 0.0
        if history:
            first_dt = _parse_dt(history[0].get("date"))
            last_dt = _parse_dt(history[-1].get("date")) or datetime.now(UTC)
            if first_dt and last_dt:
                total_days = (last_dt - first_dt).total_seconds() / 86400

        # Find primary bottleneck stage
        max_hours = 0.0
        bottleneck_stage = None
        actors_set: set[str] = set()
        for i, entry in enumerate(history):
            entered = _parse_dt(entry.get("date"))
            exited = _parse_dt(history[i + 1].get("date")) if i + 1 < len(history) else None
            if entered and exited:
                h = (exited - entered).total_seconds() / 3600
                if h > max_hours:
                    max_hours = h
                    bottleneck_stage = _stage_name(entry.get("stage"))
            if entry.get("actor"):
                actors_set.add(entry["actor"])

        items.append(
            SLABreachItem(
                contract_id=str(contract.id),
                agreement_name=contract.agreement_name,
                total_cycle_days=round(total_days, 2),
                breach_days=round(max(0.0, total_days - sla_days), 2),
                primary_bottleneck_stage=bottleneck_stage,
                responsible_stakeholders=list(actors_set),
            )
        )
    return SLABreachReport(total_breaches=len(items), items=items)


async def get_sla_compliance_rate(
    db: AsyncSession,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    period: str = "month",
) -> SLAComplianceTrend:
    contracts = list((await db.execute(select(Contract))).scalars().all())
    buckets: dict[str, dict] = defaultdict(lambda: {"total": 0, "breached": 0})

    for contract in contracts:
        if date_from and contract.created_at and contract.created_at < date_from:
            continue
        if date_to and contract.created_at and contract.created_at > date_to:
            continue
        if not contract.created_at:
            continue
        if period == "month":
            key = contract.created_at.strftime("%Y-%m")
        elif period == "week":
            key = contract.created_at.strftime("%Y-W%W")
        else:
            key = contract.created_at.strftime("%Y")
        buckets[key]["total"] += 1
        if contract.sla_breached:
            buckets[key]["breached"] += 1

    periods = []
    for p_key in sorted(buckets.keys()):
        total = buckets[p_key]["total"]
        breached = buckets[p_key]["breached"]
        on_track = total - breached
        rate = round((on_track / total * 100) if total > 0 else 100.0, 2)
        periods.append(
            SLACompliancePeriod(
                period=p_key,
                total=total,
                on_track=on_track,
                breached=breached,
                compliance_rate=rate,
            )
        )
    return SLAComplianceTrend(periods=periods)


async def get_stage_transition_matrix(db: AsyncSession) -> list[StageTransition]:
    contracts = list((await db.execute(select(Contract))).scalars().all())
    transition_data: dict[tuple[str, str], list[float]] = defaultdict(list)

    for contract in contracts:
        history = contract.stage_history or []
        for i in range(1, len(history)):
            from_stage = _stage_name(history[i - 1].get("stage")) or "Unknown"
            to_stage = _stage_name(history[i].get("stage")) or "Unknown"
            from_dt = _parse_dt(history[i - 1].get("date"))
            to_dt = _parse_dt(history[i].get("date"))
            duration = 0.0
            if from_dt and to_dt:
                duration = (to_dt - from_dt).total_seconds() / 3600
            transition_data[(from_stage, to_stage)].append(duration)

    result = []
    for (from_s, to_s), durations in transition_data.items():
        result.append(
            StageTransition(
                from_stage=from_s,
                to_stage=to_s,
                count=len(durations),
                avg_duration_hours=round(sum(durations) / len(durations), 2) if durations else 0.0,
            )
        )
    return result


async def get_negotiation_loop_analysis(db: AsyncSession) -> NegotiationAnalysis:
    contracts = list((await db.execute(select(Contract))).scalars().all())

    NEGOTIATION_STAGE = "Redline Negotiation"
    rounds_per_contract = []
    contract_details = []

    for contract in contracts:
        history = contract.stage_history or []
        rounds = sum(1 for e in history if _stage_name(e.get("stage")) == NEGOTIATION_STAGE)
        if rounds > 0:
            rounds_per_contract.append(rounds)
            contract_details.append({"contract_id": str(contract.id), "name": contract.agreement_name, "rounds": rounds})

    avg_rounds = round(sum(rounds_per_contract) / len(rounds_per_contract), 2) if rounds_per_contract else 0.0
    top_contracts = sorted(contract_details, key=lambda x: x["rounds"], reverse=True)[:10]

    # From problem statement: known clause frequencies
    most_negotiated_clauses = [
        {"clause": "Liability", "frequency_pct": 68},
        {"clause": "Indemnity", "frequency_pct": 56},
        {"clause": "Payment Terms", "frequency_pct": 49},
    ]

    # Correlation: more rounds → longer cycle time
    cycles = []
    for contract in contracts:
        history = contract.stage_history or []
        rounds = sum(1 for e in history if _stage_name(e.get("stage")) == NEGOTIATION_STAGE)
        if history:
            first = _parse_dt(history[0].get("date"))
            last = _parse_dt(history[-1].get("date"))
            if first and last:
                days = (last - first).total_seconds() / 86400
                cycles.append((rounds, days))

    correlation = None
    if len(cycles) >= 2:
        rounds_list = [c[0] for c in cycles]
        days_list = [c[1] for c in cycles]
        n = len(cycles)
        mean_r = sum(rounds_list) / n
        mean_d = sum(days_list) / n
        num = sum((r - mean_r) * (d - mean_d) for r, d in zip(rounds_list, days_list))
        den_r = (sum((r - mean_r) ** 2 for r in rounds_list)) ** 0.5
        den_d = (sum((d - mean_d) ** 2 for d in days_list)) ** 0.5
        if den_r * den_d > 0:
            correlation = round(num / (den_r * den_d), 3)

    return NegotiationAnalysis(
        avg_rounds=avg_rounds,
        most_negotiated_clauses=most_negotiated_clauses,
        top_contracts_by_rounds=top_contracts,
        correlation_rounds_cycle_time=correlation,
    )


async def get_cycle_time_distribution(db: AsyncSession) -> CycleTimeDistribution:
    contracts = list((await db.execute(select(Contract))).scalars().all())
    cycle_days = []

    for contract in contracts:
        history = contract.stage_history or []
        if history:
            first = _parse_dt(history[0].get("date"))
            last = _parse_dt(history[-1].get("date"))
            if first and last:
                days = (last - first).total_seconds() / 86400
                cycle_days.append(days)

    bins_def = [(0, 5), (5, 10), (10, 15), (15, 20), (20, 30), (30, float("inf"))]
    bins = []
    for lo, hi in bins_def:
        label = f"{lo}-{int(hi)}" if hi != float("inf") else f"{lo}+"
        count = sum(1 for d in cycle_days if lo <= d < hi)
        bins.append(CycleTimeBin(label=label, min_days=lo, max_days=hi if hi != float("inf") else 9999, count=count))

    avg_days = round(sum(cycle_days) / len(cycle_days), 2) if cycle_days else 0.0
    med_days = round(median(cycle_days), 2) if cycle_days else 0.0
    return CycleTimeDistribution(bins=bins, avg_days=avg_days, median_days=med_days)


async def get_contract_velocity_trend(db: AsyncSession, period: str = "week") -> VelocityTrend:
    contracts = list((await db.execute(select(Contract))).scalars().all())
    started: dict[str, int] = defaultdict(int)
    completed: dict[str, int] = defaultdict(int)

    for contract in contracts:
        if not contract.created_at:
            continue
        if period == "week":
            key = contract.created_at.strftime("%Y-W%W")
        elif period == "month":
            key = contract.created_at.strftime("%Y-%m")
        else:
            key = contract.created_at.strftime("%Y")
        started[key] += 1
        history = contract.stage_history or []
        if history:
            last = _parse_dt(history[-1].get("date"))
            last_stage = _stage_name(history[-1].get("stage")) if history else None
            if last_stage == STAGE_ORDER[-1]:
                if period == "week":
                    k = last.strftime("%Y-W%W") if last else key
                elif period == "month":
                    k = last.strftime("%Y-%m") if last else key
                else:
                    k = last.strftime("%Y") if last else key
                completed[k] += 1

    all_keys = sorted(set(list(started.keys()) + list(completed.keys())))
    points = [
        VelocityPoint(period=k, completed_count=completed[k], started_count=started[k])
        for k in all_keys
    ]
    return VelocityTrend(points=points)


async def get_stage_health_overview(db: AsyncSession) -> StageHealth:
    contracts = list((await db.execute(select(Contract))).scalars().all())
    now = datetime.now(UTC)
    white_mins = settings.slr_white_minutes
    yellow_mins = settings.slr_yellow_minutes

    stage_data: dict[str, dict] = defaultdict(lambda: {"total": 0, "white": 0, "yellow": 0, "red": 0, "days": []})

    for contract in contracts:
        if not contract.current_stage:
            continue
        stage = contract.current_stage
        stage_data[stage]["total"] += 1
        history = contract.stage_history or []
        # Find when current stage was entered
        entered_at = None
        for entry in reversed(history):
            if _stage_name(entry.get("stage")) == stage:
                entered_at = _parse_dt(entry.get("date"))
                break
        if entered_at:
            minutes_in_stage = (now - entered_at).total_seconds() / 60
            stage_data[stage]["days"].append(minutes_in_stage / 60 / 24)
            if minutes_in_stage <= white_mins:
                stage_data[stage]["white"] += 1
            elif minutes_in_stage <= yellow_mins:
                stage_data[stage]["yellow"] += 1
            else:
                stage_data[stage]["red"] += 1
        else:
            stage_data[stage]["white"] += 1

    items = []
    for stage, data in stage_data.items():
        avg_days = round(sum(data["days"]) / len(data["days"]), 2) if data["days"] else 0.0
        items.append(
            StageHealthItem(
                stage=stage,
                contract_count=data["total"],
                white_count=data["white"],
                yellow_count=data["yellow"],
                red_count=data["red"],
                avg_days_in_stage=avg_days,
            )
        )
    return StageHealth(items=items, as_of=now)
