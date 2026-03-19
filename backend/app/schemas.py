from __future__ import annotations

from datetime import date
from uuid import UUID
from pydantic import BaseModel, Field, model_validator

from .models import RoomStatus, RoomType, BookingStatus


class RoomCreate(BaseModel):
    number: str = Field(..., examples=["305"])
    floor: int = Field(..., ge=0, le=200)
    room_type: RoomType
    status: RoomStatus = RoomStatus.available


class RoomOut(BaseModel):
    id: UUID
    number: str
    floor: int
    room_type: RoomType
    status: RoomStatus

    model_config = {"from_attributes": True}


class BookingCreate(BaseModel):
    guest_id: int = Field(..., ge=1)
    room_id: UUID
    check_in_date: date
    check_out_date: date

    @model_validator(mode="after")
    def validate_dates(self):
        if self.check_in_date >= self.check_out_date:
            raise ValueError("check_out_date must be after check_in_date")
        return self


class BookingUpdate(BaseModel):
    guest_id: int = Field(..., ge=1)
    room_id: UUID
    check_in_date: date
    check_out_date: date
    status: BookingStatus = BookingStatus.created

    @model_validator(mode="after")
    def validate_dates(self):
        if self.check_in_date >= self.check_out_date:
            raise ValueError("check_out_date must be after check_in_date")
        return self


class BookingOut(BaseModel):
    id: UUID
    guest_id: int
    room_id: UUID
    check_in_date: date
    check_out_date: date
    status: BookingStatus

    model_config = {"from_attributes": True}


class HealthOut(BaseModel):
    status: str
    db: str
