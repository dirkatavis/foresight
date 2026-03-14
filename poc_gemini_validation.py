import pandas as pd
import hashlib
import random
import json

print("Step 1: Generating synthetic data...")

# Generate synthetic data with historical attendance
data = []

for i in range(100):  # Demo size
    employee_id = f"emp_{i}"
    hashed_id = hashlib.sha256(employee_id.encode()).hexdigest()
    # Historical attendance: e.g., absence rate over last 30 days
    historical_absence_rate = round(random.uniform(0, 1), 2)  # 0.0-1.0
    weather_precip = round(random.uniform(0, 50), 2)
    weather_temp = round(random.uniform(-10, 40), 1)
    traffic_congestion = round(random.uniform(0, 1), 2)
    data.append({
        'employee_id': hashed_id,
        'historical_absence_rate': historical_absence_rate,  # Prominent factor
        'weather_precip': weather_precip,
        'weather_temp': weather_temp,
        'traffic_congestion': traffic_congestion
    })

df = pd.DataFrame(data)
df.to_csv('synthetic_data.csv', index=False)
print(f"Generated {len(data)} rows. Sample row: {data[0]}")

print("Step 2: Processing data and predicting risks...")

# POC: Predict risk using mock Gemini
def mock_gemini_predict(attendance, precip, temp, congestion):
    print(f"  Mock Gemini input: attendance={attendance}, precip={precip}, temp={temp}, congestion={congestion}")
    # Predictive algorithm mapping:
    # - Historical absence rate: Primary factor (70% weight) - past patterns indicate future risk
    # - Weather: Secondary (15% weight) - correlates with absences (e.g., bad weather exacerbates)
    # - Traffic: Secondary (15% weight) - commute issues affect attendance
    risk = attendance * 0.7  # Assuming attendance is historical_rate
    weather_penalty = 0.0
    if precip > 20:
        weather_penalty += 0.1
    if temp < 0 or temp > 35:
        weather_penalty += 0.1
    risk += weather_penalty * 0.15
    traffic_penalty = congestion * 0.15
    risk += traffic_penalty
    noise = random.uniform(-0.05, 0.05)
    risk += noise
    final_risk = max(0.0, min(1.0, risk))
    print(f"  Calculated risk: {final_risk} (historical: {attendance * 0.7}, weather: {weather_penalty * 0.15}, traffic: {traffic_penalty}, noise: {noise})")
    return final_risk
    final_risk = max(0.0, min(1.0, risk))
    print(f"  Calculated risk: {final_risk} (attendance contrib: {0.5 if attendance == 'absent' else 0.2 if attendance == 'late' else 0.0}, weather: {0.3 if precip > 20 or temp < 0 or temp > 35 else 0.0}, traffic: {congestion * 0.3}, noise: {noise})")
    return final_risk

results = []
for idx, row in df.iterrows():
    if idx >= 3:  # Step through first 3
        break
    print(f"Processing employee {idx+1}...")
    risk = mock_gemini_predict(row['historical_absence_rate'], row['weather_precip'], row['weather_temp'], row['traffic_congestion'])
    factors = {
        'historical_attendance': row['historical_absence_rate'] * 0.7,
        'weather': 0.15 * (0.1 if row['weather_precip'] > 20 or row['weather_temp'] < 0 or row['weather_temp'] > 35 else 0.0),
        'traffic': row['traffic_congestion'] * 0.15
    }
    results.append({
        'employee_id': row['employee_id'],
        'risk_score': round(risk, 2),
        'factors': factors
    })

print("Step 3: Saving results...")
with open('poc_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print("POC complete (stepped through first 3). Full results in poc_results.json")