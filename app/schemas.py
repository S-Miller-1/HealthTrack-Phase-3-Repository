"""Input validation and example payloads for OpenAPI."""
from datetime import date, datetime, timezone, timedelta
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

class ORMResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class PatientCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=150, examples=['Sample Patient'])
    date_of_birth: date = Field(examples=['1980-04-15'])
    monitoring_consent: bool = False
    user_id: int | None = Field(default=None, gt=0)
    @field_validator('date_of_birth')
    @classmethod
    def adult_only(cls, dob: date):
        today = date.today()
        if dob > today or (today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))) < 18:
            raise ValueError('Patients must be at least 18 years old')
        return dob

class PatientUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    enrolled: bool | None = None
    monitoring_consent: bool | None = None

class PatientOut(ORMResponse):
    id: int
    user_id: int | None
    full_name: str
    date_of_birth: date
    enrolled: bool
    monitoring_consent: bool
    created_at: datetime

class VitalCreate(BaseModel):
    systolic: int = Field(ge=50, le=300, examples=[122])
    diastolic: int = Field(ge=30, le=200, examples=[79])
    pulse: int = Field(ge=30, le=250, examples=[68])
    measured_at: datetime = Field(examples=['2026-11-08T09:00:00Z'])
    source: Literal['manual', 'device'] = 'manual'
    @model_validator(mode='after')
    def logical_reading(self):
        if self.systolic <= self.diastolic:
            raise ValueError('Systolic must exceed diastolic')
        if self.measured_at.tzinfo is None:
            raise ValueError('measured_at must include a timezone')
        if self.measured_at > datetime.now(timezone.utc) + timedelta(minutes=5):
            raise ValueError('A reading cannot be more than five minutes in the future')
        return self

class VitalUpdate(VitalCreate):
    pass

class VitalOut(ORMResponse):
    id: int
    patient_id: int
    systolic: int
    diastolic: int
    pulse: int
    measured_at: datetime
    received_at: datetime
    source: str

class ActivityCreate(BaseModel):
    steps: int = Field(ge=0, le=100000, examples=[6000])
    active_minutes: int = Field(ge=0, le=1440, examples=[45])
    activity_date: date = Field(examples=['2026-11-07'])
    @field_validator('activity_date')
    @classmethod
    def not_future(cls, value: date):
        if value > date.today():
            raise ValueError('Activity date cannot be in the future')
        return value

class ActivityUpdate(ActivityCreate):
    pass

class ActivityOut(ORMResponse):
    id: int
    patient_id: int
    steps: int
    active_minutes: int
    activity_date: date

class TokenOut(BaseModel):
    access_token: str
    token_type: str = 'bearer'

class AssignmentCreate(BaseModel):
    staff_user_id: int = Field(gt=0)
    patient_id: int = Field(gt=0)
