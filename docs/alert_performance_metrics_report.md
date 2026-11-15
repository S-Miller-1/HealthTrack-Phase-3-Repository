# Alert Performance and Reliability Report
**Shawn Miller | MSCS-699-B01 | University of the Cumberlands | November 15, 2026**

## Testing approach
I tested HealthTrack's alert evaluation using `python -m scripts.benchmark_alerts` on a Windows computer running Python 3.12. The script creates fictional patient data in a temporary, in-memory SQLite database. It records the total time to insert a vital-sign reading, evaluate its alert rules, and commit the transaction. This is a local single-process benchmark, not an HTTP load test.

## Measured results
The benchmark ran successfully on November 15, 2026. The output was:

| Measure | Result |
|---|---:|
| Synthetic vital-sign readings | 500 |
| Alerts generated | 100 |
| In-app notification records | 100 |
| Median processing time | 0.510 ms |
| 95th percentile processing time | 1.691 ms |
| Maximum processing time | 6.249 ms |

The automated test suite also reached 100% progress without failures in the provided local execution. The only pytest warning was a third-party Starlette TestClient deprecation notice.

## What the results mean
For this small educational test, the database stored the expected alerts and in-app notifications, and most inserts and alert evaluations finished quickly. This suggests that the alert rules add little overhead in a simple SQLite setting. It does not mean that alerts reach staff in 0.510 milliseconds: staff must open or poll the in-app notification list.

## Reliability and limitations
Each alert uses a unique source key to prevent duplicates. Status changes, acknowledgments, resolutions and escalation events are stored for review. High-priority alerts are not suppressed by low-priority alerts. Escalation occurs when an administrator invokes the escalation-check endpoint: the project does not have an always-running scheduler or external delivery channel.

Performance may differ with larger databases, concurrent requests, network delay, or downtime. This prototype is not clinically validated or intended for real patient use. The measurements are limited to the synthetic single-process workload; no uptime or delivery-time guarantees are claimed.
