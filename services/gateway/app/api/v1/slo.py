from fastapi import APIRouter, Depends, Request
from app.core.security import get_current_user, require_role
from app.models.user import User
from app.core.config import settings
import httpx

router = APIRouter()

async def _proxy(base: str, path: str, method: str = "GET", data=None, params=None):
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.request(method, f"{base}{path}", json=data, params=params)
        return r.json()
