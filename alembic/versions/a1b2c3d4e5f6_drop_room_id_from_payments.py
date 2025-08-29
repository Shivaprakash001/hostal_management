"""
drop room_id from payments

Revision ID: a1b2c3d4e5f6
Revises: f6d7ff381f25
Create Date: 2025-08-20
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'f6d7ff381f25'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Use batch operations for SQLite compatibility
    with op.batch_alter_table('payments', schema=None) as batch_op:
        # Drop the room_id column; data in other columns is preserved
        batch_op.drop_column('room_id')


def downgrade() -> None:
    # Recreate the column and FK on downgrade
    with op.batch_alter_table('payments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('room_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_payments_room_id_rooms',
            'rooms',
            ['room_id'],
            ['id']
        )


