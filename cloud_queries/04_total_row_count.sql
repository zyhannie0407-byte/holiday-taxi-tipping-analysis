-- 04_total_row_count.sql
-- Count total rows in the cloud-scale Athena yellow taxi table.
-- This query confirms that the project satisfies the 100M+ row requirement.

SELECT
  COUNT(*) AS total_rows
FROM holiday_taxi_tipping.yellow_taxi_trips;
