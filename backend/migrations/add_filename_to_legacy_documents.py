"""add filename to legacy documents

Revision ID: add_filename_to_legacy_documents
Revises: remove_description_from_legacy_documents
Create Date: 2024-05-28 04:15:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_filename_to_legacy_documents'
down_revision = 'remove_description_from_legacy_documents'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('legacy_documents', sa.Column('filename', sa.String(), nullable=True))
    # Aggiorna i record esistenti con un valore di default
    op.execute("UPDATE legacy_documents SET filename = 'legacy_document' WHERE filename IS NULL")
    # Rendi la colonna non nullable
    op.alter_column('legacy_documents', 'filename', nullable=False)

def downgrade():
    op.drop_column('legacy_documents', 'filename') 