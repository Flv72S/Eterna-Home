def test_create_room(db_session):
    """Test creating a new room"""
    # Create test room data
    room_data = {
        "name": "Test Room",
        "description": "A test room",
        "max_occupancy": 4,
        "price_per_night": 100.00,
        "room_type": "standard"
    }
    
    # Create room
    room = crud.create_room(db_session, room_data)
    
    # Verify room was created
    assert room is not None
    assert room.name == room_data["name"]
    assert room.description == room_data["description"]
    assert room.max_occupancy == room_data["max_occupancy"]
    assert room.price_per_night == room_data["price_per_night"]
    assert room.room_type == room_data["room_type"]
    
    # Verify room can be retrieved from database
    db_room = db_session.query(models.Room).filter(models.Room.name == room_data["name"]).first()
    assert db_room is not None
    assert db_room.name == room_data["name"]
    assert db_room.description == room_data["description"]
    assert db_room.max_occupancy == room_data["max_occupancy"]
    assert db_room.price_per_night == room_data["price_per_night"]
    assert db_room.room_type == room_data["room_type"]

def test_get_room(db_session):
    """Test retrieving a room by ID"""
    # Create test room
    room_data = {
        "name": "Test Room",
        "description": "A test room",
        "max_occupancy": 4,
        "price_per_night": 100.00,
        "room_type": "standard"
    }
    room = crud.create_room(db_session, room_data)
    
    # Get room by ID
    retrieved_room = crud.get_room(db_session, room.id)
    
    # Verify room was retrieved correctly
    assert retrieved_room is not None
    assert retrieved_room.id == room.id
    assert retrieved_room.name == room_data["name"]
    assert retrieved_room.description == room_data["description"]
    assert retrieved_room.max_occupancy == room_data["max_occupancy"]
    assert retrieved_room.price_per_night == room_data["price_per_night"]
    assert retrieved_room.room_type == room_data["room_type"] 

def test_get_rooms(db_session):
    """Test retrieving multiple rooms"""
    # Create test rooms
    rooms_data = [
        {
            "name": "Test Room 1",
            "description": "A test room 1",
            "max_occupancy": 4,
            "price_per_night": 100.00,
            "room_type": "standard"
        },
        {
            "name": "Test Room 2",
            "description": "A test room 2",
            "max_occupancy": 2,
            "price_per_night": 80.00,
            "room_type": "deluxe"
        }
    ]
    
    created_rooms = []
    for room_data in rooms_data:
        room = crud.create_room(db_session, room_data)
        created_rooms.append(room)
    
    # Get all rooms
    rooms = crud.get_rooms(db_session)
    
    # Verify rooms were retrieved correctly
    assert len(rooms) >= len(created_rooms)  # There might be other rooms in the database
    for created_room in created_rooms:
        assert any(r.id == created_room.id for r in rooms)
        assert any(r.name == created_room.name for r in rooms)
        assert any(r.description == created_room.description for r in rooms)

def test_update_room(db_session):
    """Test updating a room"""
    # Create test room
    room_data = {
        "name": "Test Room",
        "description": "A test room",
        "max_occupancy": 4,
        "price_per_night": 100.00,
        "room_type": "standard"
    }
    room = crud.create_room(db_session, room_data)
    
    # Update room data
    update_data = {
        "name": "Updated Room",
        "description": "An updated room",
        "price_per_night": 120.00
    }
    
    # Update room
    updated_room = crud.update_room(db_session, room.id, update_data)
    
    # Verify room was updated correctly
    assert updated_room is not None
    assert updated_room.id == room.id
    assert updated_room.name == update_data["name"]
    assert updated_room.description == update_data["description"]
    assert updated_room.price_per_night == update_data["price_per_night"]
    assert updated_room.max_occupancy == room_data["max_occupancy"]  # Unchanged
    assert updated_room.room_type == room_data["room_type"]  # Unchanged
    
    # Verify changes are in database
    db_room = db_session.query(models.Room).filter(models.Room.id == room.id).first()
    assert db_room is not None
    assert db_room.name == update_data["name"]
    assert db_room.description == update_data["description"]
    assert db_room.price_per_night == update_data["price_per_night"]

def test_delete_room(db_session):
    """Test deleting a room"""
    # Create test room
    room_data = {
        "name": "Test Room",
        "description": "A test room",
        "max_occupancy": 4,
        "price_per_night": 100.00,
        "room_type": "standard"
    }
    room = crud.create_room(db_session, room_data)
    
    # Delete room
    deleted_room = crud.delete_room(db_session, room.id)
    
    # Verify room was deleted correctly
    assert deleted_room is not None
    assert deleted_room.id == room.id
    
    # Verify room no longer exists in database
    db_room = db_session.query(models.Room).filter(models.Room.id == room.id).first()
    assert db_room is None 