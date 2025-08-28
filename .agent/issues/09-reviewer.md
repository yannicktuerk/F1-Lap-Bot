Title: Reviewer: Classify Attempt/Success/Overshoot/No-Attempt + Drive Intensity Adjustment

Context
- Evaluate next 1-3 valid laps post-tip to classify: Attempt, Success, Overshoot, No Attempt; adjust intensity or switch theme accordingly.

Scope
- Detection patterns:
  - Earlier brake: brake start detectably earlier, no endless coast
  - Pressure faster: steeper build, earlier peak, no front slip red
  - Release earlier: pressure off before apex, calmer hands
  - Earlier throttle: earlier/softer opening without wheelspin
  - Reduce steering: smaller steering plateau before throttle, less counter-steer
- Classifications:
  - Success: better apex/exit speed, no slip red, sector not worse
  - Overshoot: wheelspin/oversteer (exit) or strong front slip (entry), time loss
  - No Attempt: pattern unchanged
- Reactions:
  - Success → next bottleneck or consistency drill
  - Overshoot → one intensity level softer or stability tip
  - No Attempt → micro-drill (same theme, focus), no theme switch

Acceptance Criteria (README §8, §10.3)
- [ ] Reviewer watches next 1-3 valid laps after tip.
- [ ] Reviewer robustly classifies per pattern.
- [ ] On overshoot, intensity reduced or stability focus.
- [ ] On no-attempt, no new theme; micro-drill.

Design
- Application: ReviewerService tracking pending tips and matching patterns.
- Domain: ReviewOutcome enum, PatternMatcher.

References
- Spec: readme_tt_coach_qualitativ_acceptance.md §8, §9, §10.3
