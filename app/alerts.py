"""Alert detection, notifications and acknowledgment for HealthTrack's educational pilot."""
from datetime import date, datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, model_validator, ConfigDict
from sqlalchemy import DateTime, ForeignKey, Integer, String, select
from sqlalchemy.orm import Mapped, mapped_column, Session
from .database import Base, get_db
from .models import ActivityData, Patient, PatientAssignment, User
from .security import current_user, can_access_patient

def now():
    return datetime.now(timezone.utc)

class AlertConfig(Base):
    __tablename__ = "alert_configs"
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), unique=True)
    systolic_min: Mapped[int] = mapped_column(Integer, default=90)
    systolic_max: Mapped[int] = mapped_column(Integer, default=139)
    diastolic_min: Mapped[int] = mapped_column(Integer, default=60)
    diastolic_max: Mapped[int] = mapped_column(Integer, default=89)
    pulse_min: Mapped[int] = mapped_column(Integer, default=50)
    pulse_max: Mapped[int] = mapped_column(Integer, default=100)

class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"))
    rule: Mapped[str] = mapped_column(String(60))
    severity: Mapped[str] = mapped_column(String(12))
    message: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), default="open")
    source_key: Mapped[str] = mapped_column(String(120), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    acknowledged_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    escalated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

class AlertEvent(Base):
    __tablename__ = "alert_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id", ondelete="CASCADE"))
    event: Mapped[str] = mapped_column(String(30))
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class AlertNotification(Base):
    __tablename__ = "alert_notifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id", ondelete="CASCADE"))
    recipient_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    channel: Mapped[str] = mapped_column(String(12), default="in_app")
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

DEFAULT = dict(systolic_min=90, systolic_max=139, diastolic_min=60, diastolic_max=89, pulse_min=50, pulse_max=100)

class ConfigInput(BaseModel):
    systolic_min: int = Field(ge=50, le=300)
    systolic_max: int = Field(ge=50, le=300)
    diastolic_min: int = Field(ge=30, le=200)
    diastolic_max: int = Field(ge=30, le=200)
    pulse_min: int = Field(ge=30, le=250)
    pulse_max: int = Field(ge=30, le=250)
    @model_validator(mode="after")
    def check_order(self):
        if any(getattr(self, f"{k}_min") >= getattr(self, f"{k}_max") for k in ("systolic", "diastolic", "pulse")):
            raise ValueError("Minimum must be less than maximum")
        return self

class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    patient_id: int
    rule: str
    severity: str
    message: str
    status: str
    created_at: datetime
    acknowledged_at: datetime | None
    resolved_at: datetime | None
    escalated_at: datetime | None

def bounds(db, patient_id):
    config = db.query(AlertConfig).filter_by(patient_id=patient_id).first()
    return {key: getattr(config, key) if config else val for key, val in DEFAULT.items()}

def recipients(db, patient_id):
    return [r[0] for r in db.query(User.id).join(PatientAssignment, PatientAssignment.staff_user_id == User.id)
            .filter(PatientAssignment.patient_id == patient_id, User.active.is_(True),
                    User.role.in_(("nurse", "clinician"))).distinct().all()]

def emit(db, patient_id, rule, severity, message, source_key):
    previous = db.query(Alert).filter_by(source_key=source_key).first()
    if previous:
        return previous
    if severity == "low" and db.query(Alert.id).filter(
        Alert.patient_id == patient_id, Alert.status != "resolved", Alert.severity.in_(("high", "critical"))).first():
        return None
    item = Alert(patient_id=patient_id, rule=rule, severity=severity, message=message, source_key=source_key)
    db.add(item)
    db.flush()
    db.add(AlertEvent(alert_id=item.id, event="created"))
    for uid in recipients(db, patient_id):
        db.add(AlertNotification(alert_id=item.id, recipient_id=uid))
    return item

def evaluate_vital(db, reading):
    b = bounds(db, reading.patient_id)
    abnormal = any(not b[f"{name}_min"] <= getattr(reading, name) <= b[f"{name}_max"]
                   for name in ("systolic", "diastolic", "pulse"))
    critical = (reading.systolic >= 180 or reading.systolic < 80 or
                reading.diastolic >= 120 or reading.pulse < 40 or reading.pulse > 130)
    if not (abnormal or critical):
        return None
    return emit(db, reading.patient_id, "vital_threshold", "critical" if critical else "high",
                "A vital sign reading needs review.", f"vital:{reading.id}")

def evaluate_activity(db, activity):
    readings = db.query(ActivityData).filter(
        ActivityData.patient_id == activity.patient_id, ActivityData.activity_date <= activity.activity_date
    ).order_by(ActivityData.activity_date.desc()).limit(10).all()
    if len(readings) < 10:
        return None
    readings.reverse()
    if any((readings[i].activity_date - readings[i-1].activity_date).days != 1 for i in range(1, 10)):
        return None
    baseline = sum(r.steps for r in readings[:7]) / 7
    recent = sum(r.steps for r in readings[7:]) / 3
    if baseline < 1000 or recent >= baseline * 0.5:
        return None
    return emit(db, activity.patient_id, "activity_decline", "low",
                "Daily activity dropped compared with last week.",
                f"activity:{activity.patient_id}:{activity.activity_date}")

def require_access(db, user, patient_id, staff=False):
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(404, "Patient not found")
    if not can_access_patient(db, user, patient) or (staff and user.role not in ("nurse", "clinician")):
        raise HTTPException(403, "Assigned patient access required")
    return patient

def authorized_alert(db, user, alert_id):
    alert = db.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(404, "Alert not found")
    require_access(db, user, alert.patient_id, staff=True)
    return alert

router = APIRouter(tags=["Alerts"])

@router.get("/patients/{patient_id}/alert-config", response_model=ConfigInput)
def read_config(patient_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    require_access(db, user, patient_id)
    return bounds(db, patient_id)

@router.put("/patients/{patient_id}/alert-config", response_model=ConfigInput)
def update_config(patient_id: int, new: ConfigInput, db: Session = Depends(get_db),
                  user: User = Depends(current_user)):
    require_access(db, user, patient_id, staff=True)
    config = db.query(AlertConfig).filter_by(patient_id=patient_id).first()
    if not config:
        config = AlertConfig(patient_id=patient_id)
        db.add(config)
    for key, value in new.model_dump().items():
        setattr(config, key, value)
    db.commit()
    return new

@router.get("/patients/{patient_id}/alerts", response_model=list[AlertOut])
def list_alerts(patient_id: int, severity: str | None = None, status: str | None = None,
                offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100),
                db: Session = Depends(get_db), user: User = Depends(current_user)):
    require_access(db, user, patient_id, staff=True)
    if severity is not None and severity not in ("low", "high", "critical"):
        raise HTTPException(422, "Invalid severity")
    if status is not None and status not in ("open", "acknowledged", "resolved"):
        raise HTTPException(422, "Invalid status")
    query = db.query(Alert).filter_by(patient_id=patient_id)
    if severity:
        query = query.filter_by(severity=severity)
    if status:
        query = query.filter_by(status=status)
    return query.order_by(Alert.created_at.desc(), Alert.id.desc()).offset(offset).limit(limit).all()

@router.post("/alerts/{alert_id}/acknowledge", response_model=AlertOut)
def acknowledge(alert_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    item = authorized_alert(db, user, alert_id)
    if item.status == "resolved":
        raise HTTPException(409, "Already resolved")
    if item.status == "open":
        item.status, item.acknowledged_at, item.acknowledged_by = "acknowledged", now(), user.id
        db.add(AlertEvent(alert_id=item.id, event="acknowledged", actor_id=user.id))
        db.commit()
    return item

@router.post("/alerts/{alert_id}/resolve", response_model=AlertOut)
def resolve(alert_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    item = authorized_alert(db, user, alert_id)
    if item.status != "resolved":
        item.status, item.resolved_at, item.resolved_by = "resolved", now(), user.id
        db.add(AlertEvent(alert_id=item.id, event="resolved", actor_id=user.id))
        db.commit()
    return item

@router.get("/alerts/{alert_id}/history")
def history(alert_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    item = authorized_alert(db, user, alert_id)
    events = db.query(AlertEvent).filter_by(alert_id=item.id).order_by(AlertEvent.occurred_at, AlertEvent.id).all()
    return [{"event": e.event, "actor_id": e.actor_id, "occurred_at": e.occurred_at.isoformat()} for e in events]

@router.get("/notifications")
def inbox(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = db.query(AlertNotification).filter_by(recipient_id=user.id).order_by(AlertNotification.id.desc()).limit(100).all()
    return [{"id": n.id, "alert_id": n.alert_id, "channel": n.channel,
             "read_at": n.read_at.isoformat() if n.read_at else None} for n in rows]

@router.post("/notifications/{notification_id}/read")
def mark_read(notification_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    item = db.get(AlertNotification, notification_id)
    if not item or item.recipient_id != user.id:
        raise HTTPException(404, "Notification not found")
    item.read_at = now()
    db.commit()
    return {"id": item.id, "read": True}

def process_escalations(db, current_time=None):
    current_time = current_time or now()
    count = 0
    open_alerts = db.query(Alert).filter(Alert.status == "open", Alert.escalated_at.is_(None),
                                         Alert.severity.in_(("high", "critical"))).all()
    for item in open_alerts:
        created = item.created_at.replace(tzinfo=timezone.utc) if item.created_at.tzinfo is None else item.created_at
        delay = 15 if item.severity == "critical" else 60
        if current_time < created + timedelta(minutes=delay):
            continue
        patient = db.get(Patient, item.patient_id)
        if not patient or not patient.enrolled or not patient.monitoring_consent:
            continue
        item.escalated_at = current_time
        db.add(AlertEvent(alert_id=item.id, event="escalated"))
        for uid in recipients(db, item.patient_id):
            db.add(AlertNotification(alert_id=item.id, recipient_id=uid))
        count += 1
    db.commit()
    return count

@router.post("/alerts/process-escalations")
def escalation_check(db: Session = Depends(get_db), user: User = Depends(current_user)):
    if user.role != "admin":
        raise HTTPException(403, "Administrator required")
    return {"escalated": process_escalations(db)}

@router.post("/alerts/check-activity-gaps")
def check_activity_gaps(db: Session = Depends(get_db), user: User = Depends(current_user)):
    if user.role != "admin":
        raise HTTPException(403, "Administrator required")
    count = 0
    today = date.today()
    for patient in db.query(Patient).filter_by(enrolled=True, monitoring_consent=True):
        last = db.query(ActivityData).filter(ActivityData.patient_id == patient.id,
               ActivityData.activity_date <= today).order_by(ActivityData.activity_date.desc()).first()
        if last and (today - last.activity_date).days >= 2:
            if emit(db, patient.id, "missing_activity", "low",
                    "Activity data has not been submitted for two days.", f"gap:{patient.id}:{today}"):
                count += 1
    db.commit()
    return {"matches": count}
