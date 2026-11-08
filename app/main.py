"""HealthTrack teaching prototype: FastAPI REST endpoints and access control."""
import logging, uuid
from datetime import date, datetime, timezone
from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from .database import get_db
from .models import User, Patient, PatientAssignment, VitalSigns, ActivityData, AuditEvent
from . import crud, schemas
from .security import current_user, require_admin, require_patient_access, verify_password, make_token

logging.basicConfig(level=logging.INFO, format='%(levelname)s %(name)s %(message)s')
logger = logging.getLogger('healthtrack.api')
app = FastAPI(title='HealthTrack Phase 3 API', version='0.3.0',
              description='Educational hypertension monitoring prototype. Not for real patient data or clinical decision-making.')

@app.middleware('http')
async def request_id(request: Request, call_next):
    correlation_id = str(uuid.uuid4())
    response = await call_next(request)
    response.headers['X-Correlation-ID'] = correlation_id
    return response

@app.exception_handler(crud.DuplicateRecord)
async def duplicate_handler(_request: Request, exc: crud.DuplicateRecord):
    return JSONResponse(status_code=409, content={'detail': str(exc)})

def not_found(obj):
    if obj is None:
        raise HTTPException(404, 'Resource not found')
    return obj

def audit(db: Session, user: User, action: str, resource: str):
    # Resource is a generic category only: never write chart values to audit data.
    try:
        db.add(AuditEvent(user_id=user.id, action=action, resource=resource,
                          correlation_id=str(uuid.uuid4())))
        db.commit()
    except Exception:
        db.rollback()
        logger.exception('Failed to persist audit event')
        raise HTTPException(503, 'Audit service unavailable')

def chart_patient(patient_id: int, db: Session, user: User):
    patient = not_found(db.get(Patient, patient_id))
    require_patient_access(db, user, patient)
    return patient

def ensure_monitoring(patient: Patient):
    if not patient.enrolled or not patient.monitoring_consent:
        raise HTTPException(403, 'Active enrollment and monitoring consent required')

@app.get('/health', tags=['System'])
def health():
    return {'status': 'ok', 'purpose': 'educational prototype'}

@app.post('/auth/token', response_model=schemas.TokenOut, tags=['Authentication'])
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter_by(username=form.username).first()
    if not user or not user.active or not verify_password(form.password, user.password_hash):
        raise HTTPException(401, 'Incorrect username or password', headers={'WWW-Authenticate': 'Bearer'})
    return {'access_token': make_token(user), 'token_type': 'bearer'}

@app.post('/patients', response_model=schemas.PatientOut, status_code=201, tags=['Patients'])
def create_patient(data: schemas.PatientCreate, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    if data.user_id:
        owner = db.get(User, data.user_id)
        if owner is None or owner.role != 'patient':
            raise HTTPException(422, 'user_id must identify a patient-role account')
    obj = crud.create(db, Patient, {'full_name': data.full_name, 'date_of_birth': data.date_of_birth,
                                    'monitoring_consent': data.monitoring_consent, 'user_id': data.user_id})
    audit(db, user, 'create', 'patient')
    return obj

@app.get('/patients', response_model=list[schemas.PatientOut], tags=['Patients'])
def list_patients(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100),
                  db: Session = Depends(get_db), user: User = Depends(current_user)):
    if user.role == 'admin':
        return crud.list_records(db, Patient, skip=skip, limit=limit)
    if user.role == 'patient':
        return db.query(Patient).filter(Patient.user_id == user.id).offset(skip).limit(limit).all()
    patient_ids = db.query(PatientAssignment.patient_id).filter_by(staff_user_id=user.id)
    return db.query(Patient).filter(Patient.id.in_(patient_ids)).order_by(Patient.id).offset(skip).limit(limit).all()

@app.get('/patients/{patient_id}', response_model=schemas.PatientOut, tags=['Patients'])
def get_patient(patient_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    patient = not_found(db.get(Patient, patient_id))
    if user.role != 'admin':
        require_patient_access(db, user, patient)
    audit(db, user, 'read', 'patient')
    return patient

@app.patch('/patients/{patient_id}', response_model=schemas.PatientOut, tags=['Patients'])
def update_patient(patient_id: int, data: schemas.PatientUpdate, db: Session = Depends(get_db),
                   user: User = Depends(require_admin)):
    obj = not_found(db.get(Patient, patient_id))
    result = crud.update(db, obj, data.model_dump(exclude_unset=True))
    audit(db, user, 'update', 'patient')
    return result

@app.delete('/patients/{patient_id}', status_code=204, tags=['Patients'])
def delete_patient(patient_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    # Demo-only destructive delete; retention workflow is required for a production clinic.
    crud.delete(db, not_found(db.get(Patient, patient_id)))
    audit(db, user, 'delete', 'patient')

@app.post('/assignments', status_code=201, tags=['Administration'])
def assign_staff(data: schemas.AssignmentCreate, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    staff = db.get(User, data.staff_user_id)
    not_found(db.get(Patient, data.patient_id))
    if staff is None or staff.role not in {'nurse', 'clinician'}:
        raise HTTPException(422, 'staff_user_id must identify a nurse or clinician')
    a = crud.create(db, PatientAssignment, data.model_dump())
    audit(db, user, 'assign', 'patient')
    return {'id': a.id}

@app.delete('/assignments/{assignment_id}', status_code=204, tags=['Administration'])
def unassign_staff(assignment_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    crud.delete(db, not_found(db.get(PatientAssignment, assignment_id)))
    audit(db, user, 'unassign', 'patient')

@app.post('/patients/{patient_id}/vitals', response_model=schemas.VitalOut, status_code=201, tags=['Vital signs'])
def create_vital(patient_id: int, data: schemas.VitalCreate, db: Session = Depends(get_db),
                 user: User = Depends(current_user)):
    patient = chart_patient(patient_id, db, user)
    ensure_monitoring(patient)
    if data.source == 'device':
        raise HTTPException(422, 'Device integration requires a validated device registry (future phase)')
    result = crud.create(db, VitalSigns, {'patient_id': patient_id, **data.model_dump()})
    audit(db, user, 'create', 'vital_signs')
    return result

@app.get('/patients/{patient_id}/vitals', response_model=list[schemas.VitalOut], tags=['Vital signs'])
def list_vitals(patient_id: int, start: datetime | None = None, end: datetime | None = None,
                skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100),
                db: Session = Depends(get_db), user: User = Depends(current_user)):
    chart_patient(patient_id, db, user)
    if start and end and start > end:
        raise HTTPException(422, 'start must be before or equal to end')
    results = crud.list_records(db, VitalSigns, patient_id=patient_id, start=start, end=end,
                                date_field='measured_at', skip=skip, limit=limit)
    audit(db, user, 'read', 'vital_signs')
    return results

@app.get('/vitals/{vital_id}', response_model=schemas.VitalOut, tags=['Vital signs'])
def get_vital(vital_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    obj = not_found(db.get(VitalSigns, vital_id))
    chart_patient(obj.patient_id, db, user)
    audit(db, user, 'read', 'vital_signs')
    return obj

@app.put('/vitals/{vital_id}', response_model=schemas.VitalOut, tags=['Vital signs'])
def update_vital(vital_id: int, data: schemas.VitalUpdate, db: Session = Depends(get_db),
                 user: User = Depends(current_user)):
    obj = not_found(db.get(VitalSigns, vital_id))
    patient = chart_patient(obj.patient_id, db, user)
    ensure_monitoring(patient)
    if user.role != 'patient' or obj.source != 'manual' or data.source != 'manual':
        raise HTTPException(403, 'Only the owning patient can correct a manual reading')
    result = crud.update(db, obj, data.model_dump())
    audit(db, user, 'correct', 'vital_signs')
    return result

@app.delete('/vitals/{vital_id}', status_code=204, tags=['Vital signs'])
def delete_vital(vital_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    obj = not_found(db.get(VitalSigns, vital_id))
    patient = chart_patient(obj.patient_id, db, user)
    ensure_monitoring(patient)
    if user.role != 'patient' or obj.source != 'manual':
        raise HTTPException(403, 'Only the owning patient can remove a manual reading')
    crud.delete(db, obj)
    audit(db, user, 'delete', 'vital_signs')

@app.post('/patients/{patient_id}/activities', response_model=schemas.ActivityOut, status_code=201, tags=['Activities'])
def create_activity(patient_id: int, data: schemas.ActivityCreate, db: Session = Depends(get_db),
                    user: User = Depends(current_user)):
    patient = chart_patient(patient_id, db, user)
    ensure_monitoring(patient)
    result = crud.create(db, ActivityData, {'patient_id': patient_id, **data.model_dump()})
    audit(db, user, 'create', 'activity_data')
    return result

@app.get('/patients/{patient_id}/activities', response_model=list[schemas.ActivityOut], tags=['Activities'])
def list_activities(patient_id: int, start: date | None = None, end: date | None = None,
                    skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100),
                    db: Session = Depends(get_db), user: User = Depends(current_user)):
    chart_patient(patient_id, db, user)
    if start and end and start > end:
        raise HTTPException(422, 'start must be before or equal to end')
    results = crud.list_records(db, ActivityData, patient_id=patient_id, start=start, end=end,
                                date_field='activity_date', skip=skip, limit=limit)
    audit(db, user, 'read', 'activity_data')
    return results

@app.get('/activities/{activity_id}', response_model=schemas.ActivityOut, tags=['Activities'])
def get_activity(activity_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    obj = not_found(db.get(ActivityData, activity_id))
    chart_patient(obj.patient_id, db, user)
    audit(db, user, 'read', 'activity_data')
    return obj

@app.put('/activities/{activity_id}', response_model=schemas.ActivityOut, tags=['Activities'])
def update_activity(activity_id: int, data: schemas.ActivityUpdate, db: Session = Depends(get_db),
                    user: User = Depends(current_user)):
    obj = not_found(db.get(ActivityData, activity_id))
    patient = chart_patient(obj.patient_id, db, user)
    ensure_monitoring(patient)
    if user.role != 'patient':
        raise HTTPException(403, 'Only the owning patient can update activities')
    result = crud.update(db, obj, data.model_dump())
    audit(db, user, 'update', 'activity_data')
    return result

@app.delete('/activities/{activity_id}', status_code=204, tags=['Activities'])
def delete_activity(activity_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    obj = not_found(db.get(ActivityData, activity_id))
    patient = chart_patient(obj.patient_id, db, user)
    ensure_monitoring(patient)
    if user.role != 'patient':
        raise HTTPException(403, 'Only the owning patient can delete activities')
    crud.delete(db, obj)
    audit(db, user, 'delete', 'activity_data')
