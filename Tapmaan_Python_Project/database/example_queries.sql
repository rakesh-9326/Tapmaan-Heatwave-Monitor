-- Open database/tapmaan.db with a SQLite viewer, or use Python's sqlite3 module.

-- 1. List available cities.
SELECT * FROM cities;

-- 2. Explain the foreign-key JOIN between cities and readings.
SELECT c.name, r.recorded_at, r.temperature, r.humidity, r.source, r.kind
FROM readings r JOIN cities c ON r.city_id = c.id
ORDER BY r.recorded_at DESC;

-- 3. Only the user's manual observations.
SELECT * FROM readings WHERE source = 'manual' ORDER BY recorded_at DESC;

-- 4. Average and maximum sample observation temperatures by city.
-- Filter kind so forecast rows do not count as recorded observations.
SELECT c.name, ROUND(AVG(r.temperature), 1) AS average_c,
       MAX(r.temperature) AS maximum_c
FROM readings r JOIN cities c ON r.city_id = c.id
WHERE r.source = 'demo' AND r.kind = 'observation'
GROUP BY c.id, c.name;

-- 5. Unreviewed warnings, with the source and reading type visible.
SELECT a.id, c.name, r.temperature, r.recorded_at, r.source, r.kind, a.level
FROM alerts a
JOIN readings r ON a.reading_id = r.id
JOIN cities c ON r.city_id = c.id
WHERE a.acknowledged = 0
ORDER BY r.recorded_at DESC;

-- 6. Count stored rows by source and type.
SELECT source, kind, COUNT(*) AS total
FROM readings GROUP BY source, kind;

-- The application uses ? placeholders rather than concatenating user inputs:
-- SELECT * FROM readings WHERE city_id = ? AND source = ?;
-- db.execute(sql, ('dombivli', 'manual'))
