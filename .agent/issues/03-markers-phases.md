Title: Telemetry Derivations: Markers & Phases (Entry, Rotation, Exit)

Context
- Detect key markers and phases per turn: brake start, pressure build, peak, release; throttle pickup and opening; apex. Derive Entry/Min/Exit speeds, trail duration, pressure dynamics, pedal coordination.

Scope
- Build a robust event detector that is resilient to telemetry jitter and packet loss (soft windows, hysteresis).
- Produce per‑turn segmentation into phases: Entry → Rotation → Exit.
- Expose derived features needed by Safety Gates, Candidate Generation, Utility Estimator, Reviewer.

Acceptance Criteria (README §2, §10.7, §11 Unit)
- [ ] Detect markers reliably across jitter (unit tests per §11).
- [ ] Provide Entry/Min/Exit speeds, trail braking duration, pressure gradients, throttle pickup timing.
- [ ] Deterministic outputs for offline replay (§10.7).

Design
- Domain services: MarkerDetector, PhaseSegmenter.
- Inputs: PlayerTelemetrySample stream; Outputs: TurnSegments with markers/metrics.
- Use configurable thresholds and hysteresis windows from config (see §12).

References
- Spec: readme_tt_coach_qualitativ_acceptance.md §2, §11
- UDP: C:\Users\yanni\Desktop\f1bot\f1-lap-bot\Data-Output-from-F1-25-v3.txt (Car Telemetry ID 6, Motion Ex ID 13)

