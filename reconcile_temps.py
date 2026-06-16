#!/usr/bin/env python3
"""
Backfill daily high temperatures from Jan 1, 2026 to yesterday
using Open-Meteo Historical Weather API (free, no key, ERA5 reanalysis data).

Fills gaps in daily_high_temps.json without overwriting existing entries.
"""

import json
import urllib.request
from datetime import date, timedelta
from pathlib import Path

# Config
ZIP_CODE = "98375"
LAT = 47.10670352169889
LON = -122.32434017043883
DATA_FILE = Path(__file__).parent / "daily_high_temps.json"
START_DATE = date(2026, 1, 1)


def fetch_historical_highs(start: date, end: date) -> dict[str, float]:
    """Fetch daily max temps from Open-Meteo historical archive. Returns {date_str: temp_f}."""
    url = (
        f"https://archive-api.open-meteo.com/v1/archive"
        f"?latitude={LAT}&longitude={LON}"
        f"&start_date={start.isoformat()}&end_date={end.isoformat()}"
        f"&daily=temperature_2m_max&temperature_unit=fahrenheit&timezone=America%2FLos_Angeles"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "daily-temp-reconcile/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read())

    dates = data["daily"]["time"]
    highs = data["daily"]["temperature_2m_max"]
    return {d: h for d, h in zip(dates, highs) if h is not None}


def load_records() -> list:
    if DATA_FILE.exists():
        with open(DATA_FILE) as f:
            return json.load(f)
    return []


def save_records(records: list):
    records.sort(key=lambda r: r["date"])
    with open(DATA_FILE, "w") as f:
        json.dump(records, f, indent=2)


def main():
    today = date.today()
    end_date = today - timedelta(days=1)  # yesterday — today runs via nightly cron

    if end_date < START_DATE:
        print("Nothing to backfill.")
        return

    records = load_records()
    existing_dates = {r["date"] for r in records}

    # Find gaps between START_DATE and yesterday
    missing = [
        START_DATE + timedelta(days=i)
        for i in range((end_date - START_DATE).days + 1)
        if (START_DATE + timedelta(days=i)).isoformat() not in existing_dates
    ]

    if not missing:
        print("No gaps found — daily_high_temps.json is already complete.")
        return

    print(f"Fetching {len(missing)} missing days ({missing[0]} → {missing[-1]})...")

    historical = fetch_historical_highs(missing[0], missing[-1])

    added = 0
    for d in missing:
        ds = d.isoformat()
        if ds not in historical:
            print(f"  [SKIP] {ds} — no data returned")
            continue
        high_f = round(historical[ds], 1)
        high_c = round((high_f - 32) * 5 / 9, 1)
        records.append({
            "date": ds,
            "zip": ZIP_CODE,
            "high_f": high_f,
            "high_c": high_c,
            "source": "Open-Meteo archive-api.open-meteo.com (ERA5)"
        })
        added += 1

    save_records(records)
    print(f"Done. Added {added} records. Total in file: {len(records)}")


if __name__ == "__main__":
    main()
