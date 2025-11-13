# F1 Lap Bot Telemetry System - Implementation Roadmap

This document defines the recommended order for implementing the telemetry system expansion (Issues #32-63).

## Overview

The implementation follows a **bottom-up approach** respecting Clean Architecture principles:
1. Domain Layer (entities, value objects, interfaces)
2. Infrastructure Layer (database, persistence)
3. Domain Services (algorithms, business logic)
4. Application Layer (use cases)
5. Presentation Layer (API, Discord commands)
6. Testing & Documentation

---

## Phase 1: Foundation - Domain Model & Persistence (Issues #32-37)

**Goal:** Establish core domain entities and database foundation.

### Priority Order:

1. **#35 - Define TelemetryRepository Interface**
   - Depends on: #32, #33, #34
   - Domain layer contract for persistence

5. **#36 - Implement SQLite Database Schema**
   - Can be done in parallel with domain modeling
   - Defines tables: sessions, lap_telemetry, car_setups, lap_metadata

6. **#37 - Implement SQLiteTelemetryRepository**
   - Depends on: #35, #36
   - Maps domain entities to database
   - **Completes Phase 1**

**Checkpoint:** After Phase 1, you can persist and retrieve telemetry data.

---

## Phase 2: Track Reconstruction (Issues #38-42)

**Goal:** Build track geometry from telemetry data.

### Priority Order:

7. **#38 - Implement Centerline Computation Algorithm**
   - Depends on: #32 (TelemetrySample)
   - Core algorithm for track reconstruction

8. **#39 - Implement Curvature Calculation**
   - Depends on: #38 (centerline output)
   - Extends TrackReconstructor

9. **#40 - Implement Elevation Profile Extraction**
   - Depends on: #38 (centerline)
   - Can be done in parallel with #39

10. **#41 - Create TrackProfile Value Object**
    - Depends on: #38, #39, #40
    - Encapsulates all track geometry

11. **#42 - Create ReconstructTrackUseCase**
    - Depends on: #37, #38-41
    - Orchestrates track reconstruction
    - **Completes Phase 2**

**Checkpoint:** After Phase 2, you can reconstruct track geometry from laps.

---

## Phase 3: Mathe-Coach (Physics-Based Coaching) (Issues #43-48)

**Goal:** Implement physics-based lap analysis and feedback.

### Priority Order:

12. **#44 - Create IdealLap Value Object**
    - Can be done early (simple data structure)
    - No complex dependencies

13. **#43 - Implement IdealLapConstructor**
    - Depends on: #41 (TrackProfile), #44 (IdealLap VO)
    - Core physics calculations

14. **#45 - Implement LapComparator**
    - Depends on: #34 (LapTrace), #44 (IdealLap), #41 (TrackProfile)
    - Compares actual vs ideal

15. **#46 - Implement MatheCoachFeedbackGenerator**
    - Depends on: #45 (LapComparator output)
    - Generates human-readable feedback

16. **#47 - Create MatheCoachAnalysisUseCase**
    - Depends on: #42, #43, #45, #46
    - Orchestrates full Mathe-Coach pipeline

17. **#48 - Add /lap coach Discord Command**
    - Depends on: #47
    - Exposes Mathe-Coach via Discord
    - **Completes Phase 3**

**Checkpoint:** After Phase 3, users can request physics-based coaching via Discord.

---

## Phase 4: KI-Coach (AI-Based Coaching) (Issues #49-56)

**Goal:** Implement optimal lap planning with world model.

### Priority Order:

18. **#49 - Define WorldModelState Representation**
    - Independent VO
    - Foundation for world model

19. **#50 - Define WorldModelAction Representation**
    - Independent VO
    - Can be done in parallel with #49

20. **#51 - Implement IWorldModel Interface and StubWorldModel**
    - Depends on: #49, #50
    - Stub implementation for testing

21. **#53 - Create OptimalLap Value Object**
    - Can be done early (data structure)
    - Similar to IdealLap

22. **#52 - Implement Dynamic Programming Planner**
    - Depends on: #41 (TrackProfile), #51 (IWorldModel), #53 (OptimalLap)
    - Complex algorithm, may take time

23. **#54 - Implement KICoachFeedbackGenerator**
    - Depends on: #53 (OptimalLap), #34 (LapTrace)
    - Generates AI-coach feedback

24. **#55 - Create KICoachAnalysisUseCase**
    - Depends on: #42, #51, #52, #54
    - Orchestrates KI-Coach pipeline

25. **#56 - Add /lap kicoach Discord Command**
    - Depends on: #55
    - Exposes KI-Coach via Discord
    - **Completes Phase 4**

**Checkpoint:** After Phase 4, users can request AI-powered optimal lap feedback.

---

## Phase 5: Integration & Infrastructure (Issues #57-59)

**Goal:** Complete system integration and real-time telemetry ingestion.

### Priority Order:

26. **#57 - Create Session Management Use Case**
    - Depends on: #37 (ITelemetryRepository extended)
    - Session lifecycle management

27. **#59 - Implement Telemetry Ingestion Service**
    - Depends on: #32, #33, #34, #37
    - **Critical:** Bridges UDP listener to domain
    - Real-time telemetry persistence

28. **#58 - Extend HTTP API with Telemetry Endpoints**
    - Depends on: #37, #47, #55
    - REST API for external tools
    - **Completes Phase 5**

**Checkpoint:** After Phase 5, full system integration complete with real-time telemetry.

---

## Phase 6: Quality & Documentation (Issues #60-63)

**Goal:** Ensure quality, testability, and maintainability.

### Priority Order:

29. **#60 - Add Unit Tests for Domain Layer**
    - Should be done **incrementally** throughout Phases 1-4
    - Target: ≥90% coverage
    - Test domain entities, VOs, services

30. **#61 - Add Integration Tests**
    - Should be done **incrementally** after use cases are complete
    - Target: ≥80% application, ≥60% infrastructure
    - Test end-to-end flows

31. **#63 - Implement Database Migration System**
    - Depends on: #36 (schema defined)
    - Can be done in parallel with other work
    - Important for future schema evolution

32. **#62 - Update Documentation**
    - Should be done **continuously** throughout implementation
    - Final comprehensive review at end
    - **Completes Phase 6**

**Checkpoint:** After Phase 6, system is production-ready with full documentation.

---

## Recommended Implementation Strategy

### Parallel Work Streams

You can work on multiple issues in parallel if you have multiple developers:

**Stream A (Core Domain):**
- Phase 1 → Phase 2 → Phase 3
- Focus: #32-48

**Stream B (Infrastructure):**
- #36, #37 (early) → #63 → #57, #59
- Focus: Database and persistence

**Stream C (Testing):**
- #60 (continuously) → #61
- Focus: Quality assurance

**Stream D (Advanced Features):**
- Phase 4 (after Phase 2 complete)
- Focus: #49-56

### Critical Path

The **minimum viable product (MVP)** requires:
1. Phase 1 (Foundation) - **~2-3 weeks**
2. Phase 2 (Track Reconstruction) - **~2 weeks**
3. Phase 3 (Mathe-Coach) - **~2 weeks**
4. #59 (Telemetry Ingestion) - **~1 week**
5. Basic tests (#60, #61) - **~1 week**

**Estimated MVP timeline: ~8-9 weeks**

Full implementation including KI-Coach: **~12-14 weeks**

---

## Dependencies Visualization

```
Foundation (Phase 1)
├── #32 TelemetrySample VO
├── #33 CarSetupSnapshot
├── #34 LapTrace ──────────┐
├── #35 ITelemetryRepo     │
├── #36 SQLite Schema      │
└── #37 SQLiteRepo ────────┼──────────┐
                           │          │
Track Reconstruction       │          │
├── #38 Centerline ────────┤          │
├── #39 Curvature          │          │
├── #40 Elevation          │          │
├── #41 TrackProfile ──────┼──────┐   │
└── #42 ReconstructUC ─────┘      │   │
                                  │   │
Mathe-Coach                       │   │
├── #44 IdealLap VO               │   │
├── #43 IdealLapConstructor ──────┤   │
├── #45 LapComparator ────────────┤   │
├── #46 FeedbackGenerator         │   │
├── #47 MatheCoachUC ─────────────┼───┤
└── #48 Discord Command           │   │
                                  │   │
KI-Coach                          │   │
├── #49 WorldModelState           │   │
├── #50 WorldModelAction          │   │
├── #51 IWorldModel               │   │
├── #53 OptimalLap VO             │   │
├── #52 DP Planner ───────────────┤   │
├── #54 KIFeedbackGen             │   │
├── #55 KICoachUC ────────────────┼───┤
└── #56 Discord Command           │   │
                                  │   │
Integration                       │   │
├── #57 SessionMgmt ──────────────┘   │
├── #59 TelemetryIngestion ───────────┘
└── #58 HTTP API

Quality
├── #60 Unit Tests (parallel)
├── #61 Integration Tests (parallel)
├── #63 DB Migrations (parallel)
└── #62 Documentation (continuous)
```

---

## Risk Mitigation

### High-Risk Issues (Complex/Time-Consuming)

- **#52 - DP Planner:** Complex algorithm, allocate extra time
- **#59 - Telemetry Ingestion:** Real-time performance critical
- **#38 - Centerline Computation:** Core algorithm, needs validation

### Quick Wins (Easy/High-Value)

- **#32, #33, #44, #53:** Simple data structures
- **#48, #56:** Discord commands (if use cases work)
- **#57:** Session management (straightforward CRUD)

---

## Success Metrics

After each phase, verify:

✅ **Phase 1:** Can persist and retrieve lap with telemetry samples  
✅ **Phase 2:** Can reconstruct track centerline with curvature  
✅ **Phase 3:** `/lap coach` returns actionable physics-based feedback  
✅ **Phase 4:** `/lap kicoach` returns optimal lap suggestions  
✅ **Phase 5:** Real-time telemetry ingestion works without data loss  
✅ **Phase 6:** >90% domain coverage, documentation complete  

---

## Notes

- **Clean Architecture:** Always respect layer boundaries (domain → application → infrastructure)
- **F1 25 UDP Mapping:** Keep exact field mappings from spec for traceability
- **Testing:** Write tests incrementally, not at the end
- **Documentation:** Update docs as you implement, not after

---

**Start with Issue #32 and work through systematically!** 🏎️
