# API usage, request/response examples, and errors

## Access and authorization

Base URL: `http://127.0.0.1:8000` (local development only). The OAuth2 password route is `POST /auth/token` with `application/x-www-form-urlencoded` fields `username` and `password`. Put the resulting token in `Authorization: Bearer <access_token>`. Token lifetime is 30 minutes. A patient can read their own profile and manual measurements; a nurse/clinician can read assigned charts; an administrator can enroll, update and remove patient profiles and manage assignments, but is denied clinical measurement endpoints. Only the owning patient can correct/delete manual readings or edit/delete activity entries.

## REST endpoint overview

| Method | Route | Role |
|---|---|---|
| POST | `/auth/token` | Public login |
| GET | `/health` | Public status |
| POST / GET | `/patients` | Admin create; scoped read |
| GET / PATCH / DELETE | `/patients/{patient_id}` | Scoped read; admin update/delete |
| POST | `/assignments` | Admin creates staff assignment |
| DELETE | `/assignments/{assignment_id}` | Admin revokes assignment |
| POST / GET | `/patients/{patient_id}/vitals` | Patient or assigned staff create/read |
| GET / PUT / DELETE | `/vitals/{vital_id}` | Scoped read; patient manual-edit/delete |
| POST / GET | `/patients/{patient_id}/activities` | Patient or assigned staff create/read |
| GET / PUT / DELETE | `/activities/{activity_id}` | Scoped read; patient edit/delete |

All collection endpoints accept `skip` (default 0) and `limit` (default 50, maximum 100). Vital lists accept inclusive RFC3339 `start`/`end` datetimes; activity lists accept ISO `YYYY-MM-DD` dates. Supply timezone offsets in vital inputs, for example `+00:00` or `Z`. Send timezone offsets as properly URL-encoded query parameters.

## Request and response samples

**Create patient (admin):**

`POST /patients` with `Content-Type: application/json`

```json
{"full_name":"Sample Patient","date_of_birth":"1980-04-15","monitoring_consent":true,"user_id":2}
```

Success: `201 Created`, with generated ID, enrollment state and creation timestamp. The `user_id` must reference an existing patient-role account; omit it for an unlinked profile. No personal information here is real.

**Create vital reading (own or assigned patient):**

`POST /patients/1/vitals`

```json
{"systolic":122,"diastolic":79,"pulse":68,"measured_at":"2026-11-08T09:00:00Z","source":"manual"}
```

Success: `201 Created`:

```json
{"id":1,"patient_id":1,"systolic":122,"diastolic":79,"pulse":68,"measured_at":"2026-11-08T09:00:00Z","received_at":"2026-11-08T09:00:01Z","source":"manual"}
```

The `received_at` value is illustrative, not promised. **Do not submit a future timestamp**: update the sample to a measured time appropriate to the actual date of testing.

**Create activity (own or assigned patient):** `POST /patients/1/activities`

```json
{"steps":6000,"active_minutes":45,"activity_date":"2026-11-07"}
```

Success: `201 Created`:

```json
{"id":1,"patient_id":1,"steps":6000,"active_minutes":45,"activity_date":"2026-11-07"}
```

A second entry for the same patient/day returns `409`. An invalid reading, missing date timezone or future activity returns `422`. Staff can submit observations and read results, but this prototype restricts correction/deletion to the owning patient.

## Error responses

| HTTP status | Meaning | Example body |
|---|---|---|
| 401 | Missing or invalid login/JWT | `{"detail":"Invalid or expired credentials"}` |
| 403 | Role, assignment, ownership or consent failure | `{"detail":"Not authorized for this patient chart"}` |
| 404 | Unknown resource ID | `{"detail":"Resource not found"}` |
| 409 | Database conflict, e.g. duplicate date | `{"detail":"Resource conflicts with a database constraint"}` |
| 422 | Invalid schema, date range or unsupported device | `{"detail":"start must be before or equal to end"}` or Pydantic error list |
| 503 | Audit write could not complete | `{"detail":"Audit service unavailable"}` |

## Suggested Postman workflow

Import `postman/HealthTrack_Phase3.postman_collection.json`, set the `baseUrl` variable, run `Log in as patient` (which stores its token), and run `Create Vital`, `List Vitals`, `Create Activity`, and `List Activities`. Admin-specific requests require running `Log in as admin`. The sample collection uses fictional records only. Review HTTP responses and the audit-events table locally to document test evidence. OpenAPI snapshots can be imported into Swagger UI, Redoc or other OpenAPI-compatible tooling.

## Clinical-use warning

The original design has many more entities and a trusted OIDC/MFA identity model. This Phase 3 exercise is not a replacement for that work and does not represent medical-grade validation. The interface never promises emergency or round-the-clock monitoring. In an emergency, contact local emergency services rather than using this API.
