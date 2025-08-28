Title: Infra: UDP Listener + Packet Decoder (F1® 25 v3) for TT-only Player Telemetry

Context
- Implement the UDP ingest pipeline for F1® 25 v3, focusing on Time Trial sessions and the player car only, as the foundation for the TT‑Coach.
- Clean Architecture: define an application port for TelemetryIngest, implement infrastructure adapter(s) to read and decode UDP packets into domain DTOs.

Scope
- UDP listener and packet decoder for these packets (Little Endian):
  - PacketHeader (session timestamp, frame identifiers, playerCarIndex)
  - Session (ID 1) — session type, track ID, remaining time
  - Lap Data (ID 2) — per‑car lap timing and validity
  - Event (ID 3) — notable events; use if needed for lap start/end markers
  - Participants (ID 4) — to map player index if necessary
  - Car Telemetry (ID 6) — speed, throttle, brake, steering, gear, etc.
  - Motion Ex (ID 13) — extended physics (optional for slip estimation)
  - Time Trial (ID 14) — TT‑specific info
- TT‑only, Valid‑only, Player‑only gating at ingest boundary.
- Provide high‑rate stream aggregation by frame into a PlayerTelemetrySample for downstream processing.
- Handle packet loss/jitter gracefully (soft windows, no exceptions).

Design (Clean Architecture)
- Application layer port (interface): TelemetryIngestPort with callbacks/events: onSession, onLapData, onCarTelemetry, onTimeTrial.
- Infrastructure adapter: UdpTelemetryAdapter (binds UDP, decodes packets from Data-Output spec, maps to DTOs).
- Domain/application DTOs: PlayerTelemetrySample, SessionInfo, LapInfo, TimeTrialInfo.
- Gating strategy: ignore all non‑TT sessions and non‑player cars; only push valid laps downstream.
- Time source: use m_sessionTime and frame identifiers as primary clocks.

Acceptance Criteria (maps to README §10)
- [ ] TT‑Only: Only Time Trial sessions are processed (§10.1).
- [ ] Valid‑Only: Only valid laps flow into analysis/learning (§10.1).
- [ ] Player‑Only: Only player car data is ingested (§10.1).
- [ ] Packet loss/jitter does not throw exceptions; soft windows are used (§10.7).
- [ ] The adapter exposes derived timing markers required later (lap start/end, sector boundaries if applicable) or sufficient primitives to derive them reliably.

Implementation Notes
- Decode Little Endian per Data‑Output spec.
- Use playerCarIndex from header to filter arrays.
- Lap validity signals are in Lap Data/Time Trial packets; reconcile with lap start/end detection.
- Provide a thin decoding layer and a mapping layer; keep domain free of protocol specifics.

References
- Spec: readme_tt_coach_qualitativ_acceptance.md (root of TT‑Coach requirements)
- UDP: C:\Users\yanni\Desktop\f1bot\f1-lap-bot\Data-Output-from-F1-25-v3.txt (Packet Header, Packet IDs table; Session, Lap Data, Car Telemetry, Time Trial)

