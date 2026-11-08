# Data access methods and database design

## Entity relationships

`users (1) -> (0..1) patients`; `patients (1) -> (many) vital_signs`; `patients (1) -> (many) activity_data`. `patient_assignments` joins staff users and patients through a unique `(staff_user_id, patient_id)` pair. `audit_events` records a generic resource category, actor, action, timestamp and generated correlation identifier.

## SQLAlchemy data access (`app/crud.py`)

| Method | Input | Behavior / result | Errors |
|---|---|---|---|
| `create(db, cls, values)` | Session, model class, validated dict | Inserts row and refreshes generated fields | Maps `IntegrityError` to `DuplicateRecord` (HTTP 409) |
| `get(db, cls, record_id)` | Session, class, integer PK | Returns row or `None` | Caller returns HTTP 404 |
| `list_records(db, cls, patient_id, start, end, date_field, skip, limit)` | Optional owner ID and inclusive date range | Parameterized SELECT ordered newest-first for measurement/date data, with offset/limit | Invalid query parameters rejected by FastAPI; access checked before retrieval |
| `update(db, obj, changes)` | Existing row, validated field dict | Mutates permitted columns and commits | Conflict becomes 409 |
| `delete(db, obj)` | Existing row | Deletes and commits | Caller ensures object exists and caller has permission |
| `commit(db, obj)` | Existing/new model | Transactional commit, refresh, log | On integrity conflict, rolls back to avoid a broken session |

CRUD methods contain **no role decisions**: request handlers validate JWT role, chart ownership and care-team assignment *before* invoking them. This separation simplifies testing and makes authorization visible at the HTTP boundary. Only model-approved fields can be changed through typed schemas.

## Validation and constraints

- Patient: nonempty name up to 150 characters; DOB must be at least 18 years ago (API); user linkage unique; enrollment and monitoring consent flags.
- Vital signs: systolic 50–300, diastolic 30–200, systolic > diastolic, pulse 30–250. Timestamp must be timezone-aware and no more than five minutes in the future (API). `source='device'` is blocked until a device validation registry exists.
- Activity data: steps 0–100,000; active minutes 0–1,440; activity date is not in the future (API); unique `(patient_id, activity_date)`.
- DB-level CHECK/UNIQUE/foreign key rules supplement request validation. SQLite foreign keys are explicitly enabled for both the service and unit tests.
- `received_at` and `measured_at` are stored separately to support delayed reporting. On SQLite, timezone representation can be normalized by the storage layer; use PostgreSQL with `TIMESTAMP WITH TIME ZONE` and UTC conventions for a production design.

## Performance design

Indexes include `vital_signs(patient_id, measured_at)`, `activity_data(patient_id, activity_date)` and an extra `activity_data(activity_date)` index added by migration 0002. These match common time-series, date-filtering, and per-patient listing patterns. Pagination limits a page to 100 rows. The ORM relationships avoid placing activity data inside patient rows, reducing duplication; no historical daily summaries are copied into the measurements table. For production, assess keyset pagination, connection pooling, query plans, partitioning, clinic-scoped row-level access controls and real PostgreSQL load benchmarks.

## Error handling and audit events

`404` means an entity ID was not found. `401` is missing/invalid/expired credentials. `403` indicates insufficient role, ownership, assignment, enrollment or consent. `409` is a database uniqueness or integrity conflict. `422` is invalid input, an unsupported device or an invalid date range. `503` signals audit persistence failure; the API fails closed for access requiring audit, although full transactional audit consistency is future work. Logs avoid payloads and PHI. A correlation header is added to responses, but stored audit-event correlation IDs are currently generated separately; unifying them is a known follow-up.
