# HealthTrack Dashboard User Guide
**Shawn Miller | November 2026**

## Setup
Use Python 3.11 or newer. In the repository root, create and activate a virtual environment, install `requirements.txt`, set a strong `JWT_SECRET_KEY` in your shell, then run `python -m alembic upgrade head`. For a brand-new local demo database, run `python -m scripts.seed_demo` once. Finally start the combined server with `python -m uvicorn dashboard.run:app --reload`.

Visit **http://127.0.0.1:8000/dashboard/** to open Dash. The API remains at **http://127.0.0.1:8000/docs**.

## Using the dashboard
1. Sign in as an existing demo patient, nurse, or clinician. A seeded nurse uses `demo_nurse` with the demonstration password documented in the main README. The admin role cannot open patient charts.
2. Select an available patient in the dropdown. Only enrolled, consented, authorized patients are shown.
3. Read the latest systolic, diastolic, and pulse values in the summary cards. Steps and active minutes reflect the latest available activity day.
4. Move the pointer over the charts to check a measurement date and value. The graphs use only stored readings from the Phase 3 database.
5. Read the alert banner. Green means no demonstration threshold is crossed; amber means a warning threshold is crossed; red means a critical threshold is crossed. These thresholds are examples, not medical guidance.
6. Watch the connection status. WebSocket updates typically appear after the next two-second database check. If the WebSocket is blocked, the ten-second refresh still requests a new snapshot. The last-checked field shows when the data was retrieved.
7. Use **Sign out** to clear the local dashboard session. Never enter real patient data in this demonstration.

## Adding demonstration readings
Open `/docs` and authorize as the appropriate patient account. Create a manual reading using `POST /patients/{patient_id}/vitals` with a valid timezone-aware measurement timestamp, or add daily activity through `POST /patients/{patient_id}/activities`. The dashboard shows the new information after the next update. The existing Phase 3 validation and authorization rules still apply.

## Troubleshooting
- **No patients listed:** Check that you are authorized, and that enrollment and monitoring consent are active.
- **No values yet:** The seeded sample record has no vital readings until you enter some through the API.
- **Disconnected:** Check the running Uvicorn process and browser connection. The periodic refresh remains active.
- **Session expired:** Sign in again; demonstration JWTs expire after 30 minutes.
- **Cannot connect:** Start `dashboard.run:app`, not `app.main:app`, to launch the combined dashboard server.

## Important
This is student software for fictional demonstration data. It is not a medical device, clinical alert system, or approved patient monitoring service.
