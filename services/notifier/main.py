"""RAXUS Notifier Service"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, Boolean, DateTime, Enum, JSON, Text, Integer, func, select, update
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid, os, logging, uvicorn, httpx, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("raxus.notifier")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://raxus:raxus_pass@localhost:5432/raxus")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK_URL", "")

engine = create_async_engine(DATABASE_URL, pool_pre_ping=True, pool_size=5)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Notifier(Base):
    __tablename__ = "notifiers"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), unique=True, nullable=False)
    type = Column(Enum("email","webhook","slack","teams","pagerduty","sms"), nullable=False)
    config = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    alert_id = Column(String(36))
    notifier_id = Column(String(36), nullable=False)
    status = Column(Enum("pending","sent","failed","retrying"), default="pending")
    attempts = Column(Integer, default=0)
    error_msg = Column(Text)
    sent_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="RAXUS Notifier", version="1.0.0", lifespan=lifespan)


SEVERITY_COLORS = {
    "critical": "#E24B4A", "major": "#E8742A", "minor": "#E8C53A",
    "warning": "#378ADD", "info": "#639922",
}

SEVERITY_EMOJI = {
    "critical": "🔴", "major": "🟠", "minor": "🟡", "warning": "🔵", "info": "🟢",
}


def build_alert_message(alert_data: dict, fmt: str = "text") -> str:
    sev = alert_data.get("severity", "info")
    name = alert_data.get("name", "Unknown Alert")
    instance = alert_data.get("instance", "N/A")
    summary = alert_data.get("summary", "")
    emoji = SEVERITY_EMOJI.get(sev, "⚪")

    if fmt == "html":
        color = SEVERITY_COLORS.get(sev, "#888")
        return f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto">
          <div style="background:{color};padding:16px;border-radius:8px 8px 0 0">
            <h2 style="color:white;margin:0">{emoji} {name}</h2>
            <p style="color:rgba(255,255,255,0.9);margin:4px 0 0">Severity: {sev.upper()}</p>
          </div>
          <div style="border:1px solid #ddd;padding:16px;border-radius:0 0 8px 8px">
            <p><strong>Instance:</strong> {instance}</p>
            <p><strong>Summary:</strong> {summary}</p>
            <p style="color:#888;font-size:12px">RAXUS Monitoring Platform</p>
          </div>
        </div>
        """
    return f"{emoji} [{sev.upper()}] {name}\nInstance: {instance}\nSummary: {summary}"


async def send_email_notification(notifier: Notifier, alert_data: dict) -> bool:
    cfg = notifier.config
    to_emails = cfg.get("to", [])
    if not to_emails or not SMTP_USER:
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[RAXUS] {alert_data.get('severity','').upper()} — {alert_data.get('name','Alert')}"
        msg["From"] = SMTP_USER
        msg["To"] = ", ".join(to_emails)
        msg.attach(MIMEText(build_alert_message(alert_data, "text"), "plain"))
        msg.attach(MIMEText(build_alert_message(alert_data, "html"), "html"))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, to_emails, msg.as_string())
        return True
    except Exception as e:
        logger.error(f"Email failed: {e}")
        return False


async def send_webhook_notification(notifier: Notifier, alert_data: dict) -> bool:
    cfg = notifier.config
    url = cfg.get("url")
    if not url:
        return False
    try:
        headers = cfg.get("headers", {"Content-Type": "application/json"})
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(url, json={"alert": alert_data, "source": "raxus"}, headers=headers)
            return r.status_code < 400
    except Exception as e:
        logger.error(f"Webhook failed: {e}")
        return False


async def send_slack_notification(notifier: Notifier, alert_data: dict) -> bool:
    cfg = notifier.config
    webhook_url = cfg.get("webhook_url") or SLACK_WEBHOOK
    if not webhook_url:
        return False
    sev = alert_data.get("severity", "info")
    color = SEVERITY_COLORS.get(sev, "#888")
    payload = {
        "attachments": [{
            "color": color,
            "title": f"{SEVERITY_EMOJI.get(sev,'')} {alert_data.get('name','Alert')}",
            "fields": [
                {"title": "Severity", "value": sev.upper(), "short": True},
                {"title": "Instance", "value": alert_data.get("instance","N/A"), "short": True},
                {"title": "Summary", "value": alert_data.get("summary",""), "short": False},
            ],
            "footer": "RAXUS Platform",
            "ts": int(datetime.now().timestamp()),
        }]
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(webhook_url, json=payload)
            return r.status_code == 200
    except Exception as e:
        logger.error(f"Slack failed: {e}")
        return False


@app.post("/api/v1/send")
async def send_notification(alert_data: dict):
    """Called by AlertManager to trigger notifications"""
    async with SessionLocal() as db:
        result = await db.execute(select(Notifier).where(Notifier.is_active == True))
        notifiers = result.scalars().all()
        results = []
        for notifier in notifiers:
            success = False
            if notifier.type == "email":
                success = await send_email_notification(notifier, alert_data)
            elif notifier.type == "webhook":
                success = await send_webhook_notification(notifier, alert_data)
            elif notifier.type == "slack":
                success = await send_slack_notification(notifier, alert_data)

            notif = Notification(
                alert_id=alert_data.get("alert_id"),
                notifier_id=notifier.id,
                status="sent" if success else "failed",
                attempts=1,
                sent_at=datetime.utcnow() if success else None,
            )
            db.add(notif)
            results.append({"notifier": notifier.name, "success": success})
        await db.commit()
        return {"results": results}


@app.get("/api/v1/notifiers")
async def list_notifiers():
    async with SessionLocal() as db:
        result = await db.execute(select(Notifier).where(Notifier.is_active == True))
        return [_nf(n) for n in result.scalars().all()]


@app.post("/api/v1/notifiers")
async def create_notifier(data: dict):
    async with SessionLocal() as db:
        n = Notifier(name=data["name"], type=data["type"], config=data["config"])
        db.add(n)
        await db.commit()
        return {"id": n.id, "message": "Notifier created"}


@app.patch("/api/v1/notifiers/{notifier_id}")
async def update_notifier(notifier_id: str, data: dict):
    async with SessionLocal() as db:
        allowed = {k: v for k, v in data.items() if k in ("name","config","is_active")}
        await db.execute(update(Notifier).where(Notifier.id == notifier_id).values(**allowed))
        await db.commit()
        return {"message": "Notifier updated"}


@app.delete("/api/v1/notifiers/{notifier_id}")
async def delete_notifier(notifier_id: str):
    async with SessionLocal() as db:
        await db.execute(update(Notifier).where(Notifier.id == notifier_id).values(is_active=False))
        await db.commit()
        return {"message": "Notifier deactivated"}


@app.post("/api/v1/notifiers/{notifier_id}/test")
async def test_notifier(notifier_id: str, data: dict = {}):
    test_alert = {"name": "Test Alert", "severity": "info", "instance": "test-server",
                  "summary": "This is a test notification from RAXUS"}
    async with SessionLocal() as db:
        result = await db.execute(select(Notifier).where(Notifier.id == notifier_id))
        notifier = result.scalar_one_or_none()
        if not notifier:
            raise HTTPException(404, "Notifier not found")
        success = False
        if notifier.type == "email":
            success = await send_email_notification(notifier, test_alert)
        elif notifier.type == "webhook":
            success = await send_webhook_notification(notifier, test_alert)
        elif notifier.type == "slack":
            success = await send_slack_notification(notifier, test_alert)
        return {"success": success, "message": "Test sent" if success else "Test failed"}


@app.get("/api/v1/history")
async def notification_history():
    async with SessionLocal() as db:
        result = await db.execute(select(Notification).order_by(Notification.created_at.desc()).limit(100))
        items = result.scalars().all()
        return [{"id": n.id, "alert_id": n.alert_id, "notifier_id": n.notifier_id,
                 "status": n.status, "attempts": n.attempts, "sent_at": str(n.sent_at) if n.sent_at else None,
                 "created_at": str(n.created_at)} for n in items]


@app.get("/health")
async def health():
    return {"status": "ok", "service": "raxus-notifier"}


def _nf(n): return {"id": n.id, "name": n.name, "type": n.type, "config": n.config, "is_active": n.is_active, "created_at": str(n.created_at)}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True)
