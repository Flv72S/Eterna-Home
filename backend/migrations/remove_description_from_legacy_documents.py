"""remove description from legacy documents

Revision ID: remove_description_from_legacy_documents
Revises: add_description_to_legacy_documents
Create Date: 2024-05-28 03:55:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'remove_description_from_legacy_documents'
down_revision = 'add_description_to_legacy_documents'
branch_labels = None
depends_on = None

def upgrade():
    op.drop_column('legacy_documents', 'description')

def downgrade():
    op.add_column('legacy_documents', sa.Column('description', sa.String(), nullable=True)) 