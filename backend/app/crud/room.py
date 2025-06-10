from sqlalchemy.orm import Session
from app import models, schemas
from datetime import datetime

def create_room(db: Session, room_data: dict):
    """Create a new room."""
    db_room = models.Room(
        name=room_data["name"],
        description=room_data["description"],
        max_occupancy=room_data["max_occupancy"],
        price_per_night=room_data["price_per_night"],
        room_type=room_data["room_type"]
    )
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room

def get_room(db: Session, room_id: int):
    """Get a room by ID."""
    return db.query(models.Room).filter(models.Room.id == room_id).first()

def get_rooms(db: Session, skip: int = 0, limit: int = 100):
    """Get all rooms."""
    return db.query(models.Room).offset(skip).limit(limit).all()

def update_room(db: Session, room_id: int, room_data: dict):
    """Update a room."""
    db_room = get_room(db, room_id)
    if db_room:
        for key, value in room_data.items():
            setattr(db_room, key, value)
        db.commit()
        db.refresh(db_room)
    return db_room

def delete_room(db: Session, room_id: int):
    """Delete a room."""
    db_room = get_room(db, room_id)
    if db_room:
        db.delete(db_room)
        db.commit()
    return db_room 