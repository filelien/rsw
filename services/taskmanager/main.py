"""RAXUS TaskManager Service"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, Boolean, DateTime, Enum, JSON, Text, Integer, func, select, update, text
from celery import Celery
from datetime import datetime, timezone
import uuid, os, logging, uvicorn, subprocess, asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("raxus.taskmanager")

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+aiomysql://raxus:raxus_pass@mysql:3306/raxus")
CELERY_BROKER = os.getenv("CELERY_BROKER_URL", "redis://:raxus_redis@redis:6379/5")

engine = create_async_engine(DATABASE_URL, pool_pre_ping=True, pool_size=5)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
celery_app = Celery("raxus_tasks", broker=CELERY_BROKER)


class Base(DeclarativeBase):
    pass


class Task(Base):
    __tablename__ = "tasks"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    script = Column(Text, nullable=False)
    script_type = Column(Enum("bash","python","ansible"), default="bash")
    parameters = Column(JSON)
    timeout_sec = Column(Integer, default=300)
    tags = Column(JSON)
    is_active = Column(Boolean, default=True)
    created_by = Column(String(36))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class TaskExecution(Base):
    __tablename__ = "task_executions"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(36), nullable=False)
    server_id = Column(String(36))
    triggered_by = Column(String(36))
    trigger_type = Column(Enum("manual","schedule","alert","api"), default="manual")
    status = Column(Enum("pending","running","success","failed","cancelled","timeout"), default="pending")
    parameters = Column(JSON)
    output = Column(Text)
    error_output = Column(Text)
    exit_code = Column(Integer)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    duration_ms = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())


class Schedule(Base):
    __tablename__ = "schedules"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(36), nullable=False)
    name = Column(String(255), nullable=False)
    cron_expr = Column(String(100), nullable=False)
    target_type = Column(Enum("server","environment","datacenter","component"), nullable=False)
    target_id = Column(String(36))
    parameters = Column(JSON)
    is_active = Column(Boolean, default=True)
    last_run = Column(DateTime)
    next_run = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="RAXUS TaskManager", version="1.0.0", lifespan=lifespan)


async def run_script(execution_id: str, task: Task, parameters: dict):
    async with SessionLocal() as db:
        await db.execute(update(TaskExecution).where(TaskExecution.id == execution_id).values(
            status="running", started_at=datetime.now(timezone.utc)
        ))
        await db.commit()

    start = datetime.now(timezone.utc)
    output, error_output, exit_code = "", "", -1
    try:
        if task.script_type == "bash":
            proc = await asyncio.create_subprocess_shell(
                task.script, stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=task.timeout_sec
            )
            output = stdout.decode()
            error_output = stderr.decode()
            exit_code = proc.returncode
            status = "success" if exit_code == 0 else "failed"
        else:
            output = f"Script type '{task.script_type}' execution simulated"
            exit_code = 0
            status = "success"
    except asyncio.TimeoutError:
        status, error_output, exit_code = "timeout", "Execution timed out", -1
    except Exception as e:
        status, error_output, exit_code = "failed", str(e), -1

    duration = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)
    async with SessionLocal() as db:
        await db.execute(update(TaskExecution).where(TaskExecution.id == execution_id).values(
            status=status, output=output[:50000], error_output=error_output[:10000],
            exit_code=exit_code, finished_at=datetime.now(timezone.utc), duration_ms=duration,
        ))
        await db.commit()


@app.get("/api/v1/tasks")
async def list_tasks():
    async with SessionLocal() as db:
        result = await db.execute(select(Task).where(Task.is_active == True).order_by(Task.name))
        return [_task(t) for t in result.scalars().all()]


@app.post("/api/v1/tasks")
async def create_task(data: dict):
    async with SessionLocal() as db:
        t = Task(name=data["name"], description=data.get("description"), script=data["script"],
                 script_type=data.get("script_type","bash"), parameters=data.get("parameters"),
                 timeout_sec=data.get("timeout_sec",300), tags=data.get("tags"),
                 created_by=data.get("created_by"))
        db.add(t)
        await db.commit()
        return {"id": t.id, "message": "Task created"}


@app.get("/api/v1/tasks/{task_id}")
async def get_task(task_id: str):
    async with SessionLocal() as db:
        result = await db.execute(select(Task).where(Task.id == task_id))
        t = result.scalar_one_or_none()
        if not t:
            raise HTTPException(404, "Task not found")
        return _task(t)


@app.patch("/api/v1/tasks/{task_id}")
async def update_task(task_id: str, data: dict):
    async with SessionLocal() as db:
        allowed = {k: v for k, v in data.items() if k in ("name","description","script","script_type","parameters","timeout_sec","tags","is_active")}
        await db.execute(update(Task).where(Task.id == task_id).values(**allowed))
        await db.commit()
        return {"message": "Task updated"}


@app.delete("/api/v1/tasks/{task_id}")
async def delete_task(task_id: str):
    async with SessionLocal() as db:
        await db.execute(update(Task).where(Task.id == task_id).values(is_active=False))
        await db.commit()
        return {"message": "Task deactivated"}


@app.post("/api/v1/tasks/{task_id}/execute")
async def execute_task(task_id: str, data: dict, background_tasks: BackgroundTasks):
    async with SessionLocal() as db:
        result = await db.execute(select(Task).where(Task.id == task_id, Task.is_active == True))
        task = result.scalar_one_or_none()
        if not task:
            raise HTTPException(404, "Task not found")
        execution = TaskExecution(
            task_id=task_id, server_id=data.get("server_id"),
            triggered_by=data.get("triggered_by"), trigger_type=data.get("trigger_type","manual"),
            parameters=data.get("parameters",{}),
        )
        db.add(execution)
        await db.commit()
        background_tasks.add_task(run_script, execution.id, task, data.get("parameters",{}))
        return {"execution_id": execution.id, "status": "pending", "message": "Task execution started"}


@app.get("/api/v1/executions")
async def list_executions(task_id: str = None, status: str = None, page: int = 1, limit: int = 50):
    async with SessionLocal() as db:
        q = select(TaskExecution).order_by(TaskExecution.created_at.desc())
        if task_id:
            q = q.where(TaskExecution.task_id == task_id)
        if status:
            q = q.where(TaskExecution.status == status)
        q = q.offset((page-1)*limit).limit(limit)
        result = await db.execute(q)
        return [_exec(e) for e in result.scalars().all()]


@app.get("/api/v1/executions/{exec_id}")
async def get_execution(exec_id: str):
    async with SessionLocal() as db:
        result = await db.execute(select(TaskExecution).where(TaskExecution.id == exec_id))
        e = result.scalar_one_or_none()
        if not e:
            raise HTTPException(404, "Execution not found")
        return _exec(e)


@app.get("/api/v1/schedules")
async def list_schedules():
    async with SessionLocal() as db:
        result = await db.execute(select(Schedule).where(Schedule.is_active == True))
        return [_sched(s) for s in result.scalars().all()]


@app.post("/api/v1/schedules")
async def create_schedule(data: dict):
    async with SessionLocal() as db:
        s = Schedule(task_id=data["task_id"], name=data["name"], cron_expr=data["cron_expr"],
                     target_type=data["target_type"], target_id=data.get("target_id"),
                     parameters=data.get("parameters"))
        db.add(s)
        await db.commit()
        return {"id": s.id, "message": "Schedule created"}


@app.get("/api/v1/stats")
async def stats():
    async with SessionLocal() as db:
        tasks = (await db.execute(text("SELECT COUNT(*) FROM tasks WHERE is_active=1"))).scalar()
        running = (await db.execute(text("SELECT COUNT(*) FROM task_executions WHERE status='running'"))).scalar()
        success_today = (await db.execute(text("SELECT COUNT(*) FROM task_executions WHERE status='success' AND DATE(created_at)=CURDATE()"))).scalar()
        failed_today = (await db.execute(text("SELECT COUNT(*) FROM task_executions WHERE status='failed' AND DATE(created_at)=CURDATE()"))).scalar()
        return {"tasks": tasks, "running": running, "success_today": success_today, "failed_today": failed_today}


@app.get("/health")
async def health():
    return {"status": "ok", "service": "raxus-taskmanager"}


def _task(t): return {"id": t.id, "name": t.name, "description": t.description, "script_type": t.script_type, "timeout_sec": t.timeout_sec, "tags": t.tags, "is_active": t.is_active, "created_by": t.created_by, "created_at": str(t.created_at)}
def _exec(e): return {"id": e.id, "task_id": e.task_id, "server_id": e.server_id, "triggered_by": e.triggered_by, "trigger_type": e.trigger_type, "status": e.status, "exit_code": e.exit_code, "output": e.output, "error_output": e.error_output, "duration_ms": e.duration_ms, "started_at": str(e.started_at) if e.started_at else None, "finished_at": str(e.finished_at) if e.finished_at else None, "created_at": str(e.created_at)}
def _sched(s): return {"id": s.id, "task_id": s.task_id, "name": s.name, "cron_expr": s.cron_expr, "target_type": s.target_type, "target_id": s.target_id, "is_active": s.is_active, "last_run": str(s.last_run) if s.last_run else None, "created_at": str(s.created_at)}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8004, reload=True)
