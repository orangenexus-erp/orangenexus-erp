from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class APIMessage(BaseModel):
    detail: str


class TenantCreate(BaseModel):
    name: str
    tax_id: str


class TenantRead(TenantCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime


class RoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    level: int


class UserCreate(BaseModel):
    tenant_id: UUID
    branch_id: UUID
    role_id: UUID
    email: EmailStr
    full_name: str
    password: str


class RegisterRequest(UserCreate):
    pass


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    branch_id: UUID
    role_id: UUID
    email: EmailStr
    full_name: str
    is_active: bool


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str
