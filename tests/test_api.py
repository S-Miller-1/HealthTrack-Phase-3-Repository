from datetime import date, datetime, timezone, timedelta
from app.models import Patient, AuditEvent

def vdata(**changes):
    payload = {'systolic': 121, 'diastolic': 78, 'pulse': 65,
               'measured_at': (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
               'source': 'manual'}
    payload.update(changes)
    return payload

def adata(**changes):
    payload = {'steps': 4400, 'active_minutes': 35, 'activity_date': date.today().isoformat()}
    payload.update(changes)
    return payload

def test_health(demo):
    assert demo['client'].get('/health').json()['status'] == 'ok'

def test_auth_required(demo):
    assert demo['client'].get('/patients').status_code == 401

def test_bad_login(demo):
    result = demo['client'].post('/auth/token', data={'username': 'patient', 'password': 'incorrect'})
    assert result.status_code == 401

def test_valid_login(demo):
    result = demo['client'].post('/auth/token', data={'username': 'patient', 'password': 'TestingPassword123!'})
    assert result.status_code == 200
    assert result.json()['access_token']

def test_admin_create_patient(demo, auth):
    payload = {'full_name': 'New Adult', 'date_of_birth': '1980-01-01', 'monitoring_consent': True}
    result = demo['client'].post('/patients', json=payload, headers=auth('admin'))
    assert result.status_code == 201
    assert result.json()['full_name'] == 'New Adult'

def test_non_admin_cannot_create_patient(demo, auth):
    payload = {'full_name': 'New Adult', 'date_of_birth': '1980-01-01'}
    assert demo['client'].post('/patients', json=payload, headers=auth('patient')).status_code == 403

def test_patient_list_scope(demo, auth):
    response = demo['client'].get('/patients', headers=auth('patient'))
    assert [x['id'] for x in response.json()] == [demo['patient_id']]

def test_staff_assignment_scope(demo, auth):
    assert demo['client'].get(f"/patients/{demo['patient_id']}", headers=auth('nurse')).status_code == 200
    assert demo['client'].get(f"/patients/{demo['other_id']}", headers=auth('nurse')).status_code == 403

def test_admin_cannot_access_vitals(demo, auth):
    result = demo['client'].get(f"/patients/{demo['patient_id']}/vitals", headers=auth('admin'))
    assert result.status_code == 403

def test_vital_crud_and_date_filter(demo, auth):
    pid = demo['patient_id']; c = demo['client']
    created = c.post(f'/patients/{pid}/vitals', json=vdata(), headers=auth('patient'))
    assert created.status_code == 201, created.text
    vid = created.json()['id']
    assert c.get(f'/vitals/{vid}', headers=auth('patient')).status_code == 200
    assert len(c.get(f'/patients/{pid}/vitals', headers=auth('patient')).json()) == 1
    future = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    assert c.get(f'/patients/{pid}/vitals', params={'start': future}, headers=auth('patient')).json() == []
    updated = c.put(f'/vitals/{vid}', json=vdata(pulse=70), headers=auth('patient'))
    assert updated.status_code == 200 and updated.json()['pulse'] == 70
    assert c.delete(f'/vitals/{vid}', headers=auth('patient')).status_code == 204
    assert c.get(f'/vitals/{vid}', headers=auth('patient')).status_code == 404

def test_vital_validation(demo, auth):
    pid = demo['patient_id']
    response = demo['client'].post(f'/patients/{pid}/vitals', json=vdata(systolic=60, diastolic=80), headers=auth('patient'))
    assert response.status_code == 422

def test_unvalidated_device_rejected(demo, auth):
    pid = demo['patient_id']
    response = demo['client'].post(f'/patients/{pid}/vitals', json=vdata(source='device'), headers=auth('patient'))
    assert response.status_code == 422

def test_consent_gate(demo, auth):
    with demo['session']() as db:
        patient = db.get(Patient, demo['patient_id'])
        patient.monitoring_consent = False
        db.commit()
    pid = demo['patient_id']
    assert demo['client'].post(f'/patients/{pid}/vitals', json=vdata(), headers=auth('patient')).status_code == 403
    assert demo['client'].post(f'/patients/{pid}/activities', json=adata(), headers=auth('patient')).status_code == 403

def test_activity_crud_and_range(demo, auth):
    pid = demo['patient_id']; c = demo['client']
    created = c.post(f'/patients/{pid}/activities', json=adata(), headers=auth('patient'))
    assert created.status_code == 201, created.text
    aid = created.json()['id']
    assert c.get(f'/activities/{aid}', headers=auth('patient')).status_code == 200
    assert len(c.get(f'/patients/{pid}/activities', headers=auth('patient')).json()) == 1
    assert c.get(f'/patients/{pid}/activities?start=2020-01-01&end=2020-12-31', headers=auth('patient')).json() == []
    assert c.put(f'/activities/{aid}', json=adata(steps=9000), headers=auth('patient')).json()['steps'] == 9000
    assert c.delete(f'/activities/{aid}', headers=auth('patient')).status_code == 204
    assert c.get(f'/activities/{aid}', headers=auth('patient')).status_code == 404

def test_activity_duplicate_conflict(demo, auth):
    pid = demo['patient_id']; c = demo['client']
    assert c.post(f'/patients/{pid}/activities', json=adata(), headers=auth('patient')).status_code == 201
    assert c.post(f'/patients/{pid}/activities', json=adata(), headers=auth('patient')).status_code == 409

def test_date_range_error(demo, auth):
    pid = demo['patient_id']
    response = demo['client'].get(f'/patients/{pid}/activities?start=2026-11-08&end=2026-01-01', headers=auth('patient'))
    assert response.status_code == 422

def test_staff_cannot_modify_activity(demo, auth):
    pid = demo['patient_id']; c = demo['client']
    aid = c.post(f'/patients/{pid}/activities', json=adata(), headers=auth('patient')).json()['id']
    assert c.put(f'/activities/{aid}', json=adata(steps=1), headers=auth('nurse')).status_code == 403

def test_cross_patient_access_denied(demo, auth):
    pid = demo['other_id']; c = demo['client']
    assert c.post(f'/patients/{pid}/vitals', json=vdata(), headers=auth('patient')).status_code == 403
    assert c.get(f'/patients/{pid}/activities', headers=auth('patient')).status_code == 403

def test_patient_update_and_delete(demo, auth):
    pid = demo['patient_id']; c = demo['client']
    assert c.patch(f'/patients/{pid}', json={'enrolled': False}, headers=auth('admin')).json()['enrolled'] is False
    assert c.delete(f'/patients/{pid}', headers=auth('admin')).status_code == 204
    assert c.get(f'/patients/{pid}', headers=auth('admin')).status_code == 404

def test_assignment_create_revoke(demo, auth):
    c = demo['client']; pid = demo['other_id']
    payload = {'staff_user_id': demo['users']['clinician'], 'patient_id': pid}
    a = c.post('/assignments', json=payload, headers=auth('admin'))
    assert a.status_code == 201
    assert c.get(f'/patients/{pid}', headers=auth('clinician')).status_code == 200
    assert c.delete(f"/assignments/{a.json()['id']}", headers=auth('admin')).status_code == 204
    assert c.get(f'/patients/{pid}', headers=auth('clinician')).status_code == 403

def test_audit_stored(demo, auth):
    demo['client'].get(f"/patients/{demo['patient_id']}", headers=auth('patient'))
    with demo['session']() as db:
        event = db.query(AuditEvent).first()
        assert event is not None and event.action == 'read'
        assert 'Sample Patient' not in event.resource

def test_pagination_validation(demo, auth):
    assert demo['client'].get('/patients?limit=1000', headers=auth('admin')).status_code == 422
