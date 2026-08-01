````markdown
# Cloud-Scale Analysis of Holiday vs Non-Holiday NYC Taxi Tipping

This is my final project for **CS675 Big Data: Management & Analytics**.

The project analyzes NYC Yellow Taxi tipping behavior during holiday-season periods compared with normal baseline periods. The analysis focuses on whether riders appear more generous during the holidays and how that pattern changes by airport direction, pickup borough, pickup hour, and trip composition.

## Project Question

Do NYC taxi riders tip more generously during the holiday season compared with normal non-holiday periods?

## Main Metric

The main metric is:

```text
tip rate = tip amount / fare amount
````

I use tip rate because average dollar tip amount can be misleading. Longer or more expensive trips, such as airport trips, naturally produce higher dollar tips even if riders are not tipping more generously as a percentage of fare.

The analysis focuses on **credit-card trips only** because cash tips are not reliably captured in the taxi trip records.

## Data Sources

This project uses:

* NYC TLC Yellow Taxi Trip Records in Parquet format
* NYC Taxi Zone Lookup Table in CSV format

The local demo uses a smaller sample:

* Normal baseline: March 2025
* Holiday-season sample: December 2025

The cloud-scale version uses multi-year post-COVID Yellow Taxi data stored in Amazon S3 and queried with Amazon Athena.

## Tools Used

* Python
* PySpark
* Dockerized Spark environment provided by the course
* Pandas
* Streamlit
* Amazon S3
* Amazon Athena
* GitHub

## Repository Structure

```text
.
├── README.md
├── holiday_tipping_analysis.py
├── holiday_tipping_dashboard.py
├── cloud_queries/
│   ├── 01_create_database.sql
│   ├── 02_create_yellow_taxi_table.sql
│   ├── 03_create_lookup_table.sql
│   ├── 04_total_row_count.sql
│   ├── 05_holiday_vs_baseline.sql
│   ├── 06_airport_direction.sql
│   ├── 07_tip_rate_by_pickup_hour.sql
│   ├── 08_tip_rate_by_borough.sql
│   └── 09_zone_hour_controlled_comparison.sql
├── cloud_results/
│   ├── holiday_vs_baseline.csv
│   ├── airport_direction.csv
│   ├── tip_rate_by_hour.csv
│   ├── tip_rate_by_borough.csv
│   └── zone_hour_controlled_comparison.csv
└── results/
    └── holiday_tipping/
```

## Local PySpark Demo

The local version validates the pipeline and dashboard logic before scaling the analysis to AWS.

The local PySpark pipeline:

1. Loads NYC Yellow Taxi Parquet files.
2. Creates study-period labels.
3. Runs EDA before filtering.
4. Applies cleaning filters.
5. Joins taxi trips with taxi zone lookup data.
6. Generates grouped result CSV files.
7. Powers the Streamlit dashboard.

### How to Run the Local PySpark Analysis

This project uses the course-provided Dockerized PySpark environment.

Start Docker Desktop first. Then from the course `code-starter` folder, run:

```bash
make up
```

Then run the PySpark analysis script inside the container:

```bash
docker compose exec pyspark python /home/jovyan/work/holiday_tipping_analysis.py
```

The script writes summarized result files to:

```text
work/results/holiday_tipping/
```

### How to Run the Dashboard

From the `code-starter` folder, run:

```bash
streamlit run work/holiday_tipping_dashboard.py
```

The dashboard includes both:

* Local PySpark demo results
* Cloud-scale Athena result visualizations

## Cloud-Scale Athena Workflow

The cloud-scale version uses Amazon S3 as the storage layer and Amazon Athena as the query engine.

### S3 Structure

```text
s3://cs675-holiday-nyc-taxi-yuhanzhu-288834682554-us-east-1-an/
├── raw/
│   └── yellow_taxi/
├── lookup/
└── results/
```

### Athena Tables

The Athena setup creates:

* `holiday_taxi_tipping.yellow_taxi_trips`
* `holiday_taxi_tipping.taxi_zone_lookup`

The SQL files in `cloud_queries/` document how to recreate the cloud analysis.

Athena allows one SQL statement per query execution, so the setup files should be run one at a time.

## Cloud-Scale Requirement

The Athena row-count query returned:

```text
128,202,548 rows
```

This satisfies the project requirement of analyzing at least 100 million rows at cloud scale.

## Cloud Analytical Queries

The cloud analysis includes:

1. Total row count
2. Holiday vs normal baseline tip-rate comparison
3. Airport inbound, airport outbound, and non-airport comparison
4. Tip rate by pickup hour
5. Tip rate by pickup borough
6. Zone/hour controlled comparison

The query outputs are saved in the `cloud_results/` folder and visualized in the Streamlit dashboard.

## Main Findings

The local demo and cloud-scale version produced slightly different results because the local demo only compares March 2025 and December 2025, while the cloud version uses a much larger multi-year dataset.

### Local Demo Finding

In the local demo, December holiday trips had a higher average dollar tip than the March baseline, but a lower average tip rate. This suggests that riders paid more in dollars but were not necessarily more generous relative to fare.

### Cloud-Scale Finding

In the cloud-scale Athena analysis, holiday-season trips had a slightly higher average tip rate than normal baseline trips, but the difference was small.

This suggests that holiday tipping generosity may exist, but it is subtle.

### Supporting Findings

* Airport trips had much higher dollar tips because fares were higher, but their tip rates were lower than non-airport trips.
* Manhattan had the strongest and most stable tip rate.
* Queens had higher dollar tips but lower tip rates, likely because many Queens trips are airport-related and have longer distances.
* Tip rates varied by pickup hour and tended to be higher in late afternoon and evening periods.
* The zone/hour controlled comparison showed that holiday and baseline differences vary by location and hour.

## Environment Note

The local PySpark demo was developed using the Dockerized PySpark environment provided in the CS675 course starter materials. This repository focuses on my project code, result files, Athena SQL queries, and dashboard. It does not duplicate the full course starter environment.

To reproduce the local PySpark analysis, place this project inside the `work/` directory of the course-provided `code-starter` folder and run the documented Docker command.

The cloud-scale analysis is documented separately through the SQL files in `cloud_queries/`, which can be run in Amazon Athena after setting up the S3 data folders and Athena external tables.

## Limitations

This project is descriptive, not causal.

Holiday and baseline trips may differ by pickup borough, pickup hour, airport direction, fare size, and trip purpose. Because of that, the project does not claim that the holiday season directly causes riders to tip more or less.

Instead, the project shows observed tipping patterns and uses additional breakdowns to better understand how trip composition affects the holiday vs non-holiday comparison.

## Final Takeaway

The project shows that holiday-season taxi tipping behavior is different from normal baseline behavior, but the difference is small and depends heavily on trip composition.

The main conclusion is:

> Holiday tipping differences are subtle and should be analyzed through controlled comparisons, not simple averages alone.

```
```
