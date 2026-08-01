-- 08_tip_rate_by_borough.sql
-- Analyze cloud-scale tip rates by pickup borough.
-- This query joins yellow taxi trips with the taxi zone lookup table.
-- Analysis uses credit-card trips only because cash tips are not reliably captured.

WITH cleaned_trips AS (
  SELECT
    CASE
      WHEN month(t.tpep_pickup_datetime) IN (11, 12, 1) THEN 'Holiday Season'
      WHEN month(t.tpep_pickup_datetime) IN (3, 4, 9, 10) THEN 'Normal Baseline'
      ELSE 'Other'
    END AS study_period,
    z.borough,
    t.fare_amount,
    t.tip_amount,
    t.trip_distance,
    t.tip_amount / t.fare_amount AS tip_rate
  FROM holiday_taxi_tipping.yellow_taxi_trips t
  LEFT JOIN holiday_taxi_tipping.taxi_zone_lookup z
    ON t.PULocationID = z.LocationID
  WHERE t.payment_type = 1
    AND t.fare_amount > 0
    AND t.tip_amount >= 0
    AND t.trip_distance > 0
    AND t.fare_amount < 100
    AND t.tip_amount < 25
    AND t.trip_distance < 25
    AND t.tip_amount / t.fare_amount <= 1
    AND year(t.tpep_pickup_datetime) IN (2023, 2024, 2025)
)

SELECT
  study_period,
  borough,
  COUNT(*) AS trip_count,
  ROUND(AVG(tip_amount), 2) AS avg_tip_amount,
  ROUND(AVG(tip_rate), 4) AS avg_tip_rate,
  ROUND(AVG(fare_amount), 2) AS avg_fare_amount,
  ROUND(AVG(trip_distance), 2) AS avg_trip_distance
FROM cleaned_trips
WHERE study_period IN ('Holiday Season', 'Normal Baseline')
  AND borough IS NOT NULL
GROUP BY study_period, borough
ORDER BY study_period, avg_tip_rate DESC;