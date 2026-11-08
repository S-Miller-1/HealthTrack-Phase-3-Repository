import pytest
from datetime import date, datetime, timezone, timedelta
from sqlalchemy.exc import IntegrityError
from pydantic import ValidationError
from app.models import Patient, VitalSigns, ActivityData, PatientAssignment
from app.schemas import PatientCreate, VitalCreate, ActivityCreate

def test_underage_rejected():
    with pytest.raises(ValidationError):
        PatientCreate(full_name='Junior', date_of_birth=date.today())

def test_invalid_pressure_order():
    with pytest.raises(ValidationError):
        VitalCreate(systolic=100, diastolic=120, pulse=65, measured_at=datetime.now(timezone.utc))

def test_future_reading_rejected():
    with pytest.raises(ValidationError):
        VitalCreate(systolic=120, diastolic=80, pulse=65,
                    measured_at=datetime.now(timezone.utc) + timedelta(hours=1))

def test_missing_timezone_rejected():
    with pytest.raises(ValidationError):
        VitalCreate(systolic=120, diastolic=80, pulse=65, measured_at=datetime.now())

def test_invalid_activity_rejected():
    with pytest.raises(ValidationError):
        ActivityCreate(steps=-1, active_minutes=10, activity_date=date.today())

def test_future_activity_rejected():
    with pytest.raises(ValidationError):
        ActivityCreate(steps=10, active_minutes=10, activity_date=date.today() + timedelta(days=1))

def test_database_pressure_check(demo):
    with demo['session']() as db:
        db.add(VitalSigns(patient_id=demo['patient_id'], systolic=75, diastolic=90, pulse=65,
                          measured_at=datetime.now(timezone.utc)))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

def test_database_activity_uniqueness(demo):
    with demo['session']() as db:
        a = ActivityData(patient_id=demo['patient_id'], steps=100, active_minutes=3, activity_date=date.today())
        b = ActivityData(patient_id=demo['patient_id'], steps=200, active_minutes=4, activity_date=date.today())
        db.add_all([a, b])
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

def test_database_foreign_key(demo):
    with demo['session']() as db:
        db.add(ActivityData(patient_id=999999, steps=100, active_minutes=20, activity_date=date.today()))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

def test_cascade_patient_records(demo):
    with demo['session']() as db:
        db.add(ActivityData(patient_id=demo['patient_id'], steps=100, active_minutes=20, activity_date=date.today()))
        db.commit()
        db.delete(db.get(Patient, demo['patient_id']))
        db.commit()
        assert db.query(ActivityData).filter_by(patient_id=demo['patient_id']).count() == 0

def test_duplicate_assignment(demo):
    with demo['session']() as db:
        db.add(PatientAssignment(staff_user_id=demo['users']['nurse'], patient_id=demo['patient_id']))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
