from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = SparkSession.builder.appName("Holiday Taxi Tipping Analysis").getOrCreate()

# --------------------------------------------------
# 1. Read data
# --------------------------------------------------

# For today's local demo, keep only these two files in the folder:
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
# 2. Clean data and create new fields
# --------------------------------------------------

clean_trips = (
    trips
    .withColumn("pickup_date", F.to_date("tpep_pickup_datetime"))
    .withColumn("pickup_month", F.month("tpep_pickup_datetime"))
    .withColumn("pickup_hour", F.hour("tpep_pickup_datetime"))

    # Define study periods:
    # March 2025 = normal baseline
    # December 2025 = holiday season sample
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

    # Basic validity filters
    .filter(F.col("fare_amount") > 0)
    .filter(F.col("tip_amount") >= 0)
    .filter(F.col("trip_distance") > 0)
    .filter(F.col("PULocationID").isNotNull())
    .filter(F.col("DOLocationID").isNotNull())
    .filter(F.col("payment_type").isNotNull())

    # Outlier filters
    .filter(F.col("fare_amount") < 300)
    .filter(F.col("tip_amount") < 100)
    .filter(F.col("trip_distance") < 100)

    # Create tip rate
    .withColumn("tip_rate", F.col("tip_amount") / F.col("fare_amount"))

    # Remove extreme tip-rate values
    .filter(F.col("tip_rate") <= 1)

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

print("Cleaned trip rows:", clean_trips.count())

# --------------------------------------------------
# 3. Join with taxi zone lookup table
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
# 4. Analysis 1: Holiday vs normal tipping, all valid trips
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
# 5. Analysis 2: Holiday vs normal tipping, credit-card trips only
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
# 6. Analysis 3: Credit-card tip rate by pickup borough
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
# 7. Analysis 4: Credit-card tip rate by pickup hour
# --------------------------------------------------

print("\nAnalysis 4: Credit Card Tip Rate by Pickup Hour")

hour_summary = credit_trips.groupBy("period", "pickup_hour").agg(
    F.count("*").alias("trip_count"),
    F.round(F.avg("tip_amount"), 2).alias("avg_tip_amount"),
    F.round(F.avg("tip_rate"), 4).alias("avg_tip_rate")
).orderBy("period", "pickup_hour")

hour_summary.show(100, truncate=False)

# --------------------------------------------------
# 8. Analysis 5: Airport vs non-airport tipping
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
# 9. Analysis 6: Top pickup zones by credit-card tip rate
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
# 10. Save result tables for slides / README
# --------------------------------------------------

output_path = "/home/jovyan/work/results/holiday_tipping"

(
    all_period_summary
    .coalesce(1)
    .write.mode("overwrite")
    .option("header", True)
    .csv(f"{output_path}/all_valid_holiday_vs_normal")
)

(
    credit_period_summary
    .coalesce(1)
    .write.mode("overwrite")
    .option("header", True)
    .csv(f"{output_path}/credit_card_holiday_vs_normal")
)

(
    borough_summary
    .coalesce(1)
    .write.mode("overwrite")
    .option("header", True)
    .csv(f"{output_path}/credit_card_tip_rate_by_borough")
)

(
    hour_summary
    .coalesce(1)
    .write.mode("overwrite")
    .option("header", True)
    .csv(f"{output_path}/credit_card_tip_rate_by_hour")
)

(
    airport_summary
    .coalesce(1)
    .write.mode("overwrite")
    .option("header", True)
    .csv(f"{output_path}/credit_card_airport_vs_non_airport")
)

(
    zone_summary
    .coalesce(1)
    .write.mode("overwrite")
    .option("header", True)
    .csv(f"{output_path}/credit_card_top_zones_by_tip_rate")
)


# --------------------------------------------------
# 11. Save clean single CSV files for dashboard
# --------------------------------------------------

dashboard_output_path = "/home/jovyan/work/results/holiday_tipping"

def save_single_csv(df, folder_name):
    (
        df.coalesce(1)
        .write.mode("overwrite")
        .option("header", True)
        .csv(f"{dashboard_output_path}/{folder_name}")
    )

save_single_csv(credit_period_summary, "credit_card_holiday_vs_normal")
save_single_csv(borough_summary, "credit_card_tip_rate_by_borough")
save_single_csv(hour_summary, "credit_card_tip_rate_by_hour")
save_single_csv(airport_summary, "credit_card_airport_vs_non_airport")
save_single_csv(zone_summary, "credit_card_top_zones_by_tip_rate")

print("\nDashboard CSV folders saved to:")
print(dashboard_output_path)

spark.stop()