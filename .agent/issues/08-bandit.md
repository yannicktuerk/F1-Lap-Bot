Title: Bandit: Thompson Sampling on Action Classes (+Cooldown, Safe Exploration)

Context
- Personalize choice of one candidate per corner using Thompson Sampling; reward measured as per-turn split of next valid lap; cooldown to avoid over-coaching.

Scope
- Discrete action classes aligned with candidate types.
- Reward: per-turn split on next valid lap; neutral reward on no-attempt or invalid lap.
- Cooldown: do not coach same corner every lap unless clear success/failure.
- Exploration constraint: never explore in red slip states.

Acceptance Criteria (README §7, §10.4)
- [ ] Reward is per-turn split of next valid lap; no learning on no-attempt/invalid.
- [ ] Cooldown prevents over-coaching same corner.
- [ ] No exploration in red states.

Design
- Application: BanditPolicy (Thompson) with per-corner arms and priors.
- Domain: ActionClass, Reward, CornerId.
- Infrastructure: Persistence for bandit state.

References
- Spec: readme_tt_coach_qualitativ_acceptance.md §7, §10.4
