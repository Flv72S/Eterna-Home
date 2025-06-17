"""merge_heads

Revision ID: 4fadb798b878
Revises: 20240321_rooms_bookings, 89f0f3e75e56
Create Date: 2025-06-14 22:08:38.474937

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4fadb798b878'
down_revision: Union[str, None] = ('20240321_rooms_bookings', '89f0f3e75e56')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
