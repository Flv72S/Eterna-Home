"""Add description to legacy_documents

Revision ID: add_description_to_legacy_documents
Revises: 
Create Date: 2023-10-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_description_to_legacy_documents'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('legacy_documents', sa.Column('description', sa.String(), nullable=True))

def downgrade() -> None:
    op.drop_column('legacy_documents', 'description') 