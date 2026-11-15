"""Create user, patient, assignment, vital, activity and audit tables.

Revision ID: 0001_initial
Revises:
"""
from alembic import op
from app.database import Base
from app import models  # noqa: F401
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Uses shared SQLAlchemy metadata, retaining named CHECK/FK/unique constraints.
    Base.metadata.create_all(bind=op.get_bind(), tables=[Base.metadata.tables[name] for name in ('users', 'patients', 'patient_assignments', 'vital_signs', 'activity_data', 'audit_events')])

def downgrade():
    Base.metadata.drop_all(bind=op.get_bind(), tables=[Base.metadata.tables[name] for name in ('users', 'patients', 'patient_assignments', 'vital_signs', 'activity_data', 'audit_events')])
