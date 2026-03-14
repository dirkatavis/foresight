import pandas as pd
import hashlib
import random
import json
import sys
import os
from datetime import datetime, timedelta

# Load or generate synthetic data with schedules
import os
if os.path.exists('synthetic_data.csv') and os.path.exists('synthetic_attendance.csv'):
    df = pd.read_csv('synthetic_data.csv')
    df_att = pd.read_csv('synthetic_attendance.csv')
else:
    print("Generating synthetic dataset (100 employees, 10-1000 shifts each)...")
    employees = []
    attendance_records = []
    roles = ['indoor', 'outdoor', 'mixed']
    tenure_phases = ['new_hire', 'standard', 'veteran']

    for i in range(100):
        employee_id = f"emp_{i}"
        hashed_id = hashlib.sha256(employee_id.encode()).hexdigest()
        
        schedule = {
            "monday": "09:00-17:00",
            "tuesday": "09:00-17:00",
            "wednesday": "09:00-17:00",
            "thursday": "09:00-17:00",
            "friday": "09:00-17:00",
            "saturday": None,
            "sunday": None
        }
        
        # Generate between 10 and 1000 shift records
        num_shifts = random.randint(10, 1000)
        current_date = datetime(2026, 3, 17) - timedelta(days=num_shifts)
        
        late_count = 0
        absent_count = 0
        total_latency = 0
        
        for _ in range(num_shifts):
            # Skip weekends for standard schedule alignment
            while current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                
            status_choice = random.choices(['present', 'late', 'absent'], weights=[0.8, 0.15, 0.05])[0]
            scheduled_in = current_date.replace(hour=9, minute=0)
            scheduled_out = current_date.replace(hour=17, minute=0)
            
            if status_choice == 'present':
                actual_in = scheduled_in - timedelta(minutes=random.randint(0, 15))
                actual_out = scheduled_out + timedelta(minutes=random.randint(0, 30))
                latency = 0
            elif status_choice == 'late':
                actual_in = scheduled_in + timedelta(minutes=random.randint(1, 60))
                actual_out = scheduled_out + timedelta(minutes=random.randint(0, 30))
                late_count += 1
                latency = (actual_in - scheduled_in).total_seconds() / 60
            else:
                actual_in = None
                actual_out = None
                absent_count += 1
                latency = 0
                
            total_latency += latency
            
            attendance_records.append({
                'employee_id': hashed_id,
                'date': current_date.strftime('%Y-%m-%d'),
                'scheduled_in': scheduled_in.strftime('%H:%M:%S'),
                'scheduled_out': scheduled_out.strftime('%H:%M:%S'),
                'actual_in': actual_in.strftime('%H:%M:%S') if actual_in else None,
                'actual_out': actual_out.strftime('%H:%M:%S') if actual_out else None,
                'status': status_choice
            })
            
            current_date += timedelta(days=1)
            
        employees.append({
            'employee_id': hashed_id,
            'historical_absence_rate': round(absent_count / num_shifts, 2),
            'historical_late_rate': round(late_count / num_shifts, 2),
            'punch_latency_trend': round(total_latency / max(1, late_count), 1) if late_count > 0 else 0.0,
            'absentee_momentum': min(30, absent_count),
            'role_exposure': random.choice(roles),
            'tenure_phase': random.choice(tenure_phases),
            'weekly_schedule': json.dumps(schedule)
        })
        
    df = pd.DataFrame(employees)
    df.to_csv('synthetic_data.csv', index=False)
    
    df_att = pd.DataFrame(attendance_records)
    df_att.to_csv('synthetic_attendance.csv', index=False)
    print(f"Generated {len(df)} employees and {len(df_att)} shift records.")

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