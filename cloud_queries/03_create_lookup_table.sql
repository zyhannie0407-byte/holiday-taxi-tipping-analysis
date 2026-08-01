-- 03_create_lookup_table.sql
-- Create external Athena table for NYC Taxi Zone Lookup data stored as CSV in S3.
-- Run this statement after creating the holiday_taxi_tipping database.

CREATE EXTERNAL TABLE IF NOT EXISTS holiday_taxi_tipping.taxi_zone_lookup (
  LocationID BIGINT,
  Borough STRING,
  Zone STRING,
  service_zone STRING
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
  "separatorChar" = ",",
  "quoteChar" = "\""
)
LOCATION 's3://cs675-holiday-nyc-taxi-yuhanzhu-288834682554-us-east-1-an/lookup/'
TBLPROPERTIES ("skip.header.line.count"="1");