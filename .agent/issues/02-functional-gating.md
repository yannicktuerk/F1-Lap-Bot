Title: Functional Gating: TT‑only, Valid‑only, Player‑only

Context
- Enforce the three gating rules across the ingest and processing pipeline so that only relevant data feeds the coach.

Scope
- Identify Time Trial sessions via Session packet and/or Time Trial packet; hard‑gate all non‑TT.
- Filter to player car using m_playerCarIndex and participants mapping.
- Ensure only valid laps are used for analysis, utility, and learning.
- Provide explicit metrics/counters for filtered events for observability.

Acceptance Criteria (README §10.1)
- [ ] Only Time Trial sessions are processed.
- [ ] Only valid laps flow into analysis and learning.
- [ ] Only player car data is processed.
- [ ] Unit tests cover gating logic and edge cases (e.g., session switch mid‑run, splitscreen index 255, invalid laps).

Design (Clean Architecture)
- Application Layer policy service: GatingService applying rules on incoming DTOs.
- Ports: exposed from TelemetryIngest to GatingService.
- Infrastructure: none beyond signals; all business rules in application layer.

References
- Spec: readme_tt_coach_qualitativ_acceptance.md §1, §10.1
- UDP: C:\Users\yanni\Desktop\f1bot\f1-lap-bot\Data-Output-from-F1-25-v3.txt (Session ID 1, Time Trial ID 14, Header.playerCarIndex)

