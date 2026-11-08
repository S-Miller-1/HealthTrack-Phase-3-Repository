"""Create fictional demo accounts only; NEVER enter clinical patient data."""
from datetime import date
from app.database import SessionLocal
from app.models import User, Patient, PatientAssignment
from app.security import hash_password

with SessionLocal() as db:
    if db.query(User).count():
        raise SystemExit('Existing users found; skipping seed to avoid overwriting data.')
    accounts = {}
    for role in ('admin', 'patient', 'nurse', 'clinician'):
        user = User(username=f'demo_{role}', password_hash=hash_password(f'Demo-{role}-ChangeMe!'), role=role)
        db.add(user)
        db.flush()
        accounts[role] = user
    patient = Patient(user_id=accounts['patient'].id, full_name='Sample Patient',
                      date_of_birth=date(1980, 4, 15), enrolled=True, monitoring_consent=True)
    db.add(patient)
    db.flush()
    for role in ('nurse', 'clinician'):
        db.add(PatientAssignment(staff_user_id=accounts[role].id, patient_id=patient.id))
    db.commit()
    print('Fictional accounts: demo_admin/demo_patient/demo_nurse/demo_clinician')
    print('Passwords: Demo-<role>-ChangeMe! (e.g. Demo-patient-ChangeMe!)')
    print('WARNING: training credentials only. Change/remove before any deployment.')
