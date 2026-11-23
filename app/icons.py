"""The little line icons used across the app.

ICON_SPRITE is placed once at the top of the page (hidden). Each <symbol> in it
is one icon. icon("leaf") then shows the symbol with id "i-leaf" wherever
you put it. To add an icon, add a <symbol id="i-yourname"> below.
"""
from shiny import ui

ICON_SPRITE = ui.HTML("""
<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>
  <symbol id="i-leaf" viewBox="0 0 24 24"><path fill="currentColor" d="M12 2l1.6 3.6 2.6-1.2-.7 4.4 3-1.6-.4 2.3 3.4.9-2.2 2.2 1 1.6-4.7.8.6 2.2-4-1.5V22h-.4v-6.3l-4 1.5.6-2.2-4.7-.8 1-1.6-2.2-2.2 3.4-.9-.4-2.3 3 1.6-.7-4.4 2.6 1.2z"/></symbol>
  <symbol id="i-book" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M3 5.5c3-1.3 6-1.3 9 .5v13c-3-1.8-6-1.8-9-.5z"/><path d="M21 5.5c-3-1.3-6-1.3-9 .5v13c3-1.8 6-1.8 9-.5z"/></g></symbol>
  <symbol id="i-chart" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M4 20h16"/><path d="M7 16v-5M12 16V6M17 16v-8"/></g></symbol>
  <symbol id="i-drop" viewBox="0 0 24 24"><path fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" d="M12 3s6 6.4 6 11a6 6 0 01-12 0c0-4.6 6-11 6-11z"/></symbol>
  <symbol id="i-jar" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><rect x="6" y="3" width="12" height="4" rx="1"/><path d="M7 7h10l1 3v9a2 2 0 01-2 2H8a2 2 0 01-2-2v-9z"/><path d="M6 13h12"/></g></symbol>
  <symbol id="i-flame" viewBox="0 0 24 24"><path fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" d="M12 21a6 6 0 006-6c0-4-3-6-3-9-2 1.5-3 3.5-3 5-1-1-1.5-2-1.5-3C7.5 10 6 12.5 6 15a6 6 0 006 6z"/></symbol>
  <symbol id="i-snow" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M12 2v20M3.3 7l17.4 10M3.3 17L20.7 7"/><path d="M9.5 3.5L12 6l2.5-2.5M9.5 20.5L12 18l2.5 2.5"/></g></symbol>
  <symbol id="i-sun" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></g></symbol>
  <symbol id="i-cal" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><rect x="3.5" y="5" width="17" height="15" rx="2"/><path d="M3.5 10h17M8 3v4M16 3v4" stroke-linecap="round"/></g></symbol>
  <symbol id="i-trophy" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M7 4h10v5a5 5 0 01-10 0z"/><path d="M7 6H4v1a3 3 0 003 3M17 6h3v1a3 3 0 01-3 3M12 14v3M8 21h8M9 17h6v4H9z"/></g></symbol>
  <symbol id="i-clock" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/></g></symbol>
  <symbol id="i-storm" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round"><path d="M7 16a4.5 4.5 0 01-.6-9A6 6 0 0118 9a3.5 3.5 0 01-.5 7"/><path d="M12.5 13l-2 4h3l-2 4"/></g></symbol>
  <symbol id="i-note" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round"><path d="M5 3h10l4 4v14H5z"/><path d="M9 11h6M9 15h6M9 7h3"/></g></symbol>
  <symbol id="i-left" viewBox="0 0 24 24"><path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M15 5l-7 7 7 7"/></symbol>
  <symbol id="i-right" viewBox="0 0 24 24"><path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/></symbol>
</defs></svg>
""")


def icon(name):
    """One icon from the sprite above, e.g. icon("leaf")."""
    return ui.HTML(f'<svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-{name}"/></svg>')
