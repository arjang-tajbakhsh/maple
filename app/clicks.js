// Links and buttons in the app call one of these two functions
// (search the Python files for onclick= to see where).
// Each one hands the click over to the Python server, which then redraws the page.

// Go to a page:
//   go("years")                         the "Toutes les saisons" page
//   go("season")                        the season page, same year as before
//   go("season", 2024)                  the 2024 season
//   go("season", 2024, "2024-03-12")    the 2024 season, with 12 March picked
function go(view, year, day) {
  Shiny.setInputValue("nav", { view: view, year: year, day: day }, { priority: "event" });
  window.scrollTo(0, 0);
}

// Pick a day on the season page (from the chart or the arrow buttons).
function pickDay(day) {
  Shiny.setInputValue("pick_day", day, { priority: "event" });
}
