from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class TenantCreate(BaseModel):
    user_id: int | None = None
    first_name: str
    last_name: str
    email: EmailStr
    phone: str | None = None
    date_of_birth: date | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None


class TenantUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    date_of_birth: date | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None


class TenantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    first_name: str
    last_name: str
    email: EmailStr
    phone: str | None
    date_of_birth: date | None
    emergency_contact_name: str | None
    emergency_contact_phone: str | None
    created_at: datetime
