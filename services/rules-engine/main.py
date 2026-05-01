"""RAXUS Rules Engine Service"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, Boolean, DateTime, JSON, Text, Integer, func, select, update
from datetime import datetime, timezone
import uuid, os, logging, uvicorn, httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("raxus.rules")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://raxus:raxus_pass@localhost:5432/raxus")
NOTIFIER_URL = os.getenv("NOTIFIER_URL", "http://notifier:8003")
TASKMANAGER_URL = os.getenv("TASKMANAGER_URL", "http://taskmanager:8004")

engine = create_async_engine(DATABASE_URL, pool_pre_ping=True, pool_size=5)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class AlertRule(Base):
    __tablename__ = "alert_rules"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    conditions = Column(JSON, nullable=False)
    actions = Column(JSON, nullable=False)
    priority = Column(Integer, default=100)
    is_active = Column(Boolean, default=True)
    last_triggered = Column(DateTime)
    trigger_count = Column(Integer, default=0)
    created_by = Column(String(36))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="RAXUS Rules Engine", version="1.0.0", lifespan=lifespan)


def matches_condition(condition: dict, alert_data: dict) -> bool:
    """Evaluate a single condition against alert data"""
    field = condition.get("field", "")
    operator = condition.get("operator", "eq")
    value = condition.get("value")
    alert_value = alert_data.get(field)

    if alert_value is None:
        return False

    if operator == "eq":
        return str(alert_value).lower() == str(value).lower()
    elif operator == "neq":
        return str(alert_value).lower() != str(value).lower()
    elif operator == "contains":
        return str(value).lower() in str(alert_value).lower()
    elif operator == "in":
        return str(alert_value).lower() in [str(v).lower() for v in (value if isinstance(value, list) else [value])]
    elif operator == "gt":
        try:
            return float(alert_value) > float(value)
        except (ValueError, TypeError):
            return False
    elif operator == "lt":
        try:
            return float(alert_value) < float(value)
        except (ValueError, TypeError):
            return False
    return False


def evaluate_rule(rule: AlertRule, alert_data: dict) -> bool:
    """Evaluate all conditions of a rule (AND logic)"""
    conditions = rule.conditions
    if not conditions:
        return False
    match_type = conditions.get("match", "all")
    rules_list = conditions.get("rules", [])
    if not rules_list:
        return False
    results = [matches_condition(c, alert_data) for c in rules_list]
    if match_type == "all":
        return all(results)
    elif match_type == "any":
        return any(results)
    return False


async def execute_action(action: dict, alert_data: dict):
    action_type = action.get("type")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            if action_type == "notify":
                notifier_id = action.get("notifier_id")
                if notifier_id:
                    await client.post(f"{NOTIFIER_URL}/api/v1/notifiers/{notifier_id}/test")
                else:
                    await client.post(f"{NOTIFIER_URL}/api/v1/send", json=alert_data)
            elif action_type == "execute_task":
                task_id = action.get("task_id")
                if task_id:
                    await client.post(f"{TASKMANAGER_URL}/api/v1/tasks/{task_id}/execute", json={
                        "trigger_type": "alert", "parameters": {"alert": alert_data}
                    })
            elif action_type == "webhook":
                url = action.get("url")
                if url:
                    await client.post(url, json={"alert": alert_data, "source": "raxus-rules"})
    except Exception as e:
        logger.warning(f"Action execution failed [{action_type}]: {e}")


@app.post("/api/v1/evaluate")
async def evaluate_rules(alert_data: dict):
    """Called by AlertManager when a new alert arrives"""
    async with SessionLocal() as db:
        result = await db.execute(
            select(AlertRule).where(AlertRule.is_active == True).order_by(AlertRule.priority)
        )
        rules = result.scalars().all()
        triggered = []
        for rule in rules:
            if evaluate_rule(rule, alert_data):
                for action in (rule.actions.get("list", []) if isinstance(rule.actions, dict) else []):
                    await execute_action(action, alert_data)
                await db.execute(update(AlertRule).where(AlertRule.id == rule.id).values(
                    last_triggered=datetime.now(timezone.utc),
                    trigger_count=AlertRule.trigger_count + 1,
                ))
                triggered.append(rule.name)
        await db.commit()
        return {"triggered_rules": triggered, "evaluated": len(rules)}


@app.get("/api/v1/rules")
async def list_rules():
    async with SessionLocal() as db:
        result = await db.execute(select(AlertRule).order_by(AlertRule.priority))
        return [_rule(r) for r in result.scalars().all()]


@app.post("/api/v1/rules")
async def create_rule(data: dict):
    async with SessionLocal() as db:
        r = AlertRule(
            name=data["name"], description=data.get("description"),
            conditions=data["conditions"], actions=data["actions"],
            priority=data.get("priority", 100), created_by=data.get("created_by"),
        )
        db.add(r)
        await db.commit()
        return {"id": r.id, "message": "Rule created"}


@app.get("/api/v1/rules/{rule_id}")
async def get_rule(rule_id: str):
    async with SessionLocal() as db:
        result = await db.execute(select(AlertRule).where(AlertRule.id == rule_id))
        r = result.scalar_one_or_none()
        if not r:
            raise HTTPException(404, "Rule not found")
        return _rule(r)


@app.patch("/api/v1/rules/{rule_id}")
async def update_rule(rule_id: str, data: dict):
    async with SessionLocal() as db:
        allowed = {k: v for k, v in data.items() if k in ("name","description","conditions","actions","priority","is_active")}
        await db.execute(update(AlertRule).where(AlertRule.id == rule_id).values(**allowed))
        await db.commit()
        return {"message": "Rule updated"}


@app.delete("/api/v1/rules/{rule_id}")
async def delete_rule(rule_id: str):
    async with SessionLocal() as db:
        await db.execute(update(AlertRule).where(AlertRule.id == rule_id).values(is_active=False))
        await db.commit()
        return {"message": "Rule deactivated"}


@app.post("/api/v1/rules/{rule_id}/test")
async def test_rule(rule_id: str, alert_data: dict):
    async with SessionLocal() as db:
        result = await db.execute(select(AlertRule).where(AlertRule.id == rule_id))
        rule = result.scalar_one_or_none()
        if not rule:
            raise HTTPException(404, "Rule not found")
        matched = evaluate_rule(rule, alert_data)
        return {"matched": matched, "rule": rule.name, "conditions": rule.conditions}


@app.get("/health")
async def health():
    return {"status": "ok", "service": "raxus-rules-engine"}


def _rule(r): return {"id": r.id, "name": r.name, "description": r.description, "conditions": r.conditions, "actions": r.actions, "priority": r.priority, "is_active": r.is_active, "trigger_count": r.trigger_count, "last_triggered": str(r.last_triggered) if r.last_triggered else None, "created_at": str(r.created_at)}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8006, reload=True)
