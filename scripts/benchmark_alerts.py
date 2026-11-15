"""Reproducible synthetic alert-evaluation microbenchmark (not an HTTP load test)."""
from datetime import date, datetime, timezone, timedelta
import json
import statistics
import time
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from app.database import Base
from app.models import Patient, User, PatientAssignment, VitalSigns
from app.security import hash_password
from app.alerts import Alert, AlertNotification, evaluate_vital

def run():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    @event.listens_for(engine, "connect")
    def fk(conn, _):
        conn.execute("PRAGMA foreign_keys=ON")
    Base.metadata.create_all(engine)
    readings = 500
    times = []
    with Session(engine) as db:
        nurse = User(username="benchmark_nurse", role="nurse", password_hash=hash_password("SyntheticExamplePassword!"))
        patient = Patient(full_name="Synthetic Patient", date_of_birth=date(1980, 1, 1), monitoring_consent=True)
        db.add_all([nurse, patient])
        db.flush()
        db.add(PatientAssignment(staff_user_id=nurse.id, patient_id=patient.id))
        db.commit()
        base = datetime.now(timezone.utc) - timedelta(hours=10)
        for i in range(readings):
            reading = VitalSigns(patient_id=patient.id,
                systolic=185 if i % 5 == 0 else 121, diastolic=121 if i % 5 == 0 else 79,
                pulse=70, measured_at=base + timedelta(minutes=i), source="manual")
            start = time.perf_counter()
            db.add(reading)
            db.flush()
            evaluate_vital(db, reading)
            db.commit()
            times.append((time.perf_counter() - start) * 1000)
        ordered = sorted(times)
        result = {
            "description": "Synthetic SQLite single-process database insert, evaluation and commit; not HTTP throughput",
            "readings": readings,
            "alerts": db.query(Alert).count(),
            "notifications": db.query(AlertNotification).count(),
            "median_ms": round(statistics.median(times), 3),
            "p95_ms": round(ordered[max(0, int(len(ordered) * .95) - 1)], 3),
            "max_ms": round(max(times), 3),
            "environment": "Local SQLite, single-threaded synthetic test; fictional records only"
        }
        print(json.dumps(result, indent=2))
    engine.dispose()

if __name__ == "__main__":
    run()
