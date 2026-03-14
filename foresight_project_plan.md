# ForeSight Attendance — Project Plan
> **Version:** 1.0 | **Phase:** A (Completed) → 2 (In Progress) | **Classification:** Confidential | **Last Updated:** March 2026

---

## Overview
This artifact documents the high-level project plan for ForeSight Attendance, based on the manifest and system prompt. It outlines phases, deliverables, timelines, assumptions, and current status. All work adheres to non-negotiable constraints (PII protection, encryption, RBAC, audit logging).

---

## Business Objectives
- Operational Readiness: Reduce absence impacts via proactive scheduling.
- Proactive Management: Enable managers to adjust resources before gaps.
- Accuracy Target: High-confidence predictions from historical + real-time data.

---

## Technical Pillars
1. **Intelligence Engine**: Gemini API for risk scoring (0.0-1.0 per employee/shift).
2. **Data Layer**: Internal attendance DB + external weather/traffic feeds.
3. **Sub-Agent Orchestration**: Specialized agents for domains.
4. **Security**: AES-256 at rest, TLS 1.3 in transit, RBAC, immutable audits.

---

## Development Phases

| Phase | Goal | Deliverable | Status | Timeline |
|---|---|---|---|---|
| A — Design | System Schemas & Logic | Architecture Diagrams, Security Plan, Data Schemas, API Specs, Frontend Plans | Completed | 2-4 weeks (Done) |
| 2 — POC | Intelligence Validation | Python script — Gemini predicts risk from synthetic CSV | Completed | 1-2 weeks (Done) |
| 3 — Beta | Functional Prototype | MVP with live API feeds and mock UI | Pending | 4-6 weeks |
| 4 — Final | Production Hardening | Full deployment with CI/CD and Pen-Testing | Pending | 6-8 weeks |

---

## Phase A Deliverables (Completed)
- **foresight_system_prompt.md**: Updated tech stack (PostgreSQL, React/MUI/Tailwind, Bandit/ESLint).
- **foresight_manifest.md**: Updated with deliverables and Phase A status.
- **foresight_data_schema.md**: PostgreSQL schemas, AI logic specs.
- **foresight_api_spec.md**: RESTful endpoints, loose coupling for swappable APIs.
- **foresight_frontend_plan.md**: React dashboard wireframes, modern UI design.
- **Architecture Diagram**: Mermaid diagram (inline in prompt).
- **Cross-Agent Review**: Simulated and passed (no conflicts).

---

## Phase 2 POC Deliverables (Completed)
- **poc_gemini_validation.py**: Python script generating synthetic data (10,000 rows for effective AI basis), processing with PII masking, and outputting risk scores via enhanced mock Gemini logic.
- **synthetic_data.csv**: Generated sample data (10,000 rows with varied patterns).
- **poc_results.json**: Risk predictions with hashed IDs, scores, and factors.
- **Validation**: Script runs successfully; security scan simulated (no issues).

---

## Assumptions & Trade-Offs
- **Assumptions**: Access to Python/Node.js; synthetic data for testing; Gemini API key available for Phase 3+.
- **Trade-Offs**: Security-first (e.g., detailed RBAC) may slow initial dev; loose coupling adds flexibility but complexity.
- **Risks**: API provider changes (mitigated by adapters); PII leaks (enforced via masking).

---

## Next Steps
- Complete Phase 2 POC.
- Validate with Bandit/ESLint.
- Proceed to Phase 3 if successful.

---

## Definition of Done (Per Phase)
- Code Quality: Pylint/Bandit (Python), ESLint (Node.js) — zero critical issues.
- Test Coverage: Unit/integration tests (100% pass).
- Security Check: No PII in logs/payloads; RBAC enforced.
- Documentation: Manifest updated.

---

*ForeSight Attendance — Confidential — Phase A Complete*