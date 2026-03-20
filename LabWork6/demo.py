from __future__ import annotations

from datetime import date

from .behavioral import (
    AuditObserver,
    BookingSubject,
    CreateBookingCommand,
    HighSeasonPricingStrategy,
    NotificationObserver,
    PremiumBookingWorkflow,
    RoomStateContext,
    AvailableState,
)
from .creational import (
    BookingBuilder,
    EmailNotificationFactory,
    RoomPrototypeRegistry,
)
from .domain import Room, RoomType, RoomStatus
from .structural import (
    InMemoryBookingRepository,
    InMemoryRoomRepository,
    LegacySmartLockApi,
    LoggingNotifierDecorator,
    ReservationFacade,
    SmartLockAdapter,
)


def build_demo_facade() -> ReservationFacade:
    prototype_registry = RoomPrototypeRegistry()
    prototype_registry.register(
        RoomType.LUX,
        Room(number="template", floor=1, room_type=RoomType.LUX, amenities=["spa", "ocean view"]),
    )
    room = prototype_registry.clone(RoomType.LUX, number="305", floor=3, status=RoomStatus.AVAILABLE)

    notifier = LoggingNotifierDecorator(EmailNotificationFactory().create_notifier())
    room_repo = InMemoryRoomRepository([room])
    booking_repo = InMemoryBookingRepository()
    lock_adapter = SmartLockAdapter(LegacySmartLockApi())
    facade = ReservationFacade(room_repo, booking_repo, notifier, lock_adapter)
    return facade


def run_demo() -> None:
    facade = build_demo_facade()
    room = facade.room_repository.list_available()[0]

    subject = BookingSubject()
    subject.subscribe(AuditObserver())
    subject.subscribe(NotificationObserver(facade.notifier))

    workflow = PremiumBookingWorkflow(HighSeasonPricingStrategy(), subject)
    command = CreateBookingCommand(
        workflow=workflow,
        guest_id=42,
        room=room,
        check_in=date(2026, 4, 1),
        check_out=date(2026, 4, 5),
    )
    booking = command.execute()

    state_context = RoomStateContext(room=room, state=AvailableState())
    state_context.state.reserve(state_context)

    facade.reserve_room(room, booking)
    print("Demo complete", booking.booking_id)


if __name__ == "__main__":
    run_demo()
