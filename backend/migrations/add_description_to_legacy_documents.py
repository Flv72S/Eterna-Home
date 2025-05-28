"""add description to legacy documents

Revision ID: add_description_to_legacy_documents
Revises: 
Create Date: 2024-05-28 03:45:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_description_to_legacy_documents'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('legacy_documents', sa.Column('description', sa.String(), nullable=True))

def downgrade():
    op.drop_column('legacy_documents', 'description') 