# HealthTrack — Phase 3 API and Alert System

**Shawn Miller | MSCS-699-B01 | University of the Cumberlands**  
**Instructor: Michael Solomon | November 2026**

HealthTrack is a local FastAPI healthcare-monitoring project built with SQLAlchemy and SQLite. It stores fictional patient records, blood pressure and pulse readings, and activity data. This branch adds the **Alert System Implementation** assignment to the existing Phase 3 application.

**Classroom demonstration only. Use fictional data; this is not clinically validated or suitable for real patient monitoring.**

## Alert features

- Detects vital-sign readings outside configured thresholds, with separate high and critical severity.
- Allows assigned nurses and clinicians to customize patient-specific vital-sign thresholds.
- Detects substantial declines in activity over ten consecutive days, and supports an admin-triggered missing-activity check.
- Stores in-app notifications for assigned care-team members, with severity-based suppression of low-priority alerts.
- Records alerts, acknowledgments, resolutions, and escalation history.
- Supports escalation checks for unacknowledged critical alerts after 15 minutes and high alerts after 60 minutes.

**Limitations:** Notifications are stored in the app and must be checked by users; they are not sent by email or SMS. Escalations require an administrator to run the check endpoint—there is no automatic background scheduler.

## Set up and run

From the folder containing `requirements.txt` and `alembic.ini` (Python 3.11+):

```powershell
python -m pip install -r requirements.txt
$env:JWT_SECRET_KEY = "REPLACE_WITH_A_LONG_RANDOM_SECRET"
python -m alembic upgrade head
python -m scripts.seed_demo
python -m uvicorn app.main:app --reload
```

The seed command creates fictional demo users: `demo_admin`, `demo_patient`, `demo_nurse`, and `demo_clinician`. The teaching password pattern is `Demo-<role>-ChangeMe!` (for example, `Demo-patient-ChangeMe!`). These credentials must never be used for a real deployment.

Open **http://127.0.0.1:8000/docs** to use the API through Swagger. Sign in with a demo account, add a manual vital-sign reading or activity record, then review the alert and notification endpoints with an assigned nurse account.

## Tests and performance

Run these commands from the project root:

```powershell
python -m pytest -q
python -m scripts.benchmark_alerts
```

**Verified local run — November 15, 2026:** All **40 automated tests passed**, and all three database migrations completed. A synthetic SQLite benchmark processed **500 readings**, creating **100 alerts** and **100 in-app notifications**. Median processing time was **0.510 ms**, p95 was **1.691 ms**, and maximum was **6.249 ms**. These timings include local insert, evaluation and commit, **not notification delivery or production HTTP traffic**.

## Required assignment deliverables

| Deliverable | Location |
|---|---|
| Alert implementation | `app/alerts.py`, integration in `app/main.py`, migration `alembic/versions/0003_alert_system.py` |
| Alert configuration document | `docs/alert_configuration.md` |
| Testing scenarios and results | `tests/test_alerts.py`, `docs/alert_testing_scenarios_and_results.md` |
| System integration guide | `docs/alert_system_integration_guide.md` |
| Performance metrics report | `docs/alert_performance_metrics_report.md`, `scripts/benchmark_alerts.py` |

The original Phase 3 API, authentication, data models and tests remain part of this project. The alert extension uses the existing patient assignments and monitoring-consent checks. See the included documents for rules, endpoints and known limitations.
