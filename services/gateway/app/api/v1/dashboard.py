from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
import httpx
from app.core.config import settings

router = APIRouter()


async def _get(url: str, path: str):
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{url}{path}")
            return r.json()
    except Exception:
        return {}


@router.get("/summary")
async def dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns all data needed for the main dashboard in a single call"""
    # Alert stats
    alert_stats = await _get(settings.ALERTMANAGER_URL, "/api/v1/alerts/stats")

    # Inventory stats
    inv_stats = await _get(settings.INVENTORY_URL, "/api/v1/stats")

    # SLO stats
    slo_stats = await _get(settings.SLO_URL, "/api/v1/stats")

    # Task stats
    task_stats = await _get(settings.TASKMANAGER_URL, "/api/v1/stats")

    # Recent alerts
    recent_alerts = await _get(settings.ALERTMANAGER_URL, "/api/v1/alerts?limit=10&status=active")

    return {
        "alerts": alert_stats,
        "inventory": inv_stats,
        "slo": slo_stats,
        "tasks": task_stats,
        "recent_alerts": recent_alerts,
    }


@router.get("/timeline")
async def alert_timeline(
    days: int = 7,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(text("""
        SELECT
            DATE(started_at) as date,
            severity,
            COUNT(*) as count
        FROM alerts
        WHERE started_at >= DATE_SUB(NOW(), INTERVAL :days DAY)
        GROUP BY DATE(started_at), severity
        ORDER BY date ASC
    """), {"days": days})
    rows = result.fetchall()
    return [{"date": str(r.date), "severity": r.severity, "count": r.count} for r in rows]


@router.get("/top-issues")
async def top_issues(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(text("""
        SELECT name, COUNT(*) as count, MAX(started_at) as last_seen
        FROM alerts
        WHERE started_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        GROUP BY name
        ORDER BY count DESC
        LIMIT :limit
    """), {"limit": limit})
    rows = result.fetchall()
    return [{"name": r.name, "count": r.count, "last_seen": str(r.last_seen)} for r in rows]
