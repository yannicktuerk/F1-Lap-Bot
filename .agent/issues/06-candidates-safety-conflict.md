Title: Candidate Generation, Safety Gates & Conflict Resolver (1 action/turn, phase priority)

Context
- Generate up to 3 candidate actions per corner (Entry → Rotation → Exit) and enforce safety gates and conflict rules to choose exactly one action per corner.

Scope
- Candidate types:
  - Entry: earlier brake; build pressure faster
  - Rotation: release earlier
  - Exit: earlier throttle, progressive; reduce steering, then gas
- Safety gates:
  - Exit red → never early throttle; choose steering reduction
  - Entry red → block pressure faster; choose earlier brake
  - Yellow → only soft/progressive variants
- Conflict rule: max one action per corner; phase priority Entry → Rotation → Exit

Acceptance Criteria (README §3–§5, §10.1, §10.2)
- [ ] Max one action per corner; max three corners per lap.
- [ ] Safety constraints applied exactly as specified.
- [ ] Phase priority respected.

Design
- Application: CandidateGenerator → SafetyGateResolver → ActionSelector.
- Domain enums: Phase, ActionClass, SafetyLevel.

References
- Spec: readme_tt_coach_qualitativ_acceptance.md §3–§5, §10.1, §10.2

