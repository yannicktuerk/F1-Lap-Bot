Title: Main Orchestration: TT-Coach Use Case & Pipeline Integration

Context
- Orchestrate the entire coach pipeline from UDP ingest to report generation within 150ms.

Scope
- Main use case coordinating all services:
  1. Receive lap completion event
  2. Run turn ranking
  3. Generate candidates
  4. Apply safety gates
  5. Estimate utility
  6. Bandit selection
  7. Generate message
  8. Track for review
- Dependency injection for all services
- Event-driven architecture where appropriate

Acceptance Criteria
- [ ] Full pipeline executes in <150ms
- [ ] Clean separation between layers maintained
- [ ] All services properly injected
- [ ] Graceful error handling

Design
- Application: CoachingUseCase as main orchestrator
- Event bus for loose coupling
- Circuit breaker for external dependencies

References
- Spec: readme_tt_coach_qualitativ_acceptance.md §3 (pipeline overview)
- All component issues feed into this orchestration
