import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base, get_db
from app.main import app
from app.models import User, Patient, PatientAssignment
from app.security import hash_password, make_token

@pytest.fixture
def demo():
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    @event.listens_for(engine, 'connect')
    def foreign_keys(connection, _):
        connection.execute('PRAGMA foreign_keys=ON')
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    with Session() as db:
        users = {}
        for role in ('admin', 'patient', 'nurse', 'clinician', 'other'):
            r = 'patient' if role == 'other' else role
            u = User(username=role, password_hash=hash_password('TestingPassword123!'), role=r)
            db.add(u)
            db.flush()
            users[role] = u
        patient = Patient(user_id=users['patient'].id, full_name='Sample Patient',
                          date_of_birth=date(1981, 1, 1), monitoring_consent=True)
        other = Patient(user_id=users['other'].id, full_name='Other Patient',
                        date_of_birth=date(1982, 1, 1), monitoring_consent=True)
        db.add_all([patient, other]); db.flush()
        db.add(PatientAssignment(staff_user_id=users['nurse'].id, patient_id=patient.id))
        db.commit()
        patient_id, other_id = patient.id, other.id
        tokens = {role: make_token(u) for role, u in users.items()}
        user_ids = {role: u.id for role, u in users.items()}
    def override():
        with Session() as db:
            yield db
    app.dependency_overrides[get_db] = override
    with TestClient(app) as client:
        yield {'client': client, 'session': Session, 'users': user_ids,
               'patient_id': patient_id, 'other_id': other_id, 'tokens': tokens}
    app.dependency_overrides.clear()
    engine.dispose()

@pytest.fixture
def auth(demo):
    return lambda role: {'Authorization': 'Bearer ' + demo['tokens'][role]}
