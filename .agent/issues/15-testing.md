Title: Testing Strategy: Unit, Integration, E2E, Scenario-based

Context
- Comprehensive testing pyramid ensuring quality and robustness.

Scope
Unit Tests (§11):
- Event detector: Entry/Rotation/Exit patterns correct, robust against jitter
- Slip ampel: boundary cases for green/yellow/red
- Language: no number tokens in output

Integration Tests (Replay runs, §11):
- A-Green Exit, no attempt → Reviewer reports no attempt, coach repeats focus, bandit neutral
- A-Green Exit, attempt→wheelspin → Reviewer overshoot, coach reduces intensity
- B-Rotation, attempt→success → Follow-up tip on exit, bandit reinforces
- C-Entry, attempt→front slip red → Switch to "earlier brake", no pace escalation
- D-Exit slip red → Never early gas tip, always stability hint

E2E Tests:
- 10 mixed rounds:
  - ≤3 tips/lap, 1/corner
  - Bandit rewards consistent
  - PB/sector PB rate improves significantly post-coaching

Coverage Targets (Clean Architecture):
- Domain layer: 90% branch coverage
- Use case layer: 80%
- Infrastructure: 60%

Acceptance Criteria (§10.7, §11)
- [ ] All unit tests green
- [ ] All integration scenarios pass
- [ ] E2E demonstrates measurable improvement
- [ ] Coverage targets met

Design
- Testing framework with replay capability
- Mock UDP source for deterministic testing
- Scenario runner for integration tests

References
- Spec: readme_tt_coach_qualitativ_acceptance.md §11, §10.7
