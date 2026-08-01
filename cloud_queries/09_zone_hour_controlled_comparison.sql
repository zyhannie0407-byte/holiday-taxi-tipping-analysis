-- 09_zone_hour_controlled_comparison.sql
-- Compare holiday and baseline tip rates within the same pickup borough and pickup hour.
-- This helps reduce trip-composition bias by comparing more similar groups of trips.
-- Analysis uses credit-card trips only because cash tips are not reliably captured.

WITH cleaned_trips AS (
  SELECT
    CASE
      WHEN month(t.tpep_pickup_datetime) IN (11, 12, 1) THEN 'Holiday Season'
      WHEN month(t.tpep_pickup_datetime) IN (3, 4, 9, 10) THEN 'Normal Baseline'
      ELSE 'Other'
    END AS study_period,
    z.borough,
    hour(t.tpep_pickup_datetime) AS pickup_hour,
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
),
grouped AS (
  SELECT
    borough,
    pickup_hour,
    study_period,
    COUNT(*) AS trip_count,
    AVG(tip_rate) AS avg_tip_rate
  FROM cleaned_trips
  WHERE study_period IN ('Holiday Season', 'Normal Baseline')
    AND borough IN ('Manhattan', 'Queens', 'Brooklyn', 'Bronx', 'Staten Island')
  GROUP BY borough, pickup_hour, study_period
),
pivoted AS (
  SELECT
    borough,
    pickup_hour,
    SUM(CASE WHEN study_period = 'Holiday Season' THEN trip_count ELSE 0 END) AS holiday_trips,
    SUM(CASE WHEN study_period = 'Normal Baseline' THEN trip_count ELSE 0 END) AS baseline_trips,
    AVG(CASE WHEN study_period = 'Holiday Season' THEN avg_tip_rate END) AS holiday_tip_rate,
    AVG(CASE WHEN study_period = 'Normal Baseline' THEN avg_tip_rate END) AS baseline_tip_rate
  FROM grouped
  GROUP BY borough, pickup_hour
)

SELECT
  borough,
  pickup_hour,
  holiday_trips,
  baseline_trips,
  ROUND(holiday_tip_rate, 4) AS holiday_tip_rate,
  ROUND(baseline_tip_rate, 4) AS baseline_tip_rate,
  ROUND(holiday_tip_rate - baseline_tip_rate, 4) AS tip_rate_difference
FROM pivoted
WHERE holiday_trips >= 10000
  AND baseline_trips >= 10000
ORDER BY ABS(holiday_tip_rate - baseline_tip_rate) DESC
LIMIT 20;