# Alert Testing Scenarios and Results
**Shawn Miller | MSCS-699-B01 | University of the Cumberlands**

The repository includes `tests/test_alerts.py`, using the existing synthetic HealthTrack test fixture and isolated SQLite database. It checks the new functionality alongside existing authorization and consent controls.

| Scenario | Expected outcome | Result |
|---|---|---|
| Critical blood-pressure reading | Critical alert and staff inbox record | Automated test added; execution pending |
| Normal vital signs | No alert | Automated test added; execution pending |
| Custom per-patient thresholds | Assigned nurse updates range; patient cannot | Automated test added; execution pending |
| Acknowledgment and resolution | Status changes; actor/timestamps appear in history | Automated test added; execution pending |
| Critical escalation after 15 minutes | One escalation; no repeat escalation | Automated test added; execution pending |
| Cross-patient access | Nurse cannot read unassigned patient alerts | Automated test added; execution pending |
| Ten-day activity decline | Low-priority activity alert | Automated test added; execution pending |
| Withdrawn consent | New vital submissions denied; no alert generated | Automated test added; execution pending |

Run `python -m alembic upgrade head` against a local development database and `python -m pytest -q` from the repository root. Record actual passed/failed totals and repair any failures before final submission. **No successful execution of the newly integrated tests has been independently verified yet**; this table is not a fabricated passing-test report.

Additional manual checks recommended: deduplication, suppression when a high alert is active, read/unread notification state, and alert filtering by severity and status. Do not use real patient information.
