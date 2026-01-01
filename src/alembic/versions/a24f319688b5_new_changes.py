"""new changes

Revision ID: a24f319688b5
Revises: ff86b228ef66
Create Date: 2026-01-01 09:25:32.661901

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a24f319688b5'
down_revision: Union[str, Sequence[str], None] = 'ff86b228ef66'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
