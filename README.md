# Shenzhen Metro Intelligence Dashboard

## 1. Project Overview

This project presents an interactive Streamlit dashboard that analyzes passenger travel patterns in the Shenzhen metro system using historical smart-card data from October 2017.

The dashboard focuses on three aspects of metro travel: passenger demand across stations, frequently used origin–destination (OD) routes, and journey duration.

Rather than simply displaying transportation statistics, the main goal is to help metro planning managers identify locations that deserve further operational attention.

**Central Business Question:**

*How can metro operators use passenger travel data to identify high-demand stations and travel corridors that should be prioritized for capacity reviews?*

The dashboard was developed using Python, Pandas, Plotly, and Streamlit.

## 2. Target Audience and Decision

### Target Audience

The primary audience is **metro planning and operations managers** responsible for monitoring passenger demand and identifying areas for potential service improvements.

### Decision Supported

Metro operators have limited resources for conducting station inspections, evaluating passenger circulation, and reviewing service capacity.

Instead of examining every station and route equally, managers need to identify where further investigation would be most valuable.

This dashboard supports that decision by helping managers:

- Identify stations with the highest passenger demand.
- Compare passenger journeys originating and ending at different stations.
- Find frequently used OD routes.
- Examine the distribution of passenger journey times.

For example, if a station handles a particularly large share of passenger journeys, managers may prioritize it for a capacity review or on-site assessment.

However, high demand does not necessarily mean overcrowding. The dashboard identifies potential priorities rather than making final operational decisions.

## 3. Dataset

**Dataset:** Shenzhen Metro Smart-Card Travel Data (2017)

**Source:** [Navi-Complexity Research Repository](https://github.com/Jzjsnow/navi-complexity)

The dataset contains aggregated passenger journeys between metro stations in Shenzhen, China.

The main variables used in this project include:

| Variable | Description |
|---|---|
| `stationname_o` | Origin station name |
| `stationname_d` | Destination station name |
| `lineid_o` | Origin station's line identifier |
| `lineid_d` | Destination station's line identifier |
| `d_time` | Journey duration in minutes |
| `count` | Number of passenger journeys |

Each record represents an aggregated combination of origin, destination, and journey duration.

Therefore, the `count` column is used when calculating passenger volumes. Simply counting the number of CSV rows would not represent the actual number of journeys.

The dataset was selected because it provides sufficient detail to analyze both station-level demand and travel patterns between stations, while remaining manageable for a Streamlit application.

## 4. Dashboard Design and Visualization Choices

The dashboard uses three key performance indicators (KPIs) and three visualizations.

### 4.1 Key Performance Indicators

| KPI | Why It Matters |
|---|---|
| Passenger Journeys | Measures the total number of recorded journeys in the selected data. |
| Average Journey Duration | Describes typical journey duration using a passenger-weighted average. |
| Busiest Origin Share | Shows how much origin demand is concentrated at the busiest departure station. |

I intentionally limited the dashboard to three KPIs because adding too many indicators could distract users from the main management decision.

### 4.2 Visualization 1: Station Passenger Demand

**Question:** Which metro stations experience the highest passenger demand?

This grouped horizontal bar chart compares origin and destination passenger volumes at the busiest stations.

I chose this visualization because ranking stations makes differences in passenger demand easy to identify.

Separating origin and destination journeys also helps reveal directional differences that would be hidden if only total passenger activity were displayed.

**Decision supported:** Identify stations that should be prioritized for further capacity assessments.

### 4.3 Visualization 2: OD Corridor Demand

**Question:** Which origin–destination pairs account for the most passenger journeys?

This chart ranks frequently used OD pairs by passenger volume. Color represents the weighted average journey duration.

I chose this visualization because station-level demand alone does not reveal where passengers are traveling.

Examining OD demand gives managers additional information about travel patterns across the metro network.

**Decision supported:** Identify high-demand travel corridors for further service and capacity reviews.

Importantly, an OD pair does not necessarily represent a direct train route. It describes passenger travel between two stations, potentially involving transfers.

### 4.4 Visualization 3: Journey Duration Distribution

**Question:** How are passenger journey durations distributed?

This chart divides journeys into duration categories and shows the percentage of total passenger journeys in each category.

It provides useful background information about typical passenger travel patterns.

I included this visualization as **supporting analysis**, rather than the main decision-making tool, because journey duration alone does not indicate whether a station needs additional operational resources.

## 5. Interactive Features

The dashboard includes four interactive controls:

| Control | Purpose |
|---|---|
| Origin Metro Line | Restricts the analysis to journeys starting on a selected line. |
| Destination Metro Line | Restricts the analysis to journeys ending on a selected line. |
| Journey Duration | Filters journeys by travel-time range. |
| Top N | Changes the number of stations or OD pairs displayed. |

The dashboard automatically updates its KPIs, visualizations, and management insights when filters are applied.

A Reset All Filters button allows users to return to the complete dataset.

These controls were included because managers may want to investigate specific parts of the metro network without examining all journeys at once.

## 6. What I Chose Not to Include — and Why

One important design decision was to avoid adding every possible chart.

### Daily and Hourly Passenger Trends

I did not include daily or hourly passenger-flow charts because the dataset does not provide individual journey timestamps.

Creating these charts would require assumptions that the data cannot support.

### Predictive Models

I did not include passenger forecasting or machine-learning models.

Although predictions could be useful for long-term planning, the purpose of this dashboard is to support exploratory analysis and operational prioritization.

Adding complex models would increase the project's scope without necessarily improving its immediate usefulness.

### Detailed Network Maps

I also chose not to include a detailed metro network map.

Although a map could be visually appealing, the current analysis focuses on ranking high-demand stations and OD pairs.

A map would require additional spatial information and more work to ensure that the geographic representation is accurate.

I prioritized clear comparisons over adding visual complexity.

### Why These Trade-offs Matter

The final dashboard focuses on answering a specific operational question rather than maximizing the number of features.

I believe a smaller set of carefully selected visualizations makes it easier for managers to interpret the data and identify potential priorities.

## 7. Data Refresh Frequency

For a real metro operations dashboard, I would recommend refreshing passenger journey data **daily**.

A daily refresh would allow managers to monitor changes in travel demand and identify shifts in station or route usage.

However, frequent updates alone would not be sufficient for real-time crowd management, which would require more detailed and timely information.

For this course project, the dataset is historical and static, so the dashboard does not automatically retrieve new records.

The purpose is to demonstrate how historical travel data can support analysis and operational planning.

## 8. Limitations

There are several limitations to consider when interpreting the results.

First, the dataset represents historical travel demand from 2017. Passenger behavior and metro infrastructure may have changed since then.

Second, the dataset does not contain individual departure timestamps. This prevents analysis of rush-hour congestion or daily passenger fluctuations.

Third, high passenger demand does not automatically indicate overcrowding. Other information, including station capacity, train frequency, and actual passenger density, would be necessary before recommending operational changes.

Finally, OD passenger volumes do not directly measure passenger loads on individual track segments.

For these reasons, the dashboard should be used to **identify priorities for further investigation**, not to make immediate service changes.

## 9. Tools and Technologies

The dashboard was developed using:

- **Python:** Data processing and application logic.
- **Pandas:** Data cleaning, filtering, and aggregation.
- **Plotly:** Interactive visualizations.
- **Streamlit:** Dashboard interface and interactive controls.
- **GitHub:** Source-code hosting.
- **Streamlit Community Cloud:** Application deployment.

## 10. How to Run the Application

Install the required Python packages:

```bash
pip install -r requirements.txt
```

Make sure `sz_2017.csv` is in the same directory as `app.py`.

Run the Streamlit application:

```bash
streamlit run app.py
```

The application will open in a web browser.

## 11. Links

**Live Streamlit Dashboard:https://transportationanalysis-qcfhydt92rvbcxpbtk6hgh.streamlit.app/

**GitHub Repository:** https://github.com/gooyan0000-furry/TransportationAnalysis

**Original Dataset:** https://github.com/Jzjsnow/navi-complexity
