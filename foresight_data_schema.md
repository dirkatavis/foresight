# ForeSight Attendance — Data Schema & AI Logic Specification
> **Version:** 1.0 | **Phase:** A — Design & Architecture | **Classification:** Confidential | **Last Updated:** March 2026

---

## Overview
This document outlines the data schemas for all ingested sources (internal attendance, external weather/traffic) and the AI logic for risk scoring via Gemini API. All designs enforce PII masking, encryption (AES-256 at rest), and RBAC (facility-scoped access). Database: PostgreSQL recommended for relational structure and stored procedures.

---

## 1. Internal Attendance Data Schema

### Employee Table (Masked PII)
- **Purpose**: Core employee records with hashed IDs for privacy.
- **Structure**:
  - `employee_id` (VARCHAR(64), PRIMARY KEY): SHA-256 hashed employee ID (never raw).
  - `facility_id` (VARCHAR(32)): Facility code for RBAC scoping.
  - `shift_pattern` (JSONB): Typical shift windows (e.g., {"monday": "09:00-17:00"}).
  - `commute_route` (VARCHAR(255)): Anonymized route description (e.g., "Highway 101 North").
- **Constraints**: No names, addresses, or personal details. Access restricted by facility.

### Attendance Events Table
- **Purpose**: Historical attendance records for pattern analysis.
- **Structure**:
  - `event_id` (SERIAL, PRIMARY KEY)
  - `employee_id` (VARCHAR(64), FK to Employee): Hashed ID.
  - `date` (DATE)
  - `shift_start` (TIME)
  - `shift_end` (TIME)
  - `status` (ENUM: 'present', 'absent', 'late', 'partial')
  - `reason` (VARCHAR(255), OPTIONAL): Categorized reason (e.g., 'illness', 'traffic') — no free text.
- **Stored Procedures**: `get_attendance_history(employee_id, facility_id)` — enforces RBAC.

---

## 2. External Weather Data Schema

### Weather Feeds Table
- **Purpose**: Real-time and historical weather data normalized for correlation.
- **Structure**:
  - `feed_id` (SERIAL, PRIMARY KEY)
  - `timestamp` (TIMESTAMP)
  - `location` (VARCHAR(100)): City/region (e.g., "Seattle, WA").
  - `precipitation_mm` (DECIMAL(5,2)): Volume in mm.
  - `temperature_c` (DECIMAL(4,1)): Celsius.
  - `heat_index` (DECIMAL(4,1)): Adjusted for extremes.
  - `alerts` (JSONB): Severe weather flags (e.g., {"storm": true}).
- **Ingestion**: Via API, stored encrypted. No PII linkage until processing.

---

## 3. External Traffic Data Schema

### Traffic Feeds Table
- **Purpose**: Commute corridor data for delay predictions.
- **Structure**:
  - `feed_id` (SERIAL, PRIMARY KEY)
  - `timestamp` (TIMESTAMP)
  - `route` (VARCHAR(255)): Anonymized route (e.g., "I-5 Southbound").
  - `congestion_level` (DECIMAL(3,2)): 0.0-1.0 scale.
  - `travel_time_minutes` (INT): Estimated duration.
  - `incidents` (JSONB): Road closures or accidents.
- **Ingestion**: Via API, correlated with employee commute routes.

---

## 4. Risk Score Output Schema

### Predictions Table
- **Purpose**: Gemini-generated risk scores per employee/shift.
- **Structure**:
  - `prediction_id` (SERIAL, PRIMARY KEY)
  - `employee_id` (VARCHAR(64), FK): Hashed ID.
  - `shift_date` (DATE)
  - `shift_window` (VARCHAR(20)): e.g., "09:00-17:00".
  - `risk_score` (DECIMAL(3,2)): 0.0-1.0 (Gemini output).
  - `factors` (JSONB): Contributing weights (e.g., {"weather": 0.3, "traffic": 0.2, "history": 0.5}).
  - `generated_at` (TIMESTAMP)
- **Audit**: All queries logged immutably (no PII).

---

## AI Logic Specification (Gemini API Integration)

### Prompt Engineering
- **Base Prompt**: "Analyze historical attendance, current weather ({precipitation}, {temperature}, {alerts}), and traffic ({congestion}, {incidents}) for employee {hashed_id} on shift {window}. Predict absence risk (0.0-1.0) based on patterns. Output JSON: {score, factors}."
- **Weighting Logic**: Pre-process data to weight factors (e.g., 40% history, 30% weather, 30% traffic). Normalize inputs to prevent bias.
- **PII Handling**: All inputs hashed/masked before API call. No raw IDs in prompts or logs.
- **Error Handling**: Fallback to historical average if API fails; log securely.

### Feature Engineering
- **Correlations**: Time-series analysis for patterns (e.g., rain + traffic increases late arrivals).
- **Normalization**: Scale environmental data to 0-1 for Gemini input.
- **Output Validation**: Ensure score is 0.0-1.0; reject invalid responses.

---

## Security & Validation Notes
- **Encryption**: All tables AES-256 encrypted at rest.
- **RBAC**: Queries scoped by `facility_id`; API layer enforces.
- **Audit**: Stored procedure `log_prediction_action(employee_id, action)` for compliance.
- **Testing**: Schema validated against PII rules; Bandit/ESLint scans for code.

---

*ForeSight Attendance — Confidential — Phase A*