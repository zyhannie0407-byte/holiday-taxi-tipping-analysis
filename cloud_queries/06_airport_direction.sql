-- 06_airport_direction.sql
-- Compare cloud-scale tip rates by airport trip direction.
-- Airport IDs used:
--   1 = Newark
--   132 = JFK
--   138 = LaGuardia
-- Analysis uses credit-card trips only because cash tips are not reliably captured.

WITH cleaned_trips AS (
  SELECT
    CASE
      WHEN month(tpep_pickup_datetime) IN (11, 12, 1) THEN 'Holiday Season'
      WHEN month(tpep_pickup_datetime) IN (3, 4, 9, 10) THEN 'Normal Baseline'
      ELSE 'Other'
    END AS study_period,
    CASE
      WHEN PULocationID IN (1, 132, 138) AND DOLocationID NOT IN (1, 132, 138)
        THEN 'Airport Inbound'
      WHEN PULocationID NOT IN (1, 132, 138) AND DOLocationID IN (1, 132, 138)
        THEN 'Airport Outbound'
      WHEN PULocationID IN (1, 132, 138) AND DOLocationID IN (1, 132, 138)
        THEN 'Airport-to-Airport'
      ELSE 'Non-Airport'
    END AS airport_direction,
    fare_amount,
    tip_amount,
    trip_distance,
    tip_amount / fare_amount AS tip_rate
  FROM holiday_taxi_tipping.yellow_taxi_trips
  WHERE payment_type = 1
    AND fare_amount > 0
    AND tip_amount >= 0
    AND trip_distance > 0
    AND fare_amount < 100
    AND tip_amount < 25
    AND trip_distance < 25
    AND tip_amount / fare_amount <= 1
    AND year(tpep_pickup_datetime) IN (2023, 2024, 2025)
)

SELECT
  study_period,
  airport_direction,
  COUNT(*) AS trip_count,
  ROUND(AVG(tip_amount), 2) AS avg_tip_amount,
  ROUND(AVG(tip_rate), 4) AS avg_tip_rate,
  ROUND(AVG(fare_amount), 2) AS avg_fare_amount,
  ROUND(AVG(trip_distance), 2) AS avg_trip_distance
FROM cleaned_trips
WHERE study_period IN ('Holiday Season', 'Normal Baseline')
GROUP BY study_period, airport_direction
ORDER BY study_period, trip_count DESC;