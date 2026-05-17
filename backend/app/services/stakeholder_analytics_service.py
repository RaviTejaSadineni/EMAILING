from __future__ import annotations

import json
from collections import defaultdict
from datetime import UTC, datetime
from statistics import median
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.classification import EmailClassification
from app.models.contract import Contract
from app.models.email import Email
from app.models.email_thread_link import EmailThreadLink
from app.models.stakeholder import Stakeholder
from app.schemas.stakeholder_analytics import (
    AIRecommendation,
    CommunicationEdge,
    CommunicationNetwork,
    CommunicationNode,
    ContractInvolvement,
    DepartmentAnalytics,
    DepartmentAnalyticsItem,
    DepartmentComparison,
    ResponseTimeStat,
    ResponseTimeTrend,
    ResponseTimeTrendPoint,
    StakeholderComparison,
    StakeholderComparisonItem,
    StakeholderPerformance,
    StakeholderRanking,
    WorkloadBalance,
    WorkloadBalanceItem,
    WorkloadPoint,
    WorkloadTimeline,
    EmailVolume,
)
from app.services.ai_service import get_ai_service
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


async def _get_stakeholder_emails(db: AsyncSession, stakeholder: Stakeholder) -> list[Email]:
    """Return all emails where this stakeholder appears (from/to/cc)."""
    from sqlalchemy import or_, String, cast
    result = await db.execute(
        select(Email).where(
            Email.from_address == stakeholder.email_address
        ).order_by(Email.date.asc())
    )
    sent = list(result.scalars().all())
    return sent


async def get_stakeholder_performance(db: AsyncSession, stakeholder_id: UUID) -> StakeholderPerformance | None:
    stakeholder = await db.get(Stakeholder, stakeholder_id)
    if stakeholder is None:
        return None

    # Response time from stored data
    avg_rt = stakeholder.avg_response_time or 0.0
    rt_dist = stakeholder.response_time_distribution or {}
    p90 = rt_dist.get("p90", avg_rt * 1.5)
    med = rt_dist.get("median", avg_rt)
    trend = rt_dist.get("trend", "stable")

    # Email volumes by month
    sent_emails = await _get_stakeholder_emails(db, stakeholder)
    monthly: dict[str, int] = defaultdict(int)
    for email in sent_emails:
        if email.date:
            key = email.date.strftime("%Y-%m")
            monthly[key] += 1

    email_volumes = [
        EmailVolume(sent=count, received=0, cc=0, period=period)
        for period, count in sorted(monthly.items())
    ]

    # Contract counts
    contracts = list((await db.execute(select(Contract))).scalars().all())
    active = completed = breached = bottleneck_count = 0
    total_delay = 0.0

    for contract in contracts:
        history = contract.stage_history or []
        involved = any(
            entry.get("actor") == stakeholder.email_address or
            entry.get("actor") == stakeholder.name
            for entry in history
        )
        if not involved and contract.counterparty_email != stakeholder.email_address:
            continue
        if contract.current_stage == "Repository & Obligation Tracking":
            completed += 1
        else:
            active += 1
        if contract.sla_breached:
            breached += 1

    sla_breach_rate = round(breached / max(active + completed, 1) * 100, 2)

    return StakeholderPerformance(
        stakeholder_id=str(stakeholder_id),
        name=stakeholder.name,
        department=stakeholder.department,
        role=stakeholder.role,
        response_time=ResponseTimeStat(
            avg_hours=round(avg_rt, 2),
            median_hours=round(float(med), 2),
            p90_hours=round(float(p90), 2),
            trend=str(trend),
        ),
        email_volumes=email_volumes,
        active_contracts=active,
        completed_contracts=completed,
        sla_breached_contracts=breached,
        bottleneck_count=bottleneck_count,
        avg_delay_caused_hours=round(total_delay, 2),
        sla_breach_rate=sla_breach_rate,
    )


async def get_stakeholder_response_time_trend(
    db: AsyncSession,
    stakeholder_id: UUID,
    period: str = "week",
) -> ResponseTimeTrend:
    stakeholder = await db.get(Stakeholder, stakeholder_id)
    if stakeholder is None:
        return ResponseTimeTrend(stakeholder_id=str(stakeholder_id), points=[])

    emails = await _get_stakeholder_emails(db, stakeholder)
    buckets: dict[str, list[float]] = defaultdict(list)
    avg_rt = stakeholder.avg_response_time or 0.0

    for email in emails:
        if not email.date:
            continue
        if period == "week":
            key = email.date.strftime("%Y-W%W")
        elif period == "month":
            key = email.date.strftime("%Y-%m")
        else:
            key = email.date.strftime("%Y")
        buckets[key].append(avg_rt)  # Approximate: use stored avg

    points = []
    for key in sorted(buckets.keys()):
        vals = buckets[key]
        points.append(
            ResponseTimeTrendPoint(
                period=key,
                avg_hours=round(sum(vals) / len(vals), 2) if vals else 0.0,
                median_hours=round(median(vals), 2) if vals else 0.0,
            )
        )
    return ResponseTimeTrend(stakeholder_id=str(stakeholder_id), points=points)


async def get_stakeholder_workload_timeline(
    db: AsyncSession,
    stakeholder_id: UUID,
) -> WorkloadTimeline:
    stakeholder = await db.get(Stakeholder, stakeholder_id)
    if stakeholder is None:
        return WorkloadTimeline(stakeholder_id=str(stakeholder_id), points=[])

    contracts = list((await db.execute(select(Contract))).scalars().all())
    monthly: dict[str, int] = defaultdict(int)

    for contract in contracts:
        history = contract.stage_history or []
        involved = any(
            entry.get("actor") in (stakeholder.email_address, stakeholder.name)
            for entry in history
        )
        if not involved:
            continue
        if contract.created_at:
            key = contract.created_at.strftime("%Y-%m")
            monthly[key] += 1

    points = [
        WorkloadPoint(period=k, active_contracts=v)
        for k, v in sorted(monthly.items())
    ]
    return WorkloadTimeline(stakeholder_id=str(stakeholder_id), points=points)


async def get_stakeholder_contracts_detail(
    db: AsyncSession,
    stakeholder_id: UUID,
) -> list[ContractInvolvement]:
    stakeholder = await db.get(Stakeholder, stakeholder_id)
    if stakeholder is None:
        return []

    contracts = list((await db.execute(select(Contract))).scalars().all())
    result = []

    for contract in contracts:
        history = contract.stage_history or []
        involved = any(
            entry.get("actor") in (stakeholder.email_address, stakeholder.name)
            for entry in history
        ) or contract.counterparty_email == stakeholder.email_address

        if not involved:
            continue

        sla_status = "breached" if contract.sla_breached else "on_track"
        result.append(
            ContractInvolvement(
                contract_id=str(contract.id),
                agreement_name=contract.agreement_name,
                role=stakeholder.role,
                contribution_score=stakeholder.influence_score or 0.5,
                avg_response_time_hours=stakeholder.avg_response_time,
                stage=contract.current_stage,
                sla_status=sla_status,
            )
        )
    return result


async def get_stakeholder_communication_network(
    db: AsyncSession,
    stakeholder_id: UUID,
) -> CommunicationNetwork:
    stakeholder = await db.get(Stakeholder, stakeholder_id)
    if stakeholder is None:
        return CommunicationNetwork(nodes=[], edges=[])

    emails = await _get_stakeholder_emails(db, stakeholder)
    partner_counts: dict[str, int] = defaultdict(int)

    for email in emails:
        for addr in (email.to_addresses or []):
            if addr != stakeholder.email_address:
                partner_counts[addr] += 1

    # Build nodes and edges
    nodes = []
    edges = []
    all_stakeholders = {s.email_address: s for s in (await db.execute(select(Stakeholder))).scalars().all()}

    # Add self
    nodes.append(CommunicationNode(
        stakeholder_id=str(stakeholder_id),
        name=stakeholder.name,
        email=stakeholder.email_address,
        department=stakeholder.department,
        total_interactions=sum(partner_counts.values()),
    ))

    for addr, count in sorted(partner_counts.items(), key=lambda x: x[1], reverse=True)[:20]:
        partner = all_stakeholders.get(addr)
        node_id = str(partner.id) if partner else addr
        nodes.append(CommunicationNode(
            stakeholder_id=node_id,
            name=partner.name if partner else addr,
            email=addr,
            department=partner.department if partner else None,
            total_interactions=count,
        ))
        edges.append(CommunicationEdge(
            source=str(stakeholder_id),
            target=node_id,
            weight=count,
            email_count=count,
        ))

    return CommunicationNetwork(nodes=nodes, edges=edges)


async def get_stakeholder_comparison(db: AsyncSession, stakeholder_ids: list[str]) -> StakeholderComparison:
    items = []
    for sid in stakeholder_ids:
        try:
            uid = UUID(sid)
        except ValueError:
            continue
        s = await db.get(Stakeholder, uid)
        if s is None:
            continue
        contracts = list((await db.execute(select(Contract))).scalars().all())
        breached = sum(
            1 for c in contracts
            if c.sla_breached and any(
                e.get("actor") in (s.email_address, s.name)
                for e in (c.stage_history or [])
            )
        )
        total_involved = sum(
            1 for c in contracts
            if any(
                e.get("actor") in (s.email_address, s.name)
                for e in (c.stage_history or [])
            )
        )
        sla_rate = round(breached / max(total_involved, 1) * 100, 2)
        items.append(
            StakeholderComparisonItem(
                stakeholder_id=str(s.id),
                name=s.name,
                department=s.department,
                avg_response_time_hours=round(s.avg_response_time or 0.0, 2),
                email_volume=s.total_emails or 0,
                contract_count=s.total_contracts or 0,
                sla_breach_rate=sla_rate,
                bottleneck_frequency=0,
            )
        )
    return StakeholderComparison(items=items)


async def get_department_analytics(db: AsyncSession) -> DepartmentAnalytics:
    stakeholders = list((await db.execute(select(Stakeholder))).scalars().all())
    dept_data: dict[str, dict] = defaultdict(
        lambda: {"members": [], "response_times": [], "contracts": 0, "bottlenecks": 0}
    )

    for s in stakeholders:
        dept = s.department or "Unknown"
        dept_data[dept]["members"].append(s)
        if s.avg_response_time:
            dept_data[dept]["response_times"].append(s.avg_response_time)
        dept_data[dept]["contracts"] += s.total_contracts or 0

    items = []
    ranked = sorted(
        dept_data.items(),
        key=lambda x: (
            sum(x[1]["response_times"]) / len(x[1]["response_times"])
            if x[1]["response_times"] else 999
        ),
    )
    for rank, (dept, data) in enumerate(ranked, start=1):
        avg_rt = (
            round(sum(data["response_times"]) / len(data["response_times"]), 2)
            if data["response_times"] else 0.0
        )
        items.append(
            DepartmentAnalyticsItem(
                department=dept,
                member_count=len(data["members"]),
                avg_response_time_hours=avg_rt,
                contract_throughput=data["contracts"],
                bottleneck_frequency=data["bottlenecks"],
                efficiency_rank=rank,
            )
        )
    return DepartmentAnalytics(items=items)


async def get_department_comparison(db: AsyncSession, dept1: str, dept2: str) -> DepartmentComparison:
    analytics = await get_department_analytics(db)
    item1 = next((i for i in analytics.items if i.department == dept1), None)
    item2 = next((i for i in analytics.items if i.department == dept2), None)

    if item1 is None:
        item1 = DepartmentAnalyticsItem(
            department=dept1, member_count=0, avg_response_time_hours=0,
            contract_throughput=0, bottleneck_frequency=0, efficiency_rank=99,
        )
    if item2 is None:
        item2 = DepartmentAnalyticsItem(
            department=dept2, member_count=0, avg_response_time_hours=0,
            contract_throughput=0, bottleneck_frequency=0, efficiency_rank=99,
        )

    # Winner = lower response time
    winner = dept1 if item1.avg_response_time_hours <= item2.avg_response_time_hours else dept2
    return DepartmentComparison(dept1=item1, dept2=item2, winner=winner)


async def get_stakeholder_rankings(
    db: AsyncSession,
    metric: str = "response_time",
    order: str = "asc",
    limit: int = 10,
) -> list[StakeholderRanking]:
    stakeholders = list((await db.execute(select(Stakeholder))).scalars().all())

    def _metric_val(s: Stakeholder) -> float:
        if metric == "response_time":
            return s.avg_response_time or 0.0
        if metric == "email_volume":
            return float(s.total_emails or 0)
        if metric == "contract_count":
            return float(s.total_contracts or 0)
        if metric == "influence":
            return s.influence_score or 0.0
        return 0.0

    sorted_s = sorted(stakeholders, key=_metric_val, reverse=(order == "desc"))[:limit]
    return [
        StakeholderRanking(
            rank=i + 1,
            stakeholder_id=str(s.id),
            name=s.name,
            department=s.department,
            metric_value=round(_metric_val(s), 2),
            metric_name=metric,
        )
        for i, s in enumerate(sorted_s)
    ]


async def get_workload_balance(db: AsyncSession) -> WorkloadBalance:
    stakeholders = list((await db.execute(select(Stakeholder))).scalars().all())
    contracts = list((await db.execute(select(Contract))).scalars().all())

    load_map: dict[str, int] = defaultdict(int)
    for contract in contracts:
        if contract.current_stage in (None, "Repository & Obligation Tracking"):
            continue
        for entry in (contract.stage_history or []):
            if entry.get("actor"):
                load_map[entry["actor"]] += 1

    values = list(load_map.values())
    avg_load = round(sum(values) / len(values), 2) if values else 0.0
    overloaded_threshold = avg_load * 1.5

    items = []
    for s in stakeholders:
        load = load_map.get(s.email_address, load_map.get(s.name or "", 0))
        if load > overloaded_threshold:
            cat = "overloaded"
        elif load < avg_load * 0.5:
            cat = "underloaded"
        else:
            cat = "normal"
        items.append(
            WorkloadBalanceItem(
                stakeholder_id=str(s.id),
                name=s.name,
                department=s.department,
                active_contracts=load,
                load_category=cat,
            )
        )

    overloaded_count = sum(1 for i in items if i.load_category == "overloaded")
    return WorkloadBalance(items=items, avg_load=avg_load, overloaded_count=overloaded_count)


async def get_communication_network(db: AsyncSession) -> CommunicationNetwork:
    stakeholders = list((await db.execute(select(Stakeholder))).scalars().all())
    emails = list((await db.execute(select(Email))).scalars().all())

    edge_map: dict[tuple[str, str], int] = defaultdict(int)
    addr_to_id: dict[str, str] = {s.email_address: str(s.id) for s in stakeholders}

    for email in emails:
        src = addr_to_id.get(email.from_address, email.from_address)
        for addr in (email.to_addresses or []):
            tgt = addr_to_id.get(addr, addr)
            if src != tgt:
                edge_map[(src, tgt)] += 1

    nodes = [
        CommunicationNode(
            stakeholder_id=str(s.id),
            name=s.name,
            email=s.email_address,
            department=s.department,
            total_interactions=s.total_emails or 0,
        )
        for s in stakeholders
    ]
    edges = [
        CommunicationEdge(source=src, target=tgt, weight=count, email_count=count)
        for (src, tgt), count in sorted(edge_map.items(), key=lambda x: x[1], reverse=True)[:200]
    ]
    return CommunicationNetwork(nodes=nodes, edges=edges)


async def get_ai_recommendations(db: AsyncSession, stakeholder_id: UUID) -> AIRecommendation:
    cache_key = f"analytics:ai_recommendations:{stakeholder_id}"
    cached = await cache_get(cache_key)
    if cached:
        return AIRecommendation(**cached)

    stakeholder = await db.get(Stakeholder, stakeholder_id)
    if stakeholder is None:
        return AIRecommendation(
            stakeholder_id=str(stakeholder_id),
            recommendations=[],
            generated_at=datetime.now(UTC),
        )

    perf = await get_stakeholder_performance(db, stakeholder_id)
    ai_service = get_ai_service()
    prompt_data = {
        "stakeholder": {
            "name": stakeholder.name,
            "department": stakeholder.department,
            "role": stakeholder.role,
            "avg_response_time_hours": stakeholder.avg_response_time,
            "total_emails": stakeholder.total_emails,
            "total_contracts": stakeholder.total_contracts,
            "sla_breach_rate": perf.sla_breach_rate if perf else 0,
        }
    }
    result = await ai_service.complete(
        system_prompt=(
            "You are an HR and process improvement consultant. "
            "Analyze this stakeholder's performance data and provide 3-5 specific, actionable recommendations. "
            "Return JSON: {\"recommendations\": [\"...\", ...]}"
        ),
        user_prompt=json.dumps(prompt_data, default=str),
        max_tokens=600,
    )
    recommendations = result.get("recommendations") or []
    if isinstance(recommendations, str):
        recommendations = [recommendations]

    rec = AIRecommendation(
        stakeholder_id=str(stakeholder_id),
        recommendations=recommendations,
        generated_at=datetime.now(UTC),
    )
    await cache_set(cache_key, rec.model_dump(mode="json"), ttl_seconds=1800)
    return rec
