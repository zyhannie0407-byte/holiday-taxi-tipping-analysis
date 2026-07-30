import streamlit as st
import pandas as pd
import glob
import os

st.set_page_config(
    page_title="Holiday Taxi Tipping Dashboard",
    layout="wide"
)

st.title("Holiday Taxi Tipping Dashboard")
st.caption("Local demo using NYC Yellow Taxi data: March 2025 baseline vs December 2025 holiday season")

BASE_PATH = "work/results/holiday_tipping"

def read_spark_csv(folder_name):
    folder_path = os.path.join(BASE_PATH, folder_name)
    csv_files = glob.glob(os.path.join(folder_path, "*.csv"))
    if not csv_files:
        st.error(f"No CSV file found in {folder_path}")
        return pd.DataFrame()
    return pd.read_csv(csv_files[0])

period_df = read_spark_csv("credit_card_holiday_vs_normal")
borough_df = read_spark_csv("credit_card_tip_rate_by_borough")
airport_df = read_spark_csv("credit_card_airport_vs_non_airport")
hour_df = read_spark_csv("credit_card_tip_rate_by_hour")

st.header("1. Key Metrics")

if not period_df.empty:
    normal = period_df[period_df["period"] == "Normal Baseline"].iloc[0]
    holiday = period_df[period_df["period"] == "Holiday Season"].iloc[0]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Holiday avg tip amount",
        f"${holiday['avg_tip_amount']:.2f}",
        f"${holiday['avg_tip_amount'] - normal['avg_tip_amount']:.2f} vs baseline"
    )

    col2.metric(
        "Holiday avg tip rate",
        f"{holiday['avg_tip_rate'] * 100:.2f}%",
        f"{(holiday['avg_tip_rate'] - normal['avg_tip_rate']) * 100:.2f} pts vs baseline"
    )

    col3.metric(
        "Holiday credit-card trips",
        f"{int(holiday['trip_count']):,}"
    )

    col4.metric(
        "Baseline credit-card trips",
        f"{int(normal['trip_count']):,}"
    )

st.header("2. Holiday vs Baseline Tipping")

if not period_df.empty:
    display_df = period_df.copy()
    display_df["avg_tip_rate_percent"] = display_df["avg_tip_rate"] * 100

    st.dataframe(display_df, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Average Tip Amount")
        st.bar_chart(display_df.set_index("period")["avg_tip_amount"])

    with col2:
        st.subheader("Average Tip Rate (Percentage)")
        st.bar_chart(display_df.set_index("period")["avg_tip_rate_percent"])

st.header("3. Tip Rate by Borough")

if not borough_df.empty:
    borough_display = borough_df.copy()
    borough_display = borough_display[
        borough_display["pickup_borough"].notna()
    ]

    borough_display["avg_tip_rate_percent"] = borough_display["avg_tip_rate"] * 100

    pivot = borough_display.pivot_table(
        index="pickup_borough",
        columns="period",
        values="avg_tip_rate_percent"
    )

    st.subheader("Heatmap-style table: darker color = higher tip rate")
    st.dataframe(
        pivot.style.background_gradient(cmap="YlOrRd").format("{:.2f}%"),
        use_container_width=True
    )

st.header("4. Airport vs Non-Airport Trips")

if not airport_df.empty:
    airport_display = airport_df.copy()
    airport_display["avg_tip_rate_percent"] = airport_display["avg_tip_rate"] * 100

    st.dataframe(airport_display, use_container_width=True)

    st.subheader("Average Tip Amount by Trip Type")
    chart_df = airport_display.pivot_table(
        index="airport_trip_flag",
        columns="period",
        values="avg_tip_amount"
    )
    st.bar_chart(chart_df)

st.header("5. Tip Rate by Pickup Hour")

if not hour_df.empty:
    hour_display = hour_df.copy()
    hour_display["avg_tip_rate_percent"] = hour_display["avg_tip_rate"] * 100

    selected_period = st.selectbox(
        "Select period",
        sorted(hour_display["period"].unique())
    )

    filtered_hour = hour_display[hour_display["period"] == selected_period]

    st.line_chart(
        filtered_hour.set_index("pickup_hour")["avg_tip_rate_percent"]
    )

st.header("Main Insight")

st.info(
    "In the local demo, December holiday trips had a higher average tip amount, "
    "but a lower average tip rate than the March baseline. This suggests that "
    "holiday riders paid and tipped more in dollars, but were not necessarily "
    "more generous as a percentage of fare."
)

st.header("Next Step")

st.write(
    "For the final project, I will expand the holiday period to November 20, 2025 "
    "through January 10, 2026, scale the data in AWS, and add a geospatial "
    "visualization where NYC pickup zones are shaded by average tip rate."
)