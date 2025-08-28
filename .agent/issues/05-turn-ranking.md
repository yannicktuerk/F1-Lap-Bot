Title: Turn Ranking by Impact (IQR-normalized vs Reference)

Context
- Rank corners by impact using deltas vs per-corner references (median p50 and IQR) filtered by assists/device.

Scope
- Compute per-corner references from historical valid laps; prefer faster mode when multiple lines exist.
- Normalize driver deltas by IQR to get robust per-corner impact.
- Output top candidates per lap.

Acceptance Criteria (README §3, §10.5)
- [ ] References per corner use median & IQR (assists/device filtered).
- [ ] For multiple corner lines, prefer faster mode.
- [ ] With high inconsistency, surface consistency drill before pace tips.

Design
- Domain: ReferenceModel repository; Statistics service for IQR.
- Application: CornerRanker producing ranked list of corners.

References
- Spec: readme_tt_coach_qualitativ_acceptance.md §2, §3, §10.5

