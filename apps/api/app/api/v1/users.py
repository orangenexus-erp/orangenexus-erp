from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.security import get_password_hash
from app.models.core import User
from app.schemas.core import UserCreate, UserRead

router = APIRouter()


@router.get("/", response_model=list[UserRead])
async def list_users(db: AsyncSession = Depends(get_db), _: dict = Depends(get_current_user)):
    users = (await db.execute(select(User).where(User.deleted_at.is_(None)))).scalars().all()
    return users


@router.post("/", response_model=UserRead)
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    user = User(
        tenant_id=payload.tenant_id,
        branch_id=payload.branch_id,
        role_id=payload.role_id,
        email=payload.email,
        full_name=payload.full_name,
        password_hash=get_password_hash(payload.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
