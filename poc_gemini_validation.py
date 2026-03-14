import pandas as pd
import hashlib
import random
import json
import sys

# Load or generate synthetic data with schedules
try:
    df = pd.read_csv('synthetic_data.csv')
except FileNotFoundError:
    # Generate if not exists
    data = []
    for i in range(1000):
        employee_id = f"emp_{i}"
        hashed_id = hashlib.sha256(employee_id.encode()).hexdigest()
        historical_absence_rate = round(random.uniform(0, 1), 2)
        historical_late_rate = round(random.uniform(0, 1), 2)
        # Weekly schedule: e.g., {"monday": "09:00-17:00", "tuesday": "10:00-18:00", ...}
        schedule = {
            "monday": "09:00-17:00",
            "tuesday": "09:00-17:00",
            "wednesday": "09:00-17:00",
            "thursday": "09:00-17:00",
            "friday": "09:00-17:00",
            "saturday": None,
            "sunday": None
        }
        data.append({
            'employee_id': hashed_id,
            'historical_absence_rate': historical_absence_rate,
            'historical_late_rate': historical_late_rate,
            'weekly_schedule': json.dumps(schedule)
        })
    df = pd.DataFrame(data)
    df.to_csv('synthetic_data.csv', index=False)

# Mock API calls
def mock_weather_api(date, time):
    # Mock: Random weather based on date/time
    precip = round(random.uniform(0, 50), 2)
    temp = round(random.uniform(-10, 40), 1)
    return {"precipitation": precip, "temperature": temp}

def mock_traffic_api(date, time):
    # Mock: Random traffic
    congestion = round(random.uniform(0, 1), 2)
    return {"congestion": congestion}

# Predictive function for shift scores
def predict_shift_scores(employee_id, shift_date, shift_time, historical_absence, historical_late):
    # Mock API calls
    weather = mock_weather_api(shift_date, shift_time)
    traffic = mock_traffic_api(shift_date, shift_time)
    
    # Scores for outcomes: on_time, late, absent (0.0-1.0 likelihood)
    base_absent = historical_absence * 0.7 + (weather['precipitation'] / 50) * 0.15 + traffic['congestion'] * 0.15
    base_late = historical_late * 0.7 + (weather['temperature'] / 50) * 0.15 + traffic['congestion'] * 0.15
    on_time = 1.0 - base_absent - base_late  # Remaining probability
    
    return {
        "on_time": max(0.0, min(1.0, on_time)),
        "late": max(0.0, min(1.0, base_late)),
        "absent": max(0.0, min(1.0, base_absent))
    }

# Main: Accept JSON input
if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1].endswith('.json'):
            with open(sys.argv[1], 'r') as f:
                input_data = json.load(f)
        else:
            input_data = json.loads(sys.argv[1])
    else:
        # Default for testing
        input_data = {
            "schedule": [
                {
                    "employee_id": "3347269991af564abc11ec0a8183a3bdfc6a3facfe132ac002185a07b64cc997",
                    "shift_date": "2026-03-17",
                    "shift_time": "09:00-17:00"
                }
            ]
        }
    
    if "schedule" in input_data:
        results = []
        for shift in input_data["schedule"]:
            hashed_id = shift["employee_id"]
            shift_date = shift["shift_date"]
            shift_time = shift["shift_time"]
            
            # Query historical data
            employee_data = df[df['employee_id'] == hashed_id]
            if employee_data.empty:
                results.append({"error": f"Employee {hashed_id} not found"})
                continue
            
            hist_absent = employee_data['historical_absence_rate'].values[0]
            hist_late = employee_data['historical_late_rate'].values[0]
            
            # Predict for the shift
            scores = predict_shift_scores(hashed_id, shift_date, shift_time, hist_absent, hist_late)
            scores["employee_id"] = hashed_id
            scores["shift_date"] = shift_date
            scores["shift_time"] = shift_time
            results.append(scores)
        
        # Aggregate for manager view
        high_risk = [r for r in results if r.get("absent", 0) > 0.3 or r.get("late", 0) > 0.5]
        output = {
            "schedule_predictions": results,
            "high_risk_alerts": high_risk,
            "summary": f"{len(high_risk)} high-risk shifts out of {len(results)}"
        }
    else:
        # Single shift (legacy)
        hashed_id = input_data["employee_id"]
        shift_date = input_data["shift_date"]
        shift_time = input_data["shift_time"]
        
        employee_data = df[df['employee_id'] == hashed_id]
        if employee_data.empty:
            output = {"error": "Employee not found"}
        else:
            hist_absent = employee_data['historical_absence_rate'].values[0]
            hist_late = employee_data['historical_late_rate'].values[0]
            output = predict_shift_scores(hashed_id, shift_date, shift_time, hist_absent, hist_late)
            if "weekly_schedule" in input_data:
                weekly_scores = {}
                schedule = input_data["weekly_schedule"]
                for day, time in schedule.items():
                    if time:
                        weekly_scores[day] = predict_shift_scores(hashed_id, shift_date, time, hist_absent, hist_late)
                output["weekly_scores"] = weekly_scores
    
    print(json.dumps(output, indent=2))