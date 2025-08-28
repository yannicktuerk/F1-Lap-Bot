Title: ML Utility Estimator (light GBDT) + Fallback Heuristic

Context
- Estimate expected time gain per candidate action using lightweight ML (e.g., GBDT) with confidence bands; fallback to heuristic when insufficient data.

Scope
- Inputs: corner type, Entry/Min/Exit speeds, internal deltas, slip bands, candidate type, assists, device.
- Output: expected corner/sector split improvement with confidence interval.
- Train incrementally from realized rewards (per-turn split after coaching).
- Conservative heuristic when confidence is low or data is sparse.

Acceptance Criteria (README §6, §10.3)
- [ ] ML provides expected gain with uncertainty band.
- [ ] Fallback heuristic used when data insufficient.
- [ ] Model trained incrementally from reviewer feedback (per-turn split rewards).

Design
- Application: UtilityEstimatorService using ML library (scikit-learn/XGBoost).
- Infrastructure: ModelPersistence for saving/loading models.
- Domain: ActionUtility value object.

References
- Spec: readme_tt_coach_qualitativ_acceptance.md §6
