#!/usr/bin/env python3
"""
ForeSight Simple Demo Builder
Shows weather correlation with absence rates
"""

import random
from datetime import datetime, timedelta
import pandas as pd

FIRST_NAMES = ["Mark", "Sarah", "James", "Jennifer", "David", "Michelle", "Robert", "Lisa"]
LAST_NAMES = ["Wilson", "Johnson", "Smith", "Brown", "Davis", "Miller", "Moore", "Taylor"]

# Job roles with exposure type
JOB_ROLES = [
    ("Phone Clerk", "indoor"),
    ("Shuttler", "outdoor"),
    ("Lot Coordinator", "outdoor"),
    ("Clerk", "indoor"),
    ("Triage", "outdoor"),
    ("Driver", "outdoor"),
    ("QTA", "outdoor"),
    ("Detailer", "outdoor"),
    ("Driver Sup.", "outdoor"),
]

# Schedule patterns: (name, off_days_list, consecutive_bonus)
SCHEDULE_PATTERNS = [
    ("Standard (Sat-Sun off)", [5, 6], -5),  # Weekends = most valuable recovery
    ("Tue-Wed off", [1, 2], -2),             # Mid-week days off = less restorative
    ("Sun-Mon off", [6, 0], -3),             # One weekend day + one weekday
    ("Rotating (Wed-Thu off)", [2, 3], -2), # Mid-week days off = less restorative
    ("Split (Sun-Wed off)", [6, 2], +3),    # Split schedule = harder on employee
]

def get_tooltip(day_idx, day_name, icon, desc, emp_type, exposure=None, schedule_pattern=None, off_days=None, traffic_icon=None, traffic_impact=None):
    """Generate tooltip text with factors affecting absence rate"""
    factors = []
    
    # Weather factor
    if icon in ["❄️", "🌧️"]:
        factors.append(f"Weather: {desc}")
        if exposure == "outdoor":
            factors.append("Outdoor role (weather-sensitive)")
    elif icon == "☀️":
        factors.append("Clear conditions")
    else:
        factors.append(f"Conditions: {desc}")
    
    # Traffic factor
    if traffic_icon and traffic_impact:
        if traffic_impact >= 3:
            factors.append("Heavy commute traffic")
        elif traffic_impact >= 2:
            factors.append("Moderate traffic")
        else:
            factors.append("Light traffic")
    
    # Employee type factor
    if emp_type == "new_hire":
        factors.append("New hire (higher absence history)")
    elif emp_type == "reliable":
        factors.append("Senior (excellent attendance record)")
    else:
        factors.append("Veteran (established routine)")
    
    # Schedule factor
    if schedule_pattern and off_days and day_idx not in off_days:
        if "Consecutive" in schedule_pattern or "Standard" in schedule_pattern or "off" in schedule_pattern.lower():
            if "Split" not in schedule_pattern:
                factors.append("Consecutive days off (better recovery)")
        else:
            factors.append("Split schedule (less recovery)")
    
    # Day of week factor
    if day_idx == 4:  # Friday
        factors.append("End of week (payday effects)")
    elif day_idx in [0, 1, 2]:  # Mon-Wed - beginning of week
        if icon in ["❄️", "🌧️"]:
            factors.append("Week start during poor weather")
    
    return " | ".join(factors)

def make_report(scenario_name):
    # Weather scenarios (day, weather_icon, temp, weather_desc, base_absence, traffic_icon, traffic_impact)
    scenarios = {
        "winter": {
            "title": "Mild Week with Light Rain",
            "desc": "Mostly clear week with one day of heavy rain",
            "count": 8,
            "days": [
                ("Mon", "☁️", 48, "Cloudy", 12, "🚗", 2),      # Light traffic
                ("Tue", "🌧️", 52, "Rain", 20, "🚙", 3),       # Moderate traffic (rain impacts)
                ("Wed", "☀️", 55, "Clear", 14, "🚗", 2),      # Light traffic
                ("Thu", "☀️", 58, "Sunny", 12, "🚕", 1),      # Very light traffic
                ("Fri", "☀️", 62, "Sunny", 11, "🚙", 3),      # Moderate (Friday congestion)
                ("Sat", "☀️", 64, "Sunny", 10, "🚗", 1),      # Light (weekend)
                ("Sun", "☀️", 63, "Sunny", 10, "🚗", 1),      # Light (weekend)
            ]
        },
        "spring_break": {
            "title": "Spring Break with Rain",
            "desc": "Rainy days during school closures",
            "count": 10,
            "days": [
                ("Mon", "☀️", 59, "Sunny", 14, "🚙", 3),      # Moderate traffic
                ("Tue", "☀️", 61, "Sunny", 15, "🚕", 1),      # Very light (spring break)
                ("Wed", "🌧️", 54, "Rain", 21, "🚙", 3),      # Moderate in rain
                ("Thu", "🌧️", 57, "Rain", 20, "🚙", 3),      # Moderate in rain
                ("Fri", "☁️", 64, "Cloudy", 14, "🚗", 2),     # Light traffic
                ("Sat", "☀️", 68, "Sunny", 13, "🚗", 1),      # Light (weekend)
                ("Sun", "☀️", 66, "Sunny", 13, "🚗", 1),      # Light (weekend)
            ]
        }
    }
    
    if scenario_name not in scenarios:
        print("Available: winter, spring_break")
        return
    
    s = scenarios[scenario_name]
    
    # Generate employees
    employees = []
    for i in range(s["count"]):
        if i >= s["count"] - 4:
            emp_type = "reliable"
        elif i >= s["count"] - 6:
            emp_type = "veteran"
        else:
            emp_type = "new_hire"
        
        job_role, exposure = random.choice(JOB_ROLES)
        schedule_name, off_days, schedule_bonus = random.choice(SCHEDULE_PATTERNS)
        
        # Generate past call-outs based on employee type
        # Most employees should have clean records
        if emp_type == "reliable":
            past_call_outs = 0
        elif emp_type == "veteran":
            past_call_outs = 0 if random.random() < 0.95 else 1
        else:  # new_hire
            past_call_outs = 0 if random.random() < 0.80 else random.randint(1, 2)
        
        # Calculate points (3 call-outs = 1 point, 3 points = termination)
        points = past_call_outs // 3
        
        employees.append({
            "name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
            "type": emp_type,
            "job_role": job_role,
            "exposure": exposure,
            "shift": "09:00-17:00",
            "schedule_pattern": schedule_name,
            "off_days": off_days,
            "schedule_bonus": schedule_bonus,
            "past_call_outs": past_call_outs,
            "points": points,
        })
    
    # Start HTML
    html = "<!DOCTYPE html>\n<html>\n<head>\n"
    html += '<meta charset="UTF-8">\n'
    html += f"<title>ForeSight Demo: {s['title']}</title>\n"
    html += "<style>\n"
    html += "body { font-family: system-ui; background: #f5f5f5; padding: 20px; margin: 0; }\n"
    html += ".container { max-width: 1900px; margin: 0 auto; background: white; padding: 40px; border-radius: 12px; }\n"
    html += "h1 { color: #667eea; text-align: center; margin: 0; }\n"
    html += ".subtitle { text-align: center; color: #666; margin: 0; }\n"
    html += ".table-wrapper { overflow-x: auto; margin: 40px 0; }\n"
    html += "table { width: 100%; border-collapse: collapse; }\n"
    html += "th, td { padding: 12px; border: 1px solid #ddd; text-align: left; }\n"
    html += "th { background: #f8f9fa; font-weight: 600; }\n"
    html += "tbody tr:hover { background: #f9f9f9; }\n"
    html += ".emp-name { font-weight: 600; }\n"
    html += ".weather-icon { font-size: 1em; }\n"
    html += ".risk-low { background: #4caf50; color: white; }\n"
    html += ".risk-med { background: #ff9800; color: white; }\n"
    html += ".risk-high { background: #f44336; color: white; }\n"
    html += ".rainy { background: #e3f2fd; }\n"
    html += ".centered { text-align: center; }\n"
    html += ".absence-pct { padding: 6px; border-radius: 4px; cursor: help; }\n"
    html += ".footer { text-align: center; color: #999; margin-top: 40px; border-top: 1px solid #eee; padding-top: 20px; }\n"
    html += "</style>\n</head>\n<body>\n"
    html += '<div class="container">\n'
    html += f"<h1>{s['title']}</h1>\n"
    html += f"<p class=\"subtitle\">{s['desc']}</p>\n"
    
    # Weather info box
    html += '<div style="background: #f0f0f0; padding: 15px; margin: 20px 0; border-radius: 8px; text-align: center;">\n'
    html += '<strong>Key Insight:</strong> Notice how absence rates rise on days with poor weather and traffic. '
    html += 'Rain (🌧️) with heavy traffic (🚙) shows 20-24% absence, while clear days (☀️) with light traffic (🚗) drop to 11-14%. '
    html += '<em>(Hover over percentages for breakdown)</em>\n'
    html += '</div>\n'
    
    # Table
    html += '<div class="table-wrapper">\n<table>\n<thead>\n<tr>\n'
    html += '<th colspan="3">Employee Profile</th>\n'
    
    week_start = datetime.now() + timedelta(days=7)
    for i, (day, icon, temp, desc, _, traffic_icon, traffic_impact) in enumerate(s["days"]):
        date = (week_start + timedelta(days=i)).strftime("%m/%d")
        is_rainy = icon in ["🌧️", "❄️", "⛈️"]
        rainy_class = ' class="rainy"' if is_rainy else ''
        html += f'<th{rainy_class} class="centered">\n'
        html += f'<div><strong>{day}</strong></div>\n'
        html += f'<div style="font-size: 0.9em; color: #666;">{date}</div>\n'
        html += f'<div style="font-size: 0.8em;"><span style="margin-right: 4px;">{icon}</span><span>{traffic_icon}</span></div>\n'
        html += f'<div style="font-size: 0.8em;">{desc}</div>\n'
        html += f'<div style="font-size: 0.8em; color: #666;"><strong>{temp}°F</strong></div>\n'
        html += '</th>\n'
    
    html += '</tr>\n</thead>\n<tbody>\n'
    
    # Employee rows
    for emp in employees:
        html += '<tr>\n'
        html += f'<td><div class="emp-name">{emp["name"]}</div><div style="color: #667eea; font-size: 0.9em;">{emp["job_role"]} ({emp["exposure"]})</div><div style="color: #999; font-size: 0.85em;">{emp["type"]} | {emp["schedule_pattern"]}</div></td>\n'
        html += f'<td><div style="font-size: 0.9em; font-weight: 600;"><strong>{emp["past_call_outs"]}</strong> c/o\'s</div><div style="font-size: 0.85em; color: #d32f2f; font-weight: 600;">{emp["points"]} pt{"s" if emp["points"] != 1 else ""}</div></td>\n'
        html += f'<td><div style="font-size: 0.9em;">{emp["shift"]} (M-F)</div><div style="font-size: 0.85em; color: #999;">40 hrs/week</div></td>\n'
        
        # Daily absence percentages (Mon-Fri only, weekends are off)
        for day_idx, (day, icon, temp, desc, base_absence, traffic_icon, traffic_impact) in enumerate(s["days"]):
            # Check if this is a day off for this employee
            is_day_off = day_idx in emp["off_days"]
            
            if is_day_off:
                is_rainy = icon in ["🌧️", "❄️", "⛈️"]
                rainy_class = ' rainy' if is_rainy else ''
                html += f'<td class="centered{rainy_class}"><div style="padding: 8px; color: #999; font-size: 0.9em;"><em>Off</em></div></td>\n'
                continue
            
            # Adjust by employee type
            if emp["type"] == "new_hire":
                absence = base_absence + 3
            elif emp["type"] == "reliable":
                absence = max(2, base_absence - 5)  # Very low absence, minimum 2%
            else:  # veteran
                absence = base_absence
            
            # Apply schedule quality bonus/penalty
            absence = absence + emp["schedule_bonus"]
            absence = max(2, min(100, absence))  # Clamp between 2% and 100%
            
            # Traffic impact
            absence = absence + traffic_impact
            
            # Outdoor roles more affected by weather (rainy/snowy days)
            if emp["exposure"] == "outdoor" and icon in ["❄️", "🌧️"]:
                absence = min(100, absence + 3)
            
            absence = max(2, min(100, absence))  # Clamp between 2% and 100%
            
            if absence < 15:
                risk_color = "risk-low"
            elif absence < 22:
                risk_color = "risk-med"
            else:
                risk_color = "risk-high"
            
            is_rainy = icon in ["🌧️", "❄️", "⛈️"]
            rainy_class = ' rainy' if is_rainy else ''
            
            # Generate tooltip
            tooltip = get_tooltip(day_idx, day, icon, desc, emp["type"], emp["exposure"], emp["schedule_pattern"], emp["off_days"], traffic_icon, traffic_impact)
            
            html += f'<td class="centered{rainy_class}"><div class="absence-pct {risk_color}" title="{tooltip}"><strong>{absence}%</strong></div></td>\n'
        
        html += '</tr>\n'
    
    html += '</tbody>\n</table>\n</div>\n'
    
    html += '<div class="footer">\n'
    html += f'<p>Generated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}</p>\n'
    html += '<p>ForeSight Attendance Prediction System</p>\n'
    html += '</div>\n'
    html += '</div>\n</body>\n</html>\n'
    
    # Save
    filename = f"demo_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"Report saved: {filename}")
    return filename


if __name__ == "__main__":
    import sys
    scenario = sys.argv[1] if len(sys.argv) > 1 else "winter"
    make_report(scenario)
