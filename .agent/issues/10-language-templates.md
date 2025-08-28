Title: Language Templates & Qualitative Output (No Numbers!)

Context
- Generate user messages using templates with qualitative intensity words; never mention meters, times, or numbers.

Scope
- Template library for all action types with intensity variations.
- Intensity words:
  - Entry earlier: "etwas früher bremsen", "früher bremsen", "deutlich früher bremsen"
  - Pressure faster: "Druck zügig aufbauen", "Druck schneller aufbauen", "Druck sehr schnell aufbauen"
  - Release earlier: "früher lösen", "klar früher lösen"
  - Early throttle: "etwas früher ans Gas, sanft öffnen", "früher ans Gas, progressiv öffnen"
  - Reduce steer: "Lenkwinkel etwas reduzieren, dann Gas", "Lenkwinkel reduzieren, dann Gas"
- Format: Cause → Action → Focus (1-3 sentences).
- Localization: de/en fully covered.

Acceptance Criteria (README §4, §10.1, §10.6)
- [ ] No numbers/meters/times in user text.
- [ ] Templates used; no generative text.
- [ ] Each message has cause → action → focus structure.

Design
- Application: MessageBuilder using TemplateEngine.
- Infrastructure: LocalizationService for i18n.
- Config: intensity_words mapping (§12).

References
- Spec: readme_tt_coach_qualitativ_acceptance.md §4, §10.1, §10.6, §14
