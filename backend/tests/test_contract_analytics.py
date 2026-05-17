"""Tests for contract analytics service and router."""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contract import Contract
from app.services import contract_analytics_service as svc


def _make_contract(
    sla_breached: bool = False,
    current_stage: str | None = "Legal Review",
    risk_score: float | None = 0.5,
) -> Contract:
    now = datetime.now(UTC)
    return Contract(
        id=uuid4(),
        thread_id=uuid4(),
        agreement_name="Test Agreement",
        agreement_type="NDA",
        counterparty_name="Acme Corp",
        current_stage=current_stage,
        stage_history=[
            {"stage": "Request", "date": "2024-01-01T00:00:00+00:00", "actor": "alice@example.com", "notes": "Started"},
            {"stage": "Legal Review", "date": "2024-01-03T00:00:00+00:00", "actor": "bob@example.com", "notes": "Review"},
        ],
        sla_breached=sla_breached,
        risk_score=risk_score,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_get_contract_timeline_no_contract(db_session: AsyncSession):
    timeline = await svc.get_contract_timeline(db_session, uuid4())
    assert timeline.contract_id is not None
    assert timeline.events == []


@pytest.mark.asyncio
async def test_get_contract_timeline_with_contract(db_session: AsyncSession):
    contract = _make_contract()
    db_session.add(contract)
    await db_session.commit()

    timeline = await svc.get_contract_timeline(db_session, contract.id)
    assert timeline.contract_id == str(contract.id)
    # Should have stage entry events
    assert len(timeline.events) >= 2
    stages = [e.event_type for e in timeline.events]
    assert "stage_entry" in stages


@pytest.mark.asyncio
async def test_get_stage_durations(db_session: AsyncSession):
    contract = _make_contract()
    db_session.add(contract)
    await db_session.commit()

    durations = await svc.get_contract_stage_durations(db_session, contract.id)
    assert len(durations) >= 1
    # First stage: Request → Legal Review = 48h
    first = durations[0]
    assert first.stage == "Request"
    assert first.duration_hours == pytest.approx(48.0, abs=1.0)


@pytest.mark.asyncio
async def test_get_stage_durations_no_contract(db_session: AsyncSession):
    result = await svc.get_contract_stage_durations(db_session, uuid4())
    assert result == []


@pytest.mark.asyncio
async def test_get_stage_duration_stats_empty(db_session: AsyncSession):
    stats = await svc.get_stage_duration_stats(db_session)
    # With no contracts, should return empty list
    assert isinstance(stats, list)


@pytest.mark.asyncio
async def test_get_stage_duration_stats_with_data(db_session: AsyncSession):
    c1 = _make_contract()
    c2 = _make_contract()
    db_session.add(c1)
    db_session.add(c2)
    await db_session.commit()

    stats = await svc.get_stage_duration_stats(db_session)
    assert isinstance(stats, list)
    if stats:
        stat = stats[0]
        assert stat.avg_hours >= 0
        assert stat.sample_count >= 1


@pytest.mark.asyncio
async def test_bottleneck_analysis(db_session: AsyncSession):
    contract = _make_contract()
    db_session.add(contract)
    await db_session.commit()

    reports = await svc.get_bottleneck_analysis(db_session)
    assert isinstance(reports, list)


@pytest.mark.asyncio
async def test_sla_breach_report_no_breaches(db_session: AsyncSession):
    contract = _make_contract(sla_breached=False)
    db_session.add(contract)
    await db_session.commit()

    report = await svc.get_sla_breach_report(db_session)
    # Our specific non-breached contract should NOT be in the report
    breach_ids = {item.contract_id for item in report.items}
    assert str(contract.id) not in breach_ids


@pytest.mark.asyncio
async def test_sla_breach_report_with_breach(db_session: AsyncSession):
    contract = _make_contract(sla_breached=True)
    db_session.add(contract)
    await db_session.commit()

    report = await svc.get_sla_breach_report(db_session)
    assert report.total_breaches >= 1
    breach_ids = {item.contract_id for item in report.items}
    assert str(contract.id) in breach_ids


@pytest.mark.asyncio
async def test_sla_compliance_trend(db_session: AsyncSession):
    contract = _make_contract(sla_breached=False)
    db_session.add(contract)
    await db_session.commit()

    trend = await svc.get_sla_compliance_rate(db_session)
    assert hasattr(trend, "periods")


@pytest.mark.asyncio
async def test_stage_transition_matrix(db_session: AsyncSession):
    contract = _make_contract()
    db_session.add(contract)
    await db_session.commit()

    transitions = await svc.get_stage_transition_matrix(db_session)
    assert isinstance(transitions, list)
    if transitions:
        t = transitions[0]
        assert t.count >= 1


@pytest.mark.asyncio
async def test_negotiation_loop_analysis(db_session: AsyncSession):
    analysis = await svc.get_negotiation_loop_analysis(db_session)
    assert analysis.avg_rounds >= 0
    assert len(analysis.most_negotiated_clauses) == 3
    assert analysis.most_negotiated_clauses[0]["clause"] == "Liability"


@pytest.mark.asyncio
async def test_cycle_time_distribution(db_session: AsyncSession):
    dist = await svc.get_cycle_time_distribution(db_session)
    assert len(dist.bins) == 6
    assert dist.avg_days >= 0


@pytest.mark.asyncio
async def test_contract_velocity_trend(db_session: AsyncSession):
    contract = _make_contract()
    db_session.add(contract)
    await db_session.commit()

    trend = await svc.get_contract_velocity_trend(db_session, period="month")
    assert hasattr(trend, "points")


@pytest.mark.asyncio
async def test_stage_health_overview(db_session: AsyncSession):
    contract = _make_contract()
    db_session.add(contract)
    await db_session.commit()

    health = await svc.get_stage_health_overview(db_session)
    assert hasattr(health, "items")
    assert hasattr(health, "as_of")


@pytest.mark.asyncio
async def test_contract_analytics_timeline_endpoint(client):
    """Test the timeline endpoint returns 401 without auth."""
    contract_id = str(uuid4())
    response = await client.get(f"/api/analytics/contracts/timeline/{contract_id}")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_contract_analytics_stage_health_endpoint(client):
    """Test the stage health endpoint returns 401 without auth."""
    response = await client.get("/api/analytics/contracts/stage-health")
    assert response.status_code == 401
