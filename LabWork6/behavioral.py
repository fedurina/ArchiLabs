from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Protocol

from .creational import BookingBuilder
from .domain import Booking, Notifier, Room, RoomStatus


# -----------------------
# Strategy
# -----------------------
class PricingStrategy(Protocol):
    def calculate(self, room: Room, nights: int) -> float: ...


class StandardPricingStrategy:
    BASE = {"standard": 100.0, "comfort": 150.0, "lux": 250.0}

    def calculate(self, room: Room, nights: int) -> float:
        return self.BASE[room.room_type.value] * nights


class HighSeasonPricingStrategy:
    BASE = {"standard": 100.0, "comfort": 150.0, "lux": 250.0}

    def calculate(self, room: Room, nights: int) -> float:
        return self.BASE[room.room_type.value] * nights * 1.35


# -----------------------
# Observer
# -----------------------
class BookingObserver(Protocol):
    def update(self, booking: Booking) -> None: ...


class BookingSubject:
    def __init__(self) -> None:
        self._observers: list[BookingObserver] = []

    def subscribe(self, observer: BookingObserver) -> None:
        self._observers.append(observer)

    def notify(self, booking: Booking) -> None:
        for observer in self._observers:
            observer.update(booking)


class AuditObserver:
    def __init__(self) -> None:
        self.events: list[str] = []

    def update(self, booking: Booking) -> None:
        self.events.append(f"AUDIT: booking={booking.booking_id} status={booking.status}")


class NotificationObserver:
    def __init__(self, notifier: Notifier) -> None:
        self.notifier = notifier

    def update(self, booking: Booking) -> None:
        self.notifier.send(booking.guest_id, f"Статус бронирования: {booking.status}")


# -----------------------
# Command
# -----------------------
class Command(Protocol):
    def execute(self) -> Booking | None: ...


class CreateBookingCommand:
    def __init__(self, workflow: "BookingWorkflowTemplate", guest_id: int, room: Room, check_in: date, check_out: date) -> None:
        self.workflow = workflow
        self.guest_id = guest_id
        self.room = room
        self.check_in = check_in
        self.check_out = check_out

    def execute(self) -> Booking:
        return self.workflow.run(self.guest_id, self.room, self.check_in, self.check_out)


class CancelBookingCommand:
    def __init__(self, booking: Booking) -> None:
        self.booking = booking

    def execute(self) -> Booking:
        self.booking.status = "cancelled"
        return self.booking


# -----------------------
# State
# -----------------------
class RoomState(ABC):
    @abstractmethod
    def reserve(self, context: "RoomStateContext") -> None: ...

    @abstractmethod
    def release(self, context: "RoomStateContext") -> None: ...


class AvailableState(RoomState):
    def reserve(self, context: "RoomStateContext") -> None:
        context.room.status = RoomStatus.RESERVED
        context.state = ReservedState()

    def release(self, context: "RoomStateContext") -> None:
        raise ValueError("Номер уже свободен")


class ReservedState(RoomState):
    def reserve(self, context: "RoomStateContext") -> None:
        raise ValueError("Номер уже забронирован")

    def release(self, context: "RoomStateContext") -> None:
        context.room.status = RoomStatus.AVAILABLE
        context.state = AvailableState()


class OutOfServiceState(RoomState):
    def reserve(self, context: "RoomStateContext") -> None:
        raise ValueError("Номер выведен из эксплуатации")

    def release(self, context: "RoomStateContext") -> None:
        context.room.status = RoomStatus.AVAILABLE
        context.state = AvailableState()


@dataclass
class RoomStateContext:
    room: Room
    state: RoomState


# -----------------------
# Template Method
# -----------------------
class BookingWorkflowTemplate(ABC):
    def __init__(self, pricing_strategy: PricingStrategy, subject: BookingSubject) -> None:
        self.pricing_strategy = pricing_strategy
        self.subject = subject

    def run(self, guest_id: int, room: Room, check_in: date, check_out: date) -> Booking:
        self.validate_dates(check_in, check_out)
        nights = self.calculate_nights(check_in, check_out)
        price = self.pricing_strategy.calculate(room, nights)
        booking = self.build_booking(guest_id, room, check_in, check_out, price)
        booking = self.persist(booking)
        self.after_save(booking)
        return booking

    def validate_dates(self, check_in: date, check_out: date) -> None:
        if check_in >= check_out:
            raise ValueError("Дата выезда должна быть позже даты заезда")

    def calculate_nights(self, check_in: date, check_out: date) -> int:
        return (check_out - check_in).days

    def build_booking(self, guest_id: int, room: Room, check_in: date, check_out: date, price: float) -> Booking:
        return (
            BookingBuilder()
            .for_guest(guest_id)
            .for_room(room.room_id)
            .between(check_in, check_out)
            .with_price(price)
            .build()
        )

    @abstractmethod
    def persist(self, booking: Booking) -> Booking:
        raise NotImplementedError

    def after_save(self, booking: Booking) -> None:
        self.subject.notify(booking)


class PremiumBookingWorkflow(BookingWorkflowTemplate):
    def __init__(self, pricing_strategy: PricingStrategy, subject: BookingSubject) -> None:
        super().__init__(pricing_strategy, subject)
        self.saved: list[Booking] = []

    def persist(self, booking: Booking) -> Booking:
        booking.status = "confirmed"
        self.saved.append(booking)
        return booking
