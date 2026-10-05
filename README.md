# 🎬 Netflix Viewing Analysis

**What two and a half years of my Netflix history says about how I actually watch, analysed with SQL and Python.**

👉 **Live site: https://c20744531.github.io/NetflixViewingAnalysis/**

![Overview](docs/screenshots/overview.png)

## Key findings

- **152 titles and episodes** across **73 shows and films**, from March 2024 to September 2026 (about **145 hours**, estimated).
- **Feast or famine:** July 2026 alone accounted for 45 titles, 30% of everything. I watched nothing at all in nine of the 31 months.
- **Weekend viewer:** 63% of my viewing happens Friday to Sunday, and Saturday is my biggest day.
- **Binge watcher:** 16 binge sessions (three or more episodes of one show in a day). The biggest was eight episodes of *The Night Agent* on 3 July 2026.
- **Crime & Thriller** is my top genre, at about a third of all titles.
- **Hollywood first, Nollywood second:** after the US, Nigeria is where most of what I watch is made.

![Titles watched per month](docs/screenshots/monthly.png)

![Where my shows come from](docs/screenshots/map.png)

## How I did it

**1. Cleaning in SQL** ([`sql/01_clean.sql`](sql/01_clean.sql))

I loaded the raw Netflix export into SQLite. Netflix gives dates as text like `9/19/26`, so I split them on the slashes and rebuilt them as proper ISO dates, and pulled the show name out of titles like `The Night Agent: Season 3: Orion`:

```sql
SELECT PRINTF('%04d-%02d-%02d', y, m, d) AS watched_on,
       title,
       TRIM(CASE WHEN INSTR(title, ':') > 0
                 THEN SUBSTR(title, 1, INSTR(title, ':') - 1)
                 ELSE title END) AS show
FROM dated;
```

**2. Tagging**

I hand-tagged all 73 titles with a genre, film or series, and country of production in [`data/title_tags.csv`](data/title_tags.csv), then joined it to the history in SQL.

**3. Analysis in SQL** ([`sql/02_analysis.sql`](sql/02_analysis.sql))

A recursive CTE fills in the months where I watched nothing, so gaps show up in the chart, and `GROUP BY` with `HAVING` finds binge sessions:

```sql
-- a binge is 3+ episodes of the same series on the same day
SELECT v.show, v.watched_on, COUNT(*) AS episodes
FROM views v
JOIN title_tags t USING (show)
WHERE t.type = 'Series'
GROUP BY v.show, v.watched_on
HAVING COUNT(*) >= 3
ORDER BY episodes DESC;
```

**4. Pipeline and visuals**

[`analysis.py`](analysis.py) loads the CSVs, runs both SQL files and exports the results to `docs/data.json`. The site draws its charts as SVG in plain JavaScript, and the world map is pre-rendered with d3-geo ([`tools/build_map.mjs`](tools/build_map.mjs)).

**A note on watch time:** Netflix's export has no durations, so hours are estimated at 45 minutes per episode and 110 minutes per film.

## Run it yourself

```bash
python3 analysis.py                 # runs the SQL and writes docs/data.json
npm install d3-geo topojson-client world-atlas
node tools/build_map.mjs            # writes docs/map.svg
cd docs && python3 -m http.server   # open http://localhost:8000
```

Swap in your own `NetflixViewingHistory.csv` and add your titles to `data/title_tags.csv` to analyse your own history.

## Tools

SQL (SQLite) · Python · JavaScript · SVG · d3-geo · Natural Earth map data · GitHub Pages
