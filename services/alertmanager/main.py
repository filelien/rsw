"""RAXUS AlertManager Service"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, Boolean, DateTime, Enum, JSON, Text, DECIMAL, func, select, update, and_, or_, text
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import uuid, hashlib, json, httpx, redis.asyncio as aioredis, os, logging, uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("raxus.alertmanager")

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+aiomysql://raxus:raxus_pass@mysql:3306/raxus")
REDIS_URL = os.getenv("REDIS_URL", "redis://:raxus_redis@redis:6379/1")
NOTIFIER_URL = os.getenv("NOTIFIER_URL", "http://notifier:8003")
RULES_URL = os.getenv("RULES_URL", "http://rules-engine:8006")

engine = create_async_engine(DATABASE_URL, pool_pre_ping=True, pool_size=10)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
redis_client = None


class Base(DeclarativeBase):
    pass


class Alert(Base):
    __tablename__ = "alerts"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    fingerprint = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    severity = Column(Enum("critical","major","minor","warning","info"), default="info")
    status = Column(Enum("active","pending","resolved","suppressed","acknowledged"), default="pending")
    source = Column(String(100), default="webhook")
    instance = Column(String(255))
    server_id = Column(String(36))
    summary = Column(Text)
    description = Column(Text)
    labels = Column(JSON)
    annotations = Column(JSON)
    value = Column(DECIMAL(20, 6))
    threshold = Column(DECIMAL(20, 6))
    acknowledged_by = Column(String(36))
    acknowledged_at = Column(DateTime)
    resolved_at = Column(DateTime)
    started_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(500), nullable=False)
    description = Column(Text)
    priority = Column(Enum("critical","high","medium","low"), default="medium")
    status = Column(Enum("open","in_progress","resolved","closed","cancelled"), default="open")
    alert_id = Column(String(36))
    assigned_to = Column(String(36))
    created_by = Column(String(36))
    tags = Column(JSON)
    resolved_at = Column(DateTime)
    closed_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class SuppressionWindow(Base):
    __tablename__ = "suppression_windows"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    reason = Column(Text)
    matchers = Column(JSON, nullable=False)
    starts_at = Column(DateTime, nullable=False)
    ends_at = Column(DateTime, nullable=False)
    created_by = Column(String(36))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client
    redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
    yield
    await redis_client.aclose()


app = FastAPI(title="RAXUS AlertManager", version="1.0.0", lifespan=lifespan)


async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def compute_fingerprint(labels: dict) -> str:
    stable = json.dumps(labels, sort_keys=True)
    return hashlib.md5(stable.encode()).hexdigest()


async def publish_alert(alert_data: dict):
    if redis_client:
        await redis_client.publish("raxus:alerts", json.dumps(alert_data))
        await redis_client.publish("raxus:dashboard", json.dumps({"type": "alert_update"}))


async def trigger_rules(alert: Alert):
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(f"{RULES_URL}/api/v1/evaluate", json={
                "alert_id": alert.id, "name": alert.name,
                "severity": alert.severity, "labels": alert.labels or {},
                "instance": alert.instance,
            })
    except Exception as e:
        logger.warning(f"Rules evaluation failed: {e}")


async def send_notification(alert: Alert):
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(f"{NOTIFIER_URL}/api/v1/send", json={
                "alert_id": alert.id, "name": alert.name,
                "severity": alert.severity, "summary": alert.summary,
                "instance": alert.instance,
            })
    except Exception as e:
        logger.warning(f"Notification failed: {e}")


# ─── Schemas ─────────────────────────────────────────────────────
class AlertIn(BaseModel):
    name: str
    severity: str = "info"
    instance: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    labels: Optional[dict] = {}
    annotations: Optional[dict] = {}
    value: Optional[float] = None
    threshold: Optional[float] = None
    source: str = "webhook"


class PrometheusPayload(BaseModel):
    version: str = "4"
    status: str = "firing"
    alerts: List[dict] = []


# ─── Alert CRUD ──────────────────────────────────────────────────
@app.get("/api/v1/alerts")
async def list_alerts(
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
):
    async with SessionLocal() as db:
        q = select(Alert)
        if status:
            q = q.where(Alert.status == status)
        if severity:
            q = q.where(Alert.severity == severity)
        if search:
            q = q.where(or_(Alert.name.ilike(f"%{search}%"), Alert.instance.ilike(f"%{search}%")))
        q = q.order_by(Alert.started_at.desc()).offset((page - 1) * limit).limit(limit)
        result = await db.execute(q)
        alerts = result.scalars().all()
        return [_serialize_alert(a) for a in alerts]


@app.get("/api/v1/alerts/stats")
async def alert_stats():
    async with SessionLocal() as db:
        result = await db.execute(text("""
            SELECT severity, status, COUNT(*) as count
            FROM alerts GROUP BY severity, status
        """))
        rows = result.fetchall()
        stats = {"total": 0, "by_severity": {}, "by_status": {}, "active": 0}
        for r in rows:
            stats["total"] += r.count
            stats["by_severity"][r.severity] = stats["by_severity"].get(r.severity, 0) + r.count
            stats["by_status"][r.status] = stats["by_status"].get(r.status, 0) + r.count
            if r.status == "active":
                stats["active"] += r.count
        return stats


@app.get("/api/v1/alerts/history")
async def alert_history(days: int = Query(7)):
    async with SessionLocal() as db:
        result = await db.execute(text("""
            SELECT DATE(started_at) as date, severity, COUNT(*) as count
            FROM alerts WHERE started_at >= DATE_SUB(NOW(), INTERVAL :days DAY)
            GROUP BY DATE(started_at), severity ORDER BY date ASC
        """), {"days": days})
        rows = result.fetchall()
        return [{"date": str(r.date), "severity": r.severity, "count": r.count} for r in rows]


@app.get("/api/v1/alerts/{alert_id}")
async def get_alert(alert_id: str):
    async with SessionLocal() as db:
        result = await db.execute(select(Alert).where(Alert.id == alert_id))
        alert = result.scalar_one_or_none()
        if not alert:
            raise HTTPException(404, "Alert not found")
        return _serialize_alert(alert)


@app.patch("/api/v1/alerts/{alert_id}")
async def update_alert(alert_id: str, data: dict):
    async with SessionLocal() as db:
        allowed = {k: v for k, v in data.items() if k in ("status", "summary", "description")}
        await db.execute(update(Alert).where(Alert.id == alert_id).values(**allowed))
        await db.commit()
        return {"message": "Alert updated"}


@app.post("/api/v1/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, data: dict, background_tasks: BackgroundTasks):
    async with SessionLocal() as db:
        await db.execute(update(Alert).where(Alert.id == alert_id).values(
            status="acknowledged",
            acknowledged_by=data.get("acknowledged_by"),
            acknowledged_at=datetime.now(timezone.utc),
        ))
        await db.commit()
        background_tasks.add_task(publish_alert, {"type": "acknowledged", "alert_id": alert_id})
        return {"message": "Alert acknowledged"}


@app.post("/api/v1/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str, data: dict, background_tasks: BackgroundTasks):
    async with SessionLocal() as db:
        await db.execute(update(Alert).where(Alert.id == alert_id).values(
            status="resolved", resolved_at=datetime.now(timezone.utc)
        ))
        await db.commit()
        background_tasks.add_task(publish_alert, {"type": "resolved", "alert_id": alert_id})
        return {"message": "Alert resolved"}


# ─── Ingestion ───────────────────────────────────────────────────
@app.post("/api/v1/ingest/webhook")
async def ingest_webhook(payload: dict, background_tasks: BackgroundTasks):
    alerts_data = payload.get("alerts", [])
    created = []
    async with SessionLocal() as db:
        for raw in alerts_data:
            alert = await _create_or_update_alert(db, raw, "webhook")
            created.append(alert.id)
            background_tasks.add_task(publish_alert, _serialize_alert(alert))
            background_tasks.add_task(trigger_rules, alert)
            background_tasks.add_task(send_notification, alert)
        await db.commit()
    return {"processed": len(created), "ids": created}


@app.post("/api/v1/ingest/prometheus")
async def ingest_prometheus(payload: PrometheusPayload, background_tasks: BackgroundTasks):
    created = []
    async with SessionLocal() as db:
        for raw in payload.alerts:
            labels = raw.get("labels", {})
            alert_data = {
                "name": labels.get("alertname", "UnknownAlert"),
                "severity": labels.get("severity", "info"),
                "instance": labels.get("instance", labels.get("job")),
                "summary": raw.get("annotations", {}).get("summary"),
                "description": raw.get("annotations", {}).get("description"),
                "labels": labels,
                "annotations": raw.get("annotations", {}),
                "source": "prometheus",
            }
            status = "active" if raw.get("status") == "firing" else "resolved"
            alert_data["force_status"] = status
            alert = await _create_or_update_alert(db, alert_data, "prometheus")
            created.append(alert.id)
            background_tasks.add_task(publish_alert, _serialize_alert(alert))
            if status == "active":
                background_tasks.add_task(trigger_rules, alert)
                background_tasks.add_task(send_notification, alert)
        await db.commit()
    return {"processed": len(created)}


async def _create_or_update_alert(db: AsyncSession, raw: dict, source: str) -> Alert:
    labels = raw.get("labels", {})
    fingerprint = compute_fingerprint({
        "alertname": raw.get("name", labels.get("alertname", "")),
        "instance": raw.get("instance", labels.get("instance", "")),
    })
    result = await db.execute(
        select(Alert).where(Alert.fingerprint == fingerprint, Alert.status != "resolved")
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.updated_at = datetime.now(timezone.utc)
        if raw.get("force_status"):
            existing.status = raw["force_status"]
        return existing

    alert = Alert(
        fingerprint=fingerprint,
        name=raw.get("name", labels.get("alertname", "Unknown")),
        severity=raw.get("severity", "info"),
        status=raw.get("force_status", "active"),
        source=source,
        instance=raw.get("instance"),
        summary=raw.get("summary"),
        description=raw.get("description"),
        labels=labels,
        annotations=raw.get("annotations", {}),
        value=raw.get("value"),
        threshold=raw.get("threshold"),
    )
    db.add(alert)
    await db.flush()
    return alert


# ─── Suppression ─────────────────────────────────────────────────
@app.post("/api/v1/suppression")
async def create_suppression(data: dict):
    async with SessionLocal() as db:
        sw = SuppressionWindow(
            name=data["name"],
            reason=data.get("reason"),
            matchers=data["matchers"],
            starts_at=datetime.fromisoformat(data["starts_at"]),
            ends_at=datetime.fromisoformat(data["ends_at"]),
            created_by=data.get("created_by"),
        )
        db.add(sw)
        await db.commit()
        return {"id": sw.id, "message": "Suppression window created"}


@app.get("/api/v1/suppression")
async def list_suppressions():
    async with SessionLocal() as db:
        result = await db.execute(select(SuppressionWindow).where(SuppressionWindow.is_active == True))
        items = result.scalars().all()
        return [{"id": s.id, "name": s.name, "reason": s.reason,
                 "starts_at": str(s.starts_at), "ends_at": str(s.ends_at)} for s in items]


# ─── Tickets ─────────────────────────────────────────────────────
@app.get("/api/v1/tickets")
async def list_tickets(status: Optional[str] = Query(None)):
    async with SessionLocal() as db:
        q = select(Ticket)
        if status:
            q = q.where(Ticket.status == status)
        q = q.order_by(Ticket.created_at.desc())
        result = await db.execute(q)
        tickets = result.scalars().all()
        return [_serialize_ticket(t) for t in tickets]


@app.post("/api/v1/tickets")
async def create_ticket(data: dict):
    async with SessionLocal() as db:
        ticket = Ticket(
            title=data["title"],
            description=data.get("description"),
            priority=data.get("priority", "medium"),
            alert_id=data.get("alert_id"),
            assigned_to=data.get("assigned_to"),
            created_by=data.get("created_by"),
            tags=data.get("tags"),
        )
        db.add(ticket)
        await db.commit()
        return {"id": ticket.id, "message": "Ticket created"}


@app.get("/api/v1/tickets/{ticket_id}")
async def get_ticket(ticket_id: str):
    async with SessionLocal() as db:
        result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
        ticket = result.scalar_one_or_none()
        if not ticket:
            raise HTTPException(404, "Ticket not found")
        return _serialize_ticket(ticket)


@app.patch("/api/v1/tickets/{ticket_id}")
async def update_ticket(ticket_id: str, data: dict):
    async with SessionLocal() as db:
        allowed = {k: v for k, v in data.items() if k in ("status","priority","assigned_to","title","description")}
        if allowed.get("status") == "resolved":
            allowed["resolved_at"] = datetime.now(timezone.utc)
        if allowed.get("status") == "closed":
            allowed["closed_at"] = datetime.now(timezone.utc)
        await db.execute(update(Ticket).where(Ticket.id == ticket_id).values(**allowed))
        await db.commit()
        return {"message": "Ticket updated"}


def _serialize_alert(a: Alert) -> dict:
    return {
        "id": a.id, "fingerprint": a.fingerprint, "name": a.name,
        "severity": a.severity, "status": a.status, "source": a.source,
        "instance": a.instance, "summary": a.summary, "description": a.description,
        "labels": a.labels, "annotations": a.annotations,
        "value": float(a.value) if a.value else None,
        "threshold": float(a.threshold) if a.threshold else None,
        "acknowledged_by": a.acknowledged_by,
        "acknowledged_at": str(a.acknowledged_at) if a.acknowledged_at else None,
        "resolved_at": str(a.resolved_at) if a.resolved_at else None,
        "started_at": str(a.started_at) if a.started_at else None,
        "updated_at": str(a.updated_at) if a.updated_at else None,
    }


def _serialize_ticket(t: Ticket) -> dict:
    return {
        "id": t.id, "title": t.title, "description": t.description,
        "priority": t.priority, "status": t.status, "alert_id": t.alert_id,
        "assigned_to": t.assigned_to, "created_by": t.created_by,
        "tags": t.tags, "created_at": str(t.created_at),
    }


@app.get("/health")
async def health():
    return {"status": "ok", "service": "raxus-alertmanager"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
