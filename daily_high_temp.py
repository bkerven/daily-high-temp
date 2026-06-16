#!/usr/bin/env python3
"""
Record daily high temperature for zip code 98375 using NOAA/NWS API.
Source: api.weather.gov (authoritative US government, no API key required)
Runs at 23:59 nightly via cron.
"""

import json
import urllib.request
import urllib.error
from datetime import date
from pathlib import Path

# Config
ZIP_CODE = "98375"
# Lat/lon for 98375 (Puyallup/South Hill, WA)
LAT = 47.10670352169889
LON = -122.32434017043883
DATA_FILE = Path(__file__).parent / "daily_high_temps.json"
NWS_UA = "daily-temp-logger/1.0 (homelab; bkerven@gmail.com)"


def nws_get(url):
    req = urllib.request.Request(url, headers={"User-Agent": NWS_UA, "Accept": "application/geo+json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def get_daily_high():
    # Step 1: resolve grid point from lat/lon
    point_data = nws_get(f"https://api.weather.gov/points/{LAT},{LON}")
    props = point_data["properties"]
    grid_id = props["gridId"]
    grid_x = props["gridX"]
    grid_y = props["gridY"]

    # Step 2: fetch hourly forecast and find today's max
    hourly_url = f"https://api.weather.gov/gridpoints/{grid_id}/{grid_x},{grid_y}/forecast/hourly"
    hourly_data = nws_get(hourly_url)

    today = date.today().isoformat()
    periods = hourly_data["properties"]["periods"]

    today_highs = [
        p["temperature"]
        for p in periods
        if p["startTime"].startswith(today) and p["temperatureUnit"] == "F"
    ]

    if not today_highs:
        raise ValueError(f"No hourly data found for {today}")

    return max(today_highs)


def load_records():
    if DATA_FILE.exists():
        with open(DATA_FILE) as f:
            return json.load(f)
    return []


def save_records(records):
    with open(DATA_FILE, "w") as f:
        json.dump(records, f, indent=2)


def main():
    today = date.today().isoformat()
    records = load_records()

    # Avoid duplicate entries for today
    existing_dates = {r["date"] for r in records}
    if today in existing_dates:
        print(f"[{today}] Already recorded for today, skipping.")
        return

    high_f = get_daily_high()
    high_c = round((high_f - 32) * 5 / 9, 1)

    entry = {
        "date": today,
        "zip": ZIP_CODE,
        "high_f": high_f,
        "high_c": high_c,
        "source": "NOAA/NWS api.weather.gov"
    }

    records.append(entry)
    save_records(records)
    print(f"[{today}] Recorded high: {high_f}°F / {high_c}°C for {ZIP_CODE}")


if __name__ == "__main__":
    main()
