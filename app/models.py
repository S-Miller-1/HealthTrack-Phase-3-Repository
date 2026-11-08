"""Normalized Phase 3 entities and supporting access-control tables."""
from datetime import datetime, timezone
from sqlalchemy import (String, Integer, Float, DateTime, Date, ForeignKey, Boolean,
                        CheckConstraint, UniqueConstraint, Index, Text)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

def utcnow():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(250), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    __table_args__ = (CheckConstraint("role IN ('admin','clinician','nurse','patient')", name='ck_user_role'),)

class Patient(Base):
    __tablename__ = 'patients'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), unique=True)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    date_of_birth: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    enrolled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    monitoring_consent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    vital_signs: Mapped[list['VitalSigns']] = relationship(back_populates='patient', cascade='all, delete-orphan')
    activities: Mapped[list['ActivityData']] = relationship(back_populates='patient', cascade='all, delete-orphan')

class PatientAssignment(Base):
    __tablename__ = 'patient_assignments'
    id: Mapped[int] = mapped_column(primary_key=True)
    staff_user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    patient_id: Mapped[int] = mapped_column(ForeignKey('patients.id', ondelete='CASCADE'), nullable=False)
    __table_args__ = (UniqueConstraint('staff_user_id', 'patient_id', name='uq_staff_patient'),
                      Index('ix_assignments_patient', 'patient_id'),)

class VitalSigns(Base):
    __tablename__ = 'vital_signs'
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey('patients.id', ondelete='CASCADE'), nullable=False)
    systolic: Mapped[int] = mapped_column(Integer, nullable=False)
    diastolic: Mapped[int] = mapped_column(Integer, nullable=False)
    pulse: Mapped[int] = mapped_column(Integer, nullable=False)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    source: Mapped[str] = mapped_column(String(20), default='manual', nullable=False)
    patient: Mapped[Patient] = relationship(back_populates='vital_signs')
    __table_args__ = (
        CheckConstraint('systolic BETWEEN 50 AND 300', name='ck_systolic_range'),
        CheckConstraint('diastolic BETWEEN 30 AND 200', name='ck_diastolic_range'),
        CheckConstraint('systolic > diastolic', name='ck_pressure_order'),
        CheckConstraint('pulse BETWEEN 30 AND 250', name='ck_pulse_range'),
        CheckConstraint("source IN ('manual','device')", name='ck_vital_source'),
        Index('ix_vital_patient_measured', 'patient_id', 'measured_at'),
    )

class ActivityData(Base):
    __tablename__ = 'activity_data'
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey('patients.id', ondelete='CASCADE'), nullable=False)
    steps: Mapped[int] = mapped_column(Integer, nullable=False)
    active_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    activity_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    patient: Mapped[Patient] = relationship(back_populates='activities')
    __table_args__ = (
        CheckConstraint('steps BETWEEN 0 AND 100000', name='ck_steps_range'),
        CheckConstraint('active_minutes BETWEEN 0 AND 1440', name='ck_active_minutes'),
        UniqueConstraint('patient_id', 'activity_date', name='uq_activity_patient_date'),
        Index('ix_activity_patient_date', 'patient_id', 'activity_date'),
    )

class AuditEvent(Base):
    __tablename__ = 'audit_events'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'))
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource: Mapped[str] = mapped_column(String(100), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(80), nullable=False)
