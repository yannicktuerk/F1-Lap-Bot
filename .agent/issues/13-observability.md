Title: Observability: Structured Logging, KPI Dashboard

Context
- Log every recommendation and track KPIs for coach effectiveness.

Scope
- Structured logs for: action type, context, expected utility, confidence, reviewer result, real delta split.
- KPI dashboard showing:
  - Per-turn delta split distribution
  - Hit rate (attempt detection rate)
  - Success rate (success without red)
  - PB/sector PB rate improvement
- Real-time metrics and offline analysis.

Acceptance Criteria (README §10.8)
- [ ] Each recommendation logged with all context.
- [ ] KPI dashboard displays metrics.

Design
- Infrastructure: StructuredLogger, MetricsCollector, DashboardService.
- Application: ObservabilityFacade coordinating logs and metrics.

References
- Spec: readme_tt_coach_qualitativ_acceptance.md §10.8
