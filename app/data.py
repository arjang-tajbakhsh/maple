"""Loads data.json (built by scripts/build_data.py) and answers small questions about it.

Nothing in here builds HTML. It only looks things up in the data.

What one season looks like in data.json (abridged):
    {
      "year": 2026, "title": "...", "blurb": "...",
      "start": "2026-03-07", "end": "2026-04-11",      first and last fire
      "totalGal": 217.25, "butterPots": 115,
      "boilDays": 16, "logDays": 18, "lengthDays": 36,
      "sapDaysWindow": 11,      sap-weather days from 15 Feb to 20 Apr
      "sapDaysInSeason": 6,     sap-weather days between start and end
      "days": [ one entry per logbook line:
          {"date", "gal", "galText", "pots", "potsText", "bottled",
           "fireStart", "fireEnd", "notes", "lo", "hi"} ],
      "weather": [ one entry per calendar day, 15 Feb to 20 Apr:
          {"d": date, "lo": night low, "hi": day high, "p": rain mm,
           "s": snow cm, "sap": true if it was a sap-weather day} ]
    }
"""
import json
from datetime import date
from pathlib import Path

DATA = json.loads((Path(__file__).parent / "data.json").read_text(encoding="utf-8"))

FARM = DATA["farm"]                  # {"name": ..., "subtitle": ...}
SAP_RULE = DATA["sapDayRule"]        # {"nightBelowC": 0.0, "dayAboveC": 4.0}
SEASONS = DATA["seasons"]            # oldest first
LATEST_YEAR = SEASONS[-1]["year"]
UPDATED_ON = DATA["generated"][:10]  # "2026-11-21"

# Rough, fun estimates shown on the "Toutes les saisons" page
PANCAKE_STACKS_PER_GAL = 64          # ¼ cup of syrup per stack
POUDING_PER_GAL = 16                 # 1 cup of syrup per pouding chômeur (16 cups in a gallon)
SAP_TO_SYRUP_RATIO = 40              # 40 gallons of sap boil down to 1 of syrup


def season(year):
    """The season for a given year, e.g. season(2024)."""
    return next(s for s in SEASONS if s["year"] == year)


def average_gal():
    """Average syrup per season, in gallons."""
    return sum(s["totalGal"] for s in SEASONS) / len(SEASONS)


def all_days():
    """Every logbook day from every season, each one tagged with its year."""
    return [{**day, "year": s["year"]} for s in SEASONS for day in s["days"]]


def biggest_day(days):
    """The day with the most syrup. On a tie, the earliest one wins."""
    return max(days, key=lambda day: day["gal"] or 0)


def logbook_entry(s, iso):
    """The logbook line for a date, or None if nothing was written that day."""
    return next((day for day in s["days"] if day["date"] == iso), None)


def weather_on(s, iso):
    """The weather for a date, or None if it's outside 15 Feb to 20 Apr."""
    return next((w for w in s["weather"] if w["d"] == iso), None)


def on_shared_calendar(iso):
    """Move a date to the same month and day in 2024.

    This lets seasons from different years line up on one calendar.
    2024 is a leap year, so 29 Feb has a place too.
    """
    d = date.fromisoformat(iso)
    return date(2024, d.month, d.day)
