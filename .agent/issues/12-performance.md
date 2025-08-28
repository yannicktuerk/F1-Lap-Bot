Title: Performance & Real-time Requirements (<150ms report generation)

Context
- Coach report must be available within 150ms of lap completion for seamless UX.

Scope
- Profile and optimize all computation from lap end detection to report output.
- Use caching, pre-computation, incremental algorithms where possible.
- Handle packet drops gracefully without blocking.

Acceptance Criteria (README §10.7)
- [ ] Coach report ≤150ms after lap end.
- [ ] No exceptions on packet drops/jitter.
- [ ] Deterministic for offline replay.

Design
- Application: CacheWarmer for references/models; StreamingAggregator for incremental computation.
- Infrastructure: Performance monitoring, metrics collector.

References
- Spec: readme_tt_coach_qualitativ_acceptance.md §10.7
