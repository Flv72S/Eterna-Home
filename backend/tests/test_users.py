def test_create_user(db_session):
    """Test creating a new user"""
    # Create test user data
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    
    # Create user
    user = crud.create_user(db_session, user_data)
    
    # Verify user was created
    assert user is not None
    assert user.email == user_data["email"]
    assert user.full_name == user_data["full_name"]
    assert user.hashed_password != user_data["password"]  # Password should be hashed
    
    # Verify user can be retrieved from database
    db_user = db_session.query(models.User).filter(models.User.email == user_data["email"]).first()
    assert db_user is not None
    assert db_user.email == user_data["email"]
    assert db_user.full_name == user_data["full_name"]

def test_get_user(db_session):
    """Test retrieving a user by ID"""
    # Create test user
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    user = crud.create_user(db_session, user_data)
    
    # Get user by ID
    retrieved_user = crud.get_user(db_session, user.id)
    
    # Verify user was retrieved correctly
    assert retrieved_user is not None
    assert retrieved_user.id == user.id
    assert retrieved_user.email == user_data["email"]
    assert retrieved_user.full_name == user_data["full_name"]

def test_get_user_by_email(db_session):
    """Test retrieving a user by email"""
    # Create test user
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    user = crud.create_user(db_session, user_data)
    
    # Get user by email
    retrieved_user = crud.get_user_by_email(db_session, user_data["email"])
    
    # Verify user was retrieved correctly
    assert retrieved_user is not None
    assert retrieved_user.id == user.id
    assert retrieved_user.email == user_data["email"]
    assert retrieved_user.full_name == user_data["full_name"]

def test_authenticate_user(db_session):
    """Test user authentication"""
    # Create test user
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    user = crud.create_user(db_session, user_data)
    
    # Test correct credentials
    authenticated_user = crud.authenticate_user(
        db_session, user_data["email"], user_data["password"]
    )
    assert authenticated_user is not None
    assert authenticated_user.id == user.id
    
    # Test incorrect password
    wrong_user = crud.authenticate_user(
        db_session, user_data["email"], "wrongpassword"
    )
    assert wrong_user is None
    
    # Test non-existent user
    nonexistent_user = crud.authenticate_user(
        db_session, "nonexistent@example.com", "anypassword"
    )
    assert nonexistent_user is None

def test_get_users(db_session):
    """Test retrieving multiple users"""
    # Create test users
    users_data = [
        {
            "email": "test1@example.com",
            "password": "testpassword123",
            "full_name": "Test User 1"
        },
        {
            "email": "test2@example.com",
            "password": "testpassword123",
            "full_name": "Test User 2"
        }
    ]
    
    created_users = []
    for user_data in users_data:
        user = crud.create_user(db_session, user_data)
        created_users.append(user)
    
    # Get all users
    users = crud.get_users(db_session)
    
    # Verify users were retrieved correctly
    assert len(users) >= len(created_users)  # There might be other users in the database
    for created_user in created_users:
        assert any(u.id == created_user.id for u in users)
        assert any(u.email == created_user.email for u in users)
        assert any(u.full_name == created_user.full_name for u in users)

def test_update_user(db_session):
    """Test updating a user"""
    # Create test user
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    user = crud.create_user(db_session, user_data)
    
    # Update user data
    update_data = {
        "full_name": "Updated User",
        "email": "updated@example.com"
    }
    
    # Update user
    updated_user = crud.update_user(db_session, user.id, update_data)
    
    # Verify user was updated correctly
    assert updated_user is not None
    assert updated_user.id == user.id
    assert updated_user.email == update_data["email"]
    assert updated_user.full_name == update_data["full_name"]
    
    # Verify changes are in database
    db_user = db_session.query(models.User).filter(models.User.id == user.id).first()
    assert db_user is not None
    assert db_user.email == update_data["email"]
    assert db_user.full_name == update_data["full_name"]

def test_delete_user(db_session):
    """Test deleting a user"""
    # Create test user
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    user = crud.create_user(db_session, user_data)
    
    # Delete user
    deleted_user = crud.delete_user(db_session, user.id)
    
    # Verify user was deleted correctly
    assert deleted_user is not None
    assert deleted_user.id == user.id
    
    # Verify user no longer exists in database
    db_user = db_session.query(models.User).filter(models.User.id == user.id).first()
    assert db_user is None 