from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Iterable
from uuid import UUID

from .domain import Booking, BookingRepository, LockPort, Notifier, Room, RoomRepository, RoomStatus


# -----------------------
# Adapter
# -----------------------
class LegacySmartLockApi:
    def create_digital_pass(self, room_number: str, guest_code: str, valid_from: str, valid_to: str) -> str:
        return f"legacy-key::{room_number}::{guest_code}::{valid_from}::{valid_to}"


class SmartLockAdapter(LockPort):
    def __init__(self, legacy_api: LegacySmartLockApi) -> None:
        self.legacy_api = legacy_api

    def issue_mobile_key(self, room: Room, booking: Booking) -> str:
        return self.legacy_api.create_digital_pass(
            room_number=room.number,
            guest_code=str(booking.guest_id),
            valid_from=booking.check_in.isoformat(),
            valid_to=booking.check_out.isoformat(),
        )


# -----------------------
# Decorator
# -----------------------
class LoggingNotifierDecorator(Notifier):
    def __init__(self, wrapped: Notifier) -> None:
        self.wrapped = wrapped
        self.log: list[str] = []

    def send(self, guest_id: int, message: str) -> None:
        self.log.append(f"{datetime.utcnow().isoformat()} guest={guest_id}: {message}")
        self.wrapped.send(guest_id, message)


# -----------------------
# Proxy
# -----------------------
class RoomCatalogProxy:
    def __init__(self, room_repository: RoomRepository) -> None:
        self.room_repository = room_repository
        self._cache: list[Room] | None = None

    def list_available_rooms(self) -> list[Room]:
        if self._cache is None:
            self._cache = self.room_repository.list_available()
        return [replace(room) for room in self._cache]

    def invalidate(self) -> None:
        self._cache = None


# -----------------------
# Facade
# -----------------------
class InMemoryRoomRepository(RoomRepository):
    def __init__(self, rooms: Iterable[Room] = ()) -> None:
        self.rooms = {room.room_id: room for room in rooms}

    def save(self, room: Room) -> Room:
        self.rooms[room.room_id] = room
        return room

    def get(self, room_id: UUID) -> Room | None:
        return self.rooms.get(room_id)

    def list_available(self) -> list[Room]:
        return [room for room in self.rooms.values() if room.status == RoomStatus.AVAILABLE]


class InMemoryBookingRepository(BookingRepository):
    def __init__(self) -> None:
        self.bookings: dict[UUID, Booking] = {}

    def save(self, booking: Booking) -> Booking:
        self.bookings[booking.booking_id] = booking
        return booking

    def get(self, booking_id: UUID) -> Booking | None:
        return self.bookings.get(booking_id)

    def cancel(self, booking_id: UUID) -> None:
        booking = self.bookings[booking_id]
        booking.status = "cancelled"


class ReservationFacade:
    def __init__(
        self,
        room_repository: RoomRepository,
        booking_repository: BookingRepository,
        notifier: Notifier,
        lock_service: LockPort,
    ) -> None:
        self.room_repository = room_repository
        self.booking_repository = booking_repository
        self.notifier = notifier
        self.lock_service = lock_service

    def reserve_room(self, room: Room, booking: Booking) -> tuple[Booking, str]:
        room.status = RoomStatus.RESERVED
        self.room_repository.save(room)
        saved_booking = self.booking_repository.save(booking)
        mobile_key = self.lock_service.issue_mobile_key(room, saved_booking)
        self.notifier.send(booking.guest_id, f"Бронирование подтверждено. Ключ: {mobile_key}")
        return saved_booking, mobile_key
