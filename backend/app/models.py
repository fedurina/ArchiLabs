from __future__ import annotations

import enum
import uuid
from sqlalchemy import String, Integer, Date, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base

class RoomStatus(str, enum.Enum):
    available = "available"
    reserved = "reserved"
    occupied = "occupied"
    needs_cleaning = "needs_cleaning"
    cleaning_in_progress = "cleaning_in_progress"
    ready = "ready"
    out_of_service = "out_of_service"

class RoomType(str, enum.Enum):
    standard = "standard"
    comfort = "comfort"
    lux = "lux"

class BookingStatus(str, enum.Enum):
    created = "created"
    confirmed = "confirmed"
    cancelled = "cancelled"

class Room(Base):
    __tablename__ = "rooms"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    number: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    floor: Mapped[int] = mapped_column(Integer, nullable=False)
    room_type: Mapped[RoomType] = mapped_column(Enum(RoomType), nullable=False)
    status: Mapped[RoomStatus] = mapped_column(Enum(RoomStatus), nullable=False, default=RoomStatus.available)
    bookings: Mapped[list["Booking"]] = relationship(back_populates="room", cascade="all, delete-orphan")

class Booking(Base):
    __tablename__ = "bookings"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    guest_id: Mapped[int] = mapped_column(Integer, nullable=False)
    room_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rooms.id", ondelete="RESTRICT"), nullable=False)
    check_in_date: Mapped[Date] = mapped_column(Date, nullable=False)
    check_out_date: Mapped[Date] = mapped_column(Date, nullable=False)
    status: Mapped[BookingStatus] = mapped_column(Enum(BookingStatus), nullable=False, default=BookingStatus.created)
    room: Mapped["Room"] = relationship(back_populates="bookings")
    __table_args__ = (
        UniqueConstraint("room_id", "check_in_date", "check_out_date", name="uq_booking_room_dates"),
    )
