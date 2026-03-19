from __future__ import annotations

from datetime import date
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from .models import Room, Booking, BookingStatus, RoomStatus, RoomType

def overlap(a_start: date, a_end: date, b_start: date, b_end: date) -> bool:
    return not (a_end <= b_start or a_start >= b_end)

def room_available(db: Session, room_id: UUID, check_in: date, check_out: date, ignore_booking_id: UUID | None = None) -> bool:
    q = select(Booking).where(and_(Booking.room_id == room_id, Booking.status != BookingStatus.cancelled))
    for b in db.scalars(q).all():
        if ignore_booking_id and b.id == ignore_booking_id:
            continue
        if overlap(check_in, check_out, b.check_in_date, b.check_out_date):
            return False
    return True

def list_rooms(db: Session, status: str | None, room_type: str | None, floor: int | None, limit: int, offset: int):
    q = select(Room)
    if status:
        q = q.where(Room.status == RoomStatus(status))
    if room_type:
        q = q.where(Room.room_type == RoomType(room_type))
    if floor is not None:
        q = q.where(Room.floor == floor)
    q = q.offset(offset).limit(limit)
    return db.scalars(q).all()

def create_room(db: Session, number: str, floor: int, room_type: str, status: str):
    room = Room(number=number, floor=floor, room_type=RoomType(room_type), status=RoomStatus(status))
    db.add(room); db.commit(); db.refresh(room)
    return room

def get_room(db: Session, room_id: UUID):
    return db.get(Room, room_id)

def update_room(db: Session, room_id: UUID, number: str, floor: int, room_type: str, status: str):
    room = db.get(Room, room_id)
    if not room:
        return None
    room.number = number
    room.floor = floor
    room.room_type = RoomType(room_type)
    room.status = RoomStatus(status)
    db.commit(); db.refresh(room)
    return room

def delete_room(db: Session, room_id: UUID):
    room = db.get(Room, room_id)
    if not room:
        return False, "not_found"
    q = select(Booking).where(and_(Booking.room_id == room_id, Booking.status != BookingStatus.cancelled))
    if db.scalars(q).first():
        return False, "has_active_bookings"
    db.delete(room); db.commit()
    return True, "deleted"

def list_bookings(db: Session, guest_id: int | None, room_id: UUID | None, status: str | None,
                  date_from: date | None, date_to: date | None, limit: int, offset: int):
    q = select(Booking)
    if guest_id is not None:
        q = q.where(Booking.guest_id == guest_id)
    if room_id is not None:
        q = q.where(Booking.room_id == room_id)
    if status is not None:
        q = q.where(Booking.status == BookingStatus(status))
    if date_from is not None:
        q = q.where(Booking.check_out_date > date_from)
    if date_to is not None:
        q = q.where(Booking.check_in_date < date_to)
    q = q.offset(offset).limit(limit)
    return db.scalars(q).all()

def create_booking(db: Session, guest_id: int, room_id: UUID, check_in: date, check_out: date):
    room = db.get(Room, room_id)
    if not room:
        return None, "room_not_found"
    if room.status == RoomStatus.out_of_service:
        return None, "room_out_of_service"
    if not room_available(db, room_id, check_in, check_out):
        return None, "room_not_available"
    booking = Booking(guest_id=guest_id, room_id=room_id, check_in_date=check_in, check_out_date=check_out, status=BookingStatus.created)
    db.add(booking); db.commit(); db.refresh(booking)
    return booking, "created"

def get_booking(db: Session, booking_id: UUID):
    return db.get(Booking, booking_id)

def update_booking(db: Session, booking_id: UUID, guest_id: int, room_id: UUID, check_in: date, check_out: date, status: str):
    booking = db.get(Booking, booking_id)
    if not booking:
        return None, "not_found"
    room = db.get(Room, room_id)
    if not room:
        return None, "room_not_found"
    if room.status == RoomStatus.out_of_service:
        return None, "room_out_of_service"
    if not room_available(db, room_id, check_in, check_out, ignore_booking_id=booking_id):
        return None, "room_not_available"
    booking.guest_id = guest_id
    booking.room_id = room_id
    booking.check_in_date = check_in
    booking.check_out_date = check_out
    booking.status = BookingStatus(status)
    db.commit(); db.refresh(booking)
    return booking, "updated"

def delete_booking(db: Session, booking_id: UUID):
    booking = db.get(Booking, booking_id)
    if not booking:
        return False
    db.delete(booking); db.commit()
    return True
