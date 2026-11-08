"""Add day-level lookup index to support activity-date reporting.

Revision ID: 0002_activity_lookup
Revises: 0001_initial
"""
from alembic import op
revision = '0002_activity_lookup'
down_revision = '0001_initial'
branch_labels = None
depends_on = None

def upgrade():
    op.create_index('ix_activity_date', 'activity_data', ['activity_date'])

def downgrade():
    op.drop_index('ix_activity_date', table_name='activity_data')
