"""RAXUS Inventory Service"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, Boolean, DateTime, Enum, JSON, Text, Integer, DECIMAL, func, select, update, text
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid, os, logging, uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("raxus.inventory")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://raxus:raxus_pass@localhost:5432/raxus")
engine = create_async_engine(DATABASE_URL, pool_pre_ping=True, pool_size=10)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Datacenter(Base):
    __tablename__ = "datacenters"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False)
    location = Column(String(255))
    description = Column(Text)
    tags = Column(JSON)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Environment(Base):
    __tablename__ = "environments"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    datacenter_id = Column(String(36), nullable=False)
    name = Column(String(100), nullable=False)
    type = Column(Enum("production","staging","development","testing"), default="development")
    description = Column(Text)
    tags = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Server(Base):
    __tablename__ = "servers"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    environment_id = Column(String(36), nullable=False)
    hostname = Column(String(255), nullable=False)
    ip_address = Column(String(45))
    os_type = Column(String(100))
    os_version = Column(String(100))
    cpu_cores = Column(Integer)
    ram_gb = Column(DECIMAL(10, 2))
    disk_gb = Column(DECIMAL(10, 2))
    status = Column(Enum("active","inactive","maintenance","decommissioned"), default="active")
    maintenance_mode = Column(Boolean, default=False)
    tags = Column(JSON)
    metadata = Column(JSON)
    last_seen = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Component(Base):
    __tablename__ = "components"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    server_id = Column(String(36), nullable=False)
    name = Column(String(255), nullable=False)
    type = Column(String(100))
    version = Column(String(100))
    port = Column(Integer)
    status = Column(Enum("running","stopped","degraded","unknown"), default="unknown")
    metadata = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="RAXUS Inventory", version="1.0.0", lifespan=lifespan)


# ─── Datacenters ─────────────────────────────────────────────────
@app.get("/api/v1/datacenters")
async def list_datacenters():
    async with SessionLocal() as db:
        result = await db.execute(select(Datacenter).where(Datacenter.is_active == True).order_by(Datacenter.name))
        return [_dc(d) for d in result.scalars().all()]


@app.post("/api/v1/datacenters")
async def create_datacenter(data: dict):
    async with SessionLocal() as db:
        dc = Datacenter(name=data["name"], location=data.get("location"),
                        description=data.get("description"), tags=data.get("tags"))
        db.add(dc)
        await db.commit()
        return {"id": dc.id, "message": "Datacenter created"}


@app.get("/api/v1/datacenters/{dc_id}")
async def get_datacenter(dc_id: str):
    async with SessionLocal() as db:
        result = await db.execute(select(Datacenter).where(Datacenter.id == dc_id))
        dc = result.scalar_one_or_none()
        if not dc:
            raise HTTPException(404, "Datacenter not found")
        return _dc(dc)


@app.patch("/api/v1/datacenters/{dc_id}")
async def update_datacenter(dc_id: str, data: dict):
    async with SessionLocal() as db:
        allowed = {k: v for k, v in data.items() if k in ("name","location","description","tags","is_active")}
        await db.execute(update(Datacenter).where(Datacenter.id == dc_id).values(**allowed))
        await db.commit()
        return {"message": "Datacenter updated"}


@app.delete("/api/v1/datacenters/{dc_id}")
async def delete_datacenter(dc_id: str):
    async with SessionLocal() as db:
        await db.execute(update(Datacenter).where(Datacenter.id == dc_id).values(is_active=False))
        await db.commit()
        return {"message": "Datacenter deactivated"}


# ─── Environments ─────────────────────────────────────────────────
@app.get("/api/v1/environments")
async def list_environments(datacenter_id: Optional[str] = Query(None)):
    async with SessionLocal() as db:
        q = select(Environment)
        if datacenter_id:
            q = q.where(Environment.datacenter_id == datacenter_id)
        result = await db.execute(q.order_by(Environment.name))
        return [_env(e) for e in result.scalars().all()]


@app.post("/api/v1/environments")
async def create_environment(data: dict):
    async with SessionLocal() as db:
        env = Environment(datacenter_id=data["datacenter_id"], name=data["name"],
                          type=data.get("type","development"), description=data.get("description"),
                          tags=data.get("tags"))
        db.add(env)
        await db.commit()
        return {"id": env.id, "message": "Environment created"}


# ─── Servers ─────────────────────────────────────────────────────
@app.get("/api/v1/servers")
async def list_servers(
    environment_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
):
    async with SessionLocal() as db:
        q = select(Server)
        if environment_id:
            q = q.where(Server.environment_id == environment_id)
        if status:
            q = q.where(Server.status == status)
        if search:
            q = q.where(Server.hostname.ilike(f"%{search}%"))
        q = q.order_by(Server.hostname).offset((page-1)*limit).limit(limit)
        result = await db.execute(q)
        return [_srv(s) for s in result.scalars().all()]


@app.post("/api/v1/servers")
async def create_server(data: dict):
    async with SessionLocal() as db:
        srv = Server(
            environment_id=data["environment_id"], hostname=data["hostname"],
            ip_address=data.get("ip_address"), os_type=data.get("os_type"),
            os_version=data.get("os_version"), cpu_cores=data.get("cpu_cores"),
            ram_gb=data.get("ram_gb"), disk_gb=data.get("disk_gb"),
            tags=data.get("tags"), metadata=data.get("metadata"),
        )
        db.add(srv)
        await db.commit()
        return {"id": srv.id, "message": "Server created"}


@app.get("/api/v1/servers/{server_id}")
async def get_server(server_id: str):
    async with SessionLocal() as db:
        result = await db.execute(select(Server).where(Server.id == server_id))
        srv = result.scalar_one_or_none()
        if not srv:
            raise HTTPException(404, "Server not found")
        return _srv(srv)


@app.patch("/api/v1/servers/{server_id}")
async def update_server(server_id: str, data: dict):
    async with SessionLocal() as db:
        allowed = {k: v for k, v in data.items() if k in ("hostname","ip_address","status","maintenance_mode","tags","metadata","os_type","os_version")}
        await db.execute(update(Server).where(Server.id == server_id).values(**allowed))
        await db.commit()
        return {"message": "Server updated"}


@app.delete("/api/v1/servers/{server_id}")
async def delete_server(server_id: str):
    async with SessionLocal() as db:
        await db.execute(update(Server).where(Server.id == server_id).values(status="decommissioned"))
        await db.commit()
        return {"message": "Server decommissioned"}


# ─── Components ──────────────────────────────────────────────────
@app.get("/api/v1/components")
async def list_components(server_id: Optional[str] = Query(None)):
    async with SessionLocal() as db:
        q = select(Component)
        if server_id:
            q = q.where(Component.server_id == server_id)
        result = await db.execute(q)
        return [_comp(c) for c in result.scalars().all()]


@app.post("/api/v1/components")
async def create_component(data: dict):
    async with SessionLocal() as db:
        comp = Component(server_id=data["server_id"], name=data["name"],
                         type=data.get("type"), version=data.get("version"),
                         port=data.get("port"), metadata=data.get("metadata"))
        db.add(comp)
        await db.commit()
        return {"id": comp.id, "message": "Component created"}


# ─── Stats ───────────────────────────────────────────────────────
@app.get("/api/v1/stats")
async def stats():
    async with SessionLocal() as db:
        dc_count = (await db.execute(text("SELECT COUNT(*) FROM datacenters WHERE is_active=1"))).scalar()
        env_count = (await db.execute(text("SELECT COUNT(*) FROM environments"))).scalar()
        srv_count = (await db.execute(text("SELECT COUNT(*) FROM servers WHERE status != 'decommissioned'"))).scalar()
        comp_count = (await db.execute(text("SELECT COUNT(*) FROM components"))).scalar()
        maintenance = (await db.execute(text("SELECT COUNT(*) FROM servers WHERE maintenance_mode=1"))).scalar()
        by_status = await db.execute(text("SELECT status, COUNT(*) as count FROM servers GROUP BY status"))
        return {
            "datacenters": dc_count, "environments": env_count,
            "servers": srv_count, "components": comp_count,
            "in_maintenance": maintenance,
            "by_status": {r.status: r.count for r in by_status.fetchall()},
        }


@app.get("/health")
async def health():
    return {"status": "ok", "service": "raxus-inventory"}


def _dc(d): return {"id": d.id, "name": d.name, "location": d.location, "description": d.description, "tags": d.tags, "is_active": d.is_active, "created_at": str(d.created_at)}
def _env(e): return {"id": e.id, "datacenter_id": e.datacenter_id, "name": e.name, "type": e.type, "description": e.description, "tags": e.tags, "created_at": str(e.created_at)}
def _srv(s): return {"id": s.id, "environment_id": s.environment_id, "hostname": s.hostname, "ip_address": s.ip_address, "os_type": s.os_type, "os_version": s.os_version, "cpu_cores": s.cpu_cores, "ram_gb": float(s.ram_gb) if s.ram_gb else None, "disk_gb": float(s.disk_gb) if s.disk_gb else None, "status": s.status, "maintenance_mode": s.maintenance_mode, "tags": s.tags, "last_seen": str(s.last_seen) if s.last_seen else None, "created_at": str(s.created_at)}
def _comp(c): return {"id": c.id, "server_id": c.server_id, "name": c.name, "type": c.type, "version": c.version, "port": c.port, "status": c.status, "metadata": c.metadata, "created_at": str(c.created_at)}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
