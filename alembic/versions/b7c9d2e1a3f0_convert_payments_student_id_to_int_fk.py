"""
convert payments.student_id from str to int FK to students.id

Revision ID: b7c9d2e1a3f0
Revises: a1b2c3d4e5f6
Create Date: 2025-08-20
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7c9d2e1a3f0'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) Add a temporary integer column
    with op.batch_alter_table('payments') as batch_op:
        batch_op.add_column(sa.Column('student_id_int', sa.Integer(), nullable=True))

    # 2) Backfill: map existing payments.student_id (string) to students.id
    conn = op.get_bind()
    conn.execute(sa.text(
        """
        UPDATE payments
        SET student_id_int = (
            SELECT s.id FROM students s WHERE CAST(s.student_id AS TEXT) = payments.student_id
        )
        """
    ))

    # 3) Drop old column and rename new one to student_id
    with op.batch_alter_table('payments') as batch_op:
        batch_op.drop_column('student_id')
        batch_op.alter_column('student_id_int', new_column_name='student_id', existing_type=sa.Integer(), nullable=True)

    # 4) Add FK constraint
    with op.batch_alter_table('payments') as batch_op:
        batch_op.create_foreign_key('fk_payments_student_id_students', 'students', ['student_id'], ['id'])


def downgrade() -> None:
    # Reverse: convert back to string student_id referencing students.student_id
    with op.batch_alter_table('payments') as batch_op:
        batch_op.add_column(sa.Column('student_id_str', sa.String(), nullable=True))

    conn = op.get_bind()
    conn.execute(sa.text(
        """
        UPDATE payments
        SET student_id_str = (
            SELECT s.student_id FROM students s WHERE s.id = payments.student_id
        )
        """
    ))

    with op.batch_alter_table('payments') as batch_op:
        batch_op.drop_constraint('fk_payments_student_id_students', type_='foreignkey')
        batch_op.drop_column('student_id')
        batch_op.alter_column('student_id_str', new_column_name='student_id', existing_type=sa.String(), nullable=True)


