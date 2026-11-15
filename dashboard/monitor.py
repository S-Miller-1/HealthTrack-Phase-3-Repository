"""Shared, testable data queries and illustrative alert logic."""
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models import Patient, VitalSigns, ActivityData
from app.security import require_patient_access

# Illustrative demonstration thresholds, NOT clinical decision rules.
def classify(systolic, diastolic, pulse):
    if systolic >= 180 or diastolic >= 120 or pulse < 45 or pulse > 130:
        return "critical"
    if systolic >= 140 or diastolic >= 90 or pulse < 55 or pulse > 105:
        return "warning"
    return "normal"

def allowed_patients(db: Session, user):
    if user.role == "admin":
        return []
    if user.role == "patient":
        return db.query(Patient).filter(Patient.user_id == user.id).order_by(Patient.id).all()
    from app.models import PatientAssignment
    ids = db.query(PatientAssignment.patient_id).filter(PatientAssignment.staff_user_id == user.id)
    return db.query(Patient).filter(Patient.id.in_(ids)).order_by(Patient.id).all()

def snapshot(db: Session, user, patient_id: int) -> dict:
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise ValueError("Patient not found")
    require_patient_access(db, user, patient)
    # Most recent readings by time, then reverse for correctly ordered trend plots.
    vitals = list(reversed(db.query(VitalSigns).filter_by(patient_id=patient_id)
                           .order_by(VitalSigns.measured_at.desc(), VitalSigns.id.desc())
                           .limit(60).all()))
    activities = list(reversed(db.query(ActivityData).filter_by(patient_id=patient_id)
                              .order_by(ActivityData.activity_date.desc()).limit(14).all()))
    last = vitals[-1] if vitals else None
    severity = classify(last.systolic, last.diastolic, last.pulse) if last else "unknown"
    return {
        "patient_id": patient.id,
        "patient_name": patient.full_name,
        "enrolled": patient.enrolled,
        "consent": patient.monitoring_consent,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "severity": severity,
        "latest": ({"systolic": last.systolic, "diastolic": last.diastolic, "pulse": last.pulse,
                    "measured_at": last.measured_at.isoformat()} if last else None),
        "vitals": [{"systolic": v.systolic, "diastolic": v.diastolic, "pulse": v.pulse,
                    "measured_at": v.measured_at.isoformat()} for v in vitals],
        "activities": [{"date": a.activity_date.isoformat(), "steps": a.steps,
                        "active_minutes": a.active_minutes} for a in activities],
    }
