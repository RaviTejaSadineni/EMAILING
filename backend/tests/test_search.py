"""Tests for search service and saved filter CRUD."""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contract import Contract
from app.models.email import Email
from app.models.stakeholder import Stakeholder
from app.models.user import User
from app.schemas.search import FilterParams, SavedFilterCreate
from app.services import search_service as svc
from app.utils.security import hash_password


def _make_email(subject: str = "Contract Review") -> Email:
    return Email(
        id=uuid4(),
        message_id=f"<{uuid4()}@test>",
        subject=subject,
        from_address="sender@example.com",
        to_addresses=["recipient@example.com"],
        cc_addresses=[],
        bcc_addresses=[],
        date=datetime.now(UTC),
        body_text=f"Body of {subject}. Contains contract discussion.",
        created_at=datetime.now(UTC),
    )


def _make_contract(
    name: str = "Software License Agreement",
    agreement_type: str = "SLA",
    stage: str = "Legal Review",
) -> Contract:
    now = datetime.now(UTC)
    return Contract(
        id=uuid4(),
        thread_id=uuid4(),
        agreement_name=name,
        agreement_type=agreement_type,
        counterparty_name="SoftCo",
        current_stage=stage,
        stage_history=[],
        sla_breached=False,
        created_at=now,
        updated_at=now,
    )


def _make_stakeholder(name: str = "SearchUser", dept: str = "Legal") -> Stakeholder:
    return Stakeholder(
        id=uuid4(),
        email_address=f"{name.lower()}@example.com",
        name=name,
        department=dept,
        role="Analyst",
        is_internal=True,
        total_emails=5,
        total_contracts=1,
        created_at=datetime.now(UTC),
    )


def _make_user() -> User:
    return User(
        id=uuid4(),
        email=f"user_{uuid4().hex[:6]}@test.com",
        username=f"user_{uuid4().hex[:6]}",
        hashed_password=hash_password("TestPass1!"),
        is_active=True,
        created_at=datetime.now(UTC),
    )


# ── Full-text search tests ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_search_emails_found(db_session: AsyncSession):
    e = _make_email(subject="Contract Review Meeting")
    db_session.add(e)
    await db_session.commit()

    results = await svc.search_emails(db_session, "Contract")
    assert len(results) >= 1
    assert results[0].entity_type == "email"
    titles = [r.title for r in results]
    assert "Contract Review Meeting" in titles


@pytest.mark.asyncio
async def test_search_emails_not_found(db_session: AsyncSession):
    e = _make_email(subject="Quarterly Report")
    db_session.add(e)
    await db_session.commit()

    results = await svc.search_emails(db_session, "zzzyyyxxx_unique_nonsense")
    assert results == []


@pytest.mark.asyncio
async def test_search_contracts_found(db_session: AsyncSession):
    c = _make_contract(name="Enterprise Software License")
    db_session.add(c)
    await db_session.commit()

    results = await svc.search_contracts(db_session, "Enterprise")
    assert len(results) >= 1
    assert results[0].entity_type == "contract"


@pytest.mark.asyncio
async def test_search_contracts_with_filters(db_session: AsyncSession):
    c1 = _make_contract(name="NDA Agreement A", agreement_type="NDA", stage="Legal Review")
    c2 = _make_contract(name="NDA Agreement B", agreement_type="NDA", stage="Finance Review")
    c3 = _make_contract(name="MSA Agreement", agreement_type="MSA", stage="Legal Review")
    db_session.add_all([c1, c2, c3])
    await db_session.commit()

    filters = FilterParams(contract_type="NDA")
    results = await svc.search_contracts(db_session, "NDA", filters)
    assert len(results) == 2
    for r in results:
        assert "NDA" in r.title


@pytest.mark.asyncio
async def test_search_contracts_stage_filter(db_session: AsyncSession):
    c1 = _make_contract(name="Legal Stage Contract", stage="Legal Review")
    c2 = _make_contract(name="Finance Stage Contract", stage="Finance Review")
    db_session.add_all([c1, c2])
    await db_session.commit()

    filters = FilterParams(stage="Legal Review")
    results = await svc.search_contracts(db_session, "Contract", filters)
    assert all("Legal" in r.snippet for r in results)


@pytest.mark.asyncio
async def test_search_stakeholders_found(db_session: AsyncSession):
    s = _make_stakeholder(name="Findable Person", dept="Procurement")
    db_session.add(s)
    await db_session.commit()

    results = await svc.search_stakeholders(db_session, "Findable")
    assert len(results) >= 1
    assert results[0].entity_type == "stakeholder"
    assert "Findable" in results[0].title


@pytest.mark.asyncio
async def test_search_stakeholders_department_filter(db_session: AsyncSession):
    s1 = _make_stakeholder(name="LegalPerson", dept="Legal")
    s2 = _make_stakeholder(name="FinancePerson", dept="Finance")
    db_session.add_all([s1, s2])
    await db_session.commit()

    filters = FilterParams(department="Legal")
    results = await svc.search_stakeholders(db_session, "Person", filters)
    assert all("Legal" in r.snippet for r in results)


@pytest.mark.asyncio
async def test_search_all(db_session: AsyncSession):
    e = _make_email(subject="Important Contract")
    c = _make_contract(name="Important Agreement")
    s = _make_stakeholder(name="Important Person")
    db_session.add_all([e, c, s])
    await db_session.commit()

    result = await svc.search_all(db_session, "Important")
    assert result.total >= 3
    entity_types = {item.entity_type for item in result.items}
    assert "email" in entity_types
    assert "contract" in entity_types
    assert "stakeholder" in entity_types


@pytest.mark.asyncio
async def test_search_all_empty_query(db_session: AsyncSession):
    result = await svc.search_all(db_session, "qwertyuiop_no_match_xyz")
    assert result.total == 0
    assert result.items == []


# ── Pagination tests ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_search_pagination(db_session: AsyncSession):
    for i in range(5):
        db_session.add(_make_email(subject=f"Page Test Email {i}"))
    await db_session.commit()

    filters_p1 = FilterParams(page=1, page_size=3)
    filters_p2 = FilterParams(page=2, page_size=3)

    results_p1 = await svc.search_emails(db_session, "Page Test", filters_p1)
    results_p2 = await svc.search_emails(db_session, "Page Test", filters_p2)

    assert len(results_p1) <= 3
    assert len(results_p2) <= 3
    # Different pages should have different items (if enough data)
    if results_p1 and results_p2:
        ids_p1 = {r.entity_id for r in results_p1}
        ids_p2 = {r.entity_id for r in results_p2}
        assert not ids_p1.intersection(ids_p2)


# ── Sort ordering tests ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_search_suggestions(db_session: AsyncSession):
    c = _make_contract(name="Unique Suggestion Contract")
    db_session.add(c)
    s = _make_stakeholder(name="Unique Suggestion Person")
    db_session.add(s)
    await db_session.commit()

    suggestions = await svc.get_search_suggestions(db_session, "Unique")
    assert len(suggestions) >= 1
    texts = [sg.text for sg in suggestions]
    assert any("Unique" in t for t in texts)


@pytest.mark.asyncio
async def test_search_suggestions_short_query(db_session: AsyncSession):
    suggestions = await svc.get_search_suggestions(db_session, "a")
    # Short query (< 2 chars) should return empty
    assert suggestions == []


# ── Saved Filter CRUD tests ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_saved_filter_create(db_session: AsyncSession):
    user = _make_user()
    db_session.add(user)
    await db_session.commit()

    payload = SavedFilterCreate(
        name="My Test Filter",
        description="Filter for contracts in Legal Review",
        filter_params={"stage": "Legal Review", "contract_type": "NDA"},
        is_default=False,
    )
    sf = await svc.create_saved_filter(db_session, user.id, payload)
    assert sf.name == "My Test Filter"
    assert sf.user_id == user.id
    assert sf.filter_params["stage"] == "Legal Review"
    assert sf.is_default is False


@pytest.mark.asyncio
async def test_saved_filter_list(db_session: AsyncSession):
    user = _make_user()
    db_session.add(user)
    await db_session.commit()

    for i in range(3):
        payload = SavedFilterCreate(
            name=f"Filter {i}",
            filter_params={"page": i},
        )
        await svc.create_saved_filter(db_session, user.id, payload)

    filters = await svc.list_saved_filters(db_session, user.id)
    assert len(filters) == 3


@pytest.mark.asyncio
async def test_saved_filter_update(db_session: AsyncSession):
    user = _make_user()
    db_session.add(user)
    await db_session.commit()

    payload = SavedFilterCreate(name="Original Name", filter_params={})
    sf = await svc.create_saved_filter(db_session, user.id, payload)

    update_payload = SavedFilterCreate(
        name="Updated Name",
        description="New description",
        filter_params={"stage": "Finance Review"},
        is_default=True,
    )
    updated = await svc.update_saved_filter(db_session, sf.id, user.id, update_payload)
    assert updated is not None
    assert updated.name == "Updated Name"
    assert updated.filter_params["stage"] == "Finance Review"
    assert updated.is_default is True


@pytest.mark.asyncio
async def test_saved_filter_update_wrong_user(db_session: AsyncSession):
    user1 = _make_user()
    user2 = _make_user()
    db_session.add_all([user1, user2])
    await db_session.commit()

    payload = SavedFilterCreate(name="User1 Filter", filter_params={})
    sf = await svc.create_saved_filter(db_session, user1.id, payload)

    # Attempt update with wrong user
    update_payload = SavedFilterCreate(name="Hacked Name", filter_params={})
    result = await svc.update_saved_filter(db_session, sf.id, user2.id, update_payload)
    assert result is None


@pytest.mark.asyncio
async def test_saved_filter_delete(db_session: AsyncSession):
    user = _make_user()
    db_session.add(user)
    await db_session.commit()

    payload = SavedFilterCreate(name="To Delete", filter_params={})
    sf = await svc.create_saved_filter(db_session, user.id, payload)

    deleted = await svc.delete_saved_filter(db_session, sf.id, user.id)
    assert deleted is True

    filters = await svc.list_saved_filters(db_session, user.id)
    assert len(filters) == 0


@pytest.mark.asyncio
async def test_saved_filter_delete_wrong_user(db_session: AsyncSession):
    user1 = _make_user()
    user2 = _make_user()
    db_session.add_all([user1, user2])
    await db_session.commit()

    payload = SavedFilterCreate(name="Protected Filter", filter_params={})
    sf = await svc.create_saved_filter(db_session, user1.id, payload)

    deleted = await svc.delete_saved_filter(db_session, sf.id, user2.id)
    assert deleted is False

    # Original still exists
    filters = await svc.list_saved_filters(db_session, user1.id)
    assert len(filters) == 1


# ── Router endpoint authorization tests ──────────────────────────────────────

@pytest.mark.asyncio
async def test_search_endpoint_requires_auth(client):
    response = await client.get("/api/search?q=test")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_search_emails_endpoint_requires_auth(client):
    response = await client.get("/api/search/emails?q=test")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_search_contracts_endpoint_requires_auth(client):
    response = await client.get("/api/search/contracts?q=test")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_search_stakeholders_endpoint_requires_auth(client):
    response = await client.get("/api/search/stakeholders?q=test")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_semantic_search_endpoint_requires_auth(client):
    response = await client.post("/api/search/semantic", json={"query": "test"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_saved_filters_endpoints_require_auth(client):
    response = await client.get("/api/filters/saved")
    assert response.status_code == 401

    response = await client.post("/api/filters/saved", json={"name": "test", "filter_params": {}})
    assert response.status_code == 401
