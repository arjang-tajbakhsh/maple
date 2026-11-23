"""The "La saison" page: one season's story and its day-by-day chart.

page() lays out the whole page. Two parts change when you pick a day, so
they're left as empty slots (ui.output_ui) that app.py fills in:
    "season_chart"  -> charts.season_chart()
    "day_detail"    -> day_detail() below
"""
from shiny import ui

from components import card, card_title, legend_item, stat
from data import SEASONS, average_gal, biggest_day, logbook_entry, weather_on
from french import NBSP, long_date, number, percent, plural, short_date, temperature, weekday
from icons import icon


def default_day(s, wanted_day):
    """The day to show: the one picked, or the season's biggest day."""
    if wanted_day and weather_on(s, wanted_day):
        return wanted_day
    return biggest_day(s["days"])["date"]


# ------------------------------------------------------------ whole page

def page(s):
    return ui.div(
        year_chips(s["year"]),
        hero(s),
        card(
            card_title(
                "La saison, jour par jour",
                "Chaque colonne est une journée. Touchez le graphique pour lire chaque journée.",
            ),
            ui.div(
                legend_item("sw-cedar", "Jour de coulée (gel, puis dégel)"),
                legend_item("sw-neutral", "Autres jours"),
                legend_item("sw-amber", "Sirop produit"),
                legend_item("sw-window", "Saison"),
                class_="legend",
            ),
            ui.output_ui("season_chart", class_="chart"),
            ui.div(ui.output_ui("day_detail"), id="detail", class_="detail"),
        ),
        footnote(s),
        class_="view",
    )


def year_chips(current_year):
    """The row of round year buttons at the top, newest first."""
    chips = [
        ui.tags.a(
            str(s["year"]),
            class_="chip",
            aria_current="true" if s["year"] == current_year else "false",
            onclick=f"go('season', {s['year']})",
        )
        for s in reversed(SEASONS)
    ]
    return ui.tags.nav(*chips, class_="chips", aria_label="Choisir une saison")


def hero(s):
    """Title, story and the four big numbers."""
    average = average_gal()
    vs_average = (s["totalGal"] - average) / average * 100
    best = biggest_day(s["days"])

    # The current season's butter count may still be growing
    still_going = s["year"] == SEASONS[-1]["year"] and "to date" in (s["days"][-1]["notes"] or "").lower()

    return card(
        ui.span(icon("leaf"), f" Saison {s['year']}", class_="kicker"),
        ui.h1(s["title"]),
        ui.p(s["blurb"], class_="lede") if s["blurb"] else None,
        ui.div(
            ui.span(icon("cal"), f" {short_date(s['start'])} → {short_date(s['end'])} {s['year']}"),
            ui.span(icon("clock"), f" {s['lengthDays']} jours entre le premier et le dernier feu"),
            class_="daterange",
        ),
        ui.div(
            stat("drop", "Sirop", number(s["totalGal"], 1), unit="gal", note=[
                ui.span(
                    ("+" if vs_average >= 0 else "−") + percent(vs_average),
                    class_="up" if vs_average >= 0 else "down",
                ),
                " par rapport à la moyenne",
            ]),
            stat("jar", "Beurre d'érable", number(s["butterPots"]), unit="pots",
                 note=f"pots de 500{NBSP}g" + (" (jusqu'ici)" if still_going else "")),
            stat("flame", "Journées de bouillage", s["boilDays"],
                 note=f"Record{NBSP}: {number(best['gal'], 2)}{NBSP}gal le {short_date(best['date'])}"),
            stat("snow", "Jours de coulée", s["sapDaysInSeason"], unit="jours",
                 note="gel la nuit, dégel le jour, pendant la saison"),
            class_="stats",
        ),
        class_="hero",
    )


def footnote(s):
    if s["totalGalSource"] == "logbook":
        where_total_comes_from = "Le total de la saison est celui inscrit dans le cahier."
    elif s["totalGalSource"] == "story":
        where_total_comes_from = "Le total de la saison a été entré à la main."
    else:
        where_total_comes_from = ("Aucun total de saison n'a été inscrit au cahier cette année; "
                                  "le total additionne donc les entrées quotidiennes.")
    return ui.p(
        where_total_comes_from,
        " Les barres quotidiennes montrent le premier nombre de gallons inscrit pour chaque journée "
        "(les cannes, les réserves et les reports ne sont pas comptés), alors elles ne donnent pas "
        "exactement le total. ",
        f"Météo{NBSP}: historique horaire d'Open-Meteo pour l'érablière. Minimum de nuit = l'heure la "
        f"plus froide en dehors de 9{NBSP}h à 18{NBSP}h; maximum de jour = l'heure la plus chaude "
        f"entre 9{NBSP}h et 18{NBSP}h.",
        class_="footnote",
    )


# ------------------------------------------------------------ the picked day

def day_title(s, iso, entry, w):
    """A short headline for the picked day."""
    best_gal = max(day["gal"] or 0 for day in s["days"])
    if entry:
        if iso == s["days"][0]["date"]:
            return "Premier feu de la saison"
        if iso == s["days"][-1]["date"]:
            return "Dernière journée de la saison"
        if entry["gal"] and entry["gal"] == best_gal:
            return "La plus grosse journée de la saison"
        if entry["gal"]:
            return f"{number(entry['gal'], 2)} {plural(entry['gal'], 'gallon', 'gallons')} de sirop"
        if entry["pots"]:
            return "Une journée de beurre d'érable"
        return "Une journée au cahier"
    sap_weather = w and w["sap"]
    if iso < s["start"]:
        return "Temps de coulée, mais pas encore de feu" if sap_weather else "Avant la saison"
    if iso > s["end"]:
        return "Après la dernière journée"
    return "Beau temps de coulée, rien d'inscrit au cahier" if sap_weather else "Une journée tranquille à la cabane"


def pill(*children, good=False):
    """A small rounded label, e.g. "Nuit −3 °C"."""
    return ui.span(*children, class_="pill good" if good else "pill")


def day_detail(s, iso):
    """The box under the chart: weather and logbook for the picked day."""
    entry = logbook_entry(s, iso)
    w = weather_on(s, iso)

    # Arrows jump to the previous / next logbook entry
    earlier = [day for day in s["days"] if day["date"] < iso]
    later = [day for day in s["days"] if day["date"] > iso]
    previous_day = earlier[-1]["date"] if earlier else None
    next_day = later[0]["date"] if later else None

    def arrow(target, icon_name, label):
        return ui.tags.button(
            icon(icon_name),
            type="button",
            class_="iconbtn",
            aria_label=label,
            disabled=None if target else True,
            onclick=f"pickDay('{target}')" if target else None,
        )

    pills = []
    if entry and entry["gal"]:
        pills.append(pill(icon("drop"), " ", ui.tags.b(f"{number(entry['gal'], 2)}{NBSP}gal")))
    if w:
        pills.append(pill(icon("snow"), " Nuit ", ui.tags.b(temperature(w["lo"]))))
        pills.append(pill(icon("sun"), " Jour ", ui.tags.b(temperature(w["hi"]))))
        if w["sap"]:
            pills.append(pill(icon("leaf"), " Jour de coulée", good=True))
        if w["s"] > 0:
            pills.append(pill("Neige au sol ", ui.tags.b(f"{w['s']}{NBSP}cm")))
        if w["p"] >= 1:
            pills.append(pill(icon("storm"), " Précipitations ", ui.tags.b(f"{number(w['p'], 1)}{NBSP}mm")))

    # Logbook values, shown exactly as written
    facts = []
    if entry:
        if entry["galText"]:
            facts.append(("Sirop", entry["galText"]))
        if entry["potsText"]:
            facts.append(("Beurre d'érable", entry["potsText"]))
        if entry["bottled"]:
            facts.append(("Bouteilles / cannes", entry["bottled"]))
        if entry["fireStart"] or entry["fireEnd"]:
            facts.append(("Feu", f"{entry['fireStart'] or '?'} → {entry['fireEnd'] or '?'}"))

    return ui.TagList(
        ui.div(
            ui.span(f"{weekday(iso)} · {long_date(iso)}", class_="detail-date"),
            ui.span(
                arrow(previous_day, "left", "Entrée précédente"),
                arrow(next_day, "right", "Entrée suivante"),
                class_="navbtns",
            ),
            class_="detail-top",
        ),
        ui.h3(day_title(s, iso, entry, w), style="margin-top:6px"),
        ui.div(*pills, class_="pills"),
        ui.div(ui.span(icon("note"), " Au cahier", class_="label"), entry["notes"], class_="journal")
        if entry and entry["notes"] else None,
        ui.tags.dl(*[[ui.tags.dt(k), ui.tags.dd(v)] for k, v in facts], class_="kv")
        if facts else None,
        ui.p("Rien au cahier pour cette journée. Utilisez les flèches pour aller à l'entrée la plus proche.",
             class_="sub", style="margin-top:12px")
        if not entry else None,
    )
