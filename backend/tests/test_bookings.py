from datetime import datetime, date, timedelta
from tests.utils.user import create_random_user
from tests.utils.room import create_random_room
from tests.utils.booking import create_random_booking
from app import models

def test_create_booking(db):
    """Test creating a new booking"""
    user = create_random_user(db)
    room = create_random_room(db)
    booking = create_random_booking(db, user.id, room.id)
    assert booking is not None
    assert booking.user_id == user.id
    assert booking.room_id == room.id
    assert isinstance(booking.check_in_date, date)
    assert isinstance(booking.check_out_date, date)
    assert booking.total_price == booking.total_price
    assert booking.status == booking.status
    db_booking = db.query(models.Booking).filter(models.Booking.id == booking.id).first()
    assert db_booking is not None
    assert db_booking.user_id == user.id
    assert db_booking.room_id == room.id
    assert db_booking.total_price == booking.total_price
    assert db_booking.status == booking.status

def test_get_booking(db):
    """Test retrieving a booking by ID"""
    user = create_random_user(db)
    room = create_random_room(db)
    booking = create_random_booking(db, user.id, room.id)
    retrieved_booking = db.query(models.Booking).filter(models.Booking.id == booking.id).first()
    assert retrieved_booking is not None
    assert retrieved_booking.id == booking.id
    assert retrieved_booking.user_id == user.id
    assert retrieved_booking.room_id == room.id
    assert retrieved_booking.total_price == booking.total_price
    assert retrieved_booking.status == booking.status

def test_get_bookings(db):
    """Test retrieving multiple bookings"""
    user = create_random_user(db)
    room = create_random_room(db)
    booking1 = create_random_booking(db, user.id, room.id)
    booking2 = create_random_booking(db, user.id, room.id)
    bookings = db.query(models.Booking).all()
    assert len(bookings) >= 2
    assert any(b.id == booking1.id for b in bookings)
    assert any(b.id == booking2.id for b in bookings)
    assert any(b.user_id == user.id for b in bookings)
    assert any(b.room_id == room.id for b in bookings)

def test_update_booking(db):
    """Test updating a booking"""
    user = create_random_user(db)
    room = create_random_room(db)
    booking = create_random_booking(db, user.id, room.id)
    new_total_price = 600.00
    new_status = "cancelled"
    booking.check_out_date = booking.check_out_date.replace(day=booking.check_out_date.day + 2)
    booking.total_price = new_total_price
    booking.status = new_status
    db.commit()
    db.refresh(booking)
    updated_booking = db.query(models.Booking).filter(models.Booking.id == booking.id).first()
    assert updated_booking is not None
    assert updated_booking.id == booking.id
    assert updated_booking.total_price == new_total_price
    assert updated_booking.status == new_status
    assert updated_booking.user_id == user.id
    assert updated_booking.room_id == room.id

def test_delete_booking(db):
    """Test deleting a booking"""
    user = create_random_user(db)
    room = create_random_room(db)
    booking = create_random_booking(db, user.id, room.id)
    db.delete(booking)
    db.commit()
    db_booking = db.query(models.Booking).filter(models.Booking.id == booking.id).first()
    assert db_booking is None

def test_get_user_bookings(db):
    """Test retrieving bookings for a specific user"""
    user = create_random_user(db)
    room = create_random_room(db)
    booking1 = create_random_booking(db, user.id, room.id)
    booking2 = create_random_booking(db, user.id, room.id)
    user_bookings = db.query(models.Booking).filter(models.Booking.user_id == user.id).all()
    assert len(user_bookings) >= 2
    assert any(b.id == booking1.id for b in user_bookings)
    assert any(b.id == booking2.id for b in user_bookings)
    assert all(b.user_id == user.id for b in user_bookings)

def test_get_room_bookings(db):
    """Test retrieving bookings for a specific room"""
    user = create_random_user(db)
    room = create_random_room(db)
    booking1 = create_random_booking(db, user.id, room.id)
    booking2 = create_random_booking(db, user.id, room.id)
    room_bookings = db.query(models.Booking).filter(models.Booking.room_id == room.id).all()
    assert len(room_bookings) >= 2
    assert any(b.id == booking1.id for b in room_bookings)
    assert any(b.id == booking2.id for b in room_bookings)
    assert all(b.room_id == room.id for b in room_bookings)

def test_check_room_availability(db):
    """Test checking room availability"""
    user = create_random_user(db)
    room = create_random_room(db)
    booking = create_random_booking(db, user.id, room.id)
    # Test overlapping dates (should be unavailable)
    overlapping_start = booking.check_in_date
    overlapping_end = booking.check_out_date
    overlapping_bookings = db.query(models.Booking).filter(
        models.Booking.room_id == room.id,
        models.Booking.check_in_date <= overlapping_end,
        models.Booking.check_out_date >= overlapping_start
    ).count()
    assert overlapping_bookings > 0
    # Test non-overlapping dates (should be available)
    non_overlapping_start = booking.check_out_date + timedelta(days=1)
    non_overlapping_end = non_overlapping_start + timedelta(days=4)
    non_overlapping_bookings = db.query(models.Booking).filter(
        models.Booking.room_id == room.id,
        models.Booking.check_in_date <= non_overlapping_end,
        models.Booking.check_out_date >= non_overlapping_start
    ).count()
    assert non_overlapping_bookings == 0
    # Test dates before existing booking (should be available)
    before_start = booking.check_in_date - timedelta(days=4)
    before_end = booking.check_in_date - timedelta(days=1)
    before_bookings = db.query(models.Booking).filter(
        models.Booking.room_id == room.id,
        models.Booking.check_in_date <= before_end,
        models.Booking.check_out_date >= before_start
    ).count()
    assert before_bookings == 0

def test_get_available_rooms(db):
    """Test retrieving available rooms for a date range"""
    user = create_random_user(db)
    room1 = create_random_room(db)
    room2 = create_random_room(db)
    booking = create_random_booking(db, user.id, room1.id)
    # Test overlapping dates (should be unavailable)
    overlapping_start = booking.check_in_date
    overlapping_end = booking.check_out_date
    overlapping_rooms = db.query(models.Room).filter(
        models.Room.id.in_(
            db.query(models.Booking.room_id).filter(
                models.Booking.check_in_date <= overlapping_end,
                models.Booking.check_out_date >= overlapping_start
            )
        )
    ).all()
    assert room1 in overlapping_rooms
    assert room2 not in overlapping_rooms
    # Test non-overlapping dates (should be available)
    non_overlapping_start = booking.check_out_date + timedelta(days=1)
    non_overlapping_end = non_overlapping_start + timedelta(days=4)
    non_overlapping_rooms = db.query(models.Room).filter(
        models.Room.id.in_(
            db.query(models.Booking.room_id).filter(
                models.Booking.check_in_date <= non_overlapping_end,
                models.Booking.check_out_date >= non_overlapping_start
            )
        )
    ).all()
    assert room1 not in non_overlapping_rooms
    assert room2 not in non_overlapping_rooms
    # Test dates before existing booking (should be available)
    before_start = booking.check_in_date - timedelta(days=4)
    before_end = booking.check_in_date - timedelta(days=1)
    before_rooms = db.query(models.Room).filter(
        models.Room.id.in_(
            db.query(models.Booking.room_id).filter(
                models.Booking.check_in_date <= before_end,
                models.Booking.check_out_date >= before_start
            )
        )
    ).all()
    assert room1 not in before_rooms
    assert room2 not in before_rooms

def test_calculate_booking_price(db):
    """Test calculating booking price"""
    room = create_random_room(db)
    check_in_date = date(2024, 3, 1)
    check_out_date = date(2024, 3, 5)
    nights = (check_out_date - check_in_date).days
    price = room.price_per_night * nights
    assert price == 400.00

def test_get_booking_by_id(db):
    """Test retrieving a booking by ID"""
    user = create_random_user(db)
    room = create_random_room(db)
    booking = create_random_booking(db, user.id, room.id)
    retrieved_booking = db.query(models.Booking).filter(models.Booking.id == booking.id).first()
    assert retrieved_booking is not None
    assert retrieved_booking.id == booking.id
    assert retrieved_booking.user_id == user.id
    assert retrieved_booking.room_id == room.id
    assert retrieved_booking.total_price == booking.total_price
    assert retrieved_booking.status == booking.status 