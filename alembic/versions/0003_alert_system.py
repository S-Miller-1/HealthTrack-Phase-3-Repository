"""Add alert configuration, history and notifications.

Revision ID: 0003_alert_system
Revises: 0002_activity_lookup
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_alert_system"
down_revision = "0002_activity_lookup"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("alert_configs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("patient_id", sa.Integer, sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("systolic_min", sa.Integer, nullable=False),
        sa.Column("systolic_max", sa.Integer, nullable=False),
        sa.Column("diastolic_min", sa.Integer, nullable=False),
        sa.Column("diastolic_max", sa.Integer, nullable=False),
        sa.Column("pulse_min", sa.Integer, nullable=False),
        sa.Column("pulse_max", sa.Integer, nullable=False))
    op.create_table("alerts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("patient_id", sa.Integer, sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rule", sa.String(60), nullable=False),
        sa.Column("severity", sa.String(12), nullable=False),
        sa.Column("message", sa.String(200), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("source_key", sa.String(120), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True)),
        sa.Column("acknowledged_by", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("resolved_by", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("escalated_at", sa.DateTime(timezone=True)))
    op.create_index("ix_alert_patient_created", "alerts", ["patient_id", "created_at"])
    op.create_table("alert_events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("alert_id", sa.Integer, sa.ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event", sa.String(30), nullable=False),
        sa.Column("actor_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("alert_notifications",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("alert_id", sa.Integer, sa.ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recipient_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("channel", sa.String(12), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))

def downgrade():
    op.drop_table("alert_notifications")
    op.drop_table("alert_events")
    op.drop_index("ix_alert_patient_created", table_name="alerts")
    op.drop_table("alerts")
    op.drop_table("alert_configs")
