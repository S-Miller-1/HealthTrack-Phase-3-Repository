# Phase 2 → Phase 3 design continuity

The attached Phase 2 rationale describes a **consent-based, 50-patient, 16-week, single-clinic hypertension pilot** and a larger 17-table schema with 43 operations across 29 paths. The Phase 3 instructions specifically require SQLAlchemy `Patient`, `VitalSigns`, and `ActivityData`, so the deliverable implements those plus authentication (`User`), care-team assignment (`PatientAssignment`) and generic audits (`AuditEvent`). **It is a limited prototype rather than a complete implementation of the existing Phase 2 contract.**

| Earlier design requirement | Phase 3 treatment |
|---|---|
| Adult admission | Implemented with DOB validation in Pydantic |
| Patient/reading relationship | Implemented through foreign keys and ORM relationships |
| UTC measurement and receive times | Both timestamps modeled |
| Enrollment and unrevoked monitoring consent | Gated for new vitals and activities via API |
| Assigned care-team access | Assignment table and role/ownership authorization |
| Time-range filtering and indexes | Implemented per patient with composite indexes |
| Validated connected cuff | Device source explicitly rejected until validated device registry exists |
| Per-patient threshold approval; alert dispositions | Not implemented in Phase 3 subset |
| Immutable reading revisions / correction reasons | Not implemented; PUT corrections are a teaching simplification |
| Unrevoked caregiver grants | Not implemented (optional later phase) |
| OIDC with staff MFA, clinic isolation | Not implemented; prototype instead uses local JWT issuance |
| Audited reads, exports, denials | Basic generic read/write audit; no export or denied-request audit; needs extension |
| Full HIPAA controls / backup recovery / notifications | Not implemented and not claimed |

Further implementation should replace hard deletes with approved retention/soft-deletion rules, add transactional read-revision history, complete clinic-level row isolation, use a trusted external identity provider and MFA, validate connected devices, complete all original data models and operations, and secure deployment and incident response before real-data use.
