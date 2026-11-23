"""The "Toutes les saisons" page: every season side by side.

The three charts need the page width, so they're empty slots
(ui.output_ui) that app.py fills in:
    "yield_chart", "timing_chart", "sap_chart"  -> charts.py
"""
import math
import re

from shiny import ui

from components import callout, card, card_title, stat
from data import (PANCAKE_STACKS_PER_GAL, SAP_RULE, SAP_TO_SYRUP_RATIO, SEASONS, UPDATED_ON,
                  all_days, average_gal, biggest_day, on_shared_calendar)
from french import NBSP, long_date, number, percent, short_date, snippet, temperature
from icons import icon

POUDING_PER_GAL = 16            # 1 cup of syrup per pouding chômeur (16 cups in a gallon)
TARTE_PER_GAL = 10.666666       # 1.5 cup of syrup per tarte au sirop d'érable (16 cups in a gallon)
GRUAU_PER_GAL = 16 * 12.5       # 1tbs (fort) of syrup per bol de gruau (16 cups in a gallon)
QUEBECOIS_PER_GAL = 4           # 4 cup of syrup per Quebecer per year (16 cups in a gallon)


def page():
    first, last = SEASONS[0]["year"], SEASONS[-1]["year"]
    count = len(SEASONS)
    total_gal = sum(s["totalGal"] for s in SEASONS)
    average = average_gal()

    best = max(SEASONS, key=lambda s: s["totalGal"])
    earliest = min(SEASONS, key=lambda s: on_shared_calendar(s["start"]))
    latest = max(SEASONS, key=lambda s: on_shared_calendar(s["end"]))

    return ui.div(
        card(
            ui.span(icon("leaf"), f" {first} – {last} · {count} saisons", class_="kicker"),
            ui.h1(f"{count} printemps sucrés"),
            ui.p("Chaque feu, chaque pot de beurre et chaque nuit de gel depuis le début du cahier.", class_="lede"),
            ui.div(
                stat("sun", "Eau d'érable", number(total_gal * SAP_TO_SYRUP_RATIO), unit="gal",
                     note=f"bouillis, au ratio habituel de {number(SAP_TO_SYRUP_RATIO)} pour 1"),
                stat("drop", "Sirop", number(total_gal), unit="gal",
                     note=f"environ {number(average)}{NBSP}gal par saison"),
                stat("jar", "Beurre d'érable", number(sum(s["butterPots"] for s in SEASONS)), unit="pots",
                     note=f"de 500{NBSP}g chacun"),
                stat("flame", "Journées de bouillage", sum(s["boilDays"] for s in SEASONS),
                     note="feux allumés et notés au cahier"),
                class_="stats",
            ),
            # callout("drop", f"C'est environ <b>{number(total_gal * SAP_TO_SYRUP_RATIO)} gallons d'eau d'érable</b> "
            #                 f"bouillis, au ratio habituel de {SAP_TO_SYRUP_RATIO} pour 1."),
            # class_="hero",
        ),

        card(
            card_title("Le sirop, saison par saison",
                       "Gallons de sirop produits chaque printemps. Touchez une saison pour lire son histoire."),
            ui.output_ui("yield_chart", class_="chart"),
            callout("trophy", f"<b>{best['year']}</b> détient le record avec <b>{number(best['totalGal'], 1)}{NBSP}gal</b>, "
                    f"soit {percent((best['totalGal'] - average) / average * 100)} au-dessus de la moyenne "
                    f"des {count}{NBSP}saisons."),
        ),

        card(
            card_title("Quand l'eau a coulé",
                       "Toutes les journées de bouillage sur un même calendrier. "
                       "Plus le point est gros, plus la journée a été bonne."),
            ui.output_ui("timing_chart", class_="chart"),
            callout("cal", f"Premier feu le plus hâtif{NBSP}: <b>{short_date(earliest['start'])} {earliest['year']}</b>. "
                    f"Dernière journée la plus tardive{NBSP}: <b>{short_date(latest['end'])} {latest['year']}</b>."),
        ),

        card(
            card_title("Le temps des sucres",
                       f"Jours avec une nuit sous {number(SAP_RULE['nightBelowC'])}{NBSP}°C et un après-midi "
                       f"au-dessus de {number(SAP_RULE['dayAboveC'])}{NBSP}°C, du 15 février au 20 avril."),
            ui.output_ui("sap_chart", class_="chart"),
            callout("snow", sap_weather_sentence()),
        ),

        card(
            card_title("Les records du cahier",
                       "Les records de tous les temps du cahier. Touchez-en un pour voir la journée."),
            ui.div(*wall_of_fame(), class_="fame"),
        ),

        card(
            card_title("Équivalences gourmandes",
                       "Comparatifs pour les dents sucrées."),
            ui.div(*gourmande(), class_="fame"),
        ),

        card(
            ui.h2("Le registre des saisons"),
            ledger(),
        ),

        footnote(),
        class_="view",
    )


def sap_weather_sentence():
    """Which season had the most / fewest sap days, and did it matter?"""
    most = max(SEASONS, key=lambda s: s["sapDaysWindow"])
    fewest = min(SEASONS, key=lambda s: s["sapDaysWindow"])
    sentence = (f"<b>{most['year']}</b> a eu le plus de jours de coulée ({most['sapDaysWindow']}) "
                f"et <b>{fewest['year']}</b> le moins ({fewest['sapDaysWindow']}).")
    if fewest["totalGal"] >= average_gal():
        sentence += (f" Pourtant, {fewest['year']} a quand même produit {number(fewest['totalGal'], 1)} gallons, "
                     f"au-dessus de la moyenne. La météo ne fait pas tout{NBSP}: les lignes d'eau, le bois "
                     f"et les longues journées au feu comptent aussi.")
    else:
        sentence += f" {fewest['year']} a aussi donné une récolte sous la moyenne."
    return sentence


# ------------------------------------------------------------ wall of fame

def fame_card(label, value, detail, icon_name, onclick=None, green=False):
    """One record. If onclick is given, tapping it opens the season (and day) it happened.

    Leave onclick out for a card that isn't clickable: Shiny drops attributes
    set to None, so the card gets no onclick, no hand cursor and no hover border.
    """
    return ui.tags.a(
        ui.span(icon(icon_name), class_="ic cedar" if green else "ic"),
        ui.span(
            ui.span(label, class_="k"),
            ui.span(value, class_="v"),
            ui.span(detail, class_="s"),
        ),
        onclick=onclick,
    )


def open_day(day):
    """onclick code that opens a logbook day on its season page."""
    return f"go('season', {day['year']}, '{day['date']}')"


def with_note(lead, note):
    """ "7 mars 2026" + a logbook note -> "7 mars 2026. Season start / test…" """
    return f"{lead}. {snippet(note)}" if note else f"{lead}."


def fire_minutes(day):
    """How long the fire burned, from "08:15" and "17:45". 0 if unknown."""
    start, end = day["fireStart"] or "", day["fireEnd"] or ""
    if not (re.fullmatch(r"\d{1,2}:\d{2}", start) and re.fullmatch(r"\d{1,2}:\d{2}", end)):
        return 0

    def minutes(clock):
        hours, mins = clock.split(":")
        return int(hours) * 60 + int(mins)

    return max(0, minutes(end) - minutes(start))


def wall_of_fame():
    days = all_days()
    cards = []

    big = biggest_day(days)
    cards.append(fame_card(
        "La plus grosse journée", f"{number(big['gal'], 2)} gallons",
        with_note(long_date(big["date"]), big["notes"]), "flame", open_day(big)))

    best = max(SEASONS, key=lambda s: s["totalGal"])
    cards.append(fame_card(
        "Meilleure saison", f"{best['year']}{NBSP}: {number(best['totalGal'], 1)}{NBSP}gal",
        f"« {best['title']} ». {best['boilDays']} journées de bouillage, {number(best['butterPots'])} pots de beurre.",
        "trophy", f"go('season', {best['year']})", green=True))

    # butter = max(days, key=lambda day: day["pots"] or 0)
    # cards.append(fame_card(
    #     "Festival du beurre", f"{number(butter['pots'])} pots en une journée",
    #     with_note(long_date(butter["date"]), butter["notes"]), "jar", open_day(butter)))

    longest = max(days, key=fire_minutes)
    minutes = fire_minutes(longest)
    if minutes:
        syrup = f" {number(longest['gal'], 2)}{NBSP}gal." if longest["gal"] else ""
        cards.append(fame_card(
            "La plus longue journée au feu", f"{minutes // 60}{NBSP}h{NBSP}{minutes % 60:02d}",
            f"{long_date(longest['date'])}, de {longest['fireStart']} à {longest['fireEnd']}.{syrup}",
            "clock", open_day(longest)))

    early = min(SEASONS, key=lambda s: on_shared_calendar(s["start"]))
    first_note = early["days"][0]["notes"]
    cards.append(fame_card(
        "Premier feu le plus hâtif", f"{short_date(early['start'])} {early['year']}",
        snippet(first_note) if first_note else "Le départ le plus hâtif du cahier.",
        "cal", f"go('season', {early['year']}, '{early['start']}')", green=True))

    late = max(SEASONS, key=lambda s: on_shared_calendar(s["end"]))
    last_note = late["days"][-1]["notes"]
    cards.append(fame_card(
        "Dernière journée la plus tardive", f"{short_date(late['end'])} {late['year']}",
        snippet(last_note) if last_note else "La fin la plus tardive du cahier.",
        "leaf", f"go('season', {late['year']}, '{late['end']}')", green=True))

    boiling_days = [day for day in days if day["gal"] and day["lo"] is not None]
    cold = min(boiling_days, key=lambda day: day["lo"])
    cards.append(fame_card(
        "La journée la plus glaciale", f"{temperature(cold['lo'])} la nuit",
        f"{long_date(cold['date'])}. Quand même {number(cold['gal'], 2)}{NBSP}gal produits.",
        "snow", open_day(cold)))

    # A day someone called the "worst day" in the logbook notes
    worst = next((day for day in days if "worst day" in (day["notes"] or "").lower()), None)
    if worst:
        cards.append(fame_card(
            "La journée la plus difficile", long_date(worst["date"]), worst["notes"],
            "storm", open_day(worst)))

    return cards


def poudings(gallons):
    """How many whole poudings chômeur that much syrup can make."""
    return math.floor(gallons * POUDING_PER_GAL)


def tarte(gallons):
    """How many whole tarte au sirop d'érable that much syrup can make."""
    return math.floor(gallons * TARTE_PER_GAL)


def gruau(gallons):
    """How many whole bols de gruau that much syrup can make."""
    return math.floor(gallons * GRUAU_PER_GAL)


def quebecois(gallons):
    """How many quebequers can it feed for a year."""
    return math.floor(gallons * QUEBECOIS_PER_GAL)


def gourmande():
    """Sweet comparisons: what all that syrup could turn into."""
    cards = []

    # All seasons together (not clickable: there's no single season to open)
    total_gal = sum(s["totalGal"] for s in SEASONS)
    cards.append(fame_card(
        "Pouding chômeur à l'érable", f"{number(poudings(total_gal))} poudings",
        f"Avec tout le sirop depuis {SEASONS[0]['year']}, à 1 tasse de sirop par pouding.",
        "flame"))

    cards.append(fame_card(
        "Tarte au sirop d'érable", f"{number(tarte(total_gal))} tartes",
        f"Avec tout le sirop depuis {SEASONS[0]['year']}, à 1.5 tasse de sirop par tarte.",
        "flame"))

    cards.append(fame_card(
        "Bols de gruau (à la Alain)", f"{number(gruau(total_gal))} bols",
        f"Avec tout le sirop depuis {SEASONS[0]['year']}, à 0.25 tasse de sirop par bol.",
        "flame"))

    cards.append(fame_card(
        "Québécois nourris pendant une année", f"{number(quebecois(total_gal))} personnes",
        f"Avec tout le sirop depuis {SEASONS[0]['year']}, à 4 tasses de sirop par personne par an.",
        "flame"))

    return cards

    cards.append(fame_card(
        "Tarte à l'érable", f"{number(big['gal'], 2)} gallons",
        with_note(long_date(big["date"]), big["notes"]), "flame", ))


# ------------------------------------------------------------ ledger table

def ledger():
    """A table with one row per season, newest first."""
    header = ui.tags.tr(*[ui.tags.th(name) for name in
                          ["Saison", "Dates", "Sirop", "Beurre", "Bouillage", "Coulée"]])
    rows = [
        ui.tags.tr(
            ui.tags.td(ui.tags.a(str(s["year"]), onclick=f"go('season', {s['year']})")),
            ui.tags.td(f"{short_date(s['start'])} – {short_date(s['end'])}"),
            ui.tags.td(f"{number(s['totalGal'], 1)}{NBSP}gal"),
            ui.tags.td(number(s["butterPots"])),
            ui.tags.td(s["boilDays"]),
            ui.tags.td(s["sapDaysWindow"]),
        )
        for s in reversed(SEASONS)
    ]
    return ui.div(
        ui.tags.table(ui.tags.thead(header), ui.tags.tbody(*rows), class_="ledger"),
        class_="scroll-x",
        style="margin-top:10px",
    )


def footnote():
    summed = [str(s["year"]) for s in SEASONS if s["totalGalSource"] == "sum"]
    summed_note = f" ({', '.join(summed)}{NBSP}: somme des entrées quotidiennes)" if summed else ""
    return ui.p(
        f"Les totaux de saison viennent du cahier quand un total y a été inscrit{summed_note}. "
        f"Les piles de crêpes et l'eau d'érable sont des estimations approximatives. "
        f"Mis à jour le {long_date(UPDATED_ON)}.",
        class_="footnote",
    )
