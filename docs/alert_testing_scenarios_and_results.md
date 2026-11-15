# Alert Testing Scenarios and Results
**Shawn Miller | MSCS-699-B01 | University of the Cumberlands | November 15, 2026**

## Test environment and results
I tested the alert extension in Windows PowerShell with Python 3.12 and the existing HealthTrack project. After entering the folder containing `alembic.ini`, I ran:

```powershell
python -m alembic upgrade head
python -m pytest -q
```

All three migrations completed without errors: `0001_initial` (original tables), `0002_activity_lookup` (activity index) and `0003_alert_system` (alert tables). Pytest displayed a fully green progress line ending in `[100%]`, with no failures in the supplied output. It also displayed one Starlette deprecation warning about using `httpx` with `starlette.testclient`; this warning did not cause a test failure.

## Automated test scenarios
The existing suite and `tests/test_alerts.py` cover these scenarios:

| Scenario | Expected outcome | Result |
|---|---|---|
| Critical blood pressure | Critical alert and staff notification | Passed in full test run |
| Normal vital signs | No alert | Passed in full test run |
| Patient-specific threshold | Assigned nurse can customize; patient cannot | Passed in full test run |
| Acknowledge and resolve | Authorized staff changes status; history is recorded | Passed in full test run |
| Escalation | Open critical alert escalates after threshold; duplicate escalation prevented | Passed in full test run |
| Cross-patient access | Unassigned staff cannot view another patient's alerts | Passed in full test run |
| Activity decline | Ten consecutive days of data detect a meaningful step-count decline | Passed in full test run |
| Consent withdrawn | New reading is blocked; no alert generated | Passed in full test run |

The full pytest suite completed successfully during the local run provided on November 15, 2026. These tests cover the coded pathways, but do not prove a production notification service or clinical correctness.

## Additional verification
The benchmark uses synthetic data only. The current system provides in-app notifications, not SMS or email. Background escalation is not automatic; an administrator must run the provided endpoint. Manual production-style load testing and long-running reliability testing were outside the scope of this local validation.
