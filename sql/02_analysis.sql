-- 02_analysis.sql
-- Analysis queries. Each one starts with a "-- name:" line so analysis.py
-- can run them one by one.

-- name: untagged
-- Every show must have a tag in title_tags.csv; this should return no rows.
SELECT DISTINCT v.show
FROM views v
LEFT JOIN title_tags t ON t.show = v.show
WHERE t.show IS NULL;

-- name: summary
-- Watch time is an estimate: 45 minutes per episode, 110 per film.
SELECT COUNT(*)                         AS total_views,
       COUNT(DISTINCT v.show)           AS unique_titles,
       MIN(watched_on)                  AS first,
       MAX(watched_on)                  AS last,
       COUNT(DISTINCT watched_on)       AS active_days,
       SUM(t.type = 'Film')             AS films,
       SUM(t.type = 'Series')           AS episodes,
       ROUND(SUM(CASE t.type WHEN 'Film' THEN 110 ELSE 45 END) / 60.0) AS est_hours
FROM views v
JOIN title_tags t USING (show);

-- name: months
-- Views per month, including months with nothing watched.
WITH RECURSIVE months(month) AS (
  SELECT STRFTIME('%Y-%m', MIN(watched_on)) FROM views
  UNION ALL
  SELECT STRFTIME('%Y-%m', DATE(month || '-01', '+1 month'))
  FROM months
  WHERE month < (SELECT STRFTIME('%Y-%m', MAX(watched_on)) FROM views)
)
SELECT m.month, COUNT(v.title) AS views
FROM months m
LEFT JOIN views v ON STRFTIME('%Y-%m', v.watched_on) = m.month
GROUP BY m.month
ORDER BY m.month;

-- name: weekdays
SELECT CASE STRFTIME('%w', watched_on)
         WHEN '1' THEN 'Mon' WHEN '2' THEN 'Tue' WHEN '3' THEN 'Wed'
         WHEN '4' THEN 'Thu' WHEN '5' THEN 'Fri' WHEN '6' THEN 'Sat'
         ELSE 'Sun' END AS day,
       COUNT(*) AS views
FROM views
GROUP BY STRFTIME('%w', watched_on)
ORDER BY (CAST(STRFTIME('%w', watched_on) AS INTEGER) + 6) % 7;

-- name: top_day
SELECT watched_on AS date, COUNT(*) AS views
FROM views
GROUP BY watched_on
ORDER BY views DESC, watched_on
LIMIT 1;

-- name: top_series
SELECT v.show, COUNT(*) AS episodes
FROM views v
JOIN title_tags t USING (show)
WHERE t.type = 'Series'
GROUP BY v.show
ORDER BY episodes DESC, v.show
LIMIT 8;

-- name: binges
-- A binge is 3+ episodes of the same series on the same day.
SELECT v.show, v.watched_on, COUNT(*) AS episodes
FROM views v
JOIN title_tags t USING (show)
WHERE t.type = 'Series'
GROUP BY v.show, v.watched_on
HAVING COUNT(*) >= 3
ORDER BY episodes DESC, v.watched_on;

-- name: genres
-- Counted per unique title, so one long series doesn't dominate.
SELECT t.genre, COUNT(DISTINCT v.show) AS titles
FROM views v
JOIN title_tags t USING (show)
GROUP BY t.genre
ORDER BY titles DESC, t.genre;

-- name: countries
SELECT t.country, t.iso, COUNT(DISTINCT v.show) AS titles
FROM views v
JOIN title_tags t USING (show)
WHERE t.country <> 'Unknown'
GROUP BY t.country, t.iso
ORDER BY titles DESC, t.country;

-- name: unknown_country
SELECT COUNT(DISTINCT v.show) AS n
FROM views v
JOIN title_tags t USING (show)
WHERE t.country = 'Unknown';
