from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, and_, or_
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import httpx

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.core.config import settings
from app.models.user import User

router = APIRouter()


# ─── Schemas ─────────────────────────────────────────────────────
class AlertWebhook(BaseModel):
    alerts: List[dict]


class AlertUpdate(BaseModel):
    status: Optional[str] = None
    note: Optional[str] = None


class PrometheusWebhook(BaseModel):
    version: str = "4"
    groupKey: Optional[str] = None
    status: str = "firing"
    alerts: List[dict] = []


# ─── Proxy helpers ───────────────────────────────────────────────
async def _proxy_get(path: str, params: dict = None):
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{settings.ALERTMANAGER_URL}{path}", params=params)
        return r.json()


async def _proxy_post(path: str, data: dict):
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(f"{settings.ALERTMANAGER_URL}{path}", json=data)
        return r.json()


async def _proxy_patch(path: str, data: dict):
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.patch(f"{settings.ALERTMANAGER_URL}{path}", json=data)
        return r.json()


# ─── Endpoints ───────────────────────────────────────────────────
@router.get("")
async def list_alerts(
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
):
    return await _proxy_get("/api/v1/alerts", {
        "status": status, "severity": severity, "search": search,
        "page": page, "limit": limit
    })


@router.get("/stats")
async def alert_stats(current_user: User = Depends(get_current_user)):
    return await _proxy_get("/api/v1/alerts/stats")


@router.get("/history")
async def alert_history(
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(get_current_user),
):
    return await _proxy_get("/api/v1/alerts/history", {"days": days})


@router.get("/{alert_id}")
async def get_alert(alert_id: str, current_user: User = Depends(get_current_user)):
    return await _proxy_get(f"/api/v1/alerts/{alert_id}")


@router.patch("/{alert_id}")
async def update_alert(
    alert_id: str,
    data: AlertUpdate,
    current_user: User = Depends(get_current_user),
):
    return await _proxy_patch(f"/api/v1/alerts/{alert_id}", {
        **data.model_dump(exclude_none=True),
        "updated_by": current_user.id,
    })


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    note: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    return await _proxy_post(f"/api/v1/alerts/{alert_id}/acknowledge", {
        "acknowledged_by": current_user.id,
        "note": note,
    })


@router.post("/{alert_id}/resolve")
async def resolve_alert(alert_id: str, current_user: User = Depends(get_current_user)):
    return await _proxy_post(f"/api/v1/alerts/{alert_id}/resolve", {"resolved_by": current_user.id})


# ─── Inbound webhooks ────────────────────────────────────────────
@router.post("/ingest/webhook")
async def ingest_webhook(data: AlertWebhook, background_tasks: BackgroundTasks):
    """Generic webhook alert ingestion"""
    background_tasks.add_task(_proxy_post, "/api/v1/ingest/webhook", data.model_dump())
    return {"message": "Alerts received", "count": len(data.alerts)}


@router.post("/ingest/prometheus")
async def ingest_prometheus(data: PrometheusWebhook, background_tasks: BackgroundTasks):
    """Prometheus Alertmanager webhook receiver"""
    background_tasks.add_task(_proxy_post, "/api/v1/ingest/prometheus", data.model_dump())
    return {"message": "Prometheus alerts received", "count": len(data.alerts)}


@router.post("/suppression")
async def create_suppression(
    data: dict,
    current_user: User = Depends(require_role("admin", "operator")),
):
    return await _proxy_post("/api/v1/suppression", {**data, "created_by": current_user.id})


@router.get("/suppression")
async def list_suppressions(current_user: User = Depends(get_current_user)):
    return await _proxy_get("/api/v1/suppression")
