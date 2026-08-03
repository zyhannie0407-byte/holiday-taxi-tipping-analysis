# Cloud-Scale Analysis of Holiday vs Non-Holiday NYC Taxi Tipping

This project is my final submission for **CS675 Big Data: Management & Analytics**.

The analysis examines whether NYC Yellow Taxi riders tip more generously during holiday periods than during normal baseline periods. It also considers differences in trip composition, including airport direction, pickup borough, pickup hour, fare size, and trip distance.

## Project Question

Do NYC taxi riders tip more generously during the holiday season compared with normal non-holiday periods?

## Quick Summary

This project combines:

- a local PySpark demo for pipeline validation
- a cloud-scale analysis using Amazon S3 and Amazon Athena
- a Streamlit dashboard for exploring the results
- a standalone Docker setup so the dashboard and Python environment can be reproduced from this repository

The core idea is to measure tipping behavior using a standardized metric rather than relying on raw dollar amounts alone.

## Main Metric

The main metric is:

```text
tip rate = tip amount / fare amount
```

I use tip rate instead of average dollar tips because larger or more expensive trips naturally produce higher tip amounts. For example, airport trips often have higher fares and therefore higher dollar tips even when the rider is not tipping more generously as a percentage of fare.

This analysis focuses on **credit-card trips only** because cash tips are not reliably captured in the taxi trip records.

## Data Sources

This project uses:

- NYC TLC Yellow Taxi Trip Records in Parquet format
- NYC Taxi Zone Lookup Table in CSV format

The local demo uses a smaller sample:

- Normal baseline: March 2025
- Holiday-season sample: December 2025

The cloud-scale version uses multi-year post-COVID Yellow Taxi data stored in Amazon S3 and queried with Amazon Athena.

The raw input files are not stored directly in this GitHub repository because the full dataset is large. The project instead includes summarized output files in `results/` and `cloud_results/`.

## Tools Used

- Python
- PySpark
- Docker
- Pandas
- Streamlit
- Plotly
- Amazon S3
- Amazon Athena
- GitHub

## Repository Structure

```text
.
├── README.md
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
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
├── results/
│   └── holiday_tipping/
└── .gitignore
```

## Reproducible Docker Environment

This repository includes a standalone Docker setup so the project environment can be reproduced without relying on another code base.

The Docker setup includes:

- `Dockerfile`
- `docker-compose.yml`
- `requirements.txt`

The container installs the Python dependencies needed for the dashboard and project code, including PySpark, Pandas, Streamlit, Plotly, PyArrow, and Matplotlib.

### Run the Dockerized Dashboard

Start Docker Desktop first.

From the root of this repository, run:

```bash
docker compose -f docker-compose.yml up --build
```

Then open the dashboard in a browser:

```text
http://localhost:8501
```

This runs the Streamlit dashboard from the self-contained Docker environment included in this repository.

To stop the container, press:

```text
Control + C
```

## Local PySpark Demo

The local version validates the end-to-end pipeline and dashboard logic before scaling the analysis to AWS.

The local PySpark pipeline includes these steps:

1. Load NYC Yellow Taxi Parquet files.
2. Create study-period labels.
3. Run EDA before filtering.
4. Apply cleaning rules.
5. Join trip data with the taxi zone lookup table.
6. Generate result CSV files by group.
7. Feed the results into the Streamlit dashboard.

The summarized local output files are included under:

```text
results/holiday_tipping/
```

The local PySpark script is:

```text
holiday_tipping_analysis.py
```

The dashboard script is:

```text
holiday_tipping_dashboard.py
```

## Cloud-Scale Athena Workflow

The cloud-scale version stores the data in Amazon S3 and uses Amazon Athena for query execution.

### S3 Structure

```text
s3://cs675-holiday-nyc-taxi-yuhanzhu-288834682554-us-east-1-an/
├── raw/
│   └── yellow_taxi/
├── lookup/
└── results/
```

### Athena Tables

The cloud setup creates the following tables:

- `holiday_taxi_tipping.yellow_taxi_trips`
- `holiday_taxi_tipping.taxi_zone_lookup`

The SQL files in `cloud_queries/` document how to recreate the cloud analysis.

Athena supports one SQL statement per query execution, so the setup files should be run one at a time.

## Cloud-Scale Requirement

The Athena row-count query returned:

```text
128,202,548 rows
```

This satisfies the project requirement of analyzing at least 100 million rows at cloud scale.

## Cloud Analytical Queries

The cloud analysis includes:

1. total row count
2. holiday vs normal baseline tip-rate comparison
3. airport inbound, airport outbound, and non-airport comparison
4. tip rate by pickup hour
5. tip rate by pickup borough
6. zone/hour controlled comparison

The query outputs are saved in the `cloud_results/` folder and visualized in the Streamlit dashboard.

## Main Findings

The local demo and cloud-scale version produced slightly different results because the local demo compares March 2025 with December 2025, while the cloud version uses a much larger multi-year dataset.

### Local Demo Finding

In the local demo, December holiday trips had a higher average dollar tip than the March baseline, but a lower average tip rate. This suggests riders paid more in dollars, but not necessarily more generously relative to fare.

### Cloud-Scale Finding

In the cloud-scale Athena analysis, holiday-season trips had a slightly higher average tip rate than normal baseline trips, but the difference was small.

This suggests that holiday-season tipping generosity may exist, but it is subtle.

### Supporting Findings

- Airport trips had much higher dollar tips because fares were higher, but their tip rates were lower than non-airport trips.
- Manhattan had the strongest and most stable tip rate.
- Queens had higher dollar tips but lower tip rates, likely because many Queens trips are airport-related and involve longer distances.
- Tip rates varied by pickup hour and tended to be higher in late afternoon and evening periods.
- The zone/hour controlled comparison showed that holiday and baseline differences vary significantly by location and hour.

## Limitations

This project is descriptive rather than causal.

Holiday and baseline trips may differ by pickup borough, pickup hour, airport direction, fare size, and trip purpose. Because of that, the project does not claim that the holiday season directly causes riders to tip more or less.

Instead, it shows observed tipping patterns and uses additional breakdowns to better understand how trip composition affects the holiday vs non-holiday comparison.

## Final Takeaway

The project shows that holiday-season taxi tipping behavior differs from normal baseline behavior, but the difference is small and depends heavily on trip composition.

The main conclusion is:

> Holiday tipping differences are subtle and should be analyzed through controlled comparisons rather than simple averages alone.