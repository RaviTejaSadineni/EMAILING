"""Tests for advanced analytics service and router."""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.classification import EmailClassification
from app.models.contract import Contract
from app.models.email import Email
from app.models.email_thread_link import EmailThreadLink
from app.models.stakeholder import Stakeholder
from app.services import advanced_analytics_service as svc


def _make_contract(
    risk_score: float | None = 0.5,
    sla_breached: bool = False,
    current_stage: str = "Legal Review",
) -> Contract:
    now = datetime.now(UTC)
    return Contract(
        id=uuid4(),
        thread_id=uuid4(),
        agreement_name="Advanced Test Contract",
        agreement_type="SOW",
        counterparty_name="BigCorp",
        current_stage=current_stage,
        stage_history=[
            {"stage": "Request", "date": "2024-04-01T00:00:00+00:00", "actor": "a@example.com"},
            {"stage": current_stage, "date": "2024-04-05T00:00:00+00:00", "actor": "b@example.com"},
        ],
        sla_breached=sla_breached,
        risk_score=risk_score,
        created_at=now,
        updated_at=now,
    )


def _make_email_with_classification(
    thread_id: uuid4 | None = None,
    sentiment: str = "neutral",
) -> tuple[Email, EmailClassification, EmailThreadLink | None]:
    email = Email(
        id=uuid4(),
        message_id=f"<{uuid4()}@test>",
        subject="Advanced Test Email",
        from_address="tester@example.com",
        to_addresses=["other@example.com"],
        cc_addresses=[],
        bcc_addresses=[],
        date=datetime.now(UTC),
        body_text="Test email for advanced analytics.",
        created_at=datetime.now(UTC),
    )
    cls = EmailClassification(
        id=uuid4(),
        email_id=email.id,
        category="contract",
        urgency="medium",
        sentiment=sentiment,
        created_at=datetime.now(UTC),
    )
    link = None
    if thread_id:
        link = EmailThreadLink(
            id=uuid4(),
            thread_id=thread_id,
            email_id=email.id,
        )
    return email, cls, link


@pytest.mark.asyncio
async def test_sentiment_timeline_no_contract(db_session: AsyncSession):
    result = await svc.get_sentiment_timeline(db_session, uuid4())
    assert result.points == []


@pytest.mark.asyncio
async def test_sentiment_timeline_with_data(db_session: AsyncSession):
    contract = _make_contract()
    db_session.add(contract)
    await db_session.commit()

    email, cls, link = _make_email_with_classification(
        thread_id=contract.thread_id, sentiment="positive"
    )
    db_session.add(email)
    db_session.add(cls)
    if link:
        db_session.add(link)
    await db_session.commit()

    result = await svc.get_sentiment_timeline(db_session, contract.id)
    assert len(result.points) >= 1
    assert result.points[0].sentiment == "positive"
    assert result.points[0].score == 1.0


@pytest.mark.asyncio
async def test_sentiment_by_stakeholder(db_session: AsyncSession):
    email, cls, _ = _make_email_with_classification(sentiment="negative")
    db_session.add(email)
    db_session.add(cls)
    await db_session.commit()

    results = await svc.get_sentiment_by_stakeholder(db_session)
    assert isinstance(results, list)
    if results:
        assert results[0].entity_type == "stakeholder"
        assert 0.0 <= results[0].avg_sentiment_score <= 1.0


@pytest.mark.asyncio
async def test_sentiment_by_stage(db_session: AsyncSession):
    results = await svc.get_sentiment_by_stage(db_session)
    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_escalation_patterns(db_session: AsyncSession):
    patterns = await svc.get_escalation_patterns(db_session)
    assert isinstance(patterns, list)
    if patterns:
        assert patterns[0].pattern_type == "consecutive_negative"


@pytest.mark.asyncio
async def test_sentiment_correlation(db_session: AsyncSession):
    result = await svc.get_sentiment_correlation(db_session)
    assert "correlation" in result
    assert "description" in result


@pytest.mark.asyncio
async def test_risk_matrix(db_session: AsyncSession):
    c = _make_contract(risk_score=0.8)
    db_session.add(c)
    await db_session.commit()

    matrix = await svc.get_risk_matrix(db_session)
    assert len(matrix.points) >= 1
    # Check that at least one point has the expected risk_score
    scores = [p.risk_score for p in matrix.points]
    assert any(abs(s - 0.8) < 0.01 for s in scores)


@pytest.mark.asyncio
async def test_risk_factors_breakdown(db_session: AsyncSession):
    c = _make_contract(sla_breached=True, risk_score=0.9)
    db_session.add(c)
    await db_session.commit()

    factors = await svc.get_risk_factors_breakdown(db_session, c.id)
    assert factors.overall_risk_score == pytest.approx(0.9, abs=0.01)
    assert len(factors.factors) >= 1
    factor_names = {f.factor for f in factors.factors}
    assert "SLA Breach" in factor_names


@pytest.mark.asyncio
async def test_risk_factors_no_contract(db_session: AsyncSession):
    factors = await svc.get_risk_factors_breakdown(db_session, uuid4())
    assert factors.overall_risk_score == 0.0
    assert factors.factors == []


@pytest.mark.asyncio
async def test_risk_trend(db_session: AsyncSession):
    c = _make_contract(risk_score=0.6)
    db_session.add(c)
    await db_session.commit()

    trend = await svc.get_risk_trend(db_session)
    assert len(trend.points) >= 1


@pytest.mark.asyncio
async def test_high_risk_alerts(db_session: AsyncSession):
    high_risk = _make_contract(risk_score=0.9, sla_breached=True)
    low_risk = _make_contract(risk_score=0.2)
    db_session.add_all([high_risk, low_risk])
    await db_session.commit()

    alerts = await svc.get_high_risk_alerts(db_session, threshold=0.7)
    assert len(alerts) >= 1
    # Check our high-risk contract is included
    alert_ids = {a.contract_id for a in alerts}
    assert str(high_risk.id) in alert_ids
    # SLA breached reason should be included
    high_alert = next(a for a in alerts if a.contract_id == str(high_risk.id))
    assert "SLA breached" in high_alert.reasons
    # Low risk contract should NOT be in alerts
    assert str(low_risk.id) not in alert_ids


@pytest.mark.asyncio
async def test_predict_contract_completion(db_session: AsyncSession):
    c = _make_contract(current_stage="Legal Review")
    db_session.add(c)
    await db_session.commit()

    prediction = await svc.predict_contract_completion(db_session, c.id)
    assert prediction.contract_id == str(c.id)
    assert 0.0 <= prediction.sla_breach_probability <= 1.0
    assert prediction.confidence >= 0.0


@pytest.mark.asyncio
async def test_predict_contract_completion_not_found(db_session: AsyncSession):
    prediction = await svc.predict_contract_completion(db_session, uuid4())
    assert prediction.sla_breach_probability == 0.0
    assert prediction.confidence == 0.0


@pytest.mark.asyncio
async def test_predict_bottleneck(db_session: AsyncSession):
    c = _make_contract()
    db_session.add(c)
    await db_session.commit()

    result = await svc.predict_bottleneck(db_session, c.id)
    assert result.contract_id == str(c.id)
    assert 0.0 <= result.probability <= 1.0
    assert result.predicted_bottleneck_stage  # non-empty string


@pytest.mark.asyncio
async def test_detect_anomalies(db_session: AsyncSession):
    result = await svc.detect_anomalies(db_session)
    assert hasattr(result, "anomalies")
    assert hasattr(result, "total")
    assert result.total == len(result.anomalies)


@pytest.mark.asyncio
async def test_detect_backward_transition_anomaly(db_session: AsyncSession):
    now = datetime.now(UTC)
    contract = Contract(
        id=uuid4(),
        thread_id=uuid4(),
        agreement_name="Backward Test",
        agreement_type="NDA",
        current_stage="Legal Review",
        stage_history=[
            {"stage": "Request", "date": "2024-04-01T00:00:00+00:00", "actor": "a@example.com"},
            {"stage": "Legal Review", "date": "2024-04-03T00:00:00+00:00", "actor": "b@example.com"},
            # Backward transition: back to Request
            {"stage": "Request", "date": "2024-04-05T00:00:00+00:00", "actor": "c@example.com"},
        ],
        sla_breached=False,
        created_at=now,
        updated_at=now,
    )
    db_session.add(contract)
    await db_session.commit()

    result = await svc.detect_anomalies(db_session)
    backward_anomalies = [a for a in result.anomalies if a.anomaly_type == "backward_stage_transition"]
    assert len(backward_anomalies) >= 1


@pytest.mark.asyncio
async def test_advanced_analytics_anomalies_endpoint_unauthorized(client):
    response = await client.get("/api/analytics/advanced/anomalies")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_advanced_analytics_risk_matrix_unauthorized(client):
    response = await client.get("/api/analytics/advanced/risk/matrix")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_predict_workload(db_session: AsyncSession):
    s = Stakeholder(
        id=uuid4(),
        email_address="workload@example.com",
        name="Workload User",
        department="Legal",
        is_internal=True,
        total_emails=5,
        total_contracts=2,
        created_at=datetime.now(UTC),
    )
    db_session.add(s)
    await db_session.commit()

    forecast = await svc.predict_workload(db_session, department="Legal", period="month")
    assert forecast.department == "Legal"
    assert forecast.period == "month"
