from __future__ import annotations

from uuid import UUID
from fastapi import FastAPI, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from .db import Base, engine, get_db
from . import crud, schemas

def require_auth(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Empty Bearer token")
    return token

app = FastAPI(title="Hotel NextGen API (Lab 5)", version="1.0.0")

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

@app.get("/health", response_model=schemas.HealthOut)
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_ok = "ok"
    except Exception:
        db_ok = "fail"
    return {"status": "ok", "db": db_ok}

# Rooms
@app.get("/api/v1/rooms", response_model=list[schemas.RoomOut])
def list_rooms(status_: schemas.RoomStatus | None = None, room_type: schemas.RoomType | None = None,
               floor: int | None = None, limit: int = 50, offset: int = 0,
               _: str = Depends(require_auth), db: Session = Depends(get_db)):
    return crud.list_rooms(db, status_, room_type, floor, limit, offset)

@app.post("/api/v1/rooms", response_model=schemas.RoomOut, status_code=status.HTTP_201_CREATED)
def create_room(payload: schemas.RoomCreate, _: str = Depends(require_auth), db: Session = Depends(get_db)):
    try:
        return crud.create_room(db, payload.number, payload.floor, payload.room_type, payload.status)
    except Exception:
        raise HTTPException(status_code=409, detail=f"Room number '{payload.number}' already exists")

@app.get("/api/v1/rooms/{room_id}", response_model=schemas.RoomOut)
def get_room(room_id: UUID, _: str = Depends(require_auth), db: Session = Depends(get_db)):
    room = crud.get_room(db, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room

@app.put("/api/v1/rooms/{room_id}", response_model=schemas.RoomOut)
def put_room(room_id: UUID, payload: schemas.RoomCreate, _: str = Depends(require_auth), db: Session = Depends(get_db)):
    try:
        room = crud.update_room(db, room_id, payload.number, payload.floor, payload.room_type, payload.status)
    except Exception:
        raise HTTPException(status_code=409, detail=f"Room number '{payload.number}' already exists")
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room

@app.delete("/api/v1/rooms/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_room(room_id: UUID, _: str = Depends(require_auth), db: Session = Depends(get_db)):
    ok, reason = crud.delete_room(db, room_id)
    if not ok:
        if reason == "not_found":
            raise HTTPException(status_code=404, detail="Room not found")
        if reason == "has_active_bookings":
            raise HTTPException(status_code=409, detail="Room has active bookings; cannot delete")
        raise HTTPException(status_code=400, detail="Cannot delete room")
    return None

# Bookings
@app.get("/api/v1/bookings", response_model=list[schemas.BookingOut])
def list_bookings(guest_id: int | None = None, room_id: UUID | None = None,
                  status_: schemas.BookingStatus | None = None,
                  date_from: schemas.date | None = None, date_to: schemas.date | None = None,
                  limit: int = 50, offset: int = 0,
                  _: str = Depends(require_auth), db: Session = Depends(get_db)):
    return crud.list_bookings(db, guest_id, room_id, status_, date_from, date_to, limit, offset)

@app.post("/api/v1/bookings", response_model=schemas.BookingOut, status_code=status.HTTP_201_CREATED)
def create_booking(payload: schemas.BookingCreate, _: str = Depends(require_auth), db: Session = Depends(get_db)):
    booking, reason = crud.create_booking(db, payload.guest_id, payload.room_id, payload.check_in_date, payload.check_out_date)
    if not booking:
        if reason == "room_not_found":
            raise HTTPException(status_code=404, detail="Room not found")
        if reason == "room_out_of_service":
            raise HTTPException(status_code=409, detail="Room is out of service")
        if reason == "room_not_available":
            raise HTTPException(status_code=409, detail="Room is not available for selected dates")
        raise HTTPException(status_code=400, detail="Cannot create booking")
    return booking

@app.get("/api/v1/bookings/{booking_id}", response_model=schemas.BookingOut)
def get_booking(booking_id: UUID, _: str = Depends(require_auth), db: Session = Depends(get_db)):
    booking = crud.get_booking(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking

@app.put("/api/v1/bookings/{booking_id}", response_model=schemas.BookingOut)
def put_booking(booking_id: UUID, payload: schemas.BookingUpdate, _: str = Depends(require_auth), db: Session = Depends(get_db)):
    booking, reason = crud.update_booking(db, booking_id, payload.guest_id, payload.room_id, payload.check_in_date, payload.check_out_date, payload.status)
    if not booking:
        if reason == "not_found":
            raise HTTPException(status_code=404, detail="Booking not found")
        if reason == "room_not_found":
            raise HTTPException(status_code=404, detail="Room not found")
        if reason == "room_out_of_service":
            raise HTTPException(status_code=409, detail="Room is out of service")
        if reason == "room_not_available":
            raise HTTPException(status_code=409, detail="Room is not available for selected dates")
        raise HTTPException(status_code=400, detail="Cannot update booking")
    return booking

@app.delete("/api/v1/bookings/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_booking(booking_id: UUID, _: str = Depends(require_auth), db: Session = Depends(get_db)):
    ok = crud.delete_booking(db, booking_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Booking not found")
    return None
