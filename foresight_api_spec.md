# ForeSight Attendance — API & Backend Specifications
> **Version:** 1.0 | **Phase:** A — Design & Architecture | **Classification:** Confidential | **Last Updated:** March 2026

---

## Overview
This document specifies the API endpoints and backend services for ForeSight Attendance. Backend uses Python (core logic) and Node.js (API layer). All endpoints enforce RBAC at the API layer, TLS 1.3, and audit logging. No PII in responses or logs.

---

## API Design Principles
- **Loose Coupling**: External APIs (weather/traffic) use adapter patterns for easy swapping (e.g., interface-based design to replace providers without code changes).
- **Market-Ready**: Versioned endpoints (/v1/), OpenAPI 3.0 documentation, rate limiting, and OAuth 2.0 for external clients.
- **Comprehensive Security**: Beyond hashing, includes input validation, rate limiting, and audit trails for all calls.

---

## API Endpoints

### 1. POST /api/predictions/generate
- **Purpose**: Generate risk scores for employees in a facility.
- **RBAC**: Manager role, scoped to facility.
- **Request Body**:
  ```json
  {
    "facility_id": "FAC001",
    "employee_ids": ["hash1", "hash2"],
    "shift_date": "2026-03-15",
    "shift_window": "09:00-17:00"
  }
  ```
- **Response**:
  ```json
  {
    "predictions": [
      {"employee_id": "hash1", "risk_score": 0.75, "factors": {"weather": 0.4}}
    ]
  }
  ```
- **Security**: Inputs validated; Gemini called with masked data; action logged.

### 2. GET /api/predictions/history
- **Purpose**: Retrieve historical predictions for dashboard.
- **RBAC**: Manager role, facility-scoped.
- **Query Params**: facility_id, date_range.
- **Response**: Array of prediction objects (as above).
- **Security**: No PII; encrypted storage.

### 3. POST /api/data/ingest
- **Purpose**: Ingest external data (weather/traffic).
- **RBAC**: System/internal role only.
- **Request Body**: Normalized feed data (JSON).
- **Response**: Success status.
- **Security**: Data encrypted before storage.

### 4. GET /api/dashboard/heatmap
- **Purpose**: Aggregated data for manager heatmap visualization (trends over time/facility).
- **RBAC**: Manager role, facility-scoped.
- **Query Params**: facility_id, date_range (e.g., "2026-03-10 to 2026-03-17").
- **Response**:
  ```json
  {
    "heatmap_data": [
      {"date": "2026-03-17", "shift": "09:00-17:00", "high_risk_count": 3, "total_employees": 10},
      ...
    ]
  }
  ```
- **Security**: Aggregated only; no individual scores.

---

## Backend Logic
- **Data Pipeline**: Python scripts pull from APIs, process with stored procedures, feed to Gemini.
- **Error Handling**: Graceful failures; audit logs for all actions.
- **Testing**: 100% unit/integration coverage; ESLint/Pylint + security plugins.

---

## Security Plan
- **RBAC Enforcement**: Middleware checks JWT tokens for facility scope.
- **Encryption**: All payloads TLS 1.3; data AES-256.
- **Audit**: Every endpoint call logs action (e.g., "Prediction generated for facility FAC001").

---

*ForeSight Attendance — Confidential — Phase A*