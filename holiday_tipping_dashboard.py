import streamlit as st
import pandas as pd
import glob
import os
from pathlib import Path
import plotly.express as px


# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(
    page_title="Cloud-Scale Analysis of Holiday vs Non-Holiday NYC Taxi Tipping",
    layout="wide"
)

st.title("Cloud-Scale Analysis of Holiday vs Non-Holiday NYC Taxi Tipping")
st.caption(
    "Comparing NYC Yellow Taxi tipping behavior across local PySpark demo results and cloud-scale Athena analysis"
)


# -----------------------------
# Paths
# -----------------------------
BASE_DIR = Path(__file__).parent

# Local PySpark result files
LOCAL_RESULTS_PATH = BASE_DIR / "results" / "holiday_tipping"

# Cloud Athena result files
CLOUD_RESULTS_PATH = BASE_DIR / "cloud_results"


# -----------------------------
# Helper functions
# -----------------------------
def read_spark_csv(folder_name):
    """
    Read the single Spark output CSV from a result folder.
    Spark writes result folders with part-*.csv files, so this function finds the CSV automatically.
    """
    folder_path = LOCAL_RESULTS_PATH / folder_name
    csv_files = glob.glob(str(folder_path / "*.csv"))

    if not csv_files:
        st.error(f"No CSV file found in {folder_path}")
        return pd.DataFrame()

    return pd.read_csv(csv_files[0])


def read_cloud_csv(file_name):
    """
    Read an Athena-exported CSV from the cloud_results folder.
    """
    file_path = CLOUD_RESULTS_PATH / file_name

    if not file_path.exists():
        st.error(f"Cloud result file not found: {file_path}")
        return pd.DataFrame()

    return pd.read_csv(file_path)


# -----------------------------
# Load local PySpark results
# -----------------------------
period_df = read_spark_csv("credit_card_holiday_vs_normal")
borough_df = read_spark_csv("credit_card_tip_rate_by_borough")
airport_df = read_spark_csv("credit_card_airport_vs_non_airport")
hour_df = read_spark_csv("credit_card_tip_rate_by_hour")


# ============================================================
# Local Demo Section
# ============================================================
st.header("Local Demo Results: PySpark + Streamlit")
st.markdown(
    """
    This section shows the **local demo version** of the project.  
    The local demo uses NYC Yellow Taxi data for **March 2025 as the normal baseline**
    and **December 2025 as the holiday-season sample**.

    The goal of the local demo is to validate the PySpark data pipeline and dashboard logic
    before scaling the analysis to AWS.
    """
)


# -----------------------------
# Local key metrics
# -----------------------------
st.subheader("Local Demo: Key Metrics")

if not period_df.empty:
    normal = period_df[period_df["period"] == "Normal Baseline"].iloc[0]
    holiday = period_df[period_df["period"] == "Holiday Season"].iloc[0]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Local holiday avg tip amount",
        f"${holiday['avg_tip_amount']:.2f}",
        f"${holiday['avg_tip_amount'] - normal['avg_tip_amount']:.2f} vs local baseline"
    )

    col2.metric(
        "Local holiday avg tip rate",
        f"{holiday['avg_tip_rate'] * 100:.2f}%",
        f"{(holiday['avg_tip_rate'] - normal['avg_tip_rate']) * 100:.2f} pts vs local baseline"
    )

    col3.metric(
        "Local holiday credit-card trips",
        f"{int(holiday['trip_count']):,}"
    )

    col4.metric(
        "Local baseline credit-card trips",
        f"{int(normal['trip_count']):,}"
    )


# -----------------------------
# Local holiday vs baseline
# -----------------------------
st.subheader("Local Demo: Holiday vs Baseline Tipping")

if not period_df.empty:
    display_df = period_df.copy()
    display_df["avg_tip_rate_percent"] = display_df["avg_tip_rate"] * 100

    st.dataframe(display_df, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Local average tip amount**")
        st.bar_chart(display_df.set_index("period")["avg_tip_amount"])

    with col2:
        st.markdown("**Local average tip rate**")
        st.bar_chart(display_df.set_index("period")["avg_tip_rate_percent"])

    st.info(
        "Local demo finding: December holiday trips had a higher average dollar tip than the March baseline, "
        "but a lower average tip rate. This suggests that in the local sample, riders paid more in dollars "
        "but were not necessarily more generous relative to the fare."
    )


# -----------------------------
# Local borough analysis
# -----------------------------
st.subheader("Local Demo: Tip Rate by Borough")

if not borough_df.empty:
    borough_display = borough_df.copy()
    borough_display = borough_display[borough_display["pickup_borough"].notna()]
    borough_display["avg_tip_rate_percent"] = borough_display["avg_tip_rate"] * 100

    pivot = borough_display.pivot_table(
        index="pickup_borough",
        columns="period",
        values="avg_tip_rate_percent"
    )

    st.markdown("**Local heatmap-style table: darker color = higher tip rate**")
    st.dataframe(
        pivot.style.background_gradient(cmap="YlOrRd").format("{:.2f}%"),
        use_container_width=True
    )

    st.info(
        "Local demo finding: Manhattan showed the strongest tip rates in both periods. "
        "Queens had much higher average dollar tips, largely because many Queens trips are airport-related "
        "and have higher fares."
    )


# -----------------------------
# Local airport analysis
# -----------------------------
st.subheader("Local Demo: Airport vs Non-Airport Trips")

if not airport_df.empty:
    airport_display = airport_df.copy()
    airport_display["avg_tip_rate_percent"] = airport_display["avg_tip_rate"] * 100

    st.dataframe(airport_display, use_container_width=True)

    chart_df = airport_display.pivot_table(
        index="airport_trip_flag",
        columns="period",
        values="avg_tip_rate_percent"
    )

    st.markdown("**Local average tip rate by trip type**")
    st.bar_chart(chart_df)

    st.info(
        "Local demo finding: Airport trips had much higher average dollar tips, but lower tip rates "
        "than non-airport trips. This means the higher airport tips were mainly driven by higher fares, "
        "not stronger tipping generosity."
    )


# -----------------------------
# Local hourly analysis
# -----------------------------
st.subheader("Local Demo: Tip Rate by Pickup Hour")

if not hour_df.empty:
    hour_display = hour_df.copy()
    hour_display["avg_tip_rate_percent"] = hour_display["avg_tip_rate"] * 100

    selected_period = st.selectbox(
        "Select local demo period",
        sorted(hour_display["period"].unique())
    )

    filtered_hour = hour_display[hour_display["period"] == selected_period]

    st.line_chart(
        filtered_hour.set_index("pickup_hour")["avg_tip_rate_percent"]
    )

    st.info(
        "Local demo finding: Tip rates vary by pickup hour, which shows why time of day should be considered "
        "when comparing holiday and baseline tipping behavior."
    )


# ============================================================
# Cloud-Scale Athena Section
# ============================================================
st.header("Cloud-Scale Athena Results")
st.markdown(
    """
    This section shows the **cloud-scale version** of the project.  
    These results were generated from Amazon Athena using NYC Yellow Taxi Parquet files stored in Amazon S3.

    The Athena table contains **128,202,548 yellow taxi trip records**, satisfying the 100M+ row requirement.

    The cloud analysis focuses on **credit-card trips only** because cash tips are not reliably captured
    in the dataset.
    """
)


# -----------------------------
# Load cloud Athena results
# -----------------------------
holiday_cloud = read_cloud_csv("holiday_vs_baseline.csv")
airport_cloud = read_cloud_csv("airport_direction.csv")
hour_cloud = read_cloud_csv("tip_rate_by_hour.csv")
borough_cloud = read_cloud_csv("tip_rate_by_borough.csv")
control_cloud = read_cloud_csv("zone_hour_controlled_comparison.csv")


# -----------------------------
# Cloud holiday vs baseline
# -----------------------------
st.subheader("Cloud-Scale: Holiday vs Normal Baseline Tip Rate")

if not holiday_cloud.empty:
    fig = px.bar(
        holiday_cloud,
        x="study_period",
        y="avg_tip_rate",
        text="avg_tip_rate",
        title="Cloud-Scale Tip Rate: Holiday Season vs Normal Baseline",
    )
    fig.update_traces(texttemplate="%{text:.2%}", textposition="outside")
    fig.update_layout(
        yaxis_tickformat=".0%",
        xaxis_title="Study Period",
        yaxis_title="Average Tip Rate"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(holiday_cloud, use_container_width=True)

    st.info(
        "Cloud-scale finding: Holiday-season trips had a slightly higher average tip rate than normal baseline trips, "
        "but the difference was small. This suggests that holiday tipping generosity exists, but it is subtle."
    )


# -----------------------------
# Cloud airport direction
# -----------------------------
st.subheader("Cloud-Scale: Airport Direction and Tip Rate")

if not airport_cloud.empty:
    airport_display_cloud = airport_cloud[
        airport_cloud["airport_direction"] != "Airport-to-Airport"
    ]

    fig = px.bar(
        airport_display_cloud,
        x="airport_direction",
        y="avg_tip_rate",
        color="study_period",
        barmode="group",
        text="avg_tip_rate",
        title="Cloud-Scale Tip Rate by Airport Direction",
    )
    fig.update_traces(texttemplate="%{text:.2%}", textposition="outside")
    fig.update_layout(
        yaxis_tickformat=".0%",
        xaxis_title="Airport Direction",
        yaxis_title="Average Tip Rate"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(airport_cloud, use_container_width=True)

    st.info(
        "Cloud-scale finding: Airport trips had much higher dollar tips because fares were higher, "
        "but their tip rates were lower than non-airport trips. This confirms that tip rate is a better "
        "measure of generosity than raw tip amount."
    )


# -----------------------------
# Cloud hourly analysis
# -----------------------------
st.subheader("Cloud-Scale: Tip Rate by Pickup Hour")

if not hour_cloud.empty:
    fig = px.line(
        hour_cloud,
        x="pickup_hour",
        y="avg_tip_rate",
        color="study_period",
        markers=True,
        title="Cloud-Scale Hourly Tip Rate Pattern",
    )
    fig.update_layout(
        yaxis_tickformat=".0%",
        xaxis_title="Pickup Hour",
        yaxis_title="Average Tip Rate"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(hour_cloud, use_container_width=True)

    st.info(
        "Cloud-scale finding: Both holiday and baseline periods show similar hourly patterns. "
        "Tip rates tend to be lower in the early morning and higher in the late afternoon and evening."
    )


# -----------------------------
# Cloud borough analysis
# -----------------------------
st.subheader("Cloud-Scale: Tip Rate by Pickup Borough")

if not borough_cloud.empty:
    real_boroughs = ["Manhattan", "Queens", "Brooklyn", "Bronx", "Staten Island"]
    borough_display_cloud = borough_cloud[
        borough_cloud["borough"].isin(real_boroughs)
    ]

    fig = px.bar(
        borough_display_cloud,
        x="borough",
        y="avg_tip_rate",
        color="study_period",
        barmode="group",
        text="avg_tip_rate",
        title="Cloud-Scale Tip Rate by Pickup Borough",
    )
    fig.update_traces(texttemplate="%{text:.2%}", textposition="outside")
    fig.update_layout(
        yaxis_tickformat=".0%",
        xaxis_title="Pickup Borough",
        yaxis_title="Average Tip Rate"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(borough_cloud, use_container_width=True)

    st.info(
        "Cloud-scale finding: Manhattan had the strongest and most stable tip rate. "
        "Queens had higher dollar tips, but lower tip rates because many Queens trips are longer "
        "and airport-related."
    )


# -----------------------------
# Cloud controlled comparison
# -----------------------------
st.subheader("Cloud-Scale: Zone/Hour Controlled Comparison")

if not control_cloud.empty:
    st.markdown(
        """
        This query compares holiday and baseline tip rates within the same borough and pickup hour.
        It helps reduce trip-composition bias by comparing more similar groups of trips.
        """
    )

    st.dataframe(control_cloud, use_container_width=True)

    st.info(
        "Cloud-scale finding: The controlled comparison shows that holiday and baseline differences vary "
        "by location and hour. This supports the final conclusion that holiday tipping differences are subtle "
        "and should be interpreted with trip composition in mind."
    )


# ============================================================
# Final takeaway
# ============================================================
st.header("Final Takeaway")

st.success(
    "The local demo validates the PySpark pipeline and dashboard prototype, while the cloud-scale Athena analysis "
    "confirms the project at 128M+ rows. Overall, holiday-season trips show a slightly higher cloud-scale tip rate, "
    "but the difference is small. Tipping behavior is strongly shaped by trip composition, especially airport direction, "
    "pickup borough, and pickup hour."
)