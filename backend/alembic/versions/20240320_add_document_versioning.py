"""add document versioning

Revision ID: 20240320_add_document_versioning
Revises: 20240319_initial
Create Date: 2024-03-20 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20240320_add_document_versioning'
down_revision: Union[str, None] = '20240319_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Creazione della tabella document_versions
    op.create_table(
        'document_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('user_id', postgresql.UUID(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('storage_path', sa.String(), nullable=False),
        sa.Column('change_description', sa.String(), nullable=True),
        sa.Column('previous_version_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['previous_version_id'], ['document_versions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_versions_id'), 'document_versions', ['id'], unique=False)
    
    # Aggiunta di un indice composto per document_id e version_number
    op.create_index(
        'ix_document_versions_document_version',
        'document_versions',
        ['document_id', 'version_number'],
        unique=True
    )

def downgrade() -> None:
    op.drop_index('ix_document_versions_document_version', table_name='document_versions')
    op.drop_index(op.f('ix_document_versions_id'), table_name='document_versions')
    op.drop_table('document_versions') 