# Alert Performance and Reliability Report
**Shawn Miller | MSCS-699-B01 | University of the Cumberlands**

## Measurement plan
The performance benchmark in `scripts/benchmark_alerts.py` runs with fictional readings against a temporary SQLite database. It measures the elapsed time for alert evaluation and database commit for 500 synthetic vital readings, reports median, 95th percentile and maximum durations, and counts generated alerts and notifications. Repeated runs should be compared only on the same machine.

## Results
The benchmark script has been added, but has **not been executed and validated in the integrated GitHub repository**. Therefore, no verified latency, throughput or success-rate measurements are claimed in this report. Run the script and attach its JSON output before final submission:

```powershell
python -m scripts.benchmark_alerts
```

The earlier Phase 3 database retrieval measurements are not alert-system measurements and should not be presented as such.

## Reliability controls and limitations
A unique source key prevents duplicate alerts for the same reading or activity date. A relational record tracks alert status, times, acknowledgments, resolutions and escalations. Escalation is idempotent after the first successful check. Authorization limits notification access to the recipient; alert checks occur within the app's database transaction.

The implementation uses polling of stored in-app notifications rather than pushed notifications. It has no durable delivery queue, external paging integration, or autonomous periodic escalation worker. A slow or unavailable database can delay both ingestion and alerts; the code does not claim continuous uptime. Performance results from local SQLite do not prove production concurrency or real-time clinical safety.

## Verification steps
Execute the full test suite and benchmark; note environment, Python version and machine, sample count, median, p95, maximum and errors. Investigate any missed or duplicated alerts. This educational project should not be used for healthcare decisions or production monitoring.
