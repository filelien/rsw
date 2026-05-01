"""
RAXUS Gateway Service
Main API gateway with auth, routing, rate limiting
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging

from app.core.config import settings
from app.core.database import init_db
from app.core.redis_client import init_redis
from app.api.v1 import auth, users, alerts, inventory, tasks, slo, notifications, rules, tickets, dashboard, websocket

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("raxus.gateway")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting RAXUS Gateway...")
    await init_db()
    await init_redis()
    yield
    logger.info("Shutting down RAXUS Gateway...")


app = FastAPI(
    title="RAXUS API",
    description="RAXUS — Unified IT Operations Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENVIRONMENT == "development" else settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Register routers
app.include_router(auth.router,          prefix="/api/v1/auth",          tags=["Authentication"])
app.include_router(users.router,         prefix="/api/v1/users",         tags=["Users"])
app.include_router(alerts.router,        prefix="/api/v1/alerts",        tags=["Alerts"])
app.include_router(inventory.router,     prefix="/api/v1/inventory",     tags=["Inventory"])
app.include_router(tasks.router,         prefix="/api/v1/tasks",         tags=["Tasks"])
app.include_router(slo.router,           prefix="/api/v1/slo",           tags=["SLO"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["Notifications"])
app.include_router(rules.router,         prefix="/api/v1/rules",         tags=["Rules"])
app.include_router(tickets.router,       prefix="/api/v1/tickets",       tags=["Tickets"])
app.include_router(dashboard.router,     prefix="/api/v1/dashboard",     tags=["Dashboard"])
app.include_router(websocket.router,     prefix="/ws",                   tags=["WebSocket"])


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "raxus-gateway", "version": "1.0.0"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.ENVIRONMENT == "development")
