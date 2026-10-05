"""Netflix viewing history analysis.

Reads my Netflix export (data/NetflixViewingHistory.csv), joins it with a
hand-tagged lookup of genre, type and country (data/title_tags.csv) and
writes the numbers the site uses to docs/data.json.

Watch time is an estimate: Netflix's export has no durations, so I assume
45 minutes per episode and 110 minutes per film.
"""
import collections
import csv
import datetime as dt
import json

EPISODE_MIN = 45
FILM_MIN = 110

rows = [r for r in csv.DictReader(open("data/NetflixViewingHistory.csv", encoding="utf-8")) if r["Title"]]
tags = {t["show"]: t for t in csv.DictReader(open("data/title_tags.csv", encoding="utf-8"))}

for r in rows:
    r["date"] = dt.datetime.strptime(r["Date"], "%m/%d/%y").date()
    r["show"] = r["Title"].split(":")[0].strip()
    missing = r["show"] not in tags
    if missing:
        raise SystemExit(f"no tag for {r['show']!r}")
    r.update(tags[r["show"]])

dates = [r["date"] for r in rows]
first, last = min(dates), max(dates)
minutes = sum(EPISODE_MIN if r["type"] == "Series" else FILM_MIN for r in rows)

# monthly views, including empty months so gaps show up
months, d = [], first.replace(day=1)
while d <= last:
    months.append(d.strftime("%Y-%m"))
    d = (d.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
by_month = collections.Counter(r["date"].strftime("%Y-%m") for r in rows)

weekday_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
by_weekday = collections.Counter(r["date"].strftime("%a") for r in rows)

by_day = collections.Counter(dates)
top_day, top_day_n = by_day.most_common(1)[0]

shows = collections.Counter(r["show"] for r in rows)
series_shows = collections.Counter(r["show"] for r in rows if r["type"] == "Series")

# a binge = 3+ episodes of the same series on the same day
binge = collections.Counter((r["show"], r["date"]) for r in rows if r["type"] == "Series")
binges = [(s, d, n) for (s, d), n in binge.items() if n >= 3]

# genre and country counted per unique title, so one long series doesn't dominate
unique = {r["show"]: r for r in rows}
by_genre = collections.Counter(t["genre"] for t in unique.values())
by_country = collections.Counter(t["country"] for t in unique.values() if t["country"] != "Unknown")
by_type = collections.Counter(r["type"] for r in rows)

out = {
    "total_views": len(rows),
    "unique_titles": len(shows),
    "first": first.isoformat(),
    "last": last.isoformat(),
    "active_days": len(by_day),
    "est_hours": round(minutes / 60),
    "films": by_type["Film"],
    "episodes": by_type["Series"],
    "top_day": {"date": top_day.isoformat(), "views": top_day_n},
    "months": [{"month": m, "views": by_month.get(m, 0)} for m in months],
    "weekdays": [{"day": w, "views": by_weekday.get(w, 0)} for w in weekday_order],
    "top_series": [{"show": s, "episodes": n} for s, n in series_shows.most_common(8)],
    "genres": [{"genre": g, "titles": n} for g, n in by_genre.most_common()],
    "countries": [{"country": c, "iso": tags_iso, "titles": n}
                  for (c, tags_iso), n in collections.Counter(
                      (t["country"], t["iso"]) for t in unique.values() if t["country"] != "Unknown").most_common()],
    "unknown_country": sum(1 for t in unique.values() if t["country"] == "Unknown"),
    "binges": len(binges),
    "biggest_binge": max(binges, key=lambda b: b[2])[0] if binges else None,
    "biggest_binge_n": max(b[2] for b in binges) if binges else 0,
}
json.dump(out, open("docs/data.json", "w"), indent=2, ensure_ascii=False)
print(json.dumps({k: v for k, v in out.items() if not isinstance(v, list)}, indent=2, ensure_ascii=False))
