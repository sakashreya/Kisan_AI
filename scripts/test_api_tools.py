"""
scripts/test_api_tools.py
Phase 6: Verify API Tools (OpenWeatherMap and SoilGrids).
Tests live weather data retrieval, geocoding, and ISRIC SoilGrids soil properties.
"""

import os
import sys
import time
from dotenv import load_dotenv

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

load_dotenv(os.path.join(ROOT_DIR, ".env"), override=True)

if sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app.tools import get_weather, get_soil, geocode
from app.config import OPENWEATHER_API_KEY

def run_tests():
    print("=" * 80)
    print("PHASE 6: API TOOLS VERIFICATION (WEATHER & SOIL)")
    print("=" * 80)

    # 1. OpenWeather API Key Presence Check
    has_key = bool(OPENWEATHER_API_KEY and len(OPENWEATHER_API_KEY.strip()) > 5)
    masked_key = (OPENWEATHER_API_KEY[:4] + "..." + OPENWEATHER_API_KEY[-4:]) if has_key else "NOT SET"
    print(f"OpenWeather API Key configured: {has_key} ({masked_key})")

    # 2. Step 6.1: Live Weather Test (Chennai: lat=13.08, lon=80.27)
    print("\n" + "-" * 80)
    print("[Step 6.1] TESTING GET_WEATHER (lat=13.08, lon=80.27 - Chennai)")
    print("-" * 80)
    t0 = time.perf_counter()
    weather_chennai = get_weather.invoke({"lat": 13.08, "lon": 80.27})
    t_weather = time.perf_counter() - t0
    print(f"Chennai Weather ({t_weather:.2f}s):")
    print(f"  --> {weather_chennai}")

    # Geocoding test
    print("\nTesting Geocode for 'Thanjavur':")
    t0 = time.perf_counter()
    geo_res = geocode("Thanjavur")
    t_geo = time.perf_counter() - t0
    print(f"Response ({t_geo:.2f}s): {geo_res}")

    # Weather for Thanjavur (agricultural delta)
    if geo_res:
        t0 = time.perf_counter()
        weather_thanjavur = get_weather.invoke({"lat": geo_res[0], "lon": geo_res[1]})
        t_w_thanj = time.perf_counter() - t0
        print(f"Thanjavur Weather ({t_w_thanj:.2f}s):")
        print(f"  --> {weather_thanjavur}")

    # 3. Step 6.2: Live SoilGrids Test
    print("\n" + "-" * 80)
    print("[Step 6.2] TESTING GET_SOIL")
    print("-" * 80)

    # 3a. Chennai test (as requested in Step 6.2)
    t0 = time.perf_counter()
    soil_chennai = get_soil.invoke({"lat": 13.08, "lon": 80.27})
    t_soil_ch = time.perf_counter() - t0
    print(f"Chennai (13.08, 80.27) ({t_soil_ch:.2f}s):")
    print(f"  --> {soil_chennai}")

    # 3b. Thanjavur test (Agricultural Delta soil)
    t0 = time.perf_counter()
    soil_thanjavur = get_soil.invoke({"lat": 10.78, "lon": 79.13})
    t_soil_th = time.perf_counter() - t0
    print(f"Thanjavur Agricultural Delta (10.78, 79.13) ({t_soil_th:.2f}s):")
    print(f"  --> {soil_thanjavur}")

    # 4. Summary Table
    print("\n" + "=" * 80)
    print("PHASE 6 RESULTS SUMMARY")
    print("=" * 80)
    weather_ok = not weather_chennai.startswith("Weather lookup failed")
    soil_ok = not soil_thanjavur.startswith("Soil lookup failed") and "clay" in soil_thanjavur
    geo_ok = geo_res is not None

    print(f"Geocoding (OpenWeatherMap Geo): {'PASS' if geo_ok else 'FAIL'} ({t_geo:.2f}s)")
    print(f"Weather Tool (OpenWeatherMap):  {'PASS' if weather_ok else 'FAIL'} ({t_weather:.2f}s)")
    print(f"Soil Tool (ISRIC SoilGrids):     {'PASS' if soil_ok else 'FAIL'} ({t_soil_th:.2f}s)")
    print("=" * 80)

if __name__ == "__main__":
    run_tests()
