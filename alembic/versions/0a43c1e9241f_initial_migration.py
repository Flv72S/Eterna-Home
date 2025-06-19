import sqlalchemy as sa
# ... existing code ... 
sa.Column('email', sa.String(), nullable=False),
sa.Column('username', sa.String(), nullable=True),
sa.Column('hashed_password', sa.String(), nullable=False),
sa.Column('full_name', sa.String(), nullable=True),
sa.Column('phone_number', sa.String(), nullable=True),
# ... existing code ... 