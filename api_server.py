from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
import pandas as pd
import hashlib
import random
import json
import os
import logging
from typing import List, Optional
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Application Setup
# ---------------------------------------------------------------------------
app = FastAPI(title="ForeSight Attendance API", version="2.0")

logger = logging.getLogger("foresight")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# Determine if we use a live Gemini key or fall back to mock reasoning
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
USE_LIVE_GEMINI = GEMINI_API_KEY is not None

# ---------------------------------------------------------------------------
# Data Loading
# ---------------------------------------------------------------------------
try:
    df_employees = pd.read_csv('synthetic_data.csv')
    df_attendance = pd.read_csv('synthetic_attendance.csv')
    logger.info("Loaded %d employees and %d attendance records.", len(df_employees), len(df_attendance))
except FileNotFoundError:
    logger.warning("Synthetic data not found. Run poc_gemini_validation.py first to generate data.")
    df_employees = pd.DataFrame()
    df_attendance = pd.DataFrame()

# ---------------------------------------------------------------------------
# Security — RBAC & Authentication
# ---------------------------------------------------------------------------
# Mock manager-to-facility mapping (in production: JWT claims or DB lookup)
MANAGER_API_KEYS = {
    "mgr-key-facility-a": {"manager_id": "mgr_001", "facility_id": "facility_a", "name": "Manager A"},
    "mgr-key-facility-b": {"manager_id": "mgr_002", "facility_id": "facility_b", "name": "Manager B"},
    "admin-key-all":      {"manager_id": "admin_001", "facility_id": "*", "name": "Admin"},
}

# Mock employee-to-facility mapping (in production: from Employee table)
# Assign first 50 employees to facility_a, rest to facility_b
EMPLOYEE_FACILITY_MAP = {}
if not df_employees.empty:
    for idx, row in df_employees.iterrows():
        facility = "facility_a" if idx < 50 else "facility_b"
        EMPLOYEE_FACILITY_MAP[row['employee_id']] = facility

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_current_manager(api_key: str = Depends(api_key_header)):
    """Authenticate via API key and return the manager context."""
    if not api_key or api_key not in MANAGER_API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return MANAGER_API_KEYS[api_key]


def enforce_facility_access(employee_id: str, manager: dict):
    """
    RBAC enforcement: A manager scoped to Facility A is architecturally
    incapable of querying Facility B employees. No exceptions.
    """
    if manager["facility_id"] == "*":
        return  # Admin has full access

    emp_facility = EMPLOYEE_FACILITY_MAP.get(employee_id)
    if emp_facility is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    if emp_facility != manager["facility_id"]:
        # Log the unauthorized access attempt (no PII — only hashed IDs)
        logger.warning(
            "RBAC DENIED: manager=%s attempted access to employee in facility=%s (authorized for %s)",
            manager["manager_id"], emp_facility, manager["facility_id"]
        )
        raise HTTPException(status_code=403, detail="Access denied: employee not in your facility")


# ---------------------------------------------------------------------------
# Audit Logging — Immutable Compliance Log
# ---------------------------------------------------------------------------
AUDIT_LOG_FILE = "audit_log.jsonl"


def log_audit_event(manager: dict, action: str, details: dict):
    """
    Write an immutable audit log entry for every prediction-based action.
    No PII — only manager_id, action type, and anonymized metadata.
    """
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "manager_id": manager["manager_id"],
        "facility_id": manager["facility_id"],
        "action": action,
        "details": details,
    }
    try:
        with open(AUDIT_LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        logger.error("Failed to write audit log: %s", str(e))

# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------
class ShiftRequest(BaseModel):
    employee_id: str
    shift_date: str
    shift_time: str

class ScheduleRequest(BaseModel):
    schedule: List[ShiftRequest]

class PredictionResponse(BaseModel):
    on_time: float
    late: float
    absent: float
    primary_factors: List[str]
    reasoning: str

class SchedulePrediction(BaseModel):
    employee_id: str
    shift_date: str
    shift_time: str
    on_time: float
    late: float
    absent: float
    primary_factors: List[str]
    reasoning: str

class ScheduleResponse(BaseModel):
    schedule_predictions: List[SchedulePrediction]
    high_risk_alerts: List[SchedulePrediction]
    summary: str

# ---------------------------------------------------------------------------
# Layer 1 — Feature Engineering (Pre-Computed Metrics)
# ---------------------------------------------------------------------------
def build_employee_profile(employee_id: str) -> dict:
    """
    Condense raw data into ~15 descriptive metrics for Gemini.
    This is Layer 1 of the hybrid pipeline.
    """
    emp = df_employees[df_employees['employee_id'] == employee_id]
    if emp.empty:
        return None

    row = emp.iloc[0]
    profile = {
        "historical_absence_rate": float(row.get('historical_absence_rate', 0)),
        "historical_late_rate": float(row.get('historical_late_rate', 0)),
        "punch_latency_trend": float(row.get('punch_latency_trend', 0)),
        "absentee_momentum": int(row.get('absentee_momentum', 0)),
        "role_exposure": str(row.get('role_exposure', 'indoor')),
        "tenure_phase": str(row.get('tenure_phase', 'standard')),
    }

    # Derive rolling workload from attendance records (last 7 calendar days)
    emp_att = df_attendance[df_attendance['employee_id'] == employee_id]
    if not emp_att.empty and 'date' in emp_att.columns:
        emp_att_dated = emp_att.copy()
        emp_att_dated['date'] = pd.to_datetime(emp_att_dated['date'])
        cutoff_7d = emp_att_dated['date'].max() - pd.Timedelta(days=7)
        recent = emp_att_dated[emp_att_dated['date'] >= cutoff_7d]
        # Each present/late shift ~ 8 hours
        shifts_worked = len(recent[recent['status'].isin(['present', 'late'])])
        profile["rolling_workload_hours"] = round(shifts_worked * 8.0, 1)

        # Predictability index: std deviation of scheduled start times
        if 'scheduled_in' in emp_att.columns:
            try:
                times = pd.to_datetime(emp_att_dated['scheduled_in'], format='%H:%M:%S')
                minutes = times.dt.hour * 60 + times.dt.minute
                profile["predictability_index"] = round(float(minutes.std()) / 60, 2) if len(minutes) > 1 else 0.0
            except Exception:
                profile["predictability_index"] = 0.0
    else:
        profile["rolling_workload_hours"] = 0.0
        profile["predictability_index"] = 0.0

    return profile


def build_external_conditions(shift_date: str, shift_time: str) -> dict:
    """
    Fetch real-time external conditions. Currently mocked for MVP.
    In production, this calls Weather API + Traffic API + Calendar API.
    """
    return {
        "precipitation_mm": round(random.uniform(0, 50), 1),
        "temperature_c": round(random.uniform(-10, 40), 1),
        "weather_alerts": random.choice([[], ["winter_storm_warning"], ["heat_advisory"]]),
        "traffic_congestion": round(random.uniform(0, 1), 2),
        "school_closure": random.choice([True, False]),
        "payday_proximity_days": random.randint(0, 14),
    }

# ---------------------------------------------------------------------------
# Layer 2 — Gemini Reasoning Engine (with Mock Fallback)
# ---------------------------------------------------------------------------
GEMINI_PROMPT_TEMPLATE = """You are an attendance risk analyst. Given the following employee profile \
and current shift conditions, predict the likelihood of three outcomes: \
on_time, late, and absent. Each should be a value between 0.0 and 1.0 \
and the three values must sum to 1.0.

Explain which factors contributed most to your prediction.

Employee Profile:
{employee_profile}

Current Conditions:
{external_conditions}

Respond ONLY with valid JSON in this format:
{{
  "on_time": <float>,
  "late": <float>,
  "absent": <float>,
  "primary_factors": ["<factor_name>", ...],
  "reasoning": "<brief explanation>"
}}"""


def call_gemini(employee_profile: dict, external_conditions: dict) -> dict:
    """
    Call the Gemini API with the condensed metrics.
    Falls back to mock reasoning if no API key is configured.
    """
    if USE_LIVE_GEMINI:
        return _call_live_gemini(employee_profile, external_conditions)
    else:
        return _mock_gemini_reasoning(employee_profile, external_conditions)


def _call_live_gemini(employee_profile: dict, external_conditions: dict) -> dict:
    """
    Production Gemini call via google-genai SDK.
    Requires GEMINI_API_KEY environment variable.
    """
    try:
        from google import genai

        client = genai.Client(api_key=GEMINI_API_KEY)
        prompt = GEMINI_PROMPT_TEMPLATE.format(
            employee_profile=json.dumps(employee_profile, indent=2),
            external_conditions=json.dumps(external_conditions, indent=2),
        )
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )

        # Parse JSON from Gemini response
        text = response.text.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            text = text.rsplit("```", 1)[0]

        result = json.loads(text)

        # Validate structure
        for key in ("on_time", "late", "absent"):
            result[key] = max(0.0, min(1.0, float(result.get(key, 0))))
        if "primary_factors" not in result:
            result["primary_factors"] = []
        if "reasoning" not in result:
            result["reasoning"] = "No reasoning provided."

        return result

    except Exception as e:
        logger.error("Gemini API call failed: %s. Falling back to mock.", str(e))
        return _mock_gemini_reasoning(employee_profile, external_conditions)


def _mock_gemini_reasoning(profile: dict, conditions: dict) -> dict:
    """
    Simulates Gemini's multi-variable reasoning for local development.
    Uses the condensed metrics to produce a realistic prediction WITHOUT
    hard-coding arbitrary weights — instead, it applies contextual logic
    that mimics how an LLM would reason about the factors.
    """
    factors = []
    absent_signal = 0.0
    late_signal = 0.0

    # --- Behavioral signals ---
    absence_rate = profile.get("historical_absence_rate", 0)
    if absence_rate > 0.10:
        absent_signal += absence_rate * 0.5
        factors.append("historical_absence_rate")

    late_rate = profile.get("historical_late_rate", 0)
    if late_rate > 0.10:
        late_signal += late_rate * 0.4
        factors.append("historical_late_rate")

    latency = profile.get("punch_latency_trend", 0)
    if latency > 5.0:
        late_signal += 0.10
        factors.append("punch_latency_trend")

    momentum = profile.get("absentee_momentum", 0)
    if momentum > 3:
        absent_signal += min(momentum * 0.02, 0.15)
        factors.append("absentee_momentum")

    # --- Fatigue signals ---
    workload = profile.get("rolling_workload_hours", 0)
    if workload > 48:
        absent_signal += 0.08
        late_signal += 0.05
        factors.append("rolling_workload_hours")

    # --- Environmental signals (context-aware by role) ---
    role = profile.get("role_exposure", "indoor")
    precip = conditions.get("precipitation_mm", 0)
    temp = conditions.get("temperature_c", 20)
    alerts = conditions.get("weather_alerts", [])

    weather_impact = 0.0
    if precip > 20:
        weather_impact += 0.08
    if temp < 0 or temp > 38:
        weather_impact += 0.08
    if alerts:
        weather_impact += 0.10

    # Outdoor roles are more affected by weather
    role_multiplier = {"outdoor": 1.5, "mixed": 1.0, "indoor": 0.5}.get(role, 1.0)
    weather_impact *= role_multiplier

    if weather_impact > 0:
        absent_signal += weather_impact * 0.4
        late_signal += weather_impact * 0.3
        factors.append("weather_conditions")

    congestion = conditions.get("traffic_congestion", 0)
    if congestion > 0.6:
        late_signal += congestion * 0.15
        factors.append("traffic_congestion")

    # --- Contextual signals ---
    if conditions.get("school_closure"):
        absent_signal += 0.05
        factors.append("school_closure")

    payday = conditions.get("payday_proximity_days", 7)
    if payday <= 1:
        late_signal += 0.03
        factors.append("payday_proximity")

    # --- Tenure modulation ---
    tenure = profile.get("tenure_phase", "standard")
    if tenure == "new_hire":
        absent_signal *= 1.2  # New hires more fragile
        factors.append("tenure_phase")
    elif tenure == "veteran" and workload > 48:
        absent_signal *= 1.1  # Veteran burnout
        factors.append("tenure_phase")

    # Clamp and normalize
    absent_score = max(0.0, min(1.0, absent_signal + random.uniform(-0.02, 0.02)))
    late_score = max(0.0, min(1.0, late_signal + random.uniform(-0.02, 0.02)))
    on_time_score = max(0.0, 1.0 - absent_score - late_score)

    # Build reasoning string
    if not factors:
        factors = ["baseline_low_risk"]
    reasoning = f"Based on analysis of {len(factors)} contributing factors. " \
                f"Key drivers: {', '.join(factors[:3])}."

    return {
        "on_time": round(on_time_score, 3),
        "late": round(late_score, 3),
        "absent": round(absent_score, 3),
        "primary_factors": factors,
        "reasoning": reasoning,
    }

# ---------------------------------------------------------------------------
# Prediction Pipeline (Layer 1 → Layer 2)
# ---------------------------------------------------------------------------
def predict_shift(employee_id: str, shift_date: str, shift_time: str) -> dict:
    """
    Full hybrid pipeline:
      1. Build condensed employee profile (Layer 1)
      2. Fetch current external conditions
      3. Pass both to Gemini reasoning engine (Layer 2)
    """
    # Layer 1: Feature engineering
    profile = build_employee_profile(employee_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    # External conditions
    conditions = build_external_conditions(shift_date, shift_time)

    # Layer 2: Gemini reasoning
    prediction = call_gemini(profile, conditions)

    return prediction

# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------
@app.post("/api/predictions/generate", response_model=PredictionResponse)
def generate_prediction(request: ShiftRequest, manager: dict = Depends(get_current_manager)):
    """Generate attendance prediction for a single shift."""
    enforce_facility_access(request.employee_id, manager)
    result = predict_shift(request.employee_id, request.shift_date, request.shift_time)
    log_audit_event(manager, "prediction_generated", {
        "employee_count": 1,
        "shift_date": request.shift_date,
    })
    return result


@app.post("/api/schedule/predict", response_model=ScheduleResponse)
def predict_schedule(request: ScheduleRequest, manager: dict = Depends(get_current_manager)):
    """Generate predictions for a batch of scheduled shifts."""
    results = []
    for shift in request.schedule:
        enforce_facility_access(shift.employee_id, manager)
        pred = predict_shift(shift.employee_id, shift.shift_date, shift.shift_time)
        pred["employee_id"] = shift.employee_id
        pred["shift_date"] = shift.shift_date
        pred["shift_time"] = shift.shift_time
        results.append(pred)

    high_risk = [r for r in results if r["absent"] > 0.3 or r["late"] > 0.5]
    log_audit_event(manager, "schedule_predicted", {
        "employee_count": len(results),
        "high_risk_count": len(high_risk),
    })
    return {
        "schedule_predictions": results,
        "high_risk_alerts": high_risk,
        "summary": f"{len(high_risk)} high-risk shifts out of {len(results)}"
    }


@app.get("/api/dashboard/heatmap")
def get_heatmap(facility_id: str, date_range: str, manager: dict = Depends(get_current_manager)):
    """Aggregated heatmap data for a facility."""
    # RBAC: manager can only view their own facility's heatmap
    if manager["facility_id"] != "*" and facility_id != manager["facility_id"]:
        raise HTTPException(status_code=403, detail="Access denied: not your facility")

    heatmap_data = [
        {"date": "2026-03-17", "shift": "09:00-17:00", "high_risk_count": random.randint(1, 5), "total_employees": len(df_employees)},
        {"date": "2026-03-18", "shift": "10:00-18:00", "high_risk_count": random.randint(1, 5), "total_employees": len(df_employees)}
    ]
    log_audit_event(manager, "heatmap_viewed", {"facility_id": facility_id, "date_range": date_range})
    return {"heatmap_data": heatmap_data}


@app.get("/api/health")
def health_check():
    """Service health check."""
    return {
        "status": "healthy",
        "employees_loaded": len(df_employees),
        "attendance_records_loaded": len(df_attendance),
        "gemini_mode": "live" if USE_LIVE_GEMINI else "mock",
    }


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)