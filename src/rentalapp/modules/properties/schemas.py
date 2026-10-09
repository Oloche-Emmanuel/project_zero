from datetime import datetime

from pydantic import BaseModel, ConfigDict

from rentalapp.modules.properties.models import PropertyType, UnitStatus


class PropertyCreate(BaseModel):
    name: str
    address_line1: str
    city: str
    state: str
    zip_code: str
    property_type: PropertyType


class PropertyUpdate(BaseModel):
    name: str | None = None
    address_line1: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    property_type: PropertyType | None = None


class PropertyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    name: str
    address_line1: str
    city: str
    state: str
    zip_code: str
    property_type: PropertyType
    created_at: datetime


class UnitCreate(BaseModel):
    unit_number: str
    bedrooms: int = 1
    bathrooms: float = 1.0
    square_feet: int | None = None
    rent_amount: float


class UnitUpdate(BaseModel):
    unit_number: str | None = None
    bedrooms: int | None = None
    bathrooms: float | None = None
    square_feet: int | None = None
    rent_amount: float | None = None
    status: UnitStatus | None = None


class UnitRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    property_id: int
    unit_number: str
    bedrooms: int
    bathrooms: float
    square_feet: int | None
    rent_amount: float
    status: UnitStatus
    created_at: datetime
