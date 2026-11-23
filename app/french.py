"""Quebec French formatting for numbers, temperatures and dates.

Every number or date the app shows passes through one of these functions,
so this is the place to change how "1 234,5 gal" or "1er mars" is written.
"""
import re
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

# A space that never breaks across lines, so "12 gal" or "−3 °C" stay together.
NBSP = " "

MONTHS = ["janv.", "févr.", "mars", "avr.", "mai", "juin",
          "juil.", "août", "sept.", "oct.", "nov.", "déc."]
MONTHS_LONG = ["janvier", "février", "mars", "avril", "mai", "juin",
               "juillet", "août", "septembre", "octobre", "novembre", "décembre"]

# Python counts weekdays from Monday = 0.
WEEKDAYS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
WEEKDAYS_SHORT = ["lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim."]


# ------------------------------------------------------------ numbers

def number(value, decimals=0):
    """1234.5 -> "1 234,5". Trailing zeros are dropped: 12.50 -> "12,5"."""
    if value is None:
        return "–"
    # Round halves up (217.25 -> 217.3). Plain Python rounding would give 217.2,
    # because 217.25 is stored as 217.2499999... inside the computer.
    rounded = Decimal(str(value)).quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP)
    text = f"{rounded:,.{decimals}f}"        # "1,234.50"
    if decimals:
        text = text.rstrip("0").rstrip(".")  # "1,234.5"
    return text.replace(",", NBSP).replace(".", ",")


def percent(value):
    """-12.3 -> "12 %" (the sign is shown separately by whoever calls this)."""
    return f"{number(abs(value))}{NBSP}%"


def temperature(celsius):
    """-3.4 -> "−3 °C" (with a real minus sign, not a hyphen)."""
    if celsius is None:
        return "–"
    sign = "−" if celsius < 0 else ""
    return f"{sign}{abs(round(celsius))}{NBSP}°C"


def plural(amount, one, many):
    """French uses the singular below 2: "1,5 gallon", "2 gallons"."""
    return many if abs(amount) >= 2 else one


def snippet(text, max_length=110):
    """Shorten long logbook notes at a word boundary and add "…"."""
    if not text or len(text) <= max_length:
        return text or ""
    cut = text[:max_length]
    cut = re.sub(r"[\s;,]+\S*$", "", cut)  # drop the half-cut last word
    return cut + "…"


# ------------------------------------------------------------ dates
# Dates arrive from data.json as text like "2026-03-07".

def day_number(day):
    """The 1st of the month is written "1er" in French."""
    return "1er" if day == 1 else str(day)


def short_date(iso):
    """ "2026-03-07" -> "7 mars" """
    d = date.fromisoformat(iso)
    return f"{day_number(d.day)} {MONTHS[d.month - 1]}"


def long_date(iso):
    """ "2026-03-07" -> "7 mars 2026" """
    d = date.fromisoformat(iso)
    return f"{day_number(d.day)} {MONTHS_LONG[d.month - 1]} {d.year}"


def weekday(iso):
    """ "2026-03-07" -> "samedi" """
    return WEEKDAYS[date.fromisoformat(iso).weekday()]


def weekday_short(iso):
    """ "2026-03-07" -> "sam." """
    return WEEKDAYS_SHORT[date.fromisoformat(iso).weekday()]
