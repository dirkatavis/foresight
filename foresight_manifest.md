# ForeSight Attendance — Project Manifest
> **Version:** 1.0 | **Phase:** A — Design & Architecture | **Classification:** Confidential | **Last Updated:** March 2026

---

## Purpose
This manifest is the canonical source of truth for all AI sub-agents and human contributors. Provide this file at the start of any new session to ensure every code change, architectural decision, and integration aligns with the requirements below. Do not modify the Definition of Done or Security constraints without formal review.

---

## Business Objectives

| Objective | Description |
|---|---|
| Operational Readiness | Reduce the operational impact of unexpected absences on daily facility and department performance. |
| Proactive Management | Enable managers to adjust schedules and resources before a staffing gap materialises. |
| Accuracy Target | Achieve high-confidence predictions by correlating internal attendance history with real-time external environmental stressors. |

---

## Technical Pillars

### 1. The Intelligence Engine (Gemini API)
- **Role:** Multi-variable reasoning and time-series forecasting across all ingested data streams.
- **Logic:** Process historical attendance patterns alongside real-time API feeds.
- **Output:** A continuous `Risk Score` (0.0 – 1.0) per employee per shift window. A score of `1.0` represents maximum absence risk.

### 2. Data Layer & Integrations

**Internal Sources**
- Employer Attendance Database (SQL / NoSQL) — authoritative record of all historical attendance events.

**External — Weather**
- Precipitation volume and probability
- Temperature extremes and heat / cold indices
- Severe weather alerts and watch regions

**External — Traffic**
- Real-time congestion and travel-time data for employee commute corridors
- Incident and road-closure reports affecting route viability

### 3. Sub-Agent Orchestration
Development is divided across four specialised agents. Each agent owns a defined scope and must not make decisions outside that boundary without cross-agent review.

| Agent | Scope |
|---|---|
| Architecture / Security | System integrity, infrastructure design, and PII protection controls. |
| Data / AI | Model prompts, weighting logic, feature engineering, and API payload normalisation. |
| API / Backend | Core service layer, business logic, scheduled jobs, and data pipeline orchestration. |
| Frontend | Manager dashboard, attendance heatmaps, and forecast visualisation components. |

---

## Security & Privacy — NON-NEGOTIABLE

> ⚠️ The following controls are mandatory across all phases and all sub-agents. Any code or design pattern that cannot satisfy these constraints must be escalated immediately and not shipped.

| Control | Requirement |
|---|---|
| PII Protection | Employee names and IDs must be masked or hashed before passing to any external API or writing to general application logs. |
| Encryption at Rest | AES-256 encryption required for all persistent data stores containing attendance or employee records. |
| Encryption in Transit | TLS 1.3 required for all service-to-service and client-to-server communication. |
| Access Control (RBAC) | Enforced at the API layer. A manager assigned to Facility A cannot read, query, or receive predictions for Facility B under any circumstances. |
| Audit Logging | Every prediction-based manager action (view, export, schedule adjustment) must be written to an immutable compliance log for HR review. |

---

## Development Phases

| Phase | Goal | Deliverable |
|---|---|---|
| A — Design | System Schemas & Logic | Architecture Diagrams, Security Plan, Data Schemas, API Specs, Frontend Plans |
| 2 — POC | Intelligence Validation | Python script — Gemini predicts risk from a CSV |
| 3 — Beta | Functional Prototype | MVP with live API feeds and mock UI |
| 4 — Final | Production Hardening | Full deployment with CI/CD and Pen-Testing |

---

## Phase A Deliverables (Completed)
- **foresight_system_prompt.md**: Updated with tech stack recommendations.
- **foresight_data_schema.md**: Data schemas and AI logic specs.
- **foresight_api_spec.md**: API endpoints and backend designs.
- **foresight_frontend_plan.md**: Dashboard wireframes and integrations.
- **Architecture Diagram**: Mermaid diagram in prompt (inline).

## Definition of Done

All four criteria must be satisfied for every task and sprint before work is considered complete. No exceptions.

| # | Criterion | Requirement |
|---|---|---|
| 1 | Code Quality | All Python and Node.js code must pass static analysis (Pylint / ESLint) with zero critical or high-severity issues. |
| 2 | Test Coverage | 100% pass rate on all Unit and Integration tests. No test skips or suppressions without documented justification. |
| 3 | Security Check | Verified that no PII appears in application logs, error traces, or outbound API payloads. Reviewed by Architecture agent. |
| 4 | Documentation | This Manifest and any affected Technical Spec documents updated to reflect logic changes before sprint close. |

---

*ForeSight Attendance — Confidential & Proprietary — Phase A / v1.0*
