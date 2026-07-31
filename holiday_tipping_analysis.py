from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = SparkSession.builder.appName("Holiday Taxi Tipping Analysis").getOrCreate()

# --------------------------------------------------
# 1. Read data
# --------------------------------------------------

# For local demo, keep only these two files in the folder:
# yellow_tripdata_2025-03.parquet
# yellow_tripdata_2025-12.parquet
taxi_path = "/home/jovyan/work/data/taxi/yellow_tripdata_*.parquet"
zone_path = "/home/jovyan/work/data/taxi/taxi_zone_lookup.csv"

trips = spark.read.parquet(taxi_path)

zones = (
    spark.read
    .option("header", True)
    .option("inferSchema", True)
    .csv(zone_path)
)

print("Original trip rows:", trips.count())
print("Zone rows:", zones.count())

print("\nTrip schema:")
trips.printSchema()

# --------------------------------------------------
# 2. Create study period fields before cleaning
# --------------------------------------------------

taxi_with_period = (
    trips
    .withColumn("pickup_date", F.to_date("tpep_pickup_datetime"))
    .withColumn("pickup_month", F.month("tpep_pickup_datetime"))
    .withColumn("pickup_hour", F.hour("tpep_pickup_datetime"))
    .withColumn(
        "period",
        F.when(
            (F.col("pickup_date") >= F.lit("2025-03-01")) &
            (F.col("pickup_date") <= F.lit("2025-03-31")),
            "Normal Baseline"
        )
        .when(
            (F.col("pickup_date") >= F.lit("2025-12-01")) &
            (F.col("pickup_date") <= F.lit("2025-12-31")),
            "Holiday Season"
        )
        .otherwise("Outside Study Period")
    )
    .filter(F.col("period") != "Outside Study Period")
)

print("Study period rows:", taxi_with_period.count())

# ============================================================
# 3. EDA: Understand raw data distribution before cleaning
# ============================================================

print("\n================ EDA: Raw Data Distribution ================\n")

taxi_eda = taxi_with_period.withColumn(
    "raw_tip_rate",
    F.when(F.col("fare_amount") > 0, F.col("tip_amount") / F.col("fare_amount"))
)

eda_columns = [
    "fare_amount",
    "tip_amount",
    "trip_distance",
    "raw_tip_rate"
]

eda_summary = taxi_eda.select(eda_columns).summary(
    "count", "mean", "stddev", "min", "25%", "50%", "75%", "max"
)

print("Basic summary statistics before filtering:")
eda_summary.show(truncate=False)

percentiles = [0.5, 0.75, 0.9, 0.95, 0.99]

# More detailed upper percentiles for deciding reasonable cleaning thresholds
detailed_percentiles = [0.95, 0.99, 0.995, 0.999, 0.9999]

print("\nPercentiles before filtering:")
for col_name in eda_columns:
    quantiles = taxi_eda.approxQuantile(col_name, percentiles, 0.01)
    print(f"\n{col_name}:")
    for p, q in zip(percentiles, quantiles):
        print(f"  {int(p * 100)}th percentile: {q}")

print("\nDetailed upper percentiles before filtering:")
for col_name in ["fare_amount", "tip_amount", "trip_distance", "raw_tip_rate"]:
    quantiles = taxi_eda.approxQuantile(col_name, detailed_percentiles, 0.001)
    print(f"\n{col_name}:")
    for p, q in zip(detailed_percentiles, quantiles):
        print(f"  {p * 100:.2f}th percentile: {q}")

invalid_records = taxi_eda.select(
    F.count("*").alias("total_rows"),
    F.sum(F.when(F.col("fare_amount") <= 0, 1).otherwise(0)).alias("non_positive_fare"),
    F.sum(F.when(F.col("tip_amount") < 0, 1).otherwise(0)).alias("negative_tip"),
    F.sum(F.when(F.col("trip_distance") <= 0, 1).otherwise(0)).alias("non_positive_distance"),
    F.sum(F.when(F.col("PULocationID").isNull(), 1).otherwise(0)).alias("missing_pickup_location"),
    F.sum(F.when(F.col("DOLocationID").isNull(), 1).otherwise(0)).alias("missing_dropoff_location"),
    F.sum(F.when(F.col("payment_type").isNull(), 1).otherwise(0)).alias("missing_payment_type")
)

print("\nPotentially invalid records before filtering:")
invalid_records.show(truncate=False)

# Analyze extreme but potentially meaningful tips separately.
# These records are not automatically treated as errors.
high_tip_trips = taxi_eda.filter(
    (F.col("fare_amount") > 0) &
    (
        (F.col("tip_amount") >= 20) |
        (F.col("raw_tip_rate") >= 0.5)
    )
)

high_tip_summary = high_tip_trips.groupBy("period").agg(
    F.count("*").alias("high_tip_trip_count"),
    F.round(F.avg("tip_amount"), 2).alias("avg_high_tip_amount"),
    F.round(F.avg("raw_tip_rate"), 4).alias("avg_high_tip_rate"),
    F.round(F.avg("fare_amount"), 2).alias("avg_fare_amount"),
    F.round(F.avg("trip_distance"), 2).alias("avg_trip_distance")
).orderBy("period")

print("\nHigh-tip trips before filtering:")
high_tip_summary.show(truncate=False)

# Save EDA outputs
eda_output_path = "/home/jovyan/work/results/holiday_tipping/eda"

eda_summary.coalesce(1).write.mode("overwrite").option("header", True).csv(
    f"{eda_output_path}/raw_summary_statistics"
)

invalid_records.coalesce(1).write.mode("overwrite").option("header", True).csv(
    f"{eda_output_path}/invalid_record_counts"
)

high_tip_summary.coalesce(1).write.mode("overwrite").option("header", True).csv(
    f"{eda_output_path}/high_tip_trips_by_period"
)

# --------------------------------------------------
# 4. Clean data and create analysis fields
# --------------------------------------------------

clean_trips_w_extreme = (
    taxi_with_period

    # Basic validity filters
    .filter(F.col("fare_amount") > 0)
    .filter(F.col("tip_amount") >= 0)
    .filter(F.col("trip_distance") > 0)
    .filter(F.col("PULocationID").isNotNull())
    .filter(F.col("DOLocationID").isNotNull())
    .filter(F.col("payment_type").isNotNull())

    # Create tip rate
    .withColumn("tip_rate", F.col("tip_amount") / F.col("fare_amount"))

    # Create airport trip flag
    # TLC Location IDs: Newark Airport = 1, JFK = 132, LaGuardia = 138
    .withColumn(
        "airport_trip_flag",
        F.when(
            (F.col("PULocationID").isin(1, 132, 138)) |
            (F.col("DOLocationID").isin(1, 132, 138)),
            "Airport Trip"
        ).otherwise("Non-Airport Trip")
    )
)

clean_trips = (
    clean_trips_w_extreme

    # EDA-driven filters for the main comparison dataset.
    # Detailed percentiles showed that 99.5% of trips had:
    # fare_amount below about $93, tip_amount below about $20,
    # and trip_distance below about 21 miles.
    # These thresholds keep nearly all normal trips while reducing
    # the influence of likely data-quality errors.
    # High-tip behavior is still analyzed separately in the EDA section.
    .filter(F.col("fare_amount") < 100)
    .filter(F.col("tip_amount") < 25)
    .filter(F.col("trip_distance") < 25)
    .filter(F.col("tip_rate") <= 1)
)

print("Cleaned trip rows:", clean_trips.count())

# --------------------------------------------------
# 5. Join with taxi zone lookup table
# --------------------------------------------------

pickup_zones = zones.select(
    F.col("LocationID").alias("PULocationID"),
    F.col("Borough").alias("pickup_borough"),
    F.col("Zone").alias("pickup_zone")
)

joined = clean_trips.join(pickup_zones, on="PULocationID", how="left")

print("Joined rows:", joined.count())

# Main tipping analysis uses credit-card trips because recorded tips are more reliable
credit_trips = joined.filter(F.col("payment_type") == 1)

print("Credit card trip rows:", credit_trips.count())

# --------------------------------------------------
# 6. Analysis 1: Holiday vs normal tipping, all valid trips
# --------------------------------------------------

print("\nAnalysis 1: Holiday vs Normal Tipping - All Valid Trips")

all_period_summary = joined.groupBy("period").agg(
    F.count("*").alias("trip_count"),
    F.round(F.avg("tip_amount"), 2).alias("avg_tip_amount"),
    F.round(F.avg("tip_rate"), 4).alias("avg_tip_rate"),
    F.round(F.avg("fare_amount"), 2).alias("avg_fare_amount"),
    F.round(F.avg("trip_distance"), 2).alias("avg_trip_distance")
).orderBy("period")

all_period_summary.show(truncate=False)

# --------------------------------------------------
# 7. Analysis 2: Holiday vs normal tipping, credit-card trips only
# --------------------------------------------------

print("\nAnalysis 2: Holiday vs Normal Tipping - Credit Card Trips Only")

credit_period_summary = credit_trips.groupBy("period").agg(
    F.count("*").alias("trip_count"),
    F.round(F.avg("tip_amount"), 2).alias("avg_tip_amount"),
    F.round(F.avg("tip_rate"), 4).alias("avg_tip_rate"),
    F.round(F.avg("fare_amount"), 2).alias("avg_fare_amount"),
    F.round(F.avg("trip_distance"), 2).alias("avg_trip_distance")
).orderBy("period")

credit_period_summary.show(truncate=False)

# --------------------------------------------------
# 8. Analysis 3: Credit-card tip rate by pickup borough
# --------------------------------------------------

print("\nAnalysis 3: Credit Card Tip Rate by Pickup Borough")

borough_summary = credit_trips.groupBy("period", "pickup_borough").agg(
    F.count("*").alias("trip_count"),
    F.round(F.avg("tip_amount"), 2).alias("avg_tip_amount"),
    F.round(F.avg("tip_rate"), 4).alias("avg_tip_rate"),
    F.round(F.avg("fare_amount"), 2).alias("avg_fare_amount")
).orderBy("period", F.desc("avg_tip_rate"))

borough_summary.show(100, truncate=False)

# --------------------------------------------------
# 9. Analysis 4: Credit-card tip rate by pickup hour
# --------------------------------------------------

print("\nAnalysis 4: Credit Card Tip Rate by Pickup Hour")

hour_summary = credit_trips.groupBy("period", "pickup_hour").agg(
    F.count("*").alias("trip_count"),
    F.round(F.avg("tip_amount"), 2).alias("avg_tip_amount"),
    F.round(F.avg("tip_rate"), 4).alias("avg_tip_rate")
).orderBy("period", "pickup_hour")

hour_summary.show(100, truncate=False)

# --------------------------------------------------
# 10. Analysis 5: Airport vs non-airport tipping
# --------------------------------------------------

print("\nAnalysis 5: Airport vs Non-Airport Tipping - Credit Card Trips Only")

airport_summary = credit_trips.groupBy("period", "airport_trip_flag").agg(
    F.count("*").alias("trip_count"),
    F.round(F.avg("tip_amount"), 2).alias("avg_tip_amount"),
    F.round(F.avg("tip_rate"), 4).alias("avg_tip_rate"),
    F.round(F.avg("fare_amount"), 2).alias("avg_fare_amount"),
    F.round(F.avg("trip_distance"), 2).alias("avg_trip_distance")
).orderBy("period", "airport_trip_flag")

airport_summary.show(100, truncate=False)

# --------------------------------------------------
# 11. Analysis 6: Top pickup zones by credit-card tip rate
# --------------------------------------------------

print("\nAnalysis 6: Top Pickup Zones by Tip Rate - Credit Card Trips Only")

zone_summary = (
    credit_trips
    .groupBy("period", "pickup_borough", "pickup_zone")
    .agg(
        F.count("*").alias("trip_count"),
        F.round(F.avg("tip_amount"), 2).alias("avg_tip_amount"),
        F.round(F.avg("tip_rate"), 4).alias("avg_tip_rate"),
        F.round(F.avg("fare_amount"), 2).alias("avg_fare_amount")
    )
    # Keep zones with enough trips so the result is more reliable
    .filter(F.col("trip_count") >= 1000)
    .orderBy("period", F.desc("avg_tip_rate"))
)

zone_summary.show(50, truncate=False)

# --------------------------------------------------
# 12. Save result tables for dashboard, slides, and README
# --------------------------------------------------

output_path = "/home/jovyan/work/results/holiday_tipping"

def save_single_csv(df, folder_name):
    (
        df.coalesce(1)
        .write.mode("overwrite")
        .option("header", True)
        .csv(f"{output_path}/{folder_name}")
    )

save_single_csv(all_period_summary, "all_valid_holiday_vs_normal")
save_single_csv(credit_period_summary, "credit_card_holiday_vs_normal")
save_single_csv(borough_summary, "credit_card_tip_rate_by_borough")
save_single_csv(hour_summary, "credit_card_tip_rate_by_hour")
save_single_csv(airport_summary, "credit_card_airport_vs_non_airport")
save_single_csv(zone_summary, "credit_card_top_zones_by_tip_rate")

print("\nDashboard CSV folders saved to:")
print(output_path)

spark.stop()