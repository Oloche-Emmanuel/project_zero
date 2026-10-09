import enum
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from rentalapp.database import Base


class PropertyType(str, enum.Enum):
    SINGLE_FAMILY = "single_family"
    MULTI_FAMILY = "multi_family"
    APARTMENT = "apartment"
    CONDO = "condo"
    COMMERCIAL = "commercial"


class UnitStatus(str, enum.Enum):
    VACANT = "vacant"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"


class Property(Base):
    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address_line1: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    zip_code: Mapped[str] = mapped_column(String(20), nullable=False)
    property_type: Mapped[PropertyType] = mapped_column(Enum(PropertyType), nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    units: Mapped[list["Unit"]] = relationship(back_populates="property", cascade="all, delete-orphan")


class Unit(Base):
    __tablename__ = "units"

    id: Mapped[int] = mapped_column(primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), nullable=False)
    unit_number: Mapped[str] = mapped_column(String(50), nullable=False)
    bedrooms: Mapped[int] = mapped_column(default=1, nullable=False)
    bathrooms: Mapped[float] = mapped_column(default=1.0, nullable=False)
    square_feet: Mapped[int | None] = mapped_column(nullable=True)
    rent_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[UnitStatus] = mapped_column(Enum(UnitStatus), default=UnitStatus.VACANT, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    property: Mapped["Property"] = relationship(back_populates="units")
