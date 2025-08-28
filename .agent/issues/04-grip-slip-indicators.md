Title: Grip/Slip Indicators & Safety Ampels (Green/Yellow/Red)

Context
- Compute grip and slip indicators from telemetry (slip ratio, slip angle, forces) to gate safety decisions.
- Map to Entry‑Slip and Exit‑Slip "traffic lights" (green/yellow/red) as safety constraints for coaching.

Scope
- Use Motion Ex packet data and Car Telemetry to derive slip ratio (longitudinal) and slip angle (lateral).
- Provide configurable banding for green/yellow/red thresholds (see §12 example).
- Expose Entry‑Ampel and Exit‑Ampel per turn for Safety Gates.

Acceptance Criteria (README §5, §10.2)
- [ ] Exit‑Slip red always blocks early throttle tips; suggests "reduce steering, then gas" (§10.2).
- [ ] Entry‑Slip red blocks "pressure faster"; suggests "brake earlier" instead (§10.2).
- [ ] Yellow restricts to safe/progressive formulations (§10.2).
- [ ] Unit tests cover boundary conditions and correct ampel assignment (§11).

Design
- Domain service: SlipCalculator computing slip metrics.
- Application service: SafetyAmpelService mapping metrics to green/yellow/red per phase.
- Config: slip_amps thresholds (§12).

References
- Spec: readme_tt_coach_qualitativ_acceptance.md §5, §10.2
- UDP: C:\Users\yanni\Desktop\f1bot\f1-lap-bot\Data-Output-from-F1-25-v3.txt (Motion Ex ID 13 for extended physics)
