# Phase 3 test results (verified execution)

**Execution context:** Python 3.13.5, SQLAlchemy 2.0.50, FastAPI 0.128.2, SQLite in-memory TestClient fixtures. Tests executed with `python -m pytest --cov=app --cov-report=term-missing --disable-warnings` on November 8, 2026. The counts below are the actual local result, not an estimate.

**Results:** **33 passed, 0 failed** in **9.73 seconds**. Total application statement coverage: **94% (431 statements, 26 missed)**.

Coverage by module: `app/models.py` **100%**, `app/schemas.py` **100%**, `app/crud.py` **96%**, `app/main.py` **92%**, `app/security.py` **88%**, `app/database.py` **81%**. Individual tests and uncovered line locations are recorded in `test_results_raw.txt`.

Test categories: adult age enforcement; minimum/maximum blood pressure and pulse; logical pressure ordering; timestamp timezone and future limit; activity ranges/future dates; database CHECK/UNIQUE/FK/cascade/assignment constraints; missing/bad auth; patient access boundaries; nurse assignment scope; restriction on admin chart access; complete patient/vital/activity CRUD; date range and pagination; duplicate activity conflict; invalid connected cuff data; consent gate; owner-only edits; auditing.

**Migration verification:** `python -m alembic upgrade head` completed migrations `0001_initial` and `0002_activity_lookup`, then `alembic current` reported `0002_activity_lookup (head)`.

**Known untested/unfinished areas:** external identity provider/MFA; real HTTPS; managed keys, rate limiting and backup restore; post-deletion patient retention; tamper-resistant audit; cross-clinic isolation; load/concurrency tests; durable reading revisions; mobile/wearable device integration. Unit tests run against SQLite and do not establish PostgreSQL production performance or regulatory compliance.
