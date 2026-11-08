"""Data access layer: pagination, filtering and CRUD independent of HTTP transport."""
import logging
from datetime import date, datetime
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .models import Patient, VitalSigns, ActivityData

log = logging.getLogger('healthtrack.crud')

class DuplicateRecord(Exception):
    pass

def commit(db: Session, obj):
    try:
        db.add(obj)
        db.commit()
        db.refresh(obj)
        log.info('Stored resource %s id=%s', type(obj).__name__, obj.id)
        return obj
    except IntegrityError as exc:
        db.rollback()
        log.warning('Database integrity error on %s', type(obj).__name__)
        raise DuplicateRecord('Resource conflicts with a database constraint') from exc

def create(db: Session, cls, values: dict):
    return commit(db, cls(**values))

def get(db: Session, cls, record_id: int):
    return db.get(cls, record_id)

def list_records(db: Session, cls, *, patient_id: int | None = None, start=None, end=None,
                 date_field: str | None = None, skip: int = 0, limit: int = 50):
    statement = select(cls)
    if patient_id is not None:
        statement = statement.where(cls.patient_id == patient_id)
    if date_field:
        column = getattr(cls, date_field)
        if start is not None:
            statement = statement.where(column >= start)
        if end is not None:
            statement = statement.where(column <= end)
        statement = statement.order_by(column.desc(), cls.id.desc())
    else:
        statement = statement.order_by(cls.id)
    return db.scalars(statement.offset(skip).limit(limit)).all()

def update(db: Session, obj, changes: dict):
    for key, value in changes.items():
        setattr(obj, key, value)
    return commit(db, obj)

def delete(db: Session, obj):
    log.info('Deleting resource %s id=%s', type(obj).__name__, obj.id)
    db.delete(obj)
    db.commit()
