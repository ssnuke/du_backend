"""init configs

Revision ID: ff86b228ef66
Revises: c43ce3811a90
Create Date: 2026-01-01 02:33:29.726270

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ff86b228ef66'
down_revision: Union[str, Sequence[str], None] = 'c43ce3811a90'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
