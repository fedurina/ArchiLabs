from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Protocol
from uuid import UUID, uuid4


class RoomType(str, Enum):
    STANDARD = "standard"
    COMFORT = "comfort"
    LUX = "lux"


class RoomStatus(str, Enum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    OUT_OF_SERVICE = "out_of_service"


@dataclass
class Room:
    number: str
    floor: int
    room_type: RoomType
    status: RoomStatus = RoomStatus.AVAILABLE
    amenities: list[str] = field(default_factory=list)
    room_id: UUID = field(default_factory=uuid4)


@dataclass
class Booking:
    guest_id: int
    room_id: UUID
    check_in: date
    check_out: date
    total_price: float = 0.0
    status: str = "created"
    booking_id: UUID = field(default_factory=uuid4)


class Notifier(Protocol):
    def send(self, guest_id: int, message: str) -> None: ...


class LockPort(Protocol):
    def issue_mobile_key(self, room: Room, booking: Booking) -> str: ...


class RoomRepository(Protocol):
    def save(self, room: Room) -> Room: ...
    def get(self, room_id: UUID) -> Room | None: ...
    def list_available(self) -> list[Room]: ...


class BookingRepository(Protocol):
    def save(self, booking: Booking) -> Booking: ...
    def get(self, booking_id: UUID) -> Booking | None: ...
    def cancel(self, booking_id: UUID) -> None: ...
