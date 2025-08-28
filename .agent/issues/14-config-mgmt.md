Title: Configuration Management (YAML-based, hot-reload)

Context
- Provide flexible configuration for all tunable parameters including phase priority, intensity words, slip thresholds, bandit settings, reviewer window.

Scope
- YAML configuration schema matching §12 example.
- Hot-reload capability for runtime adjustments.
- Validation and defaults for all parameters.

Example Config (from spec):
```yaml
phases_priority: [entry, rotation, exit]
intensity_words:
  entry_earlier:    ["etwas früher bremsen", "früher bremsen", "deutlich früher bremsen"]
  press_faster:     ["Druck zügig aufbauen", "Druck schneller aufbauen", "Druck sehr schnell aufbauen"]
  release_earlier:  ["früher lösen", "klar früher lösen"]
  early_throttle:   ["etwas früher ans Gas, sanft öffnen", "früher ans Gas, progressiv öffnen"]
  reduce_steer:     ["Lenkwinkel etwas reduzieren, dann Gas", "Lenkwinkel reduzieren, dann Gas"]
slip_amps:
  exit: {green: [0.0, 0.6], yellow: [0.6, 0.85], red: [0.85, 1.0]}
  entry:{green: [0.0, 0.6], yellow: [0.6, 0.85], red: [0.85, 1.0]}
bandit:
  policy: thompson
  cooldown_laps: 1
  reward_metric: per_turn_split
reviewer:
  window_valid_laps: 3
  outcomes: [attempt, success, overshoot, no_attempt]
```

Acceptance Criteria
- [ ] Configuration loaded from YAML at startup.
- [ ] All tunables exposed and documented.
- [ ] Hot-reload without restart.

Design
- Infrastructure: ConfigurationLoader, ConfigValidator.
- Application: ConfigurationService with change notification.

References
- Spec: readme_tt_coach_qualitativ_acceptance.md §12
