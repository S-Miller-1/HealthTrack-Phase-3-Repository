"""Prototype password authentication and signed JWTs; deploy behind TLS."""
import os, hmac, hashlib, secrets
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .database import get_db
from .models import User, PatientAssignment, Patient

SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'development-only-change-this-secret')
ALGORITHM = 'HS256'
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/token')

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    iterations = 390000
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, iterations)
    return f'pbkdf2_sha256${iterations}${salt.hex()}${digest.hex()}'

def verify_password(password: str, encoded: str) -> bool:
    try:
        algo, iterations, salt, target = encoded.split('$')
        if algo != 'pbkdf2_sha256':
            return False
        actual = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), int(iterations))
        return hmac.compare_digest(actual, bytes.fromhex(target))
    except (ValueError, TypeError):
        return False

def make_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode({'sub': str(user.id), 'iat': now, 'exp': now + timedelta(minutes=30),
                       'iss': 'healthtrack-demo', 'aud': 'healthtrack-api'}, SECRET_KEY, algorithm=ALGORITHM)

def current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    denied = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid or expired credentials',
                           headers={'WWW-Authenticate': 'Bearer'})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM],
                             issuer='healthtrack-demo', audience='healthtrack-api')
        uid = int(payload['sub'])
    except (jwt.PyJWTError, ValueError, KeyError):
        raise denied
    user = db.get(User, uid)
    if user is None or not user.active:
        raise denied
    return user

def require_admin(user: User = Depends(current_user)) -> User:
    if user.role != 'admin':
        raise HTTPException(403, 'Administrator access required')
    return user

def can_access_patient(db: Session, user: User, patient: Patient) -> bool:
    if user.role == 'patient':
        return patient.user_id == user.id
    if user.role in {'clinician', 'nurse'}:
        return db.query(PatientAssignment).filter_by(staff_user_id=user.id, patient_id=patient.id).first() is not None
    return False  # Admin handles enrollment only; no chart access.

def require_patient_access(db: Session, user: User, patient: Patient):
    if not can_access_patient(db, user, patient):
        raise HTTPException(403, 'Not authorized for this patient chart')
