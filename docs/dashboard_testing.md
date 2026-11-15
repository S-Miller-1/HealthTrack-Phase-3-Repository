# Dashboard Testing Documentation | Shawn Miller
MSCS-699-B01 • November 2026

## Testing plan
The dashboard is checked at three levels: unit tests for classification and data selection, permission tests with the existing FastAPI test database, and manual browser checks of the real-time interface. The tests use fictional patients only. The automated checks validate logic and permission boundaries, but they do not replace an end-to-end browser test.

| Area | How to check | Expected result |
| --- | --- | --- |
| Application startup | Start `python -m uvicorn dashboard.run:app`; open `/dashboard/` | Dashboard loads without errors |
| First render | Open the page with a new local database | Empty cards and a clear sign-in prompt |
| Role access | Sign in as assigned nurse and then as admin | Nurse sees assigned patient; admin cannot view charts |
| Patient isolation | Try a patient ID without assignment | Monitoring stream closes; no data shown |
| Accuracy | Enter a manual 132/84 reading with pulse 72 | Cards and plots show the saved numbers |
| Warning alert | Enter 150/95 with pulse 82 | Amber warning banner |
| Critical alert | Enter 185/122 with pulse 82 | Red critical banner |
| Real-time push | Open browser devtools WebSocket view; add reading via API | New JSON frame appears and Plotly updates after the next ~2 s check |
| Connection fallback | Block `/ws/monitor`; create a new activity record | Ten-second polling still updates the page |
| Consent boundary | Disable monitoring consent for an enrolled patient | Stream closes; patient is not returned on next login |
| Loading performance | Use browser Network/Performance panel on local machine | Record initial page load time, chart render, and connection latency |
| Load check | Use several browser sessions while writing demo readings | No wrong-patient data, errors or significant responsiveness loss |

## Automated checks
Run `python -m pytest tests/test_dashboard_monitor.py -v`, then `python -m pytest -v`. The new tests cover normal/warning/critical thresholds, ordering of readings, activity history, and assignment-based chart access. The pre-existing Phase 3 tests also need to remain passing.

## Verified local test results (November 15, 2026)

Shawn ran the project on **Windows with Python 3.12.10** using a local SQLite database populated with fictional sample readings.

| Test or observation | Actual result | Status |
| --- | --- | --- |
| Automated test suite | `python -m pytest -v`: **44 passed, 3 warnings in 42.77 seconds** | PASS |
| Dash initial display | Patient selector, five summary cards and three Plotly graphs rendered using sample records | PASS |
| API data insertion | Authenticated `POST /patients/1/vitals` with sample 185/122 mmHg and pulse 95 returned **201 Created** | PASS |
| Live browser connection | Dashboard reported **Live WebSocket connected** after installing WebSocket support for Uvicorn | PASS |
| Warning presentation | Sample reading 151/94 mmHg, pulse 91 displayed with amber warning banner | PASS |
| Critical presentation | Most recent sample reading **185/122 mmHg, pulse 95** displayed with a red critical banner | PASS |
| Trend data update | New sample reading appeared on pressure and pulse trend charts | PASS |
| Data ordering | Earlier local-offset sample reading appeared on charts but was not selected as latest; using a current UTC timestamp displayed the expected current sample reading | OBSERVED; timestamp normalization warrants a follow-up review |
| Automatic browser rendering | Live dashboard rendered updated sample reading and red alert in browser | PASS, exact push latency not measured |
| Initial page-load performance | Not measured with browser performance tools | NOT YET MEASURED |
| Concurrent-user load | Not measured | NOT YET MEASURED |
| Blocked-WebSocket fallback | Periodic updates observed while WebSocket dependency was initially missing; controlled fallback test not separately timed | PARTIALLY OBSERVED |

The three automated-test warnings concerned package deprecations in Dash, Starlette's testing integration, and Starlette WSGI middleware; they did not fail the suite. The early local WebSocket connection failed because the installed Uvicorn lacked a WebSocket transport. This was corrected by installing `uvicorn[standard]`, and the repository dependency was updated accordingly.

These results come from the supplied local console output and browser screenshots. No performance measurement or production clinical validation is being claimed. Thresholds and patient information are fictional for coursework.

## Results and limitations
**Automated and browser outcomes must be captured from the execution environment.** No full browser load time or live WebSocket latency measurement is claimed here without a recorded test run. For a complete submission, attach a browser screenshot of the cards and plots, a screenshot of a red or amber demonstration alert, a terminal screenshot of passing tests, and a screenshot of the WebSocket frames or Network panel. Record measured milliseconds rather than estimates.

The current WebSocket implementation checks SQLAlchemy data roughly every two seconds and pushes a frame only when the content changes. A separate Dash interval refresh runs every ten seconds as a fallback; it is not a direct device feed. Its thresholds are deliberately illustrative, and security testing for a clinical deployment is outside the scope of this assignment.
