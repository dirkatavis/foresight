from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import hashlib
import random
import json
from typing import List, Optional

app = FastAPI(title="ForeSight Attendance API", version="1.0")

# Load synthetic data
try:
    df = pd.read_csv('synthetic_data.csv')
except FileNotFoundError:
    df = pd.DataFrame()  # Handle later

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

class ScheduleResponse(BaseModel):
    schedule_predictions: List[dict]
    high_risk_alerts: List[dict]
    summary: str

# Mock weather/traffic
def mock_weather(date, time):
    return {"precipitation": random.uniform(0, 50), "temperature": random.uniform(-10, 40)}

def mock_traffic(date, time):
    return {"congestion": random.uniform(0, 1)}

# Prediction logic
def predict_shift(employee_id, shift_date, shift_time):
    employee_data = df[df['employee_id'] == employee_id]
    if employee_data.empty:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    hist_absent = employee_data['historical_absence_rate'].values[0]
    hist_late = employee_data['historical_late_rate'].values[0]
    
    weather = mock_weather(shift_date, shift_time)
    traffic = mock_traffic(shift_date, shift_time)
    
    base_absent = hist_absent * 0.7 + (weather['precipitation'] / 50) * 0.15 + traffic['congestion'] * 0.15
    base_late = hist_late * 0.7 + (weather['temperature'] / 50) * 0.15 + traffic['congestion'] * 0.15
    on_time = 1.0 - base_absent - base_late
    
    return {
        "on_time": max(0.0, min(1.0, on_time)),
        "late": max(0.0, min(1.0, base_late)),
        "absent": max(0.0, min(1.0, base_absent))
    }

@app.post("/api/predictions/generate", response_model=PredictionResponse)
def generate_prediction(request: ShiftRequest):
    return predict_shift(request.employee_id, request.shift_date, request.shift_time)

@app.post("/api/schedule/predict", response_model=ScheduleResponse)
def predict_schedule(request: ScheduleRequest):
    results = []
    for shift in request.schedule:
        pred = predict_shift(shift.employee_id, shift.shift_date, shift.shift_time)
        pred.update({
            "employee_id": shift.employee_id,
            "shift_date": shift.shift_date,
            "shift_time": shift.shift_time
        })
        results.append(pred)
    
    high_risk = [r for r in results if r["absent"] > 0.3 or r["late"] > 0.5]
    return {
        "schedule_predictions": results,
        "high_risk_alerts": high_risk,
        "summary": f"{len(high_risk)} high-risk shifts out of {len(results)}"
    }

@app.get("/api/dashboard/heatmap")
def get_heatmap(facility_id: str, date_range: str):
    # Mock aggregated data
    heatmap_data = [
        {"date": "2026-03-17", "shift": "09:00-17:00", "high_risk_count": random.randint(1, 5), "total_employees": 10},
        {"date": "2026-03-18", "shift": "10:00-18:00", "high_risk_count": random.randint(1, 5), "total_employees": 10}
    ]
    return {"heatmap_data": heatmap_data}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)