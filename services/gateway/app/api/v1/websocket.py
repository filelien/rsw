from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import asyncio
import json
import logging
import redis.asyncio as aioredis
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger("raxus.ws")


class ConnectionManager:
    def __init__(self):
        self.active: Dict[str, Set[WebSocket]] = {}

    async def connect(self, ws: WebSocket, channel: str):
        await ws.accept()
        if channel not in self.active:
            self.active[channel] = set()
        self.active[channel].add(ws)
        logger.info(f"WS connected to channel: {channel}")

    def disconnect(self, ws: WebSocket, channel: str):
        if channel in self.active:
            self.active[channel].discard(ws)

    async def broadcast(self, channel: str, message: dict):
        if channel not in self.active:
            return
        dead = set()
        for ws in self.active[channel]:
            try:
                await ws.send_json(message)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self.active[channel].discard(ws)


manager = ConnectionManager()


@router.websocket("/alerts")
async def ws_alerts(websocket: WebSocket):
    await manager.connect(websocket, "alerts")
    try:
        r = aioredis.from_url(settings.REDIS_URL)
        pubsub = r.pubsub()
        await pubsub.subscribe("raxus:alerts")

        async def listen():
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        await websocket.send_json(data)
                    except Exception:
                        pass

        listen_task = asyncio.create_task(listen())

        while True:
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=30)
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "ping"})
            except WebSocketDisconnect:
                break

        listen_task.cancel()
        await r.aclose()
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket, "alerts")


@router.websocket("/dashboard")
async def ws_dashboard(websocket: WebSocket):
    await manager.connect(websocket, "dashboard")
    try:
        r = aioredis.from_url(settings.REDIS_URL)
        pubsub = r.pubsub()
        await pubsub.subscribe("raxus:dashboard")

        async def listen():
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        await websocket.send_json(data)
                    except Exception:
                        pass

        listen_task = asyncio.create_task(listen())
        while True:
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=30)
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "ping"})
            except WebSocketDisconnect:
                break

        listen_task.cancel()
        await r.aclose()
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket, "dashboard")
