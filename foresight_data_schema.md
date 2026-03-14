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
  - `role_exposure` (ENUM: 'indoor', 'outdoor', 'mixed'): Indicates weather sensitivity based on job format.
  - `tenure_phase` (ENUM: 'new_hire', 'standard', 'veteran'): Indicates fragility vs. burnout risks.
  - `home_zip_code` (VARCHAR(10)): Truncated routing/postal code to correlate community health/events.
  - `work_zip_code` (VARCHAR(10)): Facility postal code for localized strain mapping.
- **Constraints**: No names, addresses, or personal details. Access restricted by facility.

### Attendance Events Table
- **Purpose**: Historical attendance records for pattern analysis.
- **Structure**:
  - `event_id` (SERIAL, PRIMARY KEY)
  - `employee_id` (VARCHAR(64), FK to Employee): Hashed ID.
  - `date` (DATE)
  - `shift_start` (TIME): Scheduled_In
  - `shift_end` (TIME): Scheduled_Out
  - `actual_in` (TIME, OPTIONAL): Actual clock-in time (used to calculate Punch Latency).
  - `actual_out` (TIME, OPTIONAL): Actual clock-out time (used to calculate Shift-End Erosion, Recovery Window).
  - `status` (ENUM: 'present', 'absent', 'late', 'partial')
  - `reason` (VARCHAR(255), OPTIONAL): Categorized reason (e.g., 'illness', 'traffic') — no free text.
- **Stored Procedures**: `get_attendance_history(employee_id, facility_id)` — enforces RBAC.

### Employee Metrics (Rolling Context)
- **Purpose**: Pre-computed rolling stats and internal balance metrics for the AI engine.
- **Structure**:
  - `employee_id` (VARCHAR(64), FK to Employee): Hashed ID.
  - `rolling_workload_hours` (DECIMAL(5,2)): Cumulative hours worked in last 7 days (identifies burnout).
  - `absentee_momentum` (INT): Rolling 30-day count of "No-Shows" or "Late-Calls".
  - `predictability_index` (DECIMAL(3,2)): Variance in the employee’s scheduled start times.
  - `punch_latency_trend` (DECIMAL(4,1)): Average discrepancy in minutes between Scheduled_In and Actual_In over the last 14 days.
  - `last_pay_date` (DATE): For calculating Payday Proximity.
- **Refresh Interval**: Calculated via nightly scheduled jobs or database triggers.

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

## AI Logic Specification — Hybrid Approach (Gemini API Integration)

### Architecture: Two-Layer Pipeline
ForeSight uses a **hybrid** prediction model. We do NOT hard-code predictive weights. Instead:

1. **Layer 1 — Feature Engineering (Pre-Computed Metrics)**
   - Raw shift records (10–1000 per employee) are processed into ~15 condensed, descriptive metrics.
   - These metrics summarize behavioral patterns, fatigue signals, and contextual factors without prescribing their importance.
   - Pre-computation happens via nightly batch jobs or on-demand before a prediction request.
   - Source metrics are defined in `predictive_metrics.md` and stored in the Employee Metrics table.

2. **Layer 2 — Gemini Reasoning Engine**
   - The condensed employee profile + real-time external conditions are sent to Gemini per prediction request.
   - Gemini discovers the correlations and weights autonomously — we do not tell it that "history = 70%."
   - Gemini returns a structured JSON response with scores AND the factors it weighted most heavily, enabling explainability.

### Design Rationale — Why Hybrid?
Three approaches were evaluated:

| Approach | Description | Rejected Because |
|---|---|---|
| **Pure Theory** (rule-based) | Hard-code predictive weights (e.g., 70% history, 15% weather, 15% traffic) into a deterministic formula. | Weights are arbitrary guesses. Patterns vary by facility, role, and season. Cannot adapt. Renders Gemini unnecessary. |
| **Pure LLM** (raw data → Gemini) | Send all raw shift records (potentially 1,000+ rows per employee) to Gemini and ask it to find patterns. | Token cost prohibitive at scale. Slow per-request latency. Non-deterministic with large payloads. Unnecessary noise in the prompt. |
| **Hybrid** (pre-compute → Gemini reasons) | Pre-compute ~15 condensed metrics per employee; send those + real-time conditions to Gemini for reasoning. | **Selected.** |

**Why Hybrid wins:**
- **Cost-efficient**: ~15 metric values per request instead of hundreds of raw rows keeps token costs low.
- **Gemini does what it's good at**: Multi-variable reasoning across contextual signals — not data crunching.
- **Explainable**: Gemini cites specific factors (e.g., "punch latency trend" + "winter storm") in its response, making results actionable for managers.
- **Adaptable**: As new metrics are identified (e.g., community health trends), they are added to Layer 1 without changing the Gemini prompt structure.
- **Testable**: Layer 1 metrics can be unit-tested independently. Layer 2 responses can be validated against expected ranges.

### Prompt Engineering
- **Structured Prompt Template**:
  ```
  You are an attendance risk analyst. Given the following employee profile
  and current shift conditions, predict the likelihood of three outcomes:
  on_time, late, and absent. Each should be a value between 0.0 and 1.0
  and the three values must sum to 1.0.

  Explain which factors contributed most to your prediction.

  Employee Profile:
  {employee_metrics_json}

  Current Conditions:
  {external_conditions_json}

  Respond ONLY with valid JSON in this format:
  {
    "on_time": <float>,
    "late": <float>,
    "absent": <float>,
    "primary_factors": ["<factor_name>", ...],
    "reasoning": "<brief explanation>"
  }
  ```
- **Employee Metrics Payload** (example):
  ```json
  {
    "historical_absence_rate": 0.05,
    "historical_late_rate": 0.14,
    "punch_latency_trend": 4.2,
    "absentee_momentum": 6,
    "rolling_workload_hours": 48.5,
    "predictability_index": 0.12,
    "role_exposure": "outdoor",
    "tenure_phase": "new_hire"
  }
  ```
- **External Conditions Payload** (example):
  ```json
  {
    "precipitation_mm": 32.0,
    "temperature_c": -2.0,
    "weather_alerts": ["winter_storm_warning"],
    "traffic_congestion": 0.8,
    "school_closure": true,
    "payday_proximity_days": 2
  }
  ```

### PII Handling
- All employee IDs are SHA-256 hashed before any external API call.
- No raw IDs, names, or identifiable data appear in prompts, logs, or payloads.
- Gemini never receives the employee hash — only the anonymous metric profile.

### Error Handling & Fallback
- If Gemini API is unavailable or returns invalid JSON, fall back to a simple weighted average using historical rates.
- All API failures are logged securely (no PII) with timestamps and error codes.
- Output validation: scores must be 0.0–1.0 and sum to ~1.0; reject and retry on invalid responses.

### Feature Engineering (Pre-Computation)
- **Behavioral Metrics**: Punch Latency Trend, Shift-End Erosion, Absentee Momentum (from `predictive_metrics.md` §3).
- **Fatigue Metrics**: Rolling Workload Hours, Recovery Window, Predictability Index (from `predictive_metrics.md` §2).
- **Contextual Metrics**: Role Exposure, Tenure Phase, Payday Proximity (from `predictive_metrics.md` §4–6).
- **Normalization**: All numeric metrics scaled to consistent ranges before inclusion in the Gemini payload.
- **Refresh Cadence**: Nightly batch job recalculates all rolling metrics; real-time conditions fetched at prediction time.

---

## Security & Validation Notes
- **Encryption**: All tables AES-256 encrypted at rest.
- **RBAC**: Queries scoped by `facility_id`; API layer enforces.
- **Audit**: Stored procedure `log_prediction_action(employee_id, action)` for compliance.
- **Testing**: Schema validated against PII rules; Bandit/ESLint scans for code.

---

*ForeSight Attendance — Confidential — Phase A*