"""Chroniques de la cabane à sucre: the Shinylive app.

Run it on your computer:   shiny run app/app.py --reload
Build the website:         shinylive export app docs

Where things live:
    app.py          this file: the page frame, and which page/season/day to show
    season_page.py  the "La saison" page
    years_page.py   the "Toutes les saisons" page
    charts.py       the four charts (drawn as SVG)
    components.py   small shared pieces: cards, big numbers, callouts
    french.py       how numbers and dates are written
    data.py         loads data.json and looks things up in it
    icons.py        the little icons
    clicks.js       passes taps on links/charts to the server
    styles.css      all colours (dark theme), fonts and spacing

How a tap works: a link's onclick calls go(...) or pickDay(...) in clicks.js.
That sets input.nav or input.pick_day here. The server updates `view`, `year`
or `day` below, and every part of the page that uses them redraws itself.
"""
from pathlib import Path

from shiny import App, reactive, render, ui

import charts
import season_page
import years_page
from data import FARM, LATEST_YEAR, season
from icons import ICON_SPRITE, icon

HERE = Path(__file__).parent
FONTS = ("https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;1,600"
         "&family=Source+Sans+3:wght@400;600;700&display=swap")


# ============================================================ layout
# The page frame: things that never change. The middle ("page") and the
# bottom tab bar are filled in by the server below.
#
# No ui.page_*() wrapper here on purpose: those add Bootstrap, whose own
# .card and button styles would fight with styles.css.

app_ui = ui.TagList(
    ui.head_content(
        ui.tags.title(FARM["name"]),
        ui.tags.meta(name="viewport", content="width=device-width, initial-scale=1, viewport-fit=cover"),
        ui.tags.meta(name="theme-color", content="#1a1512"),  # phone status bar colour = --bg
        ui.tags.link(rel="stylesheet", href=FONTS),
        ui.include_css(HERE / "styles.css"),
        ui.include_js(HERE / "clicks.js"),
    ),
    ui.busy_indicators.use(spinners=False, pulse=False),  # no loading spinners on every tap
    ICON_SPRITE,

    ui.tags.header(
        ui.div(
            ui.tags.a(
                ui.span(icon("leaf"), class_="brand-mark", aria_hidden="true"),
                ui.span(
                    ui.span("Chroniques sucrées", class_="brand-name"),
                    ui.span("Cinq saisons à la cabane Pinsept", class_="brand-sub"),
                ),
                class_="brand",
                onclick="go('season')",
            ),
            class_="topbar-inner",
        ),
        class_="topbar",
    ),

    # "shiny-report-size" makes the browser tell the server how wide this is,
    # so the charts can be drawn to fit the screen.
    ui.tags.main(ui.output_ui("page", class_="shiny-report-size"), class_="wrap"),

    ui.output_ui("tab_bar"),
)


# ============================================================ logic

def server(input, output, session):
    # What's on screen right now. Changing one of these redraws what depends on it.
    view = reactive.value("years")   # "season" or "years"
    year = reactive.value(2025)
    day = reactive.value(None)        # "2026-03-12", or None for the season's biggest day

    # --- taps (see clicks.js)

    @reactive.effect
    @reactive.event(input.nav)
    def follow_link():
        target = input.nav()          # e.g. {"view": "season", "year": 2024, "day": "2024-03-12"}
        view.set(target["view"])
        if target.get("year"):
            year.set(int(target["year"]))
        day.set(target.get("day"))

    @reactive.effect
    @reactive.event(input.pick_day)
    def follow_day():
        day.set(input.pick_day())

    # --- helpers

    def current_season():
        return season(year())

    def current_day():
        return season_page.default_day(current_season(), day())

    def width():
        return charts.chart_width(session.clientdata.output_width("page"))

    # --- the frame

    @render.ui
    def page():
        if view() == "years":
            return years_page.page()
        return season_page.page(current_season())

    @render.ui
    def tab_bar():
        def tab(name, icon_name, label):
            return ui.tags.a(
                icon(icon_name),
                ui.span(label),
                onclick=f"go('{name}')",
                aria_current="page" if view() == name else None,
            )

        return ui.tags.nav(
            tab("season", "book", "La saison"),
            tab("years", "chart", "Toutes les saisons"),
            class_="tabbar",
            aria_label="Sections",
        )

    # --- the season page's moving parts

    @render.ui
    def season_chart():
        return charts.season_chart(current_season(), current_day(), width())

    @render.ui
    def day_detail():
        return season_page.day_detail(current_season(), current_day())

    # --- the all-seasons charts

    @render.ui
    def yield_chart():
        return charts.yield_chart(width())

    @render.ui
    def timing_chart():
        return charts.timing_chart(width())

    @render.ui
    def sap_chart():
        return charts.sap_chart(width())


app = App(app_ui, server)
