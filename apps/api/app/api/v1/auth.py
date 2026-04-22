from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    safe_decode_token,
    verify_password,
)
from app.models.core import RefreshToken, Role, User
from app.schemas.core import APIMessage, LoginRequest, RefreshRequest, RegisterRequest, TokenResponse

router = APIRouter()


def _build_access_payload(user: User, role_name: str) -> dict:
    return {
        "sub": str(user.id),
        "tenant_id": str(user.tenant_id),
        "role": role_name,
        "branch_id": str(user.branch_id),
    }


async def _get_user_with_role_by_email(db: AsyncSession, email: str) -> tuple[User, str] | None:
    query = (
        select(User, Role.name)
        .join(Role, User.role_id == Role.id)
        .where(User.email == email)
        .where(User.deleted_at.is_(None))
    )
    row = (await db.execute(query)).first()
    return (row[0], row[1]) if row else None


async def _get_user_with_role_by_id(db: AsyncSession, user_id: UUID) -> tuple[User, str] | None:
    query = (
        select(User, Role.name)
        .join(Role, User.role_id == Role.id)
        .where(User.id == user_id)
        .where(User.deleted_at.is_(None))
    )
    row = (await db.execute(query)).first()
    return (row[0], row[1]) if row else None


@router.post("/register", response_model=TokenResponse)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = (
        await db.execute(
            select(User)
            .where(User.tenant_id == payload.tenant_id)
            .where(User.email == payload.email)
            .where(User.deleted_at.is_(None))
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="User already exists")

    now = datetime.now(UTC)
    user = User(
        tenant_id=payload.tenant_id,
        branch_id=payload.branch_id,
        role_id=payload.role_id,
        email=payload.email,
        full_name=payload.full_name,
        password_hash=get_password_hash(payload.password),
        created_at=now,
        updated_at=now,
    )
    db.add(user)
    await db.flush()

    role = (await db.execute(select(Role.name).where(Role.id == user.role_id))).scalar_one_or_none()
    role_name = role or "user"

    access_token = create_access_token(_build_access_payload(user, role_name))
    refresh_token = create_refresh_token({"sub": str(user.id), "tenant_id": str(user.tenant_id)})
    decoded_refresh = safe_decode_token(refresh_token)
    if not decoded_refresh:
        raise HTTPException(status_code=500, detail="Could not issue refresh token")

    db.add(
        RefreshToken(
            user_id=user.id,
            token=refresh_token,
            expires_at=datetime.fromtimestamp(decoded_refresh["exp"], tz=UTC),
            revoked=False,
            created_at=now,
        )
    )
    await db.commit()

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    row = await _get_user_with_role_by_email(db, payload.email)
    if not row:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    user, role_name = row
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    now = datetime.now(UTC)
    access_token = create_access_token(_build_access_payload(user, role_name))
    refresh_token = create_refresh_token({"sub": str(user.id), "tenant_id": str(user.tenant_id)})
    decoded_refresh = safe_decode_token(refresh_token)
    if not decoded_refresh:
        raise HTTPException(status_code=500, detail="Could not issue refresh token")

    db.add(
        RefreshToken(
            user_id=user.id,
            token=refresh_token,
            expires_at=datetime.fromtimestamp(decoded_refresh["exp"], tz=UTC),
            revoked=False,
            created_at=now,
        )
    )
    user.last_login_at = now
    await db.commit()

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    decoded = safe_decode_token(payload.refresh_token)
    if not decoded or decoded.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = decoded.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    now = datetime.now(UTC)
    token_row = (
        await db.execute(
            select(RefreshToken)
            .where(RefreshToken.token == payload.refresh_token)
            .where(RefreshToken.revoked.is_(False))
            .where(RefreshToken.expires_at > now)
        )
    ).scalar_one_or_none()
    if not token_row:
        raise HTTPException(status_code=401, detail="Refresh token revoked or expired")

    user_row = await _get_user_with_role_by_id(db, UUID(user_id))
    if not user_row:
        raise HTTPException(status_code=401, detail="User not found")
    user, role_name = user_row

    token_row.revoked = True
    access_token = create_access_token(_build_access_payload(user, role_name))
    new_refresh_token = create_refresh_token({"sub": str(user.id), "tenant_id": str(user.tenant_id)})
    decoded_new_refresh = safe_decode_token(new_refresh_token)
    if not decoded_new_refresh:
        raise HTTPException(status_code=500, detail="Could not issue refresh token")

    db.add(
        RefreshToken(
            user_id=user.id,
            token=new_refresh_token,
            expires_at=datetime.fromtimestamp(decoded_new_refresh["exp"], tz=UTC),
            revoked=False,
            created_at=now,
        )
    )
    await db.commit()

    return TokenResponse(access_token=access_token, refresh_token=new_refresh_token)


@router.post("/logout", response_model=APIMessage)
async def logout(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    decoded = safe_decode_token(payload.refresh_token)
    if not decoded or decoded.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    token_row = (
        await db.execute(
            select(RefreshToken)
            .where(RefreshToken.token == payload.refresh_token)
            .where(RefreshToken.revoked.is_(False))
        )
    ).scalar_one_or_none()

    if token_row:
        token_row.revoked = True
        await db.commit()

    return APIMessage(detail="Logged out")
