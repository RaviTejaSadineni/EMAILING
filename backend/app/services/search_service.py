from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contract import Contract
from app.models.email import Email
from app.models.saved_filter import SavedFilter
from app.models.stakeholder import Stakeholder
from app.models.user import User
from app.schemas.search import (
    FilterParams,
    SavedFilterCreate,
    SavedFilterResponse,
    SearchResult,
    SearchResultItem,
    SearchSuggestion,
)
from app.services.ai_service import get_ai_service
from app.services.cache_service import cache_get, cache_set


async def search_emails(db: AsyncSession, query: str, filters: FilterParams | None = None) -> list[SearchResultItem]:
    q = select(Email).where(
        Email.subject.ilike(f"%{query}%") | Email.body_text.ilike(f"%{query}%")
    )
    if filters:
        if filters.date_from:
            q = q.where(Email.date >= filters.date_from)
        if filters.date_to:
            q = q.where(Email.date <= filters.date_to)
    q = q.order_by(Email.date.desc())
    if filters:
        limit = filters.page_size
        offset = (filters.page - 1) * filters.page_size
        q = q.limit(limit).offset(offset)
    else:
        q = q.limit(20)

    rows = list((await db.execute(q)).scalars().all())
    results = []
    for email in rows:
        body_snippet = (email.body_text or "")[:200]
        results.append(
            SearchResultItem(
                entity_type="email",
                entity_id=str(email.id),
                title=email.subject or "(no subject)",
                snippet=body_snippet,
                relevance_score=_simple_relevance(query, (email.subject or "") + " " + body_snippet),
            )
        )
    return results


async def search_contracts(db: AsyncSession, query: str, filters: FilterParams | None = None) -> list[SearchResultItem]:
    q = select(Contract).where(
        Contract.agreement_name.ilike(f"%{query}%")
        | Contract.counterparty_name.ilike(f"%{query}%")
        | Contract.ai_summary.ilike(f"%{query}%")
    )
    if filters:
        if filters.date_from:
            q = q.where(Contract.created_at >= filters.date_from)
        if filters.date_to:
            q = q.where(Contract.created_at <= filters.date_to)
        if filters.contract_type:
            q = q.where(Contract.agreement_type == filters.contract_type)
        if filters.stage:
            q = q.where(Contract.current_stage == filters.stage)
        if filters.sla_status == "breached":
            q = q.where(Contract.sla_breached.is_(True))
        if filters.counterparty:
            q = q.where(Contract.counterparty_name.ilike(f"%{filters.counterparty}%"))
        limit = filters.page_size
        offset = (filters.page - 1) * filters.page_size
        q = q.limit(limit).offset(offset)
    else:
        q = q.limit(20)

    rows = list((await db.execute(q)).scalars().all())
    return [
        SearchResultItem(
            entity_type="contract",
            entity_id=str(c.id),
            title=c.agreement_name or "Unnamed Contract",
            snippet=f"Type: {c.agreement_type} | Stage: {c.current_stage} | Party: {c.counterparty_name}",
            relevance_score=_simple_relevance(query, (c.agreement_name or "") + " " + (c.counterparty_name or "")),
        )
        for c in rows
    ]


async def search_stakeholders(db: AsyncSession, query: str, filters: FilterParams | None = None) -> list[SearchResultItem]:
    q = select(Stakeholder).where(
        Stakeholder.name.ilike(f"%{query}%")
        | Stakeholder.email_address.ilike(f"%{query}%")
        | Stakeholder.department.ilike(f"%{query}%")
    )
    if filters:
        if filters.department:
            q = q.where(Stakeholder.department == filters.department)
        if filters.is_internal is not None:
            q = q.where(Stakeholder.is_internal.is_(filters.is_internal))
        limit = filters.page_size
        offset = (filters.page - 1) * filters.page_size
        q = q.limit(limit).offset(offset)
    else:
        q = q.limit(20)

    rows = list((await db.execute(q)).scalars().all())
    return [
        SearchResultItem(
            entity_type="stakeholder",
            entity_id=str(s.id),
            title=s.name or s.email_address,
            snippet=f"Dept: {s.department} | Role: {s.role} | Email: {s.email_address}",
            relevance_score=_simple_relevance(query, (s.name or "") + " " + s.email_address),
        )
        for s in rows
    ]


async def search_all(db: AsyncSession, query: str, filters: FilterParams | None = None) -> SearchResult:
    emails = await search_emails(db, query, filters)
    contracts = await search_contracts(db, query, filters)
    stakeholders = await search_stakeholders(db, query, filters)
    all_items = sorted(emails + contracts + stakeholders, key=lambda x: x.relevance_score, reverse=True)
    return SearchResult(
        query=query,
        total=len(all_items),
        items=all_items[:50],
        emails=emails,
        contracts=contracts,
        stakeholders=stakeholders,
    )


async def semantic_search(db: AsyncSession, query: str) -> SearchResult:
    cache_key = f"analytics:semantic_search:{hash(query)}"
    cached = await cache_get(cache_key)
    if cached:
        return SearchResult(**cached)

    ai_service = get_ai_service()
    result = await ai_service.complete(
        system_prompt=(
            "You are a search assistant for a legal contract management system. "
            "Given a natural language query, extract search keywords and entity type. "
            "Return JSON: {\"keywords\": [\"...\"], \"entity_type\": \"email|contract|stakeholder|all\", "
            "\"filters\": {\"stage\": null, \"contract_type\": null, \"department\": null}}"
        ),
        user_prompt=query,
        max_tokens=300,
    )

    keywords = result.get("keywords") or [query]
    entity_type = result.get("entity_type", "all")
    extracted_keyword = " ".join(keywords[:3])

    filters_data = result.get("filters") or {}
    fp = FilterParams(
        stage=filters_data.get("stage"),
        contract_type=filters_data.get("contract_type"),
        department=filters_data.get("department"),
    )

    if entity_type == "email":
        items = await search_emails(db, extracted_keyword, fp)
        search_result = SearchResult(query=query, total=len(items), items=items, emails=items)
    elif entity_type == "contract":
        items = await search_contracts(db, extracted_keyword, fp)
        search_result = SearchResult(query=query, total=len(items), items=items, contracts=items)
    elif entity_type == "stakeholder":
        items = await search_stakeholders(db, extracted_keyword, fp)
        search_result = SearchResult(query=query, total=len(items), items=items, stakeholders=items)
    else:
        search_result = await search_all(db, extracted_keyword, fp)

    await cache_set(cache_key, search_result.model_dump(mode="json"), ttl_seconds=300)
    return search_result


async def get_search_suggestions(db: AsyncSession, partial_query: str) -> list[SearchSuggestion]:
    suggestions: list[SearchSuggestion] = []
    q = partial_query.strip()
    if not q or len(q) < 2:
        return suggestions

    # Contract names
    contracts = list(
        (await db.execute(
            select(Contract.agreement_name)
            .where(Contract.agreement_name.ilike(f"%{q}%"))
            .limit(5)
        )).all()
    )
    for (name,) in contracts:
        if name:
            suggestions.append(SearchSuggestion(text=name, entity_type="contract", count=1))

    # Stakeholder names
    stakeholders = list(
        (await db.execute(
            select(Stakeholder.name)
            .where(Stakeholder.name.ilike(f"%{q}%"))
            .limit(5)
        )).all()
    )
    for (name,) in stakeholders:
        if name:
            suggestions.append(SearchSuggestion(text=name, entity_type="stakeholder", count=1))

    return suggestions[:10]


def _simple_relevance(query: str, text: str) -> float:
    q_lower = query.lower()
    t_lower = text.lower()
    if not t_lower:
        return 0.0
    count = t_lower.count(q_lower)
    return min(1.0, count / max(len(t_lower.split()), 1) * 10)


# ── Saved Filters ─────────────────────────────────────────────────────────────

async def list_saved_filters(db: AsyncSession, user_id: UUID) -> list[SavedFilter]:
    result = await db.execute(
        select(SavedFilter).where(SavedFilter.user_id == user_id).order_by(SavedFilter.created_at.desc())
    )
    return list(result.scalars().all())


async def create_saved_filter(db: AsyncSession, user_id: UUID, payload: SavedFilterCreate) -> SavedFilter:
    sf = SavedFilter(
        user_id=user_id,
        name=payload.name,
        description=payload.description,
        filter_params=payload.filter_params,
        is_default=payload.is_default,
    )
    db.add(sf)
    await db.commit()
    await db.refresh(sf)
    return sf


async def update_saved_filter(
    db: AsyncSession,
    filter_id: UUID,
    user_id: UUID,
    payload: SavedFilterCreate,
) -> SavedFilter | None:
    sf = await db.get(SavedFilter, filter_id)
    if sf is None or sf.user_id != user_id:
        return None
    sf.name = payload.name
    sf.description = payload.description
    sf.filter_params = payload.filter_params
    sf.is_default = payload.is_default
    await db.commit()
    await db.refresh(sf)
    return sf


async def delete_saved_filter(db: AsyncSession, filter_id: UUID, user_id: UUID) -> bool:
    sf = await db.get(SavedFilter, filter_id)
    if sf is None or sf.user_id != user_id:
        return False
    await db.delete(sf)
    await db.commit()
    return True
