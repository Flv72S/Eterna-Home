"""add_resource_action_to_permissions

Revision ID: 841a10a7cafa
Revises: e2cbf4adb236
Create Date: 2025-07-03 11:14:12.547020

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '841a10a7cafa'
down_revision: Union[str, None] = 'e2cbf4adb236'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Aggiungi colonne nullable con default temporaneo
    op.add_column('permissions', sa.Column('resource', sa.String(), nullable=True))
    op.add_column('permissions', sa.Column('action', sa.String(), nullable=True))
    op.add_column('permissions', sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.true()))
    # 2. Aggiorna tutte le righe esistenti con valori di default
    op.execute("UPDATE permissions SET resource='generic', action='manage', is_active=TRUE WHERE resource IS NULL OR action IS NULL OR is_active IS NULL")
    # 3. Rendi le colonne NOT NULL
    op.alter_column('permissions', 'resource', nullable=False)
    op.alter_column('permissions', 'action', nullable=False)
    op.alter_column('permissions', 'is_active', nullable=False, server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('permissions', 'is_active')
    op.drop_column('permissions', 'action')
    op.drop_column('permissions', 'resource')
