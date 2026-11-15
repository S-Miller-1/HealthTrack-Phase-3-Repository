"""Dashboard logic uses existing Phase 3 fixtures and fictional records."""
from datetime import datetime, timezone, date
import pytest
from fastapi import HTTPException
from app.models import User, VitalSigns, ActivityData
from dashboard.monitor import classify, snapshot, allowed_patients

@pytest.mark.parametrize("reading,expected", [
    ((120, 78, 72), "normal"),
    ((150, 82, 80), "warning"),
    ((121, 95, 70), "warning"),
    ((185, 80, 80), "critical"),
    ((120, 80, 135), "critical"),
])
def test_alert_thresholds(reading, expected):
    assert classify(*reading) == expected

def test_snapshot_uses_persisted_values_and_history(demo):
    with demo["session"]() as db:
        pid = demo["patient_id"]
        db.add(VitalSigns(patient_id=pid, systolic=129, diastolic=83,
                          pulse=73, measured_at=datetime(2026, 10, 20, tzinfo=timezone.utc),source="manual"))
        db.add(VitalSigns(patient_id=pid, systolic=151, diastolic=94,
                          pulse=89, measured_at=datetime(2026, 10, 21, tzinfo=timezone.utc),source="manual"))
        db.add(ActivityData(patient_id=pid, steps=6234, active_minutes=41,activity_date=date(2026, 10, 21)))
        db.commit()
        user=db.get(User,demo["users"]["nurse"])
        data=snapshot(db,user,pid)
        assert data["severity"] == "warning"
        assert data["latest"]["systolic"] == 151
        assert data["activities"][0]["steps"] == 6234
        assert [r["pulse"] for r in data["vitals"]] == [73,89]

def test_only_assigned_patients_are_listed(demo):
    with demo["session"]() as db:
        nurse=db.get(User,demo["users"]["nurse"])
        assert [p.id for p in allowed_patients(db,nurse)] == [demo["patient_id"]]
        admin=db.get(User,demo["users"]["admin"])
        assert allowed_patients(db,admin) == []

def test_unauthorized_patient_snapshot_is_blocked(demo):
    with demo["session"]() as db:
        nurse=db.get(User,demo["users"]["nurse"])
        with pytest.raises(HTTPException) as e:
            snapshot(db,nurse,demo["other_id"])
        assert e.value.status_code == 403
