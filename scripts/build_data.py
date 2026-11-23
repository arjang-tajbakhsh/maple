"""Build app/data.json from the production log + weather CSVs.

Usage (from the repo root):
    python scripts/build_data.py                 # rebuild from files in data/
    python scripts/build_data.py --fetch-weather # also re-download weather from Open-Meteo first

Only uses the Python standard library.
"""

import argparse
import csv
import glob
import json
import os
import re
import urllib.request
from collections import defaultdict
from datetime import date, datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "app", "data.json")

LAT, LON = 45.17, -72.48
TZ = "America/Toronto"

# A "sap day" = freezing night followed by a thawing day. Same definition as main.ipynb.
NIGHT_BELOW_C = 0.0
DAY_ABOVE_C = 4.0
DAY_HOURS = range(9, 18)  # 09:00–17:59 counts as "day", everything else as "night"

# The window shown on every season chart (month, day). Widened automatically if a season runs outside it.
WINDOW_START = (2, 15)
WINDOW_END = (4, 20)


def latest(pattern):
    files = sorted(glob.glob(os.path.join(DATA, pattern)))
    if not files:
        raise SystemExit(f"No file matching data/{pattern}")
    return files[-1]


# ---------------------------------------------------------------- weather
def fetch_weather():
    start = "2022-01-15"
    end = (date.today() - timedelta(days=7)).isoformat()
    url = (
        "https://archive-api.open-meteo.com/v1/archive"
        f"?latitude={LAT}&longitude={LON}&start_date={start}&end_date={end}"
        f"&hourly=temperature_2m,precipitation,snow_depth&timezone={TZ}&format=csv"
    )
    dest = os.path.join(DATA, "open-meteo-weather.csv")
    print("Downloading weather", start, "to", end)
    with urllib.request.urlopen(url, timeout=60) as r, open(dest, "wb") as f:
        f.write(r.read())
    print("Saved", os.path.relpath(dest, ROOT))


def load_weather(path):
    """Return {date: {lo, hi, p, s}} with night low / day high in °C, precip mm, snow depth cm."""
    hours = defaultdict(list)
    with open(path, encoding="utf-8", errors="replace") as f:
        rows = list(csv.reader(f))
    start = next(i for i, r in enumerate(rows) if r and r[0] == "time") + 1
    for r in rows[start:]:
        if len(r) < 4 or not r[1]:
            continue
        t = datetime.fromisoformat(r[0])
        hours[t.date()].append((t.hour, float(r[1]), float(r[2] or 0), float(r[3] or 0)))

    daily = {}
    for d, hs in hours.items():
        day = [h[1] for h in hs if h[0] in DAY_HOURS]
        night = [h[1] for h in hs if h[0] not in DAY_HOURS]
        if not day or not night:
            continue
        daily[d] = {
            "lo": round(min(night), 1),
            "hi": round(max(day), 1),
            "p": round(sum(h[2] for h in hs), 1),
            "s": round(max(h[3] for h in hs) * 100),
        }
    return daily


def is_sap_day(w):
    return w is not None and w["lo"] < NIGHT_BELOW_C and w["hi"] > DAY_ABOVE_C


# ---------------------------------------------------------------- production log
GAL_RE = re.compile(r"(\d+(?:\.\d+)?)(?:\s*-\s*(\d+(?:\.\d+)?))?\s*gal", re.I)
POTS_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:x\s*500\s*g|pots?\b)", re.I)
SEASON_GAL_RE = re.compile(r"season total[^0-9]*(\d+(?:\.\d+)?)\s*gal", re.I)
SEASON_POTS_RE = re.compile(r"season total[^;]*?/\s*(\d+)\s*pots", re.I)


def parse_gallons(text):
    """First gallon figure written for the day ('~9-10 gal' -> 9.5)."""
    m = GAL_RE.search(text or "")
    if not m:
        return None
    a = float(m.group(1))
    return round((a + float(m.group(2))) / 2, 3) if m.group(2) else a


def parse_pots(text):
    text = re.sub(r"\([^)]*\)", "", text or "")  # drop '(23+23)' / '(582-640g)' asides
    nums = [float(n) for n in POTS_RE.findall(text)]
    return round(sum(nums), 2) if nums else None


def clean_time(t):
    t = (t or "").strip()
    return t or None


def load_log(path):
    with open(path, encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if r.get("date")]


# ---------------------------------------------------------------- build
def build(log_path, weather_path):
    weather = load_weather(weather_path)
    try:
        with open(os.path.join(DATA, "seasons.json"), encoding="utf-8") as f:
            stories = json.load(f)
    except FileNotFoundError:
        stories = {}

    by_season = defaultdict(list)
    for r in load_log(log_path):
        by_season[str(r["season"]).strip()].append(r)

    seasons = []
    for year in sorted(by_season):
        rows = sorted(by_season[year], key=lambda r: r["date"])
        story = stories.get(year, {})
        days = []
        stated_gal = stated_pots = None
        for r in rows:
            d = date.fromisoformat(r["date"])
            notes = (r.get("notes") or "").strip()
            if m := SEASON_GAL_RE.findall(notes):
                stated_gal = float(m[-1])
            if m := SEASON_POTS_RE.findall(notes):
                stated_pots = int(m[-1])
            w = weather.get(d)
            days.append({
                "date": r["date"],
                "gal": parse_gallons(r.get("syrup_produced")),
                "galText": (r.get("syrup_produced") or "").strip(),
                "pots": parse_pots(r.get("butter_pots")),
                "potsText": (r.get("butter_pots") or "").strip(),
                "bottled": (r.get("bottled_canned_detail") or "").strip(),
                "fireStart": clean_time(r.get("fire_start")),
                "fireEnd": clean_time(r.get("fire_end")),
                "notes": notes,
                "lo": w and w["lo"],
                "hi": w and w["hi"],
                "sapDay": is_sap_day(w),
            })

        first = date.fromisoformat(days[0]["date"])
        last = date.fromisoformat(days[-1]["date"])
        y = int(year)
        w_start = min(date(y, *WINDOW_START), first - timedelta(days=3))
        w_end = max(date(y, *WINDOW_END), last + timedelta(days=3))

        wx = []
        d = w_start
        while d <= w_end:
            w = weather.get(d)
            if w:
                wx.append({"d": d.isoformat(), **w, "sap": is_sap_day(w)})
            d += timedelta(days=1)

        summed_gal = round(sum(x["gal"] or 0 for x in days), 2)
        summed_pots = round(sum(x["pots"] or 0 for x in days))
        total_gal = story.get("total_gal", stated_gal if stated_gal is not None else summed_gal)
        total_pots = story.get("butter_pots", stated_pots if stated_pots is not None else summed_pots)

        # Comparable across years: sap days in the fixed Feb 15 – Apr 20 window
        fixed = [x for x in wx if date(y, *WINDOW_START) <= date.fromisoformat(x["d"]) <= date(y, *WINDOW_END)]
        in_season = [x for x in wx if first <= date.fromisoformat(x["d"]) <= last]

        seasons.append({
            "year": y,
            "title": story.get("title", f"La saison {year}"),
            "blurb": story.get("blurb", ""),
            "start": first.isoformat(),
            "end": last.isoformat(),
            "lengthDays": (last - first).days + 1,
            "boilDays": sum(1 for x in days if x["gal"]),
            "logDays": len(days),
            "totalGal": total_gal,
            "totalGalSource": "story" if "total_gal" in story else ("logbook" if stated_gal is not None else "sum"),
            "summedGal": summed_gal,
            "butterPots": total_pots,
            "sapDaysWindow": sum(1 for x in fixed if x["sap"]),
            "sapDaysInSeason": sum(1 for x in in_season if x["sap"]),
            "snowAtStartCm": weather.get(first, {}).get("s"),
            "days": days,
            "weather": wx,
        })

    out = {
        "generated": datetime.now().isoformat(timespec="minutes"),
        "farm": stories.get("_farm", {}),
        "sapDayRule": {"nightBelowC": NIGHT_BELOW_C, "dayAboveC": DAY_ABOVE_C},
        "window": {"start": list(WINDOW_START), "end": list(WINDOW_END)},
        "seasons": seasons,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))

    print(f"Wrote {os.path.relpath(OUT, ROOT)} ({os.path.getsize(OUT) // 1024} KB)")
    print(f"  log:     {os.path.relpath(log_path, ROOT)}")
    print(f"  weather: {os.path.relpath(weather_path, ROOT)}")
    for s in seasons:
        print(f"  {s['year']}: {s['start']} -> {s['end']}  {s['totalGal']} gal ({s['totalGalSource']}; "
              f"daily entries sum {s['summedGal']})  {s['butterPots']} pots  "
              f"{s['boilDays']} boil days  {s['sapDaysWindow']} sap days")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fetch-weather", action="store_true", help="download fresh hourly weather from Open-Meteo")
    ap.add_argument("--log", help="production log CSV (default: newest data/data_*.csv)")
    ap.add_argument("--weather", help="weather CSV (default: newest data/open-meteo-*.csv)")
    a = ap.parse_args()
    if a.fetch_weather:
        fetch_weather()
    build(a.log or latest("data_*.csv"), a.weather or latest("open-meteo-*.csv"))


if __name__ == "__main__":
    main()
