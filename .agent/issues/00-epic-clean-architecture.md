Title: Epic: Clean Architecture Implementation for TT-Coach

Context
- Implement the entire TT-Coach system following Clean Architecture principles with strict layer separation.

Scope
- **Domain Layer (Core):** Business entities, value objects, domain services. No dependencies on external layers.
- **Application Layer (Use Cases):** Application services, use case implementations, port interfaces.
- **Interface Layer (Adapters):** Controllers, presenters, gateways, web/API adapters.
- **Infrastructure Layer (Frameworks & Drivers):** Database implementations, external services, framework-specific code.

Project Structure:
```
src/
├── Domain/
│   ├── Entities/        # Turn, Corner, Driver, etc.
│   ├── ValueObjects/     # TurnId, ActionClass, SafetyLevel, etc.
│   ├── DomainServices/   # MarkerDetector, SlipCalculator, etc.
│   └── Interfaces/       # Repository interfaces
├── Application/
│   ├── UseCases/         # CoachingUseCase, ReviewUseCase
│   ├── Services/         # GatingService, CandidateGenerator, etc.
│   ├── Interfaces/       # Ports for infrastructure
│   └── DTOs/             # PlayerTelemetrySample, SessionInfo, etc.
├── Infrastructure/
│   ├── Persistence/      # Model storage, bandit state
│   ├── ExternalServices/ # UDP listener, ML model service
│   └── Configuration/    # YAML config loader
└── Presentation/
    ├── Controllers/      # REST API if needed
    ├── Presenters/       # Message formatting
    └── ViewModels/       # Coach report structures
```

Acceptance Criteria (from rules document)
- [ ] Inner layers NEVER depend on outer layers
- [ ] Use dependency inversion: interfaces in inner layers, implementations in outer
- [ ] Repositories abstract data access in application layer, implement in infrastructure
- [ ] Use cases are single-responsibility services orchestrating business logic
- [ ] Entities are rich domain models with behavior, not anemic data containers
- [ ] Value objects are immutable domain concepts
- [ ] Port & Adapter pattern used throughout
- [ ] Business logic is framework-agnostic

References
- Rules: Development Guidelines with Clean Architecture Principles
- All sub-issues link back to this epic
