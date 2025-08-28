Title: Per-Turn Split & Reference Model (reward computation)

Context
- Compute per-turn splits from lap data and derived markers to enable bandit rewards and reviewer success criteria.

Scope
- Define TurnId per track and map telemetry positions to turns.
- Compute per-turn split deltas vs per-corner reference (median p50).
- Provide aggregation to sector and lap if needed.

Acceptance Criteria (README §6–§8, §10.4)
- [ ] Per-turn split available for next valid lap to act as reward.
- [ ] Deterministic across offline replay.

Design
- Domain: TurnCatalogue (track → list of turns), PerTurnSplitCalculator.
- Application: RewardService exposing per-turn reward.

References
- Spec: readme_tt_coach_qualitativ_acceptance.md §2, §6–§8, §10.4
- UDP: C:\Users\yanni\Desktop\f1bot\f1-lap-bot\Data-Output-from-F1-25-v3.txt (Lap Data ID 2, Session ID 1)

