"""The four charts, drawn as plain SVG (the same drawings as the original site).

Each function returns ui.HTML(...) holding one <svg> picture. A few things to know:
  - x grows to the right; y grows DOWNWARDS from the top of the picture.
  - Colours are CSS variables from styles.css (var(--amber), var(--cedar), ...),
    so the charts switch to dark mode along with the rest of the page.
  - A <title> inside a shape is the tooltip you see when hovering with a mouse.
  - onclick="go(...)" / onclick="pickDay(...)" call the functions in clicks.js.
"""
import math
from datetime import timedelta
from html import escape

from shiny import ui

from data import SEASONS, all_days, average_gal, on_shared_calendar
from french import NBSP, MONTHS, day_number, number, short_date, temperature, weekday_short

# The page tells us its width; a chart is narrower by the card's padding
# (20px on each side) and border (1px on each side).
CARD_INSET = 42
MIN_WIDTH = 300


def chart_width(page_width):
    """How wide (in pixels) to draw a chart, given the page's width."""
    if not page_width:
        return 360  # a phone-sized guess until the browser reports the real width
    return max(MIN_WIDTH, round(page_width - CARD_INSET))


def svg(width, height, label, shapes):
    """Wrap a list of SVG shapes into one <svg> picture."""
    return ui.HTML(
        f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
        f'role="img" aria-label="{escape(label)}">' + "".join(shapes) + "</svg>"
    )


def clamp(value, low, high):
    """Keep value between low and high."""
    return max(low, min(high, value))


def year_label(x, y, year):
    """The bold year written at the left of a row."""
    return f'<text x="{x}" y="{y:.1f}" style="font-size:13px;font-weight:600;fill:var(--ink-2)">{year}</text>'


# ============================================================ season page

# Every season uses the same scales, so flipping between years compares like with like.
_lows = [w["lo"] for s in SEASONS for w in s["weather"]]
_highs = [w["hi"] for s in SEASONS for w in s["weather"]]
_gallons = [day["gal"] or 0 for s in SEASONS for day in s["days"]]
TEMP_LOW = math.floor(min(_lows) / 10) * 10     # e.g. −30
TEMP_HIGH = math.ceil(max(_highs) / 10) * 10    # e.g. 20
GAL_MAX = math.ceil(max(_gallons) / 10) * 10    # e.g. 40


def season_chart(s, selected_day, width):
    """Day by day, 15 Feb to 20 Apr.

    Top panel:    a bar from each day's night low up to its day high.
                  Green = sap weather (froze at night, thawed by day).
    Bottom panel: gallons of syrup boiled that day (amber bars).
                  A small circle marks a logbook day with no syrup.
    Tap any column to pick that day.
    """
    days = s["weather"]                                # one entry per calendar day
    logbook = {day["date"]: day for day in s["days"]}  # date -> logbook line
    column_of = {w["d"]: i for i, w in enumerate(days)}

    # --- layout, in pixels
    left, right = 34, 6                        # room for the axis numbers
    temp_top, temp_height = 18, 150            # temperature panel
    syrup_top, syrup_height = temp_top + temp_height + 34, 92
    syrup_bottom = syrup_top + syrup_height
    height = syrup_bottom + 26                 # room for the date labels

    step = (width - left - right) / len(days)  # width of one day's column
    bar = clamp(step * 0.62, 2, 9)             # width of the bars in it
    corner = min(bar / 2, 3)

    def column_left(i):
        return left + i * step

    def column_center(i):
        return left + (i + 0.5) * step

    def temp_y(t):
        return temp_top + (TEMP_HIGH - t) / (TEMP_HIGH - TEMP_LOW) * temp_height

    def syrup_y(gal):
        return syrup_bottom - gal / GAL_MAX * syrup_height

    shapes = []  # drawn in order, so later shapes sit on top

    # Amber band behind the days the fire was going
    first = column_of.get(s["start"], 0)
    last = column_of.get(s["end"], len(days) - 1)
    shapes.append(
        f'<rect x="{column_left(first):.1f}" y="{temp_top - 6}" width="{(last - first + 1) * step:.1f}" '
        f'height="{syrup_bottom - temp_top + 6}" fill="var(--amber-tint)" rx="4"/>'
    )

    # Temperature grid lines every 10 degrees
    for t in range(TEMP_LOW, TEMP_HIGH + 1, 10):
        line_class = "zero" if t == 0 else "grid"
        label = f"−{-t}" if t < 0 else str(t)
        shapes.append(f'<line class="{line_class}" x1="{left}" x2="{width - right}" y1="{temp_y(t):.1f}" y2="{temp_y(t):.1f}"/>')
        shapes.append(f'<text x="{left - 6}" y="{temp_y(t) + 4:.1f}" text-anchor="end">{label}°</text>')
    shapes.append(f'<text class="panel-label" x="{left}" y="{temp_top - 8}">Min. de nuit → max. de jour (°C)</text>')

    # Syrup grid lines at 0, half and full scale
    for gal in (0, GAL_MAX / 2, GAL_MAX):
        line_class = "zero" if gal == 0 else "grid"
        shapes.append(f'<line class="{line_class}" x1="{left}" x2="{width - right}" y1="{syrup_y(gal):.1f}" y2="{syrup_y(gal):.1f}"/>')
        shapes.append(f'<text x="{left - 6}" y="{syrup_y(gal) + 4:.1f}" text-anchor="end">{number(gal)}</text>')
    shapes.append(f'<text class="panel-label" x="{left}" y="{syrup_top - 10}">Sirop produit (gal)</text>')

    # Dashed outline around the picked day
    if selected_day in column_of:
        i = column_of[selected_day]
        shapes.append(
            f'<rect class="sel" x="{column_left(i) + 0.5:.1f}" y="{temp_top - 6}" width="{max(step - 1, 3):.1f}" '
            f'height="{syrup_bottom - temp_top + 6}" rx="3"/>'
        )

    # The bars for each day
    best_gal = max(day["gal"] or 0 for day in s["days"])
    for i, w in enumerate(days):
        x = column_center(i) - bar / 2
        colour = "var(--cedar)" if w["sap"] else "var(--bar-neutral)"
        top, bottom = temp_y(w["hi"]), temp_y(w["lo"])
        shapes.append(
            f'<rect x="{x:.1f}" y="{top:.1f}" width="{bar:.1f}" height="{max(bottom - top, 2):.1f}" '
            f'rx="{corner:.1f}" fill="{colour}"/>'
        )

        entry = logbook.get(w["d"])
        if entry and entry["gal"]:
            top = syrup_y(entry["gal"])
            shapes.append(
                f'<rect x="{x:.1f}" y="{top:.1f}" width="{bar:.1f}" height="{syrup_bottom - top:.1f}" '
                f'rx="{corner:.1f}" fill="var(--amber)"/>'
            )
            if entry["gal"] == best_gal:  # label the season's biggest day
                label_x = clamp(column_center(i), left + 16, width - right - 16)
                shapes.append(f'<text class="lbl-strong" x="{label_x:.1f}" y="{top - 6:.1f}" text-anchor="middle">{number(entry["gal"], 1)}</text>')
        elif entry:
            shapes.append(
                f'<circle cx="{column_center(i):.1f}" cy="{syrup_bottom - 5}" r="3" '
                f'fill="none" stroke="var(--amber)" stroke-width="1.5"/>'
            )

    # Date labels on the 1st and 15th of each month
    for i, w in enumerate(days):
        month, day = int(w["d"][5:7]), int(w["d"][8:10])
        if day in (1, 15):
            x = column_center(i)
            shapes.append(f'<line class="grid" x1="{x:.1f}" x2="{x:.1f}" y1="{syrup_bottom}" y2="{syrup_bottom + 5}"/>')
            shapes.append(f'<text x="{x:.1f}" y="{syrup_bottom + 18}" text-anchor="middle">{day_number(day)} {MONTHS[month - 1]}</text>')

    # Invisible, clickable columns on top of everything, one per day
    for i, w in enumerate(days):
        shapes.append(
            f'<rect class="hit" x="{column_left(i):.1f}" y="0" width="{step:.2f}" height="{height}" '
            f'onclick="pickDay(\'{w["d"]}\')"><title>{escape(day_tooltip(w, logbook.get(w["d"])))}</title></rect>'
        )

    return svg(width, height, f"Écart de température quotidien et sirop produit, saison {s['year']}", shapes)


def day_tooltip(w, entry):
    """Hover text for one day: "sam. 4 avr. · −1 °C → 6 °C · 26,5 gal produits"."""
    text = f"{weekday_short(w['d'])} {short_date(w['d'])} · {temperature(w['lo'])} → {temperature(w['hi'])}"
    if w["sap"]:
        text += " · jour de coulée"
    if entry and entry["gal"]:
        text += f" · {number(entry['gal'], 2)}{NBSP}gal produits"
    elif entry:
        text += " · entrée au cahier"
    return text


# ============================================================ all-seasons page

def yield_chart(width):
    """One amber column per season: gallons of syrup. Dashed line = the average."""
    height = 220
    left, right, top, bottom = 8, 54, 28, 28
    average = average_gal()
    best = max(SEASONS, key=lambda s: s["totalGal"])
    scale_max = math.ceil(best["totalGal"] / 50) * 50  # round up to the next 50

    def y(gal):
        return top + (1 - gal / scale_max) * (height - top - bottom)

    slot = (width - left - right) / len(SEASONS)  # room for each season
    bar = min(64, slot * 0.6)

    shapes = [
        f'<line class="zero" x1="{left}" x2="{width - right}" y1="{y(0):.1f}" y2="{y(0):.1f}"/>',
        f'<line x1="{left}" x2="{width - right + 6}" y1="{y(average):.1f}" y2="{y(average):.1f}" '
        f'stroke="var(--ink-2)" stroke-width="1.25" stroke-dasharray="4 4"/>',
        f'<text x="{width}" y="{y(average) + 4:.1f}" text-anchor="end" '
        f'style="fill:var(--ink-2);font-weight:600">moy. {number(average)}</text>',
    ]

    for i, s in enumerate(SEASONS):
        x = left + i * slot + (slot - bar) / 2
        bar_top = y(s["totalGal"])
        star = "★ " if s is best else ""
        opacity = 1 if s is best else 0.72
        tooltip = (f"{s['year']} · {s['title']}\n{number(s['totalGal'], 2)}{NBSP}gal · "
                   f"{number(s['butterPots'])} pots de beurre\n{s['boilDays']} journées de bouillage")
        # A column with rounded top corners: up the left side, curve, across, curve, down.
        column = (f"M{x:.1f},{y(0):.1f} V{bar_top + 4:.1f} q0,-4 4,-4 h{bar - 8:.1f} "
                  f"q4,0 4,4 V{y(0):.1f} Z")
        shapes.append(
            f'<g onclick="go(\'season\', {s["year"]})"><title>{escape(tooltip)}</title>'
            f'<rect class="hit" x="{left + i * slot:.1f}" y="0" width="{slot:.1f}" height="{height}"/>'
            f'<path d="{column}" fill="var(--amber)" opacity="{opacity}"/>'
            f'<text class="lbl-strong" x="{x + bar / 2:.1f}" y="{bar_top - 8:.1f}" text-anchor="middle">{star}{number(s["totalGal"])}</text>'
            f'<text x="{x + bar / 2:.1f}" y="{height - 8}" text-anchor="middle" '
            f'style="font-size:13px;font-weight:600;fill:var(--ink-2)">{s["year"]}</text></g>'
        )

    return svg(width, height, "Gallons de sirop par saison", shapes)


def timing_chart(width):
    """One row per season (newest on top) on a shared calendar.

    A faint line runs from the first fire to the last; each dot is a boiling day,
    bigger when more syrup was made. Tap a dot to open that day.
    """
    rows = list(reversed(SEASONS))
    left, right, top, row_height = 44, 12, 8, 42
    height = top + row_height * len(rows) + 26

    # Calendar range: at least 15 Feb to 20 Apr, wider if a season went past it
    starts = [on_shared_calendar(s["start"]) for s in rows]
    ends = [on_shared_calendar(s["end"]) for s in rows]
    first_day = min([on_shared_calendar("2024-02-15")] + starts) - timedelta(days=2)
    last_day = max([on_shared_calendar("2024-04-20")] + ends) + timedelta(days=2)
    total_days = (last_day - first_day).days

    def x(iso):
        days_in = (on_shared_calendar(iso) - first_day).days
        return left + days_in / total_days * (width - left - right)

    biggest = max(day["gal"] or 0 for day in all_days())

    def dot_radius(gal):
        return 2 + math.sqrt(gal / biggest) * 5.5

    shapes = []

    # Grid line + label on the 1st and 15th of each month
    for n in range(total_days + 1):
        d = first_day + timedelta(days=n)
        if d.day in (1, 15):
            line_class = "zero" if d.day == 1 else "grid"
            px = x(d.isoformat())
            shapes.append(f'<line class="{line_class}" x1="{px:.1f}" x2="{px:.1f}" y1="{top}" y2="{top + row_height * len(rows)}"/>')
            shapes.append(f'<text x="{px:.1f}" y="{height - 8}" text-anchor="middle">{day_number(d.day)} {MONTHS[d.month - 1]}</text>')

    for row, s in enumerate(rows):
        cy = top + row * row_height + row_height / 2
        shapes.append(year_label(0, cy + 4, s["year"]))
        shapes.append(
            f'<line x1="{x(s["start"]):.1f}" x2="{x(s["end"]):.1f}" y1="{cy:.1f}" y2="{cy:.1f}" '
            f'stroke="var(--amber)" stroke-opacity=".35" stroke-width="3" stroke-linecap="round"/>'
        )
        for day in s["days"]:
            if not day["gal"]:
                continue
            cx = x(day["date"])
            tooltip = f"{short_date(day['date'])} {s['year']}\n{number(day['gal'], 2)}{NBSP}gal produits"
            shapes.append(
                f'<g onclick="go(\'season\', {s["year"]}, \'{day["date"]}\')" style="cursor:pointer">'
                f'<title>{escape(tooltip)}</title>'
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{dot_radius(day["gal"]):.1f}" '
                f'fill="var(--amber)" stroke="var(--card)" stroke-width="1.5"/>'
                f'<circle class="hit" cx="{cx:.1f}" cy="{cy:.1f}" r="9"/></g>'  # bigger, invisible tap target
            )

    return svg(width, height, "Journées de bouillage de chaque saison sur un même calendrier", shapes)


def sap_chart(width):
    """One green bar per season: how many sap-weather days it had."""
    rows = list(reversed(SEASONS))
    left, right, row_height = 44, 104, 34
    height = row_height * len(rows)
    most = max(s["sapDaysWindow"] for s in rows)

    shapes = []
    for i, s in enumerate(rows):
        cy = i * row_height + row_height / 2
        length = (s["sapDaysWindow"] / most) * (width - left - right)
        # A bar with rounded right-hand corners
        bar = (f"M{left},{cy - 9:.1f} h{length - 4:.1f} q4,0 4,4 v10 q0,4 -4,4 "
               f"h{-(length - 4):.1f} Z")
        shapes.append(
            f'<g onclick="go(\'season\', {s["year"]})">'
            f'<rect class="hit" x="0" y="{i * row_height}" width="{width}" height="{row_height}"/>'
            + year_label(0, cy + 4, s["year"]) +
            f'<path d="{bar}" fill="var(--cedar)"/>'
            f'<text class="lbl-strong" x="{left + length + 6:.1f}" y="{cy + 4:.1f}">{s["sapDaysWindow"]} jours</text>'
            f'<text x="{width}" y="{cy + 4:.1f}" text-anchor="end">{number(s["totalGal"])}{NBSP}gal</text></g>'
        )

    return svg(width, height, "Jours de coulée par saison", shapes)
