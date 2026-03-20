from __future__ import annotations

from abc import ABC, abstractmethod
from copy import deepcopy
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from .domain import Booking, Notifier, Room, RoomStatus, RoomType


# -----------------------
# Prototype
# -----------------------
class RoomPrototypeRegistry:
    def __init__(self) -> None:
        self._templates: dict[RoomType, Room] = {}

    def register(self, room_type: RoomType, template: Room) -> None:
        self._templates[room_type] = template

    def clone(self, room_type: RoomType, *, number: str, floor: int, status: RoomStatus = RoomStatus.AVAILABLE) -> Room:
        template = deepcopy(self._templates[room_type])
        template.number = number
        template.floor = floor
        template.status = status
        return template


# -----------------------
# Builder
# -----------------------
@dataclass
class BookingDraft:
    guest_id: int | None = None
    room_id: UUID | None = None
    check_in: date | None = None
    check_out: date | None = None
    total_price: float = 0.0
    status: str = "created"


class BookingBuilder:
    def __init__(self) -> None:
        self._draft = BookingDraft()

    def for_guest(self, guest_id: int) -> "BookingBuilder":
        self._draft.guest_id = guest_id
        return self

    def for_room(self, room_id: UUID) -> "BookingBuilder":
        self._draft.room_id = room_id
        return self

    def between(self, check_in: date, check_out: date) -> "BookingBuilder":
        self._draft.check_in = check_in
        self._draft.check_out = check_out
        return self

    def with_price(self, total_price: float) -> "BookingBuilder":
        self._draft.total_price = total_price
        return self

    def build(self) -> Booking:
        if None in (self._draft.guest_id, self._draft.room_id, self._draft.check_in, self._draft.check_out):
            raise ValueError("BookingBuilder: not all mandatory fields are set")
        return Booking(
            guest_id=self._draft.guest_id,
            room_id=self._draft.room_id,
            check_in=self._draft.check_in,
            check_out=self._draft.check_out,
            total_price=self._draft.total_price,
            status=self._draft.status,
        )


# -----------------------
# Factory Method
# -----------------------
class EmailNotifier:
    def send(self, guest_id: int, message: str) -> None:
        print(f"EMAIL to guest={guest_id}: {message}")


class SmsNotifier:
    def send(self, guest_id: int, message: str) -> None:
        print(f"SMS to guest={guest_id}: {message}")


class PushNotifier:
    def send(self, guest_id: int, message: str) -> None:
        print(f"PUSH to guest={guest_id}: {message}")


class NotificationFactory(ABC):
    @abstractmethod
    def create_notifier(self) -> Notifier:
        raise NotImplementedError

    def notify(self, guest_id: int, message: str) -> None:
        notifier = self.create_notifier()
        notifier.send(guest_id, message)


class EmailNotificationFactory(NotificationFactory):
    def create_notifier(self) -> Notifier:
        return EmailNotifier()


class SmsNotificationFactory(NotificationFactory):
    def create_notifier(self) -> Notifier:
        return SmsNotifier()


class PushNotificationFactory(NotificationFactory):
    def create_notifier(self) -> Notifier:
        return PushNotifier()
