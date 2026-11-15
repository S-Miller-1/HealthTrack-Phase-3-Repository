# Alert Configuration and Escalation Policy
**Shawn Miller | MSCS-699-B01 | University of the Cumberlands | November 2026**

## Purpose
This HealthTrack extension checks submitted vital signs and activity records and creates alerts for the assigned care team. The thresholds are examples for a fictional classroom prototype, not clinically validated patient-care guidelines.

## Vital-sign rules
The initial monitoring ranges are systolic blood pressure 90–139, diastolic blood pressure 60–89, and pulse 50–100. Values beyond these configurable ranges trigger a **high** alert. Fixed classroom **critical** triggers are systolic pressure at least 180 or below 80, diastolic pressure at least 120, or pulse below 40 or above 130. Critical triggers override customized ranges. Any reading that stays within the ranges creates no alert. Each reading is evaluated when entered through the existing FastAPI endpoint.

An assigned nurse or clinician can use `PUT /patients/{id}/alert-config` to adjust all six minimum and maximum values for a patient. Validation rejects a minimum that is not lower than its maximum. Patients can see their settings but cannot change them. The care-team assignment controls access to each patient's configuration.

## Activity and priority rules
A **low** alert is raised when the average number of steps over the latest three consecutive days falls below half the average over the preceding seven consecutive days, assuming at least 1,000 baseline steps. The rule requires ten consecutive dates to avoid drawing conclusions from incomplete data. A separate administrator-run check identifies patients missing activity records for at least two days. Activity rules represent changes worth reviewing, not diagnoses.

Priority is critical, high, then low. Repeated evaluation of the same source reading or date does not create duplicate alerts. New low-priority alerts are suppressed while an unresolved high or critical alert exists for the patient, reducing repeated low-value notifications.

## Notifications, acknowledgment and escalation
All alerts are stored in the database. On creation, an in-app inbox entry is generated for each active assigned nurse or clinician. Notifications reference the alert rather than embedding measurement values. Staff can acknowledge and resolve alerts; each transition is recorded with the acting user and timestamp. The history API displays the timeline.

Critical alerts are intended for immediate review. A critical alert still open after 15 minutes is eligible for escalation; a high alert still open after 60 minutes is eligible. Escalation adds an event and new in-app staff notifications. It occurs **only when** an administrator invokes `POST /alerts/process-escalations`; no external channel or automatic background scheduler is included. Acknowledged or resolved alerts are not escalated. These time limits are coursework policies rather than validated clinical service levels.

## How changes are made
An assigned nurse or clinician updates configuration through the documented authenticated API. Fixed critical boundaries, activity rules and escalation intervals are code-level settings that require a reviewed application change and regression tests. The current prototype is restricted to fictional data and has no external paging guarantee.
