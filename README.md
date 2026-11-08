# HealthTrack – Phase 3: Database and API

**Shawn Miller | MSCS-699-B01 | University of the Cumberlands**  
**Instructor: Michael Solomon | November 2026**

This is a **local educational prototype** for a consent-based outpatient hypertension monitoring pilot. It implements the three Phase 3 entities (Patient, VitalSigns, ActivityData), supporting account and assignment tables, SQLAlchemy CRUD, FastAPI, migrations, Swagger, Postman requests, and automated tests. **Use fictional data only. This is not a HIPAA-compliant, clinically deployable system.**

## Set up and run (Windows / PowerShell)

Use Python 3.11+ from the project root:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env: replace JWT_SECRET_KEY with a long random secret.
# Load environment variables into the PowerShell session:
$env:JWT_SECRET_KEY = "REPLACE_WITH_YOUR_OWN_32_CHARACTER_PLUS_RANDOM_SECRET"
python -m alembic upgrade head
python -m scripts.seed_demo
python -m uvicorn app.main:app --reload
```

On macOS/Linux: activate with `source .venv/bin/activate`, export `JWT_SECRET_KEY`, and use `python` rather than `py`. The default SQLite database is created locally as `healthtrack.db` (gitignored). For PostgreSQL, configure `DATABASE_URL` with a SQLAlchemy-compatible driver and install that driver. Do **not** use the demo SQLite setup for real patient records.

Open **http://127.0.0.1:8000/docs** for interactive Swagger or **http://127.0.0.1:8000/openapi.json** for the live OpenAPI schema. The checked-in snapshots are `docs/openapi.yaml` and `docs/openapi.json`.

## Demonstration login

The seed command creates fictional users `demo_admin`, `demo_patient`, `demo_nurse`, and `demo_clinician`. The teaching password pattern is `Demo-<role>-ChangeMe!`; for example, `Demo-patient-ChangeMe!`. These are intentionally weak, published *demo* credentials. Never deploy with them. In Swagger, click **Authorize**, enter the demo username and password to obtain a 30-minute JWT, and use only the endpoints allowed for that role.

### Suggested demonstration workflow

1. Log in as the admin, review the seeded patient (`GET /patients`), and optionally add or revoke a care-team assignment.
2. Log in as the patient, view the patient profile, and create a manual blood pressure entry under `/patients/1/vitals`.
3. Create activity data under `/patients/1/activities`; list readings with `start` and `end` filters.
4. Log in as the nurse and verify assigned charts can be read but not edited. Verify the admin cannot read vitals.
5. Test invalid blood pressure values, duplicate activity dates, and consent withdrawal; inspect 422, 409 and 403 responses.

Activity dates must not be in the future. Vital timestamps must include a timezone and cannot be more than five minutes ahead. Each patient has at most one activity entry per date.

## Test and benchmark

```powershell
python -m pytest --disable-warnings
python -m pytest --cov=app --cov-report=term-missing
python -m scripts.performance_check
python -m alembic current
```

Test results and measurement caveats are in `docs/test_results.md` and `docs/performance_results.json`.

## Project map

- `app/models.py` — SQLAlchemy models and SQL constraints
- `app/schemas.py` — Pydantic validation and OpenAPI examples
- `app/crud.py` — separate CRUD and date-filtered data access
- `app/security.py` — PBKDF2 authentication, JWTs and role/assignment checks
- `app/main.py` — FastAPI routes, error mapping and audit events
- `alembic/versions/` — initial schema and second index migration
- `tests/` — model integrity, permissions, CRUD and error cases
- `docs/openapi.yaml`, `docs/openapi.json` — exported Swagger/OpenAPI contracts
- `postman/HealthTrack_Phase3.postman_collection.json` — importable requests
- `docs/data_access.md` — methods and database optimization
- `docs/api_guide.md` — workflows, example payloads and errors
- `docs/phase3_security_performance_report.docx` — security/performance report

## Relationship to Phase 2

The previous design rationale describes a **17-table, 43-operation, 29-path** future service with clinic membership, revisions, alerts, reminders, devices, exports and other functions. This Phase 3 submission implements the *required three entity subset* plus supporting users/assignments/audits, not the full Phase 2 production contract. The existing patient-to-reading relationship, dual measurement timestamps, consent checks, staff assignment boundaries and composite patient/date indexes are retained. Deliberately unsupported areas include validated connected cuffs, full clinic isolation, clinician alert approvals, read-revision triggers, retained-record deletion controls, external OIDC/MFA, and export jobs. See `docs/phase2_alignment.md` for details.

## Security and operational limits

JWTs use a local demo issuer rather than a trusted external OpenID Connect identity provider. Passwords use salted PBKDF2. HTTPS termination, secret management, per-request rate limiting, MFA, managed encryption, backup recovery, complete denied-request auditing, tamper-resistant audit storage, versioned reading corrections and HIPAA risk assessment are **not implemented**. The hard-delete endpoints are a rubric exercise and conflict with the retention and immutable-revision requirements in the clinical proposal. **Before deploying to a clinical environment, replace this prototype architecture and complete a professional security and privacy review.**
