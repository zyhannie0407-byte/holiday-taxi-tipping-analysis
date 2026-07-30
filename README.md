# Holiday Taxi Tipping Analysis

This is my final project for CS675 Big Data: Management & Analytics.

The project analyzes NYC Yellow Taxi tipping behavior during the holiday season compared with a normal baseline period. The analysis focuses on how tipping patterns differ by pickup borough, pickup zone, time of day, airport trip status, and trip type.

## Project Question

Do NYC taxi riders tip more generously during the holiday season?

## Local Demo Scope

- Normal baseline: March 2025
- Holiday season sample: December 2025
- Main metric: tip rate = tip amount / fare amount
- Main analysis subset: credit-card trips, because recorded tips are more reliable for card payments

## Tools Used

- PySpark
- Dockerized Spark
- Pandas
- Streamlit
- GitHub

## Files

- `holiday_tipping_analysis.py`: Spark pipeline for cleaning, joining, and analyzing taxi trip data
- `holiday_tipping_dashboard.py`: Streamlit dashboard using Spark-generated result CSVs
- `results/`: summarized result tables from the local Spark analysis

## Main Finding

In the local demo, December holiday trips had a higher average tip amount than the March baseline, but a lower average tip rate. This suggests that riders tipped more in dollars during the holiday season, but not necessarily more generously as a percentage of fare.

## Final Project Plan

For the final version, I plan to expand the holiday period to November 20, 2025 through January 10, 2026, scale the analysis using AWS S3 and Athena, and add a geospatial visualization showing NYC pickup zones shaded by average tip rate.
