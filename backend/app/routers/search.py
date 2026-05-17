from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db_session
from app.models.user import User
from app.schemas.search import (
    FilterParams,
    SavedFilterCreate,
    SavedFilterResponse,
    SearchResult,
    SearchSuggestion,
)
from app.services import search_service as svc

router = APIRouter(tags=["search"])


# ── Global & Entity Search ────────────────────────────────────────────────────

@router.get("/api/search", response_model=SearchResult)
async def global_search(
    q: str = Query(..., min_length=1),
    type: str | None = Query(default=None, description="emails|contracts|stakeholders|all"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> SearchResult:
    filters = FilterParams(page=page, page_size=page_size)
    if type and type != "all":
        if type == "emails":
            items = await svc.search_emails(db, q, filters)
            return SearchResult(query=q, total=len(items), items=items, emails=items)
        if type == "contracts":
            items = await svc.search_contracts(db, q, filters)
            return SearchResult(query=q, total=len(items), items=items, contracts=items)
        if type == "stakeholders":
            items = await svc.search_stakeholders(db, q, filters)
            return SearchResult(query=q, total=len(items), items=items, stakeholders=items)
    return await svc.search_all(db, q, filters)


@router.get("/api/search/emails", response_model=SearchResult)
async def search_emails(
    q: str = Query(..., min_length=1),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    category: str | None = Query(default=None),
    urgency: str | None = Query(default=None),
    sentiment: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> SearchResult:
    filters = FilterParams(
        category=category,
        urgency=urgency,
        sentiment=sentiment,
        page=page,
        page_size=page_size,
    )
    items = await svc.search_emails(db, q, filters)
    return SearchResult(query=q, total=len(items), items=items, emails=items)


@router.get("/api/search/contracts", response_model=SearchResult)
async def search_contracts(
    q: str = Query(..., min_length=1),
    contract_type: str | None = Query(default=None),
    stage: str | None = Query(default=None),
    sla_status: str | None = Query(default=None),
    counterparty: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> SearchResult:
    filters = FilterParams(
        contract_type=contract_type,
        stage=stage,
        sla_status=sla_status,
        counterparty=counterparty,
        page=page,
        page_size=page_size,
    )
    items = await svc.search_contracts(db, q, filters)
    return SearchResult(query=q, total=len(items), items=items, contracts=items)


@router.get("/api/search/stakeholders", response_model=SearchResult)
async def search_stakeholders(
    q: str = Query(..., min_length=1),
    department: str | None = Query(default=None),
    is_internal: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> SearchResult:
    filters = FilterParams(
        department=department,
        is_internal=is_internal,
        page=page,
        page_size=page_size,
    )
    items = await svc.search_stakeholders(db, q, filters)
    return SearchResult(query=q, total=len(items), items=items, stakeholders=items)


class SemanticSearchRequest(BaseModel):
    query: str


@router.post("/api/search/semantic", response_model=SearchResult)
async def semantic_search(
    body: SemanticSearchRequest,
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> SearchResult:
    return await svc.semantic_search(db, body.query)


@router.get("/api/search/suggestions", response_model=list[SearchSuggestion])
async def search_suggestions(
    q: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> list[SearchSuggestion]:
    return await svc.get_search_suggestions(db, q)


# ── Saved Filters ─────────────────────────────────────────────────────────────

@router.get("/api/filters/saved", response_model=list[SavedFilterResponse])
async def list_saved_filters(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> list:
    return await svc.list_saved_filters(db, current_user.id)


@router.post("/api/filters/saved", response_model=SavedFilterResponse, status_code=status.HTTP_201_CREATED)
async def create_saved_filter(
    payload: SavedFilterCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    return await svc.create_saved_filter(db, current_user.id, payload)


@router.put("/api/filters/saved/{filter_id}", response_model=SavedFilterResponse)
async def update_saved_filter(
    filter_id: UUID,
    payload: SavedFilterCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    result = await svc.update_saved_filter(db, filter_id, current_user.id, payload)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved filter not found")
    return result


@router.delete("/api/filters/saved/{filter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_filter(
    filter_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    deleted = await svc.delete_saved_filter(db, filter_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved filter not found")
