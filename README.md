# daily-high-temp

Records the daily high temperature for zip code 98375 (Puyallup/South Hill, WA) using the authoritative NOAA/NWS API (api.weather.gov — no API key required).

## Setup

```bash
# Clone to beebox or wherever you want it to run
git clone https://github.com/bkerven/daily-high-temp.git
cd daily-high-temp
```

## Cron

Add to crontab (`crontab -e`):

```
59 23 * * * /usr/bin/python3 /path/to/daily-high-temp/daily_high_temp.py >> /path/to/daily-high-temp/daily_high_temp.log 2>&1
```

## Output

Appends to `daily_high_temps.json`:

```json
[
  {
    "date": "2026-06-16",
    "zip": "98375",
    "high_f": 72,
    "high_c": 22.2,
    "source": "NOAA/NWS api.weather.gov"
  }
]
```

## Notes

- Runs at 23:59 to capture the full day's hourly forecast data
- Skips duplicate entries if run more than once on the same day
- NWS hourly forecast covers the next 7 days; tonight's reading reflects today's peak
