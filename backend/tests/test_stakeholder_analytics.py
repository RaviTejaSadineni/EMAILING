"""Tests for stakeholder analytics service and router."""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contract import Contract
from app.models.stakeholder import Stakeholder
from app.services import stakeholder_analytics_service as svc


def _make_stakeholder(
    name: str = "Alice",
    department: str = "Legal",
    is_internal: bool = True,
    avg_response_time: float = 4.5,
) -> Stakeholder:
    unique_suffix = uuid4().hex[:8]
    return Stakeholder(
        id=uuid4(),
        email_address=f"{name.lower()}_{unique_suffix}@example.com",
        name=name,
        department=department,
        role="Manager",
        is_internal=is_internal,
        avg_response_time=avg_response_time,
        total_emails=10,
        total_contracts=3,
        response_time_distribution={"p90": 8.0, "median": 4.0, "trend": "stable"},
        communication_patterns={},
        influence_score=0.7,
        department_mentions=[department],
        created_at=datetime.now(UTC),
    )


def _make_contract(actor: str = "Alice", stage: str = "Legal Review") -> Contract:
    now = datetime.now(UTC)
    return Contract(
        id=uuid4(),
        thread_id=uuid4(),
        agreement_name="Service Agreement",
        agreement_type="MSA",
        current_stage=stage,
        stage_history=[
            {"stage": "Request", "date": "2024-02-01T00:00:00+00:00", "actor": actor},
            {"stage": stage, "date": "2024-02-03T00:00:00+00:00", "actor": actor},
        ],
        sla_breached=False,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_performance_not_found(db_session: AsyncSession):
    result = await svc.get_stakeholder_performance(db_session, uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_performance_basic(db_session: AsyncSession):
    s = _make_stakeholder()
    db_session.add(s)
    await db_session.commit()

    perf = await svc.get_stakeholder_performance(db_session, s.id)
    assert perf is not None
    assert perf.stakeholder_id == str(s.id)
    assert perf.name == "Alice"
    assert perf.response_time.avg_hours == pytest.approx(4.5, abs=0.1)
    assert perf.response_time.trend == "stable"


@pytest.mark.asyncio
async def test_response_time_trend(db_session: AsyncSession):
    s = _make_stakeholder()
    db_session.add(s)
    await db_session.commit()

    trend = await svc.get_stakeholder_response_time_trend(db_session, s.id, period="month")
    assert trend.stakeholder_id == str(s.id)
    assert isinstance(trend.points, list)


@pytest.mark.asyncio
async def test_workload_timeline(db_session: AsyncSession):
    s = _make_stakeholder("Bob")
    db_session.add(s)
    c = _make_contract(actor="Bob")
    db_session.add(c)
    await db_session.commit()

    timeline = await svc.get_stakeholder_workload_timeline(db_session, s.id)
    assert timeline.stakeholder_id == str(s.id)


@pytest.mark.asyncio
async def test_contracts_detail(db_session: AsyncSession):
    s = _make_stakeholder("Carol")
    db_session.add(s)
    c = _make_contract(actor="Carol")
    db_session.add(c)
    await db_session.commit()

    result = await svc.get_stakeholder_contracts_detail(db_session, s.id)
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_communication_network(db_session: AsyncSession):
    s = _make_stakeholder("Dave")
    db_session.add(s)
    await db_session.commit()

    network = await svc.get_stakeholder_communication_network(db_session, s.id)
    assert len(network.nodes) >= 1  # At least the stakeholder itself
    assert isinstance(network.edges, list)


@pytest.mark.asyncio
async def test_stakeholder_comparison(db_session: AsyncSession):
    s1 = _make_stakeholder("Eve", department="Legal", avg_response_time=2.0)
    s2 = _make_stakeholder("Frank", department="Finance", avg_response_time=6.0)
    db_session.add(s1)
    db_session.add(s2)
    await db_session.commit()

    result = await svc.get_stakeholder_comparison(db_session, [str(s1.id), str(s2.id)])
    assert len(result.items) == 2
    names = {i.name for i in result.items}
    assert "Eve" in names
    assert "Frank" in names


@pytest.mark.asyncio
async def test_department_analytics(db_session: AsyncSession):
    s1 = _make_stakeholder("Grace", department="Legal")
    s2 = _make_stakeholder("Heidi", department="Finance")
    db_session.add(s1)
    db_session.add(s2)
    await db_session.commit()

    analytics = await svc.get_department_analytics(db_session)
    assert len(analytics.items) >= 2
    depts = {i.department for i in analytics.items}
    assert "Legal" in depts
    assert "Finance" in depts


@pytest.mark.asyncio
async def test_department_comparison(db_session: AsyncSession):
    s1 = _make_stakeholder("Ivan", department="Legal", avg_response_time=3.0)
    s2 = _make_stakeholder("Judy", department="Finance", avg_response_time=7.0)
    db_session.add(s1)
    db_session.add(s2)
    await db_session.commit()

    comp = await svc.get_department_comparison(db_session, "Legal", "Finance")
    assert comp.dept1.department == "Legal"
    assert comp.dept2.department == "Finance"
    assert comp.winner == "Legal"


@pytest.mark.asyncio
async def test_stakeholder_rankings(db_session: AsyncSession):
    s1 = _make_stakeholder("Karl", avg_response_time=1.0)
    s2 = _make_stakeholder("Laura", avg_response_time=10.0)
    db_session.add(s1)
    db_session.add(s2)
    await db_session.commit()

    rankings = await svc.get_stakeholder_rankings(db_session, metric="response_time", order="asc", limit=10)
    assert len(rankings) >= 2
    # Karl (1.0h) should be first (lowest response time)
    assert rankings[0].metric_value <= rankings[1].metric_value


@pytest.mark.asyncio
async def test_workload_balance(db_session: AsyncSession):
    s = _make_stakeholder("Mary")
    db_session.add(s)
    await db_session.commit()

    balance = await svc.get_workload_balance(db_session)
    assert isinstance(balance.items, list)
    assert balance.avg_load >= 0


@pytest.mark.asyncio
async def test_communication_network_full(db_session: AsyncSession):
    s1 = _make_stakeholder("Nick")
    s2 = _make_stakeholder("Olivia")
    db_session.add(s1)
    db_session.add(s2)
    await db_session.commit()

    network = await svc.get_communication_network(db_session)
    assert len(network.nodes) >= 2


@pytest.mark.asyncio
async def test_stakeholder_performance_endpoint_unauthorized(client):
    response = await client.get(f"/api/analytics/stakeholders/{uuid4()}/performance")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_stakeholder_rankings_endpoint_unauthorized(client):
    response = await client.get("/api/analytics/stakeholders/rankings")
    assert response.status_code == 401
