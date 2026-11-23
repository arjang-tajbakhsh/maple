# Sugar Shack Chronicles 🍁

A small storytelling dashboard for the family maple season. It is built for a phone or iPad. The app is written in Python with [Shiny](https://shiny.posit.co/py/) and published as a static site with [Shinylive](https://shiny.posit.co/py/get-started/shinylive.html), so Python runs right in the browser and no server is needed.

- **Season Story**: one page per season with the headline numbers, a day-by-day chart of weather vs. syrup boiled (tap a day, or use the arrows, to read its logbook note).
- **All Seasons**: totals since the logbook began, syrup by season, when the sap ran, freeze-thaw "sap weather" per season, a Wall of Fame of all-time records, and a season ledger.

The app is in Quebec French. Logbook entries (notes, syrup and butter text, bottling details, fire times) are shown exactly as written in the CSV. The season titles and stories in `data/seasons.json` are shown as-is, so write them in French.

```
data/                     raw inputs (you edit these)
  data_YYYYMMDD.csv       production log, one row per day
  open-meteo-*.csv        hourly weather for the sugar bush
  seasons.json            hand-written season titles + stories
scripts/build_data.py     turns the inputs into app/data.json
app/                      the app's source (you edit these)
  app.py                  page frame + which page/season/day is showing
  season_page.py          the "La saison" page
  years_page.py           the "Toutes les saisons" page
  charts.py               the four charts, drawn as SVG
  components.py           shared pieces: cards, big numbers, callouts
  french.py               how numbers and dates are written
  data.py                 loads data.json and looks things up in it
  icons.py, clicks.js     icons; passing taps to Python
  styles.css              colours, fonts, spacing, dark mode
docs/                     the built website (generated: don't edit by hand)
archive/                  the earlier plain-JavaScript site and a first Shinylive prototype
```

To work on the app with live reload, install the tools once with `pip install -r requirements-dev.txt`, then run:
```
shiny run app/app.py --reload
```
and open the address it prints.

## Updating each spring

1. **Add the new season's rows** to the production log CSV, using the same columns as before (`date, season, fire_start, fire_end, …, syrup_produced, butter_pots, …, notes`).
   - Write syrup like `19.5 gal` or `~9-10 gal`. The first gallon figure in the cell is used for the daily chart.
   - Write butter like `23x500g` or `20 pots`.
   - On the last day, put `SEASON TOTAL 210gal / 180 pots` in the notes. That becomes the headline total.
   - You can keep using the same file, or save a new `data_YYYYMMDD.csv`. The script uses the newest one.
2. **Add a title and story** for the new year in `data/seasons.json`.
3. **Rebuild**, downloading fresh weather at the same time:
   ```
   python scripts/build_data.py --fetch-weather
   ```
   (Without `--fetch-weather` it reuses the weather file already in `data/`.)
   Then rebuild the website from the app:
   ```
   shinylive export app docs
   ```
4. **Preview locally**:
   ```
   python -m http.server 8000 --directory docs
   ```
   then open http://localhost:8000. Opening `index.html` directly from disk won't load the data.
5. Commit and push. The live site updates within a minute or two.

## Hosting

Pick one:

- **GitHub Pages** (free): push this repo to GitHub, then go to *Settings → Pages → Build and deployment*, choose *Deploy from a branch*, then `main` and `/docs`. The site appears at `https://<you>.github.io/<repo>/`.
- **Netlify / Cloudflare Pages**: point it at the repo with publish directory `docs` and no build command. On Netlify you can also drag and drop the `docs` folder.

On the iPad or phone, open the site in Safari, then use *Share → Add to Home Screen* to get an app-style icon.

> On a free GitHub plan, a Pages site needs a public repo, and then everything in the repo is public. That includes the scanned notes PDFs in `data/`. Leave the PDFs out of the commit (add `data/*.pdf` to `.gitignore`) or use Netlify drag-and-drop if you'd rather keep the repo private.

## How the numbers are worked out

- **Season total**: the "season total" written in the logbook notes, or the sum of the daily entries if none was written. You can override it with `"total_gal"` / `"butter_pots"` in `seasons.json`.
- **Sap weather day**: night low below 0 °C and day high above 4 °C (night = hours outside 9 am–6 pm). The thresholds are at the top of `build_data.py`.
- **Pancake stacks** (¼ cup each) and **maple water** (40:1) are rough, fun estimates.
