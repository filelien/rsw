from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.core.database import get_db
from app.core.security import get_current_user, require_role, hash_password
from app.models.user import User

router = APIRouter()


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


@router.get("")
async def list_users(
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
):
    result = await db.execute(select(User).offset((page - 1) * limit).limit(limit))
    users = result.scalars().all()
    return [{"id": u.id, "email": u.email, "username": u.username,
             "full_name": u.full_name, "role": u.role, "is_active": u.is_active,
             "last_login": u.last_login, "created_at": u.created_at} for u in users]


@router.get("/{user_id}")
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user.id, "email": user.email, "username": user.username,
            "full_name": user.full_name, "role": user.role, "is_active": user.is_active}


@router.patch("/{user_id}")
async def update_user(
    user_id: str,
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    if data.role and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can change roles")
    values = {k: v for k, v in data.model_dump().items() if v is not None}
    await db.execute(update(User).where(User.id == user_id).values(**values))
    await db.commit()
    return {"message": "User updated"}


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(update(User).where(User.id == user_id).values(is_active=False))
    await db.commit()
    return {"message": "User deactivated"}
