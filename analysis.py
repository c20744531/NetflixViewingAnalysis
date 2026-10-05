"""Netflix viewing history analysis.

1. Loads my Netflix export (data/NetflixViewingHistory.csv) and my
   hand-tagged lookup of genre, type and country (data/title_tags.csv)
   into a SQLite database.
2. Cleans the export with sql/01_clean.sql.
3. Runs the queries in sql/02_analysis.sql.
4. Writes the numbers the site uses to docs/data.json.

Watch time is an estimate: Netflix's export has no durations, so the SQL
assumes 45 minutes per episode and 110 minutes per film.
"""
import csv
import json
import re
import sqlite3

con = sqlite3.connect(":memory:")
con.row_factory = sqlite3.Row


def load_csv(table, path):
    """Load a CSV into SQLite as text columns, exactly as it is."""
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        cols = [c.strip().lower() for c in next(reader)]
        con.execute(f"CREATE TABLE {table} ({', '.join(c + ' TEXT' for c in cols)})")
        con.executemany(f"INSERT INTO {table} VALUES ({', '.join('?' * len(cols))})", reader)


def named_queries(path):
    """Split a .sql file into {name: sql} on its '-- name:' lines."""
    text = open(path, encoding="utf-8").read()
    parts = re.split(r"^-- name: (\w+)\s*$", text, flags=re.M)
    return {parts[i]: parts[i + 1].strip() for i in range(1, len(parts), 2)}


load_csv("raw_history", "data/NetflixViewingHistory.csv")
load_csv("title_tags", "data/title_tags.csv")
con.executescript(open("sql/01_clean.sql", encoding="utf-8").read())

Q = named_queries("sql/02_analysis.sql")
run = lambda name: [dict(r) for r in con.execute(Q[name])]

untagged = run("untagged")
if untagged:
    raise SystemExit(f"add these shows to data/title_tags.csv: {[r['show'] for r in untagged]}")

summary = run("summary")[0]
binges = run("binges")

out = {
    **summary,
    "est_hours": int(summary["est_hours"]),
    "top_day": run("top_day")[0],
    "months": run("months"),
    "weekdays": run("weekdays"),
    "top_series": run("top_series"),
    "genres": run("genres"),
    "countries": run("countries"),
    "unknown_country": run("unknown_country")[0]["n"],
    "binges": len(binges),
    "biggest_binge": binges[0]["show"] if binges else None,
    "biggest_binge_n": binges[0]["episodes"] if binges else 0,
    "biggest_binge_date": binges[0]["watched_on"] if binges else None,
}
json.dump(out, open("docs/data.json", "w"), indent=2, ensure_ascii=False)
print(json.dumps({k: v for k, v in out.items() if not isinstance(v, list)}, indent=2, ensure_ascii=False))
