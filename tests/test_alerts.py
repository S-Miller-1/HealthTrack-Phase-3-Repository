"""Integration tests for the HealthTrack alert system using fictional patients."""
from datetime import datetime, timezone, date, timedelta
from app.alerts import Alert, AlertEvent, process_escalations

def vital(**changes):
    data = {"systolic": 185, "diastolic": 122, "pulse": 70,
            "measured_at": datetime.now(timezone.utc).isoformat(), "source": "manual"}
    data.update(changes)
    return data

def test_critical_vital_and_in_app_notification(demo, auth):
    client, pid = demo["client"], demo["patient_id"]
    response = client.post(f"/patients/{pid}/vitals", json=vital(), headers=auth("patient"))
    assert response.status_code == 201, response.text
    alerts = client.get(f"/patients/{pid}/alerts", headers=auth("nurse"))
    assert alerts.status_code == 200
    assert len(alerts.json()) == 1
    assert alerts.json()[0]["severity"] == "critical"
    assert len(client.get("/notifications", headers=auth("nurse")).json()) == 1
    assert client.get(f"/patients/{pid}/alerts", headers=auth("patient")).status_code == 403

def test_normal_value_and_custom_thresholds(demo, auth):
    client, pid = demo["client"], demo["patient_id"]
    assert client.post(f"/patients/{pid}/vitals", json=vital(systolic=120, diastolic=80), headers=auth("patient")).status_code == 201
    assert client.get(f"/patients/{pid}/alerts", headers=auth("nurse")).json() == []
    config = {"systolic_min": 90, "systolic_max": 125, "diastolic_min": 60,
              "diastolic_max": 89, "pulse_min": 50, "pulse_max": 100}
    assert client.put(f"/patients/{pid}/alert-config", json=config, headers=auth("patient")).status_code == 403
    assert client.put(f"/patients/{pid}/alert-config", json=config, headers=auth("nurse")).status_code == 200
    assert client.post(f"/patients/{pid}/vitals", json=vital(systolic=130, diastolic=80), headers=auth("patient")).status_code == 201
    assert client.get(f"/patients/{pid}/alerts", headers=auth("nurse")).json()[0]["severity"] == "high"

def test_acknowledge_resolve_and_history(demo, auth):
    client, pid = demo["client"], demo["patient_id"]
    client.post(f"/patients/{pid}/vitals", json=vital(), headers=auth("patient"))
    alert_id = client.get(f"/patients/{pid}/alerts", headers=auth("nurse")).json()[0]["id"]
    assert client.post(f"/alerts/{alert_id}/acknowledge", headers=auth("patient")).status_code == 403
    assert client.post(f"/alerts/{alert_id}/acknowledge", headers=auth("nurse")).json()["status"] == "acknowledged"
    assert client.post(f"/alerts/{alert_id}/resolve", headers=auth("nurse")).json()["status"] == "resolved"
    events = client.get(f"/alerts/{alert_id}/history", headers=auth("nurse")).json()
    assert [e["event"] for e in events] == ["created", "acknowledged", "resolved"]

def test_escalation_after_deadline(demo, auth):
    client, pid = demo["client"], demo["patient_id"]
    client.post(f"/patients/{pid}/vitals", json=vital(), headers=auth("patient"))
    with demo["session"]() as db:
        item = db.query(Alert).one()
        created = item.created_at.replace(tzinfo=timezone.utc) if item.created_at.tzinfo is None else item.created_at
        assert process_escalations(db, created + timedelta(minutes=16)) == 1
        assert process_escalations(db, created + timedelta(minutes=17)) == 0
        assert db.query(AlertEvent).filter_by(event="escalated").count() == 1

def test_patient_boundary(demo, auth):
    client = demo["client"]
    assert client.get(f"/patients/{demo['other_id']}/alerts", headers=auth("nurse")).status_code == 403

def test_activity_decline(demo, auth):
    client, pid = demo["client"], demo["patient_id"]
    first = date.today() - timedelta(days=9)
    for i in range(10):
        response = client.post(f"/patients/{pid}/activities", headers=auth("patient"),
                               json={"steps": 6000 if i < 7 else 1000,
                                     "active_minutes": 30 if i < 7 else 10,
                                     "activity_date": (first + timedelta(days=i)).isoformat()})
        assert response.status_code == 201, response.text
    alerts = client.get(f"/patients/{pid}/alerts", headers=auth("nurse")).json()
    assert any(item["rule"] == "activity_decline" for item in alerts)

def test_no_alerts_without_consent(demo, auth):
    from app.models import Patient
    client, pid = demo["client"], demo["patient_id"]
    with demo["session"]() as db:
        db.get(Patient, pid).monitoring_consent = False
        db.commit()
    assert client.post(f"/patients/{pid}/vitals", json=vital(), headers=auth("patient")).status_code == 403
    assert client.get(f"/patients/{pid}/alerts", headers=auth("nurse")).json() == []
