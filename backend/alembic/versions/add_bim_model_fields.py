"""add missing fields to bim_models table

Revision ID: add_bim_model_fields
Revises: fd481594b0c3
Create Date: 2025-01-27 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_bim_model_fields'
down_revision: Union[str, None] = 'fd481594b0c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add missing fields to bim_models table
    op.add_column('bim_models', sa.Column('user_id', sa.Integer(), nullable=True))
    op.add_column('bim_models', sa.Column('house_id', sa.Integer(), nullable=True))
    op.add_column('bim_models', sa.Column('created_at', sa.DateTime(), nullable=True))
    op.add_column('bim_models', sa.Column('updated_at', sa.DateTime(), nullable=True))
    
    # Add foreign key constraints
    op.create_foreign_key('fk_bim_models_user_id', 'bim_models', 'users', ['user_id'], ['id'])
    op.create_foreign_key('fk_bim_models_house_id', 'bim_models', 'houses', ['house_id'], ['id'])
    
    # Create indexes for the new fields
    op.create_index(op.f('ix_bim_models_user_id'), 'bim_models', ['user_id'], unique=False)
    op.create_index(op.f('ix_bim_models_house_id'), 'bim_models', ['house_id'], unique=False)
    op.create_index(op.f('ix_bim_models_created_at'), 'bim_models', ['created_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index(op.f('ix_bim_models_created_at'), table_name='bim_models')
    op.drop_index(op.f('ix_bim_models_house_id'), table_name='bim_models')
    op.drop_index(op.f('ix_bim_models_user_id'), table_name='bim_models')
    
    # Drop foreign key constraints
    op.drop_constraint('fk_bim_models_house_id', 'bim_models', type_='foreignkey')
    op.drop_constraint('fk_bim_models_user_id', 'bim_models', type_='foreignkey')
    
    # Drop columns
    op.drop_column('bim_models', 'updated_at')
    op.drop_column('bim_models', 'created_at')
    op.drop_column('bim_models', 'house_id')
    op.drop_column('bim_models', 'user_id') 