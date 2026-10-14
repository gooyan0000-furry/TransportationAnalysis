import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path


# ============================================================
# 1. PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Shenzhen Metro Intelligence",
    page_icon="🚇",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# 2. CUSTOM CSS
# ============================================================

st.markdown("""
<style>

    .main {
        background-color: #F7F9FC;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    h1 {
        color: #17365D;
        font-weight: 750;
    }

    h2, h3 {
        color: #203B59;
    }

    [data-testid="stMetric"] {
        background-color: white;
        border: 1px solid #E1E8F0;
        border-radius: 12px;
        padding: 20px;
    }

    [data-testid="stMetricValue"] {
        color: #1768AC;
    }

    .section-description {
        color: #64748B;
        font-size: 15px;
    }

</style>
""", unsafe_allow_html=True)


# ============================================================
# 3. LOAD DATA
# ============================================================

DATA_PATH = Path(__file__).resolve().parent / "sz_2017.csv"

REQUIRED_COLUMNS = [
    "lineid_o",
    "stationid_o",
    "stationname_o",
    "lineid_d",
    "stationid_d",
    "stationname_d",
    "d_time",
    "count"
]


@st.cache_data
def load_data(file_path):

    df = pd.read_csv(file_path)

    df.columns = df.columns.str.strip()

    missing_columns = [
        col for col in REQUIRED_COLUMNS
        if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing columns: {missing_columns}"
        )

    df = df[REQUIRED_COLUMNS].copy()

    # Convert numerical columns
    df["count"] = pd.to_numeric(
        df["count"], errors="coerce"
    )

    df["d_time"] = pd.to_numeric(
        df["d_time"], errors="coerce"
    )

    # Remove invalid records
    df = df.dropna(
        subset=[
            "stationname_o",
            "stationname_d",
            "count",
            "d_time"
        ]
    )

    df = df[
        (df["count"] > 0) &
        (df["d_time"] >= 0)
    ].copy()

    # Ensure station and line labels are strings
    for col in [
        "lineid_o",
        "lineid_d",
        "stationid_o",
        "stationid_d",
        "stationname_o",
        "stationname_d"
    ]:
        df[col] = df[col].astype(str).str.strip()

    # Weighted travel-time contribution
    df["weighted_time"] = (
        df["d_time"] * df["count"]
    )

    return df


if not DATA_PATH.exists():

    st.error(
        "Data file not found. "
        "Please upload sz_2017.csv to the same "
        "GitHub folder as app.py."
    )

    st.stop()


try:
    df = load_data(DATA_PATH)

except Exception as e:

    st.error(f"Error loading dataset: {e}")

    st.stop()


if df.empty:
    st.error("The dataset contains no valid passenger records.")
    st.stop()


# ============================================================
# 4. HEADER
# ============================================================

st.title("🚇 Shenzhen Metro Intelligence")

st.markdown(
    """
    **Passenger Demand & Network Insights**

    An interactive dashboard for metro planning managers
    to identify high-demand stations, understand passenger
    travel patterns, and prioritize operational reviews.
    """
)

st.divider()


# ============================================================
# 5. SIDEBAR FILTERS
# ============================================================

st.sidebar.title("🎛️ Dashboard Controls")

st.sidebar.markdown(
    "Explore passenger demand across the Shenzhen metro network."
)

origin_lines = sorted(
    df["lineid_o"].unique().tolist()
)

destination_lines = sorted(
    df["lineid_d"].unique().tolist()
)

selected_origin_lines = st.sidebar.multiselect(
    "Origin Metro Lines",
    options=origin_lines,
    default=origin_lines
)

selected_destination_lines = st.sidebar.multiselect(
    "Destination Metro Lines",
    options=destination_lines,
    default=destination_lines
)

top_n = st.sidebar.slider(
    "Number of stations / routes",
    min_value=5,
    max_value=20,
    value=10
)

# Apply filters
filtered_df = df[
    df["lineid_o"].isin(selected_origin_lines)
    &
    df["lineid_d"].isin(selected_destination_lines)
].copy()


if filtered_df.empty:

    st.warning(
        "No passenger records match the selected filters."
    )

    st.stop()


st.sidebar.divider()

st.sidebar.markdown(
    """
    **Dataset Information**

    - City: Shenzhen, China
    - Dataset: Metro smart-card journey records
    - Period: October 2017
    - Source: Navi-Complexity research dataset

    **Important:** This dataset contains aggregated
    journeys, not individual daily timestamps.
    """
)


# ============================================================
# 6. KPI CALCULATIONS
# ============================================================

total_trips = filtered_df["count"].sum()

avg_travel_time = (
    filtered_df["weighted_time"].sum()
    / total_trips
)

origin_flow = (
    filtered_df
    .groupby(
        "stationname_o",
        as_index=False
    )["count"]
    .sum()
    .sort_values(
        "count",
        ascending=False
    )
)

destination_flow = (
    filtered_df
    .groupby(
        "stationname_d",
        as_index=False
    )["count"]
    .sum()
    .sort_values(
        "count",
        ascending=False
    )
)

busiest_station = origin_flow.iloc[0]["stationname_o"]

busiest_station_trips = origin_flow.iloc[0]["count"]

busiest_station_share = (
    busiest_station_trips / total_trips * 100
)


# ============================================================
# 7. KPI DISPLAY
# ============================================================

st.subheader("📊 Network Overview")

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        label="Total Passenger Journeys",
        value=f"{total_trips:,.0f}"
    )

    st.caption(
        "Total recorded journeys in the selected data."
    )


with col2:

    st.metric(
        label="Average Journey Time",
        value=f"{avg_travel_time:.1f} min"
    )

    st.caption(
        "Weighted by the number of passenger journeys."
    )


with col3:

    st.metric(
        label="Busiest Origin Share",
        value=f"{busiest_station_share:.1f}%"
    )

    st.caption(
        f"Highest origin demand: {busiest_station}"
    )


st.divider()


# ============================================================
# 8. CHART 1
# STATION PASSENGER DEMAND
# ============================================================

st.subheader(
    "01 | Which Stations Carry the Greatest Passenger Demand?"
)

st.markdown(
    """
    This chart compares origin and destination passenger
    volumes at the busiest stations.

    **Management decision:** Identify stations that should
    receive priority for capacity reviews and field inspections.
    """
)


# Calculate station-level total flows
origin_station = (
    filtered_df
    .groupby("stationname_o")["count"]
    .sum()
    .rename("Origin Trips")
)

destination_station = (
    filtered_df
    .groupby("stationname_d")["count"]
    .sum()
    .rename("Destination Trips")
)

station_flow = pd.concat(
    [origin_station, destination_station],
    axis=1
).fillna(0)

station_flow["Total Endpoint Activity"] = (
    station_flow["Origin Trips"]
    + station_flow["Destination Trips"]
)

station_flow = (
    station_flow
    .sort_values(
        "Total Endpoint Activity",
        ascending=False
    )
    .head(top_n)
    .reset_index()
    .rename(
        columns={"index": "Station"}
    )
)

station_long = station_flow.melt(
    id_vars=["Station"],
    value_vars=[
        "Origin Trips",
        "Destination Trips"
    ],
    var_name="Flow Type",
    value_name="Passenger Journeys"
)


fig_station = px.bar(

    station_long,

    x="Passenger Journeys",

    y="Station",

    color="Flow Type",

    orientation="h",

    barmode="group",

    color_discrete_map={
        "Origin Trips": "#2878B5",
        "Destination Trips": "#20BFA9"
    },

    title="Passenger Demand at Major Metro Stations",

    labels={
        "Passenger Journeys": "Passenger Journeys",
        "Station": "Metro Station"
    },

    hover_data={
        "Passenger Journeys": ":,.0f"
    }

)

fig_station.update_layout(

    template="plotly_white",

    height=max(450, top_n * 40),

    legend_title_text="Passenger Flow",

    margin=dict(
        l=20,
        r=20,
        t=60,
        b=20
    ),

    font=dict(
        size=13
    )

)

fig_station.update_yaxes(
    categoryorder="array",
    categoryarray=station_flow["Station"].iloc[::-1].tolist()
)

st.plotly_chart(
    fig_station,
    use_container_width=True
)


# Station imbalance calculation
station_flow["Flow Imbalance (%)"] = (
    abs(
        station_flow["Origin Trips"]
        - station_flow["Destination Trips"]
    )
    /
    station_flow["Total Endpoint Activity"].replace(0, float("nan"))
    * 100
)

station_flow["Flow Imbalance (%)"] = (
    station_flow["Flow Imbalance (%)"].fillna(0)
)

most_imbalanced = (
    station_flow
    .sort_values(
        "Flow Imbalance (%)",
        ascending=False
    )
    .iloc[0]
)

st.info(
    f"🔎 **Operational insight:** Among the displayed stations, "
    f"**{most_imbalanced['Station']}** has the largest "
    f"relative origin–destination imbalance "
    f"({most_imbalanced['Flow Imbalance (%)']:.1f}%). "
    f"This may warrant further investigation, but the "
    f"aggregated data cannot establish the cause."
)


st.divider()


# ============================================================
# 9. CHART 2
# MOST IMPORTANT OD CORRIDORS
# ============================================================

st.subheader(
    "02 | Which Travel Corridors Dominate Passenger Demand?"
)

st.markdown(
    """
    Not all station-to-station journeys attract equal demand.

    This chart highlights the most frequently used
    origin–destination (OD) pairs.

    **Management decision:** Identify major travel corridors
    that deserve further capacity and service reviews.
    """
)


# Aggregate OD journeys
od_flow = (
    filtered_df
    .groupby(
        [
            "stationname_o",
            "stationname_d"
        ],
        as_index=False
    )
    .agg(
        Passenger_Journeys=("count", "sum"),
        Weighted_Time=("weighted_time", "sum")
    )
)

od_flow["Average Journey Time"] = (
    od_flow["Weighted_Time"]
    /
    od_flow["Passenger_Journeys"]
)

od_flow["Route"] = (
    od_flow["stationname_o"]
    + " → "
    + od_flow["stationname_d"]
)

top_routes = (
    od_flow
    .sort_values(
        "Passenger_Journeys",
        ascending=False
    )
    .head(top_n)
    .copy()
)


fig_routes = px.bar(

    top_routes,

    x="Passenger_Journeys",

    y="Route",

    color="Average Journey Time",

    orientation="h",

    color_continuous_scale=[
        "#20BFA9",
        "#2878B5",
        "#F2A541"
    ],

    title="Highest-Demand Origin–Destination Corridors",

    labels={
        "Passenger_Journeys": "Passenger Journeys",
        "Route": "Origin → Destination",
        "Average Journey Time": "Avg. Time (min)"
    },

    hover_data={
        "Passenger_Journeys": ":,.0f",
        "Average Journey Time": ":.1f"
    }

)

fig_routes.update_layout(

    template="plotly_white",

    height=max(450, top_n * 45),

    margin=dict(
        l=20,
        r=20,
        t=60,
        b=20
    )

)

fig_routes.update_yaxes(
    categoryorder="total ascending"
)

st.plotly_chart(
    fig_routes,
    use_container_width=True
)


top_route = top_routes.iloc[0]

st.info(
    f"🔎 **Operational insight:** The highest-demand "
    f"directional OD pair is "
    f"**{top_route['Route']}**, representing "
    f"**{top_route['Passenger_Journeys']:,.0f} journeys**, "
    f"with a weighted average journey time of "
    f"**{top_route['Average Journey Time']:.1f} minutes**."
)


st.divider()


# ============================================================
# 10. MANAGEMENT PRIORITIES
# ============================================================

st.subheader("🎯 Management Action Priorities")

st.markdown(
    """
    Based on the selected passenger demand records,
    the following areas deserve further operational attention.
    """
)

priority_col1, priority_col2 = st.columns(2)


with priority_col1:

    st.markdown("#### 🚉 Priority Station")

    st.success(
        f"""
        **{busiest_station}**

        Recorded origin journeys:
        **{busiest_station_trips:,.0f}**

        Suggested action:
        Review station capacity, passenger circulation,
        and platform operations.
        """
    )


with priority_col2:

    st.markdown("#### 🚆 Priority Travel Corridor")

    st.warning(
        f"""
        **{top_route['Route']}**

        Recorded journeys:
        **{top_route['Passenger_Journeys']:,.0f}**

        Suggested action:
        Investigate demand concentration and
        consider whether further service-capacity
        analysis is required.
        """
    )


# ============================================================
# 11. DOWNLOAD DATA
# ============================================================

st.divider()

st.subheader("📥 Download Analysis Results")

st.markdown(
    "Download aggregated station and OD statistics "
    "for further analysis."
)

download_col1, download_col2 = st.columns(2)


with download_col1:

    station_csv = station_flow.to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        label="Download Station Statistics",
        data=station_csv,
        file_name="station_statistics.csv",
        mime="text/csv"
    )


with download_col2:

    od_csv = od_flow.to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        label="Download OD Statistics",
        data=od_csv,
        file_name="od_statistics.csv",
        mime="text/csv"
    )


# ============================================================
# 12. DATA LIMITATIONS
# ============================================================

st.divider()

with st.expander("📚 Data Source & Limitations"):

    st.markdown(
        """
        **Source**

        Shenzhen metro smart-card data from the
        Navi-Complexity research repository.

        https://github.com/Jzjsnow/navi-complexity

        **Data period**

        October 2017.

        **Unit of analysis**

        Aggregated journeys by origin station,
        destination station, and journey duration.

        **Important limitations**

        1. The dataset does not contain individual
           departure timestamps.

        2. Daily and hourly passenger patterns
           cannot be reconstructed.

        3. High passenger demand does not necessarily
           indicate congestion or inadequate capacity.

        4. OD passenger counts represent observed
           journeys rather than physical train loads
           on individual track segments.

        5. The dashboard supports prioritization
           of further investigation rather than
           immediate service-change decisions.

        **Refresh frequency**

        In a real operational setting, journey records
        should ideally be refreshed daily.

        Because this project uses a historical
        research dataset, the current dashboard
        is a static analysis rather than
        a real-time monitoring system.
        """
    )


# ============================================================
# 13. FOOTER
# ============================================================

st.divider()

st.caption(
    "Shenzhen Metro Intelligence | "
    "BANA409 Data App Project | "
    "Built with Python, Pandas, Plotly and Streamlit"
)
