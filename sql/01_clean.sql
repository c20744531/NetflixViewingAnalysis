-- 01_clean.sql
-- Cleans the raw Netflix export and joins it to my hand-tagged lookup.
-- analysis.py loads data/NetflixViewingHistory.csv into raw_history and
-- data/title_tags.csv into title_tags before running this.

DROP TABLE IF EXISTS views;

-- Netflix dates come as m/d/yy text ("9/19/26"). Split them on the slashes
-- and rebuild them as ISO dates (2026-09-19) so SQLite can work with them.
-- Titles look like "The Night Agent: Season 3: Orion"; the show is
-- everything before the first colon.
CREATE TABLE views AS
WITH parts AS (
  SELECT TRIM(title) AS title,
         date AS raw_date,
         CAST(SUBSTR(date, 1, INSTR(date, '/') - 1) AS INTEGER) AS m,
         SUBSTR(date, INSTR(date, '/') + 1) AS rest
  FROM raw_history
  WHERE TRIM(title) <> ''
),
dated AS (
  SELECT title, m,
         CAST(SUBSTR(rest, 1, INSTR(rest, '/') - 1) AS INTEGER) AS d,
         2000 + CAST(SUBSTR(rest, INSTR(rest, '/') + 1) AS INTEGER) AS y
  FROM parts
)
SELECT PRINTF('%04d-%02d-%02d', y, m, d) AS watched_on,
       title,
       TRIM(CASE WHEN INSTR(title, ':') > 0
                 THEN SUBSTR(title, 1, INSTR(title, ':') - 1)
                 ELSE title END) AS show
FROM dated;

