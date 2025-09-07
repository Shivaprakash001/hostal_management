"""Add new fields to Payment table

Revision ID: new_payment_fields
Revises: f6d7ff381f25
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = 'new_payment_fields'
down_revision = 'f6d7ff381f25'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to payments table
    op.add_column('payments', sa.Column('month', sa.Integer(), nullable=True))
    op.add_column('payments', sa.Column('year', sa.Integer(), nullable=True))
    op.add_column('payments', sa.Column('transaction_id', sa.String(length=50), nullable=True))
    op.add_column('payments', sa.Column('payment_method', sa.String(length=20), nullable=True))
    op.add_column('payments', sa.Column('receipt_generated', sa.Boolean(), nullable=True))
    
    # Set default values for existing records
    op.execute("UPDATE payments SET month = 1 WHERE month IS NULL")
    op.execute("UPDATE payments SET year = 2024 WHERE year IS NULL")
    op.execute("UPDATE payments SET payment_method = 'Cash' WHERE payment_method IS NULL")
    op.execute("UPDATE payments SET receipt_generated = 0 WHERE receipt_generated IS NULL")
    
    # Generate transaction IDs for existing records
    op.execute("""
        UPDATE payments 
        SET transaction_id = 'TXN_' || strftime('%Y%m%d_%H%M%S', 'now') || '_' || substr(hex(randomblob(4)), 1, 8)
        WHERE transaction_id IS NULL
    """)
    
    # Make columns not nullable after setting defaults
    op.alter_column('payments', 'month', nullable=False)
    op.alter_column('payments', 'year', nullable=False)
    op.alter_column('payments', 'transaction_id', nullable=False)
    op.alter_column('payments', 'payment_method', nullable=False)
    op.alter_column('payments', 'receipt_generated', nullable=False)
    
    # Add unique constraint on transaction_id
    op.create_unique_constraint('uq_payments_transaction_id', 'payments', ['transaction_id'])


def downgrade():
    # Remove unique constraint
    op.drop_constraint('uq_payments_transaction_id', 'payments', type_='unique')
    
    # Remove columns
    op.drop_column('payments', 'receipt_generated')
    op.drop_column('payments', 'payment_method')
    op.drop_column('payments', 'transaction_id')
    op.drop_column('payments', 'year')
    op.drop_column('payments', 'month')
