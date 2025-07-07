"""make bim fields nullable

Revision ID: make_bim_fields_nullable
Revises: add_bim_model_fields
Create Date: 2025-01-27 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'make_bim_fields_nullable'
down_revision: Union[str, None] = 'add_bim_model_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Make software_origin and level_of_detail nullable in bim_models table
    op.alter_column('bim_models', 'software_origin',
                    existing_type=postgresql.ENUM('REVIT', 'ARCHICAD', 'ALLPLAN', 'TEKLA', 'VECTORWORKS', 'SKETCHUP', 'OTHER', name='bimsoftware'),
                    nullable=True)
    op.alter_column('bim_models', 'level_of_detail',
                    existing_type=postgresql.ENUM('LOD_100', 'LOD_200', 'LOD_300', 'LOD_400', 'LOD_500', name='bimlevelofdetail'),
                    nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Make software_origin and level_of_detail NOT NULL again
    op.alter_column('bim_models', 'software_origin',
                    existing_type=postgresql.ENUM('REVIT', 'ARCHICAD', 'ALLPLAN', 'TEKLA', 'VECTORWORKS', 'SKETCHUP', 'OTHER', name='bimsoftware'),
                    nullable=False)
    op.alter_column('bim_models', 'level_of_detail',
                    existing_type=postgresql.ENUM('LOD_100', 'LOD_200', 'LOD_300', 'LOD_400', 'LOD_500', name='bimlevelofdetail'),
                    nullable=False) 