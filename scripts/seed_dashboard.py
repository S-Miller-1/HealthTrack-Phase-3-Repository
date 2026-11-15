"""Add fictional reading history for Dashboard Development screenshots."""
from datetime import datetime, timedelta, timezone, date
from app.database import SessionLocal
from app.models import Patient, VitalSigns, ActivityData

with SessionLocal() as db:
    patient = db.query(Patient).filter_by(full_name="Sample Patient").first()
    if patient is None:
        raise SystemExit("Seed Phase 3 accounts first: python -m scripts.seed_demo")
    if db.query(VitalSigns).filter_by(patient_id=patient.id).count():
        raise SystemExit("Readings already exist; skipping to avoid duplicates.")
    now = datetime.now(timezone.utc).replace(microsecond=0)
    series = [(122,80,70),(125,82,73),(129,84,74),(127,81,70),
              (131,85,78),(135,87,80),(139,88,82),(145,92,89),
              (137,86,77),(133,84,76),(128,82,72),(151,94,91)]
    for i,(sys,dia,pulse) in enumerate(series):
        db.add(VitalSigns(patient_id=patient.id,systolic=sys,diastolic=dia,
                          pulse=pulse,source="manual",
                          measured_at=now-timedelta(hours=2*(len(series)-i))))
    for d in range(7):
        day=date.today()-timedelta(days=6-d)
        if not db.query(ActivityData).filter_by(patient_id=patient.id,activity_date=day).first():
            db.add(ActivityData(patient_id=patient.id,activity_date=day,
                                steps=3600+d*740,active_minutes=20+d*6))
    db.commit()
    print("Fictional dashboard readings and activity added. Not for clinical use.")
