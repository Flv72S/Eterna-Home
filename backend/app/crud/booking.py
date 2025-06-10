from sqlalchemy.orm import Session
from app import models, schemas
from datetime import datetime, date
from typing import List, Optional

def create_booking(db: Session, booking_data: dict):
    """Create a new booking."""
    db_booking = models.Booking(
        user_id=booking_data["user_id"],
        room_id=booking_data["room_id"],
        check_in_date=datetime.strptime(booking_data["check_in_date"], "%Y-%m-%d").date(),
        check_out_date=datetime.strptime(booking_data["check_out_date"], "%Y-%m-%d").date(),
        total_price=booking_data["total_price"],
        status=booking_data["status"]
    )
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking

def get_booking(db: Session, booking_id: int):
    """Get a booking by ID."""
    return db.query(models.Booking).filter(models.Booking.id == booking_id).first()

def get_bookings(db: Session, skip: int = 0, limit: int = 100):
    """Get all bookings."""
    return db.query(models.Booking).offset(skip).limit(limit).all()

def get_user_bookings(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """Get all bookings for a specific user."""
    return db.query(models.Booking).filter(models.Booking.user_id == user_id).offset(skip).limit(limit).all()

def get_room_bookings(db: Session, room_id: int, skip: int = 0, limit: int = 100):
    """Get all bookings for a specific room."""
    return db.query(models.Booking).filter(models.Booking.room_id == room_id).offset(skip).limit(limit).all()

def update_booking(db: Session, booking_id: int, booking_data: dict):
    """Update a booking."""
    db_booking = get_booking(db, booking_id)
    if db_booking:
        for key, value in booking_data.items():
            if key in ["check_in_date", "check_out_date"]:
                value = datetime.strptime(value, "%Y-%m-%d").date()
            setattr(db_booking, key, value)
        db.commit()
        db.refresh(db_booking)
    return db_booking

def delete_booking(db: Session, booking_id: int):
    """Delete a booking."""
    db_booking = get_booking(db, booking_id)
    if db_booking:
        db.delete(db_booking)
        db.commit()
    return db_booking

def check_room_availability(db: Session, room_id: int, check_in_date: date, check_out_date: date) -> bool:
    """Check if a room is available for the given dates."""
    conflicting_bookings = db.query(models.Booking).filter(
        models.Booking.room_id == room_id,
        models.Booking.status != "cancelled",
        (
            (models.Booking.check_in_date <= check_in_date) & (models.Booking.check_out_date > check_in_date) |
            (models.Booking.check_in_date < check_out_date) & (models.Booking.check_out_date >= check_out_date) |
            (models.Booking.check_in_date >= check_in_date) & (models.Booking.check_out_date <= check_out_date)
        )
    ).first()
    return conflicting_bookings is None

def get_available_rooms(db: Session, check_in_date: date, check_out_date: date, room_type: Optional[str] = None):
    """Get all available rooms for the given dates."""
    query = db.query(models.Room)
    if room_type:
        query = query.filter(models.Room.room_type == room_type)
    
    all_rooms = query.all()
    available_rooms = []
    
    for room in all_rooms:
        if check_room_availability(db, room.id, check_in_date, check_out_date):
            available_rooms.append(room)
    
    return available_rooms

def calculate_booking_price(room: models.Room, check_in_date: date, check_out_date: date) -> float:
    """Calculate the total price for a booking."""
    days = (check_out_date - check_in_date).days
    return room.price_per_night * days 