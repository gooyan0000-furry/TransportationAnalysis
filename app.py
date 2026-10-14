"""Streamlit metro operations dashboard for Jzjsnow/navi-complexity OD CSVs.

Place a station-level smart-card CSV (e.g. sz_2017.csv) in data/metro.csv.
Run: streamlit run app.py
"""
from pathlib import Path
import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Metro Demand | Operations", page_icon="🚇", layout="wide")

# Optional: adjust team name to your own group.
TEAM = "Metro Operations Team"
DATA_FILE = Path(__file__).parent / "data" / "metro.csv"
REQUIRED = {
    "lineid_o", "stationid_o", "stationname_o",
    "lineid_d", "stationid_d", "stationname_d", "d_time", "count"
}

@st.cache_data(show_spinner="Reading metro dataset...")
def load_data(filename: str) -> pd.DataFrame:
    # Only load columns used by the dashboard.
    df = pd.read_csv(filename, encoding="utf-8-sig", low_memory=False)
    missing = REQUIRED - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {', '.join(sorted(missing))}")
    df = df[list(sorted(REQUIRED))].copy()
    for col in ["count", "d_time", "lineid_o", "lineid_d", "stationid_o", "stationid_d"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["stationname_o"] = df["stationname_o"].astype("string").str.strip()
    df["stationname_d"] = df["stationname_d"].astype("string").str.strip()
    df = df.dropna(subset=["lineid_o", "lineid_d", "stationid_o", "stationid_d", "stationname_o", "stationname_d", "count", "d_time"])
    df = df[(df["count"] > 0) & (df["d_time"] > 0)].copy()
    # Composite keys prevent silently merging stations with the same name on different lines.
    for part in ["o", "d"]:
        df[f"station_key_{part}"] = (
            df[f"lineid_{part}"].astype(int).astype(str) + ":" +
            df[f"stationid_{part}"].astype(int).astype(str)
        )
    return df

@st.cache_data(show_spinner=False)
def make_station_summary(df: pd.DataFrame) -> pd.DataFrame:
    departures = (
        df.groupby(["station_key_o", "stationname_o", "lineid_o"], as_index=False, observed=True)
        .agg(outbound=("count", "sum"))
        .rename(columns={"station_key_o": "key", "stationname_o": "station", "lineid_o": "line"})
    )
    arrivals = (
        df.groupby(["station_key_d", "stationname_d", "lineid_d"], as_index=False, observed=True)
        .agg(inbound=("count", "sum"))
        .rename(columns={"station_key_d": "key", "stationname_d": "station", "lineid_d": "line"})
    )
    stations = departures.merge(arrivals[["key", "inbound"]], on="key", how="outer")
    stations["station"] = stations["station"].fillna("Unknown")
    stations[["inbound", "outbound"]] = stations[["inbound", "outbound"]].fillna(0)
    # Add stations that only appear as a destination.
    missing = stations["station"].eq("Unknown")
    if missing.any():
        lookup = arrivals.set_index("key")
        stations.loc[missing, "station"] = stations.loc[missing, "key"].map(lookup["station"])
        stations.loc[missing, "line"] = stations.loc[missing, "key"].map(lookup["line"])
    stations["volume"] = stations["inbound"] + stations["outbound"]
    stations["net"] = stations["inbound"] - stations["outbound"]
    stations["imbalance_pct"] = np.where(
        stations["volume"] > 0, 100 * abs(stations["net"]) / stations["volume"], 0
    )
    stations["label"] = stations["station"] + " (" + stations["key"] + ")"
    return stations

st.title(f"🚇 {TEAM} | Metro Demand Explorer")
st.caption("For a metro planning manager: identify high-demand stations and OD corridors to prioritize capacity reviews and follow-up field checks.")

if not DATA_FILE.exists():
    st.warning("Data file missing: put your source CSV at **data/metro.csv** and restart the app.")
    st.code("metro_dashboard/\n  app.py\n  requirements.txt\n  data/\n    metro.csv", language="text")
    st.info("Expected columns: " + ", ".join(sorted(REQUIRED)))
    st.stop()

try:
    raw = load_data(str(DATA_FILE))
except Exception as e:
    st.error(f"Could not load dataset: {e}")
    st.stop()

if raw.empty:
    st.error("No valid OD records remain after removing incomplete or nonpositive trip counts/durations.")
    st.stop()

station_all = make_station_summary(raw)
line_codes = sorted(set(raw["lineid_o"].astype(int)).union(raw["lineid_d"].astype(int)))
selection = st.sidebar.selectbox("Focus on a metro line", ["All lines"] + [str(x) for x in line_codes])
min_vol = int(st.sidebar.number_input("Minimum station movements", min_value=0, value=0, step=1000,
    help="Removes tiny stations from charts, not from citywide KPI calculations."))

if selection == "All lines":
    # Entire network: preserve OD weights; never equate rows with trips.
    trips = raw
    station = station_all.copy()
    scope_name = "the full observed network"
else:
    line = int(selection)
    # Origin-defined corridor scope. A trip belongs to the selected scope when it STARTS on this line.
    trips = raw[raw["lineid_o"].eq(line)].copy()
    station = station_all[station_all["line"].eq(line)].copy()
    scope_name = f"trips originating on line {line}"

if trips.empty or station.empty:
    st.info("No trips available for this filter.")
    st.stop()

trip_count = int(trips["count"].sum())
weighted_mean = np.average(trips["d_time"], weights=trips["count"])
# Comparable across the selected origin line: departure-only share of busiest origin station.
origins = trips.groupby("station_key_o", observed=True)["count"].sum().sort_values(ascending=False)
top_share = origins.iloc[0] / origins.sum() * 100

st.caption("**Data:** Shenzhen subway smart-card OD summary, October 2017 (historical snapshot). **Proposed production refresh:** nightly; planning review weekly. Not a live congestion feed.")
c1, c2, c3 = st.columns(3)
c1.metric("Observed trips", f"{trip_count:,.0f}")
c2.metric("Avg. journey time", f"{weighted_mean:.1f} min")
c3.metric("Busiest origin share", f"{top_share:.1f}%")
st.caption(f"KPI scope: {scope_name}. Each row is an origin–destination–duration combination; trips are weighted by `count`.")

st.subheader("1 · Which stations carry the greatest passenger demand?")
visible = station[station["volume"].ge(min_vol)].nlargest(12, "volume").copy()
if visible.empty:
    st.warning("No stations meet the minimum-volume filter; lower the threshold.")
else:
    long = visible.melt(id_vars=["label", "volume"], value_vars=["inbound", "outbound"],
                        var_name="Direction", value_name="Trips")
    chart = px.bar(long, y="label", x="Trips", color="Direction", orientation="h",
                   barmode="group", color_discrete_map={"inbound": "#00A6A6", "outbound": "#F29E4C"},
                   category_orders={"label": visible.sort_values("volume")["label"].tolist()},
                   hover_data={"volume": ":,.0f"},
                   labels={"label": "Station (line:station ID)", "Trips": "Entry / exit movements"})
    chart.update_layout(height=530, legend_title_text="Direction", margin=dict(l=5, r=5, t=5, b=5))
    st.plotly_chart(chart, use_container_width=True)
    st.caption("Station movements = entries + exits. A movement is not a unique passenger; the all-lines chart counts a journey at its origin and destination. For line filtering, displayed station traffic is network-wide while KPIs and route chart refer to trips originating on that line.")

st.subheader("2 · Which station-to-station corridors dominate demand?")
# Weighted mean minutes per OD route is calculated from a sum of travel minutes, not averages of CSV rows.
weighted = trips.assign(person_minutes=trips["d_time"] * trips["count"]).groupby(
    ["station_key_o", "stationname_o", "station_key_d", "stationname_d"], as_index=False, observed=True
).agg(trips=("count", "sum"), person_minutes=("person_minutes", "sum"))
weighted["avg_minutes"] = weighted["person_minutes"] / weighted["trips"]
weighted["route"] = weighted["stationname_o"] + " → " + weighted["stationname_d"]
weighted = weighted.nlargest(12, "trips").sort_values("trips", ascending=True)
fig = px.bar(weighted, y="route", x="trips", orientation="h", color="avg_minutes",
             color_continuous_scale="Tealgrn", custom_data=["avg_minutes", "station_key_o", "station_key_d"],
             labels={"route": "Origin → destination", "trips": "Observed trips", "avg_minutes": "Avg. journey (min)"})
fig.update_traces(hovertemplate="%{y}<br>Trips: %{x:,.0f}<br>Weighted avg. minutes: %{customdata[0]:.1f}<extra></extra>")
fig.update_layout(height=520, margin=dict(l=5, r=5, t=5, b=5), coloraxis_colorbar_title="Minutes")
st.plotly_chart(fig, use_container_width=True)
st.caption("Routes are directional (A → B differs from B → A). Longer average journey times are not proof of delays because travel distance and transfers are not controlled for.")

with st.expander("Operational interpretation and downloadable station table"):
    high_priority = station[station["volume"].ge(min_vol)].nlargest(5, "volume")
    st.write("**Suggested next step:** audit capacity, signage and staffing plans at the highest-demand stations; verify current demand and peak-hour crowding with recent data before reallocating resources.")
    st.dataframe(high_priority[["station", "key", "line", "inbound", "outbound", "volume", "imbalance_pct"]], hide_index=True)
    st.download_button("Download station summary CSV", station.to_csv(index=False).encode("utf-8-sig"),
                       file_name="station_summary.csv", mime="text/csv")

st.divider()
st.caption("Source: Jiang et al. (2022), *Quantifying navigation complexity in transportation networks*, PNAS Nexus. Original files: https://github.com/Jzjsnow/navi-complexity. If the course strictly requires a Kaggle dataset, confirm a Kaggle-hosted copy or use your team's Kaggle source instead. 2017 data cannot justify present-day staffing changes without validation.")
