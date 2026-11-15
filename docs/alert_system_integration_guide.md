# HealthTrack Alert System Integration Guide
**Shawn Miller | MSCS-699-B01 | University of the Cumberlands**

## Overview
The alert extension plugs into the existing HealthTrack Phase 3 FastAPI and SQLAlchemy application. It uses the current user accounts, patient assignments, and monitoring-consent rules. There is no separate application or external notification provider to configure.

## Install and start
Use Python 3.11+ and the existing development environment. From the repository root in PowerShell:

```powershell
python -m pip install -r requirements.txt
python -m alembic upgrade head
python -m pytest -q
python -m uvicorn app.main:app --reload
```

Migration `0003_alert_system` adds alert configuration, alerts, event history and notification tables. The previous migrations remain unchanged. The new models are in `app/alerts.py`, imported by Alembic and registered as a FastAPI router. A successfully saved new vital-sign or activity entry is evaluated for alerts.

## Usage
At `http://127.0.0.1:8000/docs`, sign in using the existing fictional demo accounts. Add a manual vital reading from `POST /patients/{patient_id}/vitals` or an activity record from `POST /patients/{patient_id}/activities`. An assigned nurse can list the associated alerts using `GET /patients/{patient_id}/alerts`. Filters include `severity` and `status`.

An assigned nurse or clinician can view and update `GET/PUT /patients/{patient_id}/alert-config`, acknowledge an alert through `POST /alerts/{id}/acknowledge`, resolve it through `POST /alerts/{id}/resolve`, or review `GET /alerts/{id}/history`. Assigned staff receive in-app entries visible through `GET /notifications`. The recipient can mark an entry read through `POST /notifications/{id}/read`.

An administrator can manually run `POST /alerts/process-escalations` to apply elapsed-time escalation checks and `POST /alerts/check-activity-gaps` to evaluate missing activity records. Neither check runs in the background. No email, SMS, or push-notification guarantee is provided.

## Security and compatibility
Existing JWT authentication, care-team assignment authorization and consent checks remain in use. No external medical devices or real patient records should be used. The alert system is an educational demonstration, not a clinical monitoring service. Running the full original test suite is necessary to verify compatibility before submission.
