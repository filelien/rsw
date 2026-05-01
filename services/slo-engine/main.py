"""RAXUS SLO Engine Service"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, Boolean, DateTime, Enum, JSON, Text, Integer, DECIMAL, BigInteger, func, select, update, text
from datetime import datetime, timezone, timedelta
import uuid, os, logging, uvicorn, httpx, asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("raxus.slo")

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+aiomysql://raxus:raxus_pass@mysql:3306/raxus")
VICTORIA_URL = os.getenv("VICTORIA_URL", "http://victoriametrics:8428")

engine = create_async_engine(DATABASE_URL, pool_pre_ping=True, pool_size=5)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class SLOTarget(Base):
    __tablename__ = "slo_targets"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    service_name = Column(String(255), nullable=False)
    sli_type = Column(Enum("availability","latency","error_rate","throughput"), nullable=False)
    target_percent = Column(DECIMAL(8,4), nullable=False)
    window_days = Column(Integer, default=30)
    metric_query = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class SLOMeasurement(Base):
    __tablename__ = "slo_measurements"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    slo_id = Column(String(36), nullable=False)
    good_events = Column(BigInteger, default=0)
    total_events = Column(BigInteger, default=0)
    compliance = Column(DECIMAL(8,4))
    error_budget_remaining = Column(DECIMAL(8,4))
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class Probe(Base):
    __tablename__ = "probes"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    type = Column(Enum("http","tcp","icmp","dns"), default="http")
    target = Column(String(500), nullable=False)
    interval_sec = Column(Integer, default=60)
    timeout_sec = Column(Integer, default=10)
    expected_status = Column(Integer)
    headers = Column(JSON)
    slo_id = Column(String(36))
    is_active = Column(Boolean, default=True)
    last_check = Column(DateTime)
    last_status = Column(Enum("up","down","degraded","unknown"), default="unknown")
    created_at = Column(DateTime, server_default=func.now())


class ProbeResult(Base):
    __tablename__ = "probe_results"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    probe_id = Column(String(36), nullable=False)
    status = Column(Enum("up","down","degraded"), nullable=False)
    response_ms = Column(Integer)
    status_code = Column(Integer)
    error_msg = Column(Text)
    checked_at = Column(DateTime, server_default=func.now())


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(probe_scheduler())
    yield


app = FastAPI(title="RAXUS SLO Engine", version="1.0.0", lifespan=lifespan)


async def run_http_probe(probe: Probe) -> dict:
    start = datetime.now(timezone.utc)
    try:
        headers = probe.headers or {}
        async with httpx.AsyncClient(timeout=probe.timeout_sec) as client:
            r = await client.get(probe.target, headers=headers)
        response_ms = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)
        expected = probe.expected_status or 200
        status = "up" if r.status_code == expected else "degraded"
        return {"status": status, "response_ms": response_ms, "status_code": r.status_code}
    except Exception as e:
        return {"status": "down", "response_ms": None, "status_code": None, "error_msg": str(e)}


async def probe_scheduler():
    while True:
        try:
            async with SessionLocal() as db:
                result = await db.execute(select(Probe).where(Probe.is_active == True))
                probes = result.scalars().all()
                for probe in probes:
                    if probe.last_check is None or \
                       (datetime.now(timezone.utc) - probe.last_check.replace(tzinfo=timezone.utc)).total_seconds() >= probe.interval_sec:
                        if probe.type == "http":
                            result_data = await run_http_probe(probe)
                        else:
                            result_data = {"status": "up", "response_ms": 0}

                        probe_result = ProbeResult(probe_id=probe.id, **result_data)
                        db.add(probe_result)
                        await db.execute(update(Probe).where(Probe.id == probe.id).values(
                            last_check=datetime.now(timezone.utc),
                            last_status=result_data["status"]
                        ))
                await db.commit()
        except Exception as e:
            logger.error(f"Probe scheduler error: {e}")
        await asyncio.sleep(30)


@app.get("/api/v1/slo")
async def list_slos():
    async with SessionLocal() as db:
        result = await db.execute(select(SLOTarget).where(SLOTarget.is_active == True))
        slos = result.scalars().all()
        items = []
        for slo in slos:
            latest = await db.execute(
                select(SLOMeasurement).where(SLOMeasurement.slo_id == slo.id)
                .order_by(SLOMeasurement.created_at.desc()).limit(1)
            )
            m = latest.scalar_one_or_none()
            items.append({**_slo(slo), "latest_measurement": _meas(m) if m else None})
        return items


@app.post("/api/v1/slo")
async def create_slo(data: dict):
    async with SessionLocal() as db:
        s = SLOTarget(name=data["name"], description=data.get("description"),
                      service_name=data["service_name"], sli_type=data["sli_type"],
                      target_percent=data["target_percent"], window_days=data.get("window_days",30),
                      metric_query=data.get("metric_query"))
        db.add(s)
        await db.commit()
        return {"id": s.id, "message": "SLO created"}


@app.get("/api/v1/slo/{slo_id}")
async def get_slo(slo_id: str):
    async with SessionLocal() as db:
        result = await db.execute(select(SLOTarget).where(SLOTarget.id == slo_id))
        slo = result.scalar_one_or_none()
        if not slo:
            raise HTTPException(404, "SLO not found")
        measurements = await db.execute(
            select(SLOMeasurement).where(SLOMeasurement.slo_id == slo_id)
            .order_by(SLOMeasurement.created_at.desc()).limit(30)
        )
        return {**_slo(slo), "measurements": [_meas(m) for m in measurements.scalars().all()]}


@app.patch("/api/v1/slo/{slo_id}")
async def update_slo(slo_id: str, data: dict):
    async with SessionLocal() as db:
        allowed = {k: v for k, v in data.items() if k in ("name","description","target_percent","window_days","metric_query","is_active")}
        await db.execute(update(SLOTarget).where(SLOTarget.id == slo_id).values(**allowed))
        await db.commit()
        return {"message": "SLO updated"}


@app.delete("/api/v1/slo/{slo_id}")
async def delete_slo(slo_id: str):
    async with SessionLocal() as db:
        await db.execute(update(SLOTarget).where(SLOTarget.id == slo_id).values(is_active=False))
        await db.commit()
        return {"message": "SLO deactivated"}


@app.get("/api/v1/probes")
async def list_probes():
    async with SessionLocal() as db:
        result = await db.execute(select(Probe).where(Probe.is_active == True))
        return [_probe(p) for p in result.scalars().all()]


@app.post("/api/v1/probes")
async def create_probe(data: dict):
    async with SessionLocal() as db:
        p = Probe(name=data["name"], type=data.get("type","http"), target=data["target"],
                  interval_sec=data.get("interval_sec",60), timeout_sec=data.get("timeout_sec",10),
                  expected_status=data.get("expected_status"), headers=data.get("headers"),
                  slo_id=data.get("slo_id"))
        db.add(p)
        await db.commit()
        return {"id": p.id, "message": "Probe created"}


@app.get("/api/v1/probes/{probe_id}/results")
async def probe_results(probe_id: str, limit: int = 100):
    async with SessionLocal() as db:
        result = await db.execute(
            select(ProbeResult).where(ProbeResult.probe_id == probe_id)
            .order_by(ProbeResult.checked_at.desc()).limit(limit)
        )
        return [{"id": r.id, "status": r.status, "response_ms": r.response_ms,
                 "status_code": r.status_code, "error_msg": r.error_msg,
                 "checked_at": str(r.checked_at)} for r in result.scalars().all()]


@app.get("/api/v1/stats")
async def stats():
    async with SessionLocal() as db:
        total = (await db.execute(text("SELECT COUNT(*) FROM slo_targets WHERE is_active=1"))).scalar()
        probes_up = (await db.execute(text("SELECT COUNT(*) FROM probes WHERE last_status='up' AND is_active=1"))).scalar()
        probes_down = (await db.execute(text("SELECT COUNT(*) FROM probes WHERE last_status='down' AND is_active=1"))).scalar()
        probes_total = (await db.execute(text("SELECT COUNT(*) FROM probes WHERE is_active=1"))).scalar()
        return {"slo_targets": total, "probes_total": probes_total, "probes_up": probes_up, "probes_down": probes_down}


@app.get("/health")
async def health():
    return {"status": "ok", "service": "raxus-slo-engine"}


def _slo(s): return {"id": s.id, "name": s.name, "description": s.description, "service_name": s.service_name, "sli_type": s.sli_type, "target_percent": float(s.target_percent), "window_days": s.window_days, "is_active": s.is_active, "created_at": str(s.created_at)}
def _meas(m): return {"id": m.id, "good_events": m.good_events, "total_events": m.total_events, "compliance": float(m.compliance) if m.compliance else None, "error_budget_remaining": float(m.error_budget_remaining) if m.error_budget_remaining else None, "period_start": str(m.period_start), "period_end": str(m.period_end), "created_at": str(m.created_at)}
def _probe(p): return {"id": p.id, "name": p.name, "type": p.type, "target": p.target, "interval_sec": p.interval_sec, "timeout_sec": p.timeout_sec, "last_status": p.last_status, "last_check": str(p.last_check) if p.last_check else None, "slo_id": p.slo_id, "is_active": p.is_active}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8005, reload=True)
