"""Small building blocks that both pages reuse.

Each function returns a piece of HTML built with Shiny's ui.* tags. A few things
to know when reading these:
  - class_="..." becomes class="..." in the HTML (class is a Python keyword).
  - Plain text you pass in is escaped automatically, so logbook notes with
    "<" or "&" in them are safe.
  - ui.HTML("...") is the exception: it inserts its text as real HTML. It's
    used where a sentence needs <b>bold</b> words.
"""
from shiny import ui

from icons import icon


def card(*children, class_=""):
    """A white rounded box. Every section of both pages is one."""
    return ui.tags.section(*children, class_=f"card {class_}".strip())


def card_title(title, subtitle=None):
    """A section heading, with an optional grey line under it."""
    return ui.div(
        ui.div(
            ui.h2(title),
            ui.p(subtitle, class_="sub") if subtitle else None,
        ),
        class_="card-head",
    )


def stat(icon_name, label, value, note, unit=None):
    """One of the four big numbers at the top of each page."""
    return ui.div(
        ui.span(icon(icon_name), " ", label, class_="stat-label"),
        ui.span(value, ui.tags.small(unit) if unit else None, class_="stat-value num"),
        ui.span(note, class_="stat-note"),
        class_="stat",
    )


def callout(icon_name, sentence):
    """A highlighted sentence under a chart. The sentence may use <b>bold</b>."""
    return ui.div(icon(icon_name), ui.span(ui.HTML(sentence)), class_="callout")


def legend_item(swatch_class, label):
    """One coloured square + label in a chart legend."""
    return ui.span(ui.tags.i(class_=f"sw {swatch_class}"), label)
