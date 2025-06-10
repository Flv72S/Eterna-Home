from sqlalchemy.orm import Session
from app.models.room import Room
from . import random_lower_string

def create_random_room(db: Session) -> Room:
    room_data = {
        "name": f"Test Room {random_lower_string()}",
        "description": f"A test room {random_lower_string()}",
        "max_occupancy": 4,
        "price_per_night": 100.00,
        "room_type": "standard"
    }
    room = Room(**room_data)
    db.add(room)
    db.commit()
    db.refresh(room)
    return room 