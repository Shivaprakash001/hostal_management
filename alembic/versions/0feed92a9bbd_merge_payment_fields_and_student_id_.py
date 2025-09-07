"""merge payment fields and student id conversion

Revision ID: 0feed92a9bbd
Revises: b7c9d2e1a3f0, new_payment_fields
Create Date: 2025-08-29 22:07:47.903739

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0feed92a9bbd'
down_revision: Union[str, Sequence[str], None] = ('b7c9d2e1a3f0', 'new_payment_fields')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
