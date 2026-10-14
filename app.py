import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
# 2. CUSTOM STYLE
# ============================================================

st.markdown("""
<style>

.block-container {
    padding-top: 1.8rem;
    padding-bottom: 2rem;
    max-width: 1450px;
}

h1 {
    color: #174A75;
    font-weight: 750;
}

h2, h3 {
    color: #24476B;
}

[data-testid="stMetric"] {
    background: #F5F9FD;
    border: 1px solid #DCE7F1;
    border-radius: 12px;
    padding: 18px;
}

[data-testid="stMetricValue"] {
    color: #1565A8;
}

[data-testid="stSidebar"] {
    background-color: #F5F8FC;
}

.insight-box {
    background-color: #F4F7FB;
    border-left: 4px solid #2478B7;
    padding: 15px 20px;
    border-radius: 6px;
    margin-top: 12px;
    margin-bottom: 18px;
}

.subtitle {
    color: #64748B;
    font-size: 16px;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# 3. DATA LOADING
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_PATH = BASE_DIR / "sz_2017.csv"

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
def load_data(path):

    df = pd.read_csv(path)

    df.columns = df.columns.str.strip()

    missing = [
        col for col in REQUIRED_COLUMNS
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    df = df[REQUIRED_COLUMNS].copy()

    df["count"] = pd.to_numeric(
        df["count"],
        errors="coerce"
    )

    df["d_time"] = pd.to_numeric(
        df["d_time"],
        errors="coerce"
    )

    df = df.dropna(
        subset=[
            "lineid_o",
            "lineid_d",
            "stationname_o",
            "stationname_d",
            "count",
            "d_time"
        ]
    )

    df = df[
        (df["count"] > 0)
        &
        (df["d_time"] >= 0)
    ].copy()

    df["weighted_time"] = (
        df["count"] * df["d_time"]
    )

    for col in [
        "lineid_o",
        "lineid_d",
        "stationid_o",
        "stationid_d",
        "stationname_o",
        "stationname_d"
    ]:
        df[col] = df[col].astype(str).str.strip()

    # Use line and station ID together to distinguish stations.
    df["origin_key"] = (
        df["lineid_o"]
        + " | "
        + df["stationid_o"]
    )

    df["destination_key"] = (
        df["lineid_d"]
        + " | "
        + df["stationid_d"]
    )

    return df


if not DATA_PATH.exists():

    st.error(
        "CSV file not found. "
        "Please place sz_2017.csv in the same "
        "GitHub directory as app.py."
    )

    st.stop()


try:

    df = load_data(DATA_PATH)

except Exception as error:

    st.error(
        f"Unable to load dataset: {error}"
    )

    st.stop()


if df.empty:

    st.error("No valid records were found.")

    st.stop()


# ============================================================
# 4. SESSION STATE
# ============================================================

origin_lines = sorted(
    df["lineid_o"].unique().tolist()
)

destination_lines = sorted(
    df["lineid_d"].unique().tolist()
)

max_duration = max(
    1,
    int(df["d_time"].max())
)

DEFAULT_FILTERS = {
    "origin_filter": "All Lines",
    "destination_filter": "All Lines",
    "duration_filter": (0, max_duration),
    "top_n_filter": 10
}


for key, value in DEFAULT_FILTERS.items():

    if key not in st.session_state:
        st.session_state[key] = value


def reset_filters():

    for key, value in DEFAULT_FILTERS.items():
        st.session_state[key] = value


# ============================================================
# 5. HEADER
# ============================================================

st.title("🚇 Shenzhen Metro Intelligence")

st.markdown(
    """
    <div class="subtitle">
    Passenger Demand, Travel Patterns & Operational Priorities
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    **Decision Maker:** Metro Planning & Operations Manager

    **Business Question:** Where should metro operators
    prioritize further capacity reviews and passenger-flow
    investigations?
    """
)

st.divider()


# ============================================================
# 6. SIDEBAR CONTROLS
# ============================================================

st.sidebar.title("🎛️ Dashboard Controls")

st.sidebar.markdown(
    "Use the filters below to explore metro travel demand."
)


st.sidebar.selectbox(
    "🚉 Origin Metro Line",
    options=["All Lines"] + origin_lines,
    key="origin_filter"
)


st.sidebar.selectbox(
    "🏁 Destination Metro Line",
    options=["All Lines"] + destination_lines,
    key="destination_filter"
)


st.sidebar.slider(
    "⏱️ Journey Duration (minutes)",
    min_value=0,
    max_value=max_duration,
    step=1,
    key="duration_filter"
)


st.sidebar.slider(
    "📊 Number of Stations / Routes",
    min_value=5,
    max_value=20,
    step=1,
    key="top_n_filter"
)


st.sidebar.button(
    "🔄 Reset All Filters",
    on_click=reset_filters,
    use_container_width=True
)


# ============================================================
# 7. APPLY FILTERS
# ============================================================

filtered_df = df.copy()

selected_origin = st.session_state["origin_filter"]

selected_destination = st.session_state["destination_filter"]

selected_duration = st.session_state["duration_filter"]

top_n = st.session_state["top_n_filter"]


if selected_origin != "All Lines":

    filtered_df = filtered_df[
        filtered_df["lineid_o"] == selected_origin
    ]


if selected_destination != "All Lines":

    filtered_df = filtered_df[
        filtered_df["lineid_d"] == selected_destination
    ]


filtered_df = filtered_df[
    filtered_df["d_time"].between(
        selected_duration[0],
        selected_duration[1]
    )
]


if filtered_df.empty:

    st.warning(
        "No journeys match these filters. "
        "Please change your selection."
    )

    st.stop()


# ============================================================
# 8. FILTER IMPACT
# ============================================================

original_trips = df["count"].sum()

filtered_trips = filtered_df["count"].sum()

retained_share = (
    filtered_trips / original_trips * 100
)


st.sidebar.divider()

st.sidebar.subheader("📈 Filter Impact")

st.sidebar.metric(
    "Selected Passenger Journeys",
    f"{filtered_trips:,.0f}"
)

st.sidebar.progress(
    min(1.0, float(retained_share / 100))
)

st.sidebar.caption(
    f"{retained_share:.1f}% of recorded journeys retained"
)

st.sidebar.markdown("**Current Selection**")

st.sidebar.write(
    f"Origin: {selected_origin}"
)

st.sidebar.write(
    f"Destination: {selected_destination}"
)

st.sidebar.write(
    f"Duration: {selected_duration[0]}–"
    f"{selected_duration[1]} min"
)


# ============================================================
# 9. KPI CALCULATIONS
# ============================================================

total_trips = filtered_df["count"].sum()

average_duration = (
    filtered_df["weighted_time"].sum()
    / total_trips
)


origin_flow = (
    filtered_df
    .groupby(
        ["origin_key", "stationname_o"],
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
        ["destination_key", "stationname_d"],
        as_index=False
    )["count"]
    .sum()
    .sort_values(
        "count",
        ascending=False
    )
)


busiest_origin = origin_flow.iloc[0]

busiest_origin_name = (
    busiest_origin["stationname_o"]
)

busiest_origin_trips = (
    busiest_origin["count"]
)

busiest_origin_share = (
    busiest_origin_trips
    / total_trips
    * 100
)


# ============================================================
# 10. KPI DISPLAY
# ============================================================

st.subheader("📊 Network Overview")

kpi1, kpi2, kpi3 = st.columns(3)


with kpi1:

    st.metric(
        "Passenger Journeys",
        f"{total_trips:,.0f}"
    )

    st.caption(
        "Total journeys matching the selected filters"
    )


with kpi2:

    st.metric(
        "Average Journey Duration",
        f"{average_duration:.1f} min"
    )

    st.caption(
        "Passenger-weighted average travel time"
    )


with kpi3:

    st.metric(
        "Busiest Origin Share",
        f"{busiest_origin_share:.1f}%"
    )

    st.caption(
        f"Highest origin demand: {busiest_origin_name}"
    )


st.divider()


# ============================================================
# 11. STATION FLOW ANALYSIS
# ============================================================

st.subheader(
    "01 | Where Is Passenger Demand Most Concentrated?"
)

st.markdown(
    """
    Compare origin and destination passenger demand
    across major metro stations.

    **Decision supported:** Identify stations that may
    require priority capacity assessments.
    """
)


origin_station = (
    filtered_df
    .groupby(
        ["origin_key", "stationname_o"],
        as_index=False
    )["count"]
    .sum()
    .rename(
        columns={
            "origin_key": "station_key",
            "stationname_o": "Station",
            "count": "Origin Trips"
        }
    )
)


destination_station = (
    filtered_df
    .groupby(
        ["destination_key", "stationname_d"],
        as_index=False
    )["count"]
    .sum()
    .rename(
        columns={
            "destination_key": "station_key",
            "stationname_d": "Station",
            "count": "Destination Trips"
        }
    )
)


station_flow = pd.merge(
    origin_station,
    destination_station,
    on="station_key",
    how="outer",
    suffixes=("_origin", "_destination")
)

station_flow["Station"] = (
    station_flow["Station_origin"]
    .fillna(station_flow["Station_destination"])
)

station_flow = station_flow[
    [
        "station_key",
        "Station",
        "Origin Trips",
        "Destination Trips"
    ]
].copy()

station_flow[
    ["Origin Trips", "Destination Trips"]
] = station_flow[
    ["Origin Trips", "Destination Trips"]
].fillna(0)

station_flow["Total Endpoint Activity"] = (
    station_flow["Origin Trips"]
    + station_flow["Destination Trips"]
)

station_flow["Imbalance (%)"] = (
    abs(
        station_flow["Origin Trips"]
        - station_flow["Destination Trips"]
    )
    / station_flow["Total Endpoint Activity"]
    * 100
)

# Distinguish stations with the same name but different keys.
station_flow["Station Label"] = (
    station_flow["Station"]
    + " ("
    + station_flow["station_key"]
    + ")"
)

station_flow = station_flow.sort_values(
    "Total Endpoint Activity",
    ascending=False
)


top_stations = station_flow.head(top_n).copy()


station_long = top_stations.melt(
    id_vars=["Station Label"],
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
    y="Station Label",
    color="Flow Type",
    orientation="h",
    barmode="group",
    color_discrete_map={
        "Origin Trips": "#2374AB",
        "Destination Trips": "#20BFA9"
    },
    title="Passenger Demand at Major Metro Stations",
    labels={
        "Station Label": "Metro Station"
    }
)


fig_station.update_layout(
    template="plotly_white",
    height=max(450, top_n * 45),
    legend_title_text="Passenger Flow",
    hovermode="closest",
    margin=dict(
        l=10,
        r=10,
        t=60,
        b=10
    )
)

fig_station.update_yaxes(
    categoryorder="array",
    categoryarray=top_stations[
        "Station Label"
    ].iloc[::-1].tolist()
)


st.plotly_chart(
    fig_station,
    use_container_width=True
)


# ------------------------------------------------------------
# Station insight
# ------------------------------------------------------------

most_imbalanced = (
    top_stations
    .sort_values(
        "Imbalance (%)",
        ascending=False
    )
    .iloc[0]
)


st.markdown(
    f"""
    <div class="insight-box">
    <b>Operational Insight</b><br>
    Among the displayed stations,
    <b>{most_imbalanced['Station']}</b>
    has the highest relative imbalance between
    origin and destination journeys
    ({most_imbalanced['Imbalance (%)']:.1f}%).
    This is a useful candidate for further investigation,
    although it does not by itself indicate congestion.
    </div>
    """,
    unsafe_allow_html=True
)


st.divider()


# ============================================================
# 12. OD CORRIDOR ANALYSIS
# ============================================================

st.subheader(
    "02 | Which Travel Corridors Carry the Most Journeys?"
)

st.markdown(
    """
    Identify the highest-demand origin–destination
    station pairs.

    **Decision supported:** Determine which travel
    corridors deserve further operational review.
    """
)


od_flow = (
    filtered_df
    .groupby(
        [
            "origin_key",
            "destination_key",
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
    / od_flow["Passenger_Journeys"]
)


od_flow["Route"] = (
    od_flow["stationname_o"]
    + " → "
    + od_flow["stationname_d"]
)

od_flow["Route Label"] = (
    od_flow["Route"]
    + " ("
    + od_flow["origin_key"]
    + " → "
    + od_flow["destination_key"]
    + ")"
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


fig_od = px.bar(
    top_routes,
    x="Passenger_Journeys",
    y="Route Label",
    color="Average Journey Time",
    orientation="h",
    color_continuous_scale=[
        "#20BFA9",
        "#2878B5",
        "#F2A541"
    ],
    title="Highest-Demand Origin–Destination Pairs",
    labels={
        "Passenger_Journeys": "Passenger Journeys",
        "Route Label": "Origin → Destination",
        "Average Journey Time": "Average Time (min)"
    },
    hover_data={
        "Passenger_Journeys": ":,.0f",
        "Average Journey Time": ":.1f"
    }
)


fig_od.update_layout(
    template="plotly_white",
    height=max(450, top_n * 45),
    margin=dict(
        l=10,
        r=10,
        t=60,
        b=10
    )
)

fig_od.update_yaxes(
    categoryorder="total ascending"
)


st.plotly_chart(
    fig_od,
    use_container_width=True
)


top_route = top_routes.iloc[0]


st.markdown(
    f"""
    <div class="insight-box">
    <b>Operational Insight</b><br>
    The highest-demand directional OD pair is
    <b>{top_route['Route']}</b>,
    accounting for
    <b>{top_route['Passenger_Journeys']:,.0f}</b>
    recorded journeys.
    Its weighted average journey duration is
    <b>{top_route['Average Journey Time']:.1f} minutes</b>.
    This suggests a useful corridor for capacity review,
    not proof that trains along the route are overcrowded.
    </div>
    """,
    unsafe_allow_html=True
)


st.divider()


# ============================================================
# 13. JOURNEY DURATION ANALYSIS
# ============================================================

st.subheader(
    "03 | How Are Passenger Journey Times Distributed?"
)

st.markdown(
    """
    Examine the distribution of journey durations.

    Unlike a conventional histogram that counts CSV rows,
    this chart weights each journey duration by the
    actual number of passenger trips.
    """
)


duration_bins = [0, 10, 20, 30, 45, 60, 90, float("inf")]

duration_labels = [
    "0–10",
    "10–20",
    "20–30",
    "30–45",
    "45–60",
    "60–90",
    "90+"
]


duration_df = filtered_df.copy()

duration_df["Duration Group"] = pd.cut(
    duration_df["d_time"],
    bins=duration_bins,
    labels=duration_labels,
    right=False
)


duration_summary = (
    duration_df
    .groupby(
        "Duration Group",
        observed=False
    )["count"]
    .sum()
    .reset_index()
)

duration_summary["Share (%)"] = (
    duration_summary["count"]
    / total_trips
    * 100
)


fig_duration = px.bar(
    duration_summary,
    x="Duration Group",
    y="Share (%)",
    color="Share (%)",
    color_continuous_scale=[
        "#20BFA9",
        "#2374AB",
        "#F2A541"
    ],
    text="Share (%)",
    title="Distribution of Passenger Journey Durations",
    labels={
        "Duration Group": "Journey Duration (minutes)",
        "Share (%)": "Share of Passenger Journeys (%)"
    }
)


fig_duration.update_traces(
    texttemplate="%{text:.1f}%",
    textposition="outside"
)

fig_duration.update_layout(
    template="plotly_white",
    height=420,
    coloraxis_showscale=False,
    margin=dict(
        l=10,
        r=10,
        t=60,
        b=10
    )
)


st.plotly_chart(
    fig_duration,
    use_container_width=True
)


dominant_duration = (
    duration_summary
    .sort_values(
        "count",
        ascending=False
    )
    .iloc[0]
)


st.caption(
    f"The largest duration category is "
    f"{dominant_duration['Duration Group']} minutes, "
    f"representing "
    f"{dominant_duration['Share (%)']:.1f}% "
    f"of selected journeys."
)


st.divider()


# ============================================================
# 14. MANAGEMENT PRIORITIES
# ============================================================

st.subheader("🎯 Management Priorities")

st.markdown(
    """
    The following recommendations are automatically
    updated according to your selected filters.
    """
)


col_left, col_right = st.columns(2)


with col_left:

    st.markdown("#### 🚉 Priority Station")

    st.markdown(
        f"""
        **{busiest_origin_name}**

        Recorded origin journeys:
        **{busiest_origin_trips:,.0f}**

        Share of selected journeys:
        **{busiest_origin_share:.1f}%**

        **Suggested action**

        Prioritize a station-level review of
        passenger circulation and platform capacity.
        """
    )


with col_right:

    st.markdown("#### 🚆 Priority OD Corridor")

    st.markdown(
        f"""
        **{top_route['Route']}**

        Recorded journeys:
        **{top_route['Passenger_Journeys']:,.0f}**

        Average journey time:
        **{top_route['Average Journey Time']:.1f} min**

        **Suggested action**

        Review demand concentration and investigate
        whether available service capacity matches
        observed travel demand.
        """
    )


st.divider()


# ============================================================
# 15. DATA DOWNLOAD
# ============================================================

st.subheader("📥 Download Analysis Results")

download_col1, download_col2 = st.columns(2)


with download_col1:

    station_csv = station_flow.to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        "Download Station Statistics",
        data=station_csv,
        file_name="station_analysis.csv",
        mime="text/csv",
        use_container_width=True
    )


with download_col2:

    od_csv = od_flow.to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        "Download OD Statistics",
        data=od_csv,
        file_name="od_analysis.csv",
        mime="text/csv",
        use_container_width=True
    )


# ============================================================
# 16. DATA LIMITATIONS
# ============================================================

st.divider()

with st.expander("📚 Dataset Information & Limitations"):

    st.markdown(
        """
        ### Data Source

        Shenzhen metro smart-card journey data.

        Source repository:

        https://github.com/Jzjsnow/navi-complexity

        ### Data Coverage

        - City: Shenzhen, China
        - Period: October 2017
        - Unit: Aggregated OD journeys
        - Main variables: Origin, destination,
          journey duration, and passenger count

        ### Important Limitations

        **1. No individual journey timestamps**

        The dataset cannot support hourly or
        daily passenger-flow analysis.

        **2. Demand is not the same as congestion**

        A station with many journeys is not
        necessarily overcrowded.

        **3. OD demand does not equal train load**

        An OD pair represents travel between
        two stations, not direct passenger counts
        on individual track segments.

        **4. Historical data**

        The dataset represents historical travel
        demand rather than current operating conditions.

        ### Recommended Refresh Frequency

        In a real operational environment,
        daily updates would help managers monitor
        changing travel demand.

        This historical dataset is static.
        """
    )


# ============================================================
# 17. FOOTER
# ============================================================

st.divider()

st.caption(
    "Shenzhen Metro Intelligence | "
    "BANA409 Data App | "
    "Python · Pandas · Plotly · Streamlit"
)
