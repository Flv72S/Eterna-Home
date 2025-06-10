from sqlalchemy.orm import Session
from app.models.booking import Booking
from datetime import datetime, timedelta

def create_random_booking(db: Session, user_id: int, room_id: int) -> Booking:
    check_in_date = datetime.now()
    check_out_date = check_in_date + timedelta(days=4)
    booking_data = {
        "user_id": user_id,
        "room_id": room_id,
        "check_in_date": check_in_date,
        "check_out_date": check_out_date,
        "total_price": 400.00,
        "status": "confirmed"
    }
    booking = Booking(**booking_data)
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking 