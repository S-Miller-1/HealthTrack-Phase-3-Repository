# Dashboard UI Design | Shawn Miller
MSCS-699-B01 • University of the Cumberlands • November 2026

## Purpose and layout
I built the HealthTrack monitoring page to let a care-team member check a fictional patient's recent blood pressure, pulse, and daily activity without searching through API responses. The interface is a Dash application that runs alongside our existing FastAPI service. It uses the current database and permission rules instead of creating another patient list.

The top section contains the HealthTrack name and an educational-use notice. A compact sign-in panel and a patient selector sit beneath it. A status bar then calls attention to the latest reading, using green for a normal demonstration reading, amber for a warning, and red for a critical demonstration reading. Five large cards show systolic pressure, diastolic pressure, pulse, steps, and active minutes. Under the cards, Plotly plots show blood pressure and pulse over time and steps by date.

## Components and interactions
A nurse, clinician, or patient signs in with an existing demonstration account. The dropdown only lists records that account can view, and only patients with active enrollment and consent appear. After choosing a patient, the browser opens an authenticated WebSocket connection. The screen changes when a reading or activity record changes. If the connection is interrupted, a ten-second refresh provides a backup. The user can choose a different assigned patient, inspect Plotly's hover values, or sign out.

The pressure chart has a dashed reference at 140 mmHg systolic; the pulse plot has a dashed reference at 105 bpm. The banner evaluates the latest recorded blood pressure and pulse using separate demonstration warning and critical thresholds. These thresholds are *not* validated clinical protocols, and this student prototype must not be used for healthcare decisions.

## Design decisions
I kept the layout fairly simple because the values and alerts should be easier to find than the controls. Wide cards work on a desktop, while a responsive layout stacks cards and charts on smaller screens. Colors are paired with alert text so users do not have to rely on color alone.

I reused the Phase 3 role-based patient assignments, consent status, SQLAlchemy models, and JWT authentication. The server only sends a snapshot when its underlying data changes, reducing needless chart redraws. It also limits its queries to the latest 60 vital readings and 14 activity days. In this educational build, updates are pushed over a WebSocket after a two-second database check; they are not connected to live medical devices.

## Limitations
The database has blood pressure, pulse, steps, and active minutes. I deliberately did not invent oxygen saturation or temperature because those fields are not stored in Phase 3. This is a fictional demonstration, not a HIPAA-compliant clinical system. A production design would need a reviewed alert protocol, secure deployment, external authentication, logging, and validated medical-device integration.
