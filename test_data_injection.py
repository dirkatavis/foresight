"""
ForeSight Test Data Injection System
Allows controlled injection of weather, traffic, and holiday data for testing.
Enables reproducible E2E tests with specific external conditions.
"""

import json
import os
from datetime import datetime, date
from typing import Dict, Optional, List

# Global test data registry
TEST_DATA = {
    "weather": {},      # date -> weather conditions
    "traffic": {},      # date -> traffic conditions
    "holidays": {},     # date -> holiday info
    "enabled": False    # Enable/disable injection
}

# File-based persistence
TEST_DATA_FILE = "test_data_config.json"


def enable_injection():
    """Enable test data injection mode."""
    TEST_DATA["enabled"] = True
    print("[TEST-INJECT] Test data injection ENABLED")


def disable_injection():
    """Disable test data injection mode."""
    TEST_DATA["enabled"] = False
    print("[TEST-INJECT] Test data injection DISABLED")


def is_injection_enabled() -> bool:
    """Check if test data injection is enabled."""
    return TEST_DATA.get("enabled", False)


# =============================================================================
# WEATHER DATA INJECTION
# =============================================================================

def inject_weather(shift_date: str, conditions: Dict) -> None:
    """
    Inject specific weather conditions for a date.
    
    Args:
        shift_date: Date string (YYYY-MM-DD)
        conditions: Dict with keys like:
            - precipitation_mm: float (0-100)
            - temperature_c: float (-40 to 50)
            - weather_code: int (WMO code)
            - weather_alerts: list of alert strings
    
    Example:
        inject_weather("2026-03-20", {
            "precipitation_mm": 45.5,
            "temperature_c": -5,
            "weather_code": 71,  # Heavy snow
            "weather_alerts": ["winter_storm_warning"]
        })
    """
    TEST_DATA["weather"][shift_date] = {
        "precipitation_mm": float(conditions.get("precipitation_mm", 0)),
        "temperature_c": float(conditions.get("temperature_c", 20)),
        "temperature_min_c": float(conditions.get("temperature_min_c", 15)),
        "weather_code": int(conditions.get("weather_code", 0)),
        "weather_alerts": conditions.get("weather_alerts", []),
        "data_source": "test_injection",
    }
    print(f"[TEST-INJECT] Weather injected for {shift_date}: {conditions}")
    _save_to_file()


def get_injected_weather(shift_date: str) -> Optional[Dict]:
    """Get injected weather data for a date, if available."""
    if not is_injection_enabled():
        return None
    return TEST_DATA["weather"].get(shift_date)


def clear_weather(shift_date: str = None) -> None:
    """Clear weather data for a specific date or all dates."""
    if shift_date:
        TEST_DATA["weather"].pop(shift_date, None)
        print(f"[TEST-INJECT] Weather cleared for {shift_date}")
    else:
        TEST_DATA["weather"].clear()
        print("[TEST-INJECT] All weather data cleared")
    _save_to_file()


# =============================================================================
# TRAFFIC DATA INJECTION
# =============================================================================

def inject_traffic(shift_date: str, conditions: Dict) -> None:
    """
    Inject specific traffic conditions for a date.
    
    Args:
        shift_date: Date string (YYYY-MM-DD)
        conditions: Dict with keys like:
            - travel_time_minutes: float
            - congestion_level: float (0.0-1.0)
    
    Example:
        inject_traffic("2026-03-20", {
            "travel_time_minutes": 90.0,
            "congestion_level": 0.95
        })
    """
    TEST_DATA["traffic"][shift_date] = {
        "travel_time_minutes": float(conditions.get("travel_time_minutes", 30)),
        "congestion_level": float(conditions.get("congestion_level", 0.5)),
        "data_source": "test_injection",
    }
    print(f"[TEST-INJECT] Traffic injected for {shift_date}: {conditions}")
    _save_to_file()


def get_injected_traffic(shift_date: str) -> Optional[Dict]:
    """Get injected traffic data for a date, if available."""
    if not is_injection_enabled():
        return None
    return TEST_DATA["traffic"].get(shift_date)


def clear_traffic(shift_date: str = None) -> None:
    """Clear traffic data for a specific date or all dates."""
    if shift_date:
        TEST_DATA["traffic"].pop(shift_date, None)
        print(f"[TEST-INJECT] Traffic cleared for {shift_date}")
    else:
        TEST_DATA["traffic"].clear()
        print("[TEST-INJECT] All traffic data cleared")
    _save_to_file()


# =============================================================================
# HOLIDAY / CALENDAR INJECTION
# =============================================================================

def inject_holiday(shift_date: str, holiday_info: Dict) -> None:
    """
    Inject holiday or calendar event for a date.
    
    Args:
        shift_date: Date string (YYYY-MM-DD)
        holiday_info: Dict with keys like:
            - name: str (holiday name)
            - type: str ('holiday', 'school_closure', 'weekend_extended')
            - region: str (optional, e.g., 'US', 'CA')
    
    Example:
        inject_holiday("2026-03-17", {
            "name": "St. Patrick's Day",
            "type": "public_holiday",
            "region": "US"
        })
    """
    TEST_DATA["holidays"][shift_date] = {
        "name": holiday_info.get("name", ""),
        "type": holiday_info.get("type", "event"),
        "region": holiday_info.get("region", "US"),
    }
    print(f"[TEST-INJECT] Holiday injected for {shift_date}: {holiday_info}")
    _save_to_file()


def get_injected_holiday(shift_date: str) -> Optional[Dict]:
    """Get injected holiday data for a date, if available."""
    if not is_injection_enabled():
        return None
    return TEST_DATA["holidays"].get(shift_date)


def clear_holiday(shift_date: str = None) -> None:
    """Clear holiday data for a specific date or all dates."""
    if shift_date:
        TEST_DATA["holidays"].pop(shift_date, None)
        print(f"[TEST-INJECT] Holiday cleared for {shift_date}")
    else:
        TEST_DATA["holidays"].clear()
        print("[TEST-INJECT] All holiday data cleared")
    _save_to_file()


# =============================================================================
# BATCH INJECTION (SCENARIOS)
# =============================================================================

def inject_scenario(scenario_name: str, scenario_data: Dict) -> None:
    """
    Inject a complete test scenario (weather + traffic + holidays).
    
    Args:
        scenario_name: Name of the scenario (for reference)
        scenario_data: Dict with structure:
            {
                "dates": ["2026-03-20", "2026-03-21"],
                "weather": {date: conditions},
                "traffic": {date: conditions},
                "holidays": {date: holiday_info}
            }
    
    Example:
        inject_scenario("severe_storm_day", {
            "dates": ["2026-03-20"],
            "weather": {
                "2026-03-20": {
                    "precipitation_mm": 50,
                    "temperature_c": -10,
                    "weather_alerts": ["winter_storm_warning"]
                }
            },
            "traffic": {
                "2026-03-20": {
                    "travel_time_minutes": 120,
                    "congestion_level": 0.9
                }
            },
            "holidays": {}
        })
    """
    print(f"\n[TEST-INJECT] Loading scenario: {scenario_name}")
    
    # Inject weather
    for date_str, weather_conditions in scenario_data.get("weather", {}).items():
        inject_weather(date_str, weather_conditions)
    
    # Inject traffic
    for date_str, traffic_conditions in scenario_data.get("traffic", {}).items():
        inject_traffic(date_str, traffic_conditions)
    
    # Inject holidays
    for date_str, holiday_info in scenario_data.get("holidays", {}).items():
        inject_holiday(date_str, holiday_info)
    
    print(f"[TEST-INJECT] Scenario '{scenario_name}' loaded\n")


# =============================================================================
# PERSISTENCE
# =============================================================================

def _save_to_file() -> None:
    """Save test data configuration to file."""
    try:
        with open(TEST_DATA_FILE, "w") as f:
            json.dump(TEST_DATA, f, indent=2)
    except Exception as e:
        print(f"[TEST-INJECT] Warning: Failed to save test data to file: {e}")


def load_from_file() -> None:
    """Load test data configuration from file."""
    global TEST_DATA
    try:
        if os.path.exists(TEST_DATA_FILE):
            with open(TEST_DATA_FILE, "r") as f:
                TEST_DATA = json.load(f)
            print(f"[TEST-INJECT] Loaded test data from {TEST_DATA_FILE}")
    except Exception as e:
        print(f"[TEST-INJECT] Warning: Failed to load test data from file: {e}")


def clear_all() -> None:
    """Clear all injected test data."""
    TEST_DATA["weather"].clear()
    TEST_DATA["traffic"].clear()
    TEST_DATA["holidays"].clear()
    TEST_DATA["enabled"] = False
    print("[TEST-INJECT] All test data cleared")
    _save_to_file()


def get_status() -> Dict:
    """Get current test data injection status."""
    return {
        "enabled": TEST_DATA["enabled"],
        "weather_dates": list(TEST_DATA["weather"].keys()),
        "traffic_dates": list(TEST_DATA["traffic"].keys()),
        "holiday_dates": list(TEST_DATA["holidays"].keys()),
    }


# =============================================================================
# PREDEFINED SCENARIOS
# =============================================================================

SCENARIO_SEVERE_STORM = {
    "name": "severe_storm_day",
    "description": "Winter storm with heavy snow, low temps, severe traffic",
    "dates": ["2026-03-20"],
    "weather": {
        "2026-03-20": {
            "precipitation_mm": 65.0,
            "temperature_c": -15.0,
            "temperature_min_c": -20.0,
            "weather_code": 75,  # Heavy snow
            "weather_alerts": ["winter_storm_warning", "blizzard_warning"]
        }
    },
    "traffic": {
        "2026-03-20": {
            "travel_time_minutes": 150.0,
            "congestion_level": 0.95
        }
    },
    "holidays": {}
}

SCENARIO_HOLIDAY_PERIOD = {
    "name": "holiday_period",
    "description": "Holiday with school closures and extended weekends",
    "dates": ["2026-04-10", "2026-04-11", "2026-04-12"],
    "weather": {
        "2026-04-10": {"precipitation_mm": 2.0, "temperature_c": 18.0, "weather_code": 1},
        "2026-04-11": {"precipitation_mm": 0.0, "temperature_c": 22.0, "weather_code": 0},
        "2026-04-12": {"precipitation_mm": 5.0, "temperature_c": 20.0, "weather_code": 3},
    },
    "traffic": {
        "2026-04-10": {"travel_time_minutes": 45.0, "congestion_level": 0.6},
        "2026-04-11": {"travel_time_minutes": 35.0, "congestion_level": 0.3},
        "2026-04-12": {"travel_time_minutes": 50.0, "congestion_level": 0.7},
    },
    "holidays": {
        "2026-04-10": {
            "name": "Spring Break Start",
            "type": "school_closure",
            "region": "US"
        }
    }
}

SCENARIO_HEAT_WAVE = {
    "name": "heat_wave",
    "description": "Extreme heat with high temperatures affecting outdoor workers",
    "dates": ["2026-07-15", "2026-07-16", "2026-07-17"],
    "weather": {
        "2026-07-15": {"precipitation_mm": 0.0, "temperature_c": 42.0, "weather_code": 0, "weather_alerts": ["heat_advisory"]},
        "2026-07-16": {"precipitation_mm": 0.0, "temperature_c": 45.0, "weather_code": 0, "weather_alerts": ["excessive_heat_warning"]},
        "2026-07-17": {"precipitation_mm": 0.0, "temperature_c": 43.0, "weather_code": 0, "weather_alerts": ["heat_advisory"]},
    },
    "traffic": {
        "2026-07-15": {"travel_time_minutes": 25.0, "congestion_level": 0.2},
        "2026-07-16": {"travel_time_minutes": 20.0, "congestion_level": 0.1},
        "2026-07-17": {"travel_time_minutes": 28.0, "congestion_level": 0.3},
    },
    "holidays": {}
}

SCENARIO_NORMAL_DAY = {
    "name": "normal_day",
    "description": "Clear day with normal traffic and no alerts",
    "dates": ["2026-06-15"],
    "weather": {
        "2026-06-15": {
            "precipitation_mm": 0.0,
            "temperature_c": 22.0,
            "temperature_min_c": 18.0,
            "weather_code": 0,
            "weather_alerts": []
        }
    },
    "traffic": {
        "2026-06-15": {
            "travel_time_minutes": 30.0,
            "congestion_level": 0.3
        }
    },
    "holidays": {}
}

PREDEFINED_SCENARIOS = {
    "severe_storm": SCENARIO_SEVERE_STORM,
    "holiday_period": SCENARIO_HOLIDAY_PERIOD,
    "heat_wave": SCENARIO_HEAT_WAVE,
    "normal_day": SCENARIO_NORMAL_DAY,
}


def list_scenarios() -> List[str]:
    """List all available predefined scenarios."""
    return list(PREDEFINED_SCENARIOS.keys())


def inject_predefined_scenario(scenario_key: str) -> None:
    """
    Inject a predefined test scenario.
    
    Args:
        scenario_key: Key from PREDEFINED_SCENARIOS (e.g., "severe_storm")
    """
    if scenario_key not in PREDEFINED_SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario_key}. Available: {list(PREDEFINED_SCENARIOS.keys())}")
    
    scenario = PREDEFINED_SCENARIOS[scenario_key]
    inject_scenario(scenario["name"], scenario)


# =============================================================================
# CLI HELPER
# =============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Test Data Injection CLI")
        print("\nUsage: python test_data_injection.py <command> [args]")
        print("\nCommands:")
        print("  enable                          - Enable injection mode")
        print("  disable                         - Disable injection mode")
        print("  status                          - Show current status")
        print("  clear                           - Clear all data")
        print("  list-scenarios                  - List available scenarios")
        print("  inject-scenario <scenario>      - Inject a predefined scenario")
        print("  weather <date> <json>           - Inject weather (JSON string)")
        print("  traffic <date> <json>           - Inject traffic (JSON string)")
        print("  holiday <date> <json>           - Inject holiday (JSON string)")
        print("\nExamples:")
        print('  python test_data_injection.py weather 2026-03-20 \'{"precipitation_mm": 50, "temperature_c": -10}\'')
        print("  python test_data_injection.py inject-scenario severe_storm")
        print("  python test_data_injection.py enable")
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "enable":
        enable_injection()
    elif cmd == "disable":
        disable_injection()
    elif cmd == "status":
        status = get_status()
        print(json.dumps(status, indent=2))
    elif cmd == "clear":
        clear_all()
    elif cmd == "list-scenarios":
        print("Available scenarios:")
        for key in list_scenarios():
            scenario = PREDEFINED_SCENARIOS[key]
            print(f"  - {key}: {scenario['description']}")
    elif cmd == "inject-scenario":
        if len(sys.argv) < 3:
            print("Usage: inject-scenario <scenario>")
            sys.exit(1)
        inject_predefined_scenario(sys.argv[2])
        enable_injection()
    elif cmd == "weather":
        if len(sys.argv) < 4:
            print("Usage: weather <date> <json>")
            sys.exit(1)
        date_str = sys.argv[2]
        conditions = json.loads(sys.argv[3])
        inject_weather(date_str, conditions)
        enable_injection()
    elif cmd == "traffic":
        if len(sys.argv) < 4:
            print("Usage: traffic <date> <json>")
            sys.exit(1)
        date_str = sys.argv[2]
        conditions = json.loads(sys.argv[3])
        inject_traffic(date_str, conditions)
        enable_injection()
    elif cmd == "holiday":
        if len(sys.argv) < 4:
            print("Usage: holiday <date> <json>")
            sys.exit(1)
        date_str = sys.argv[2]
        holiday_info = json.loads(sys.argv[3])
        inject_holiday(date_str, holiday_info)
        enable_injection()
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
