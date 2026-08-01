-- 02_create_yellow_taxi_table.sql
-- Create external Athena table for NYC Yellow Taxi trip records stored as Parquet files in S3.
-- Run this statement after creating the holiday_taxi_tipping database.

CREATE EXTERNAL TABLE IF NOT EXISTS holiday_taxi_tipping.yellow_taxi_trips (
  VendorID BIGINT,
  tpep_pickup_datetime TIMESTAMP,
  tpep_dropoff_datetime TIMESTAMP,
  passenger_count DOUBLE,
  trip_distance DOUBLE,
  RatecodeID DOUBLE,
  store_and_fwd_flag STRING,
  PULocationID BIGINT,
  DOLocationID BIGINT,
  payment_type BIGINT,
  fare_amount DOUBLE,
  extra DOUBLE,
  mta_tax DOUBLE,
  tip_amount DOUBLE,
  tolls_amount DOUBLE,
  improvement_surcharge DOUBLE,
  total_amount DOUBLE,
  congestion_surcharge DOUBLE,
  Airport_fee DOUBLE
)
STORED AS PARQUET
LOCATION 's3://cs675-holiday-nyc-taxi-yuhanzhu-288834682554-us-east-1-an/raw/yellow_taxi/';