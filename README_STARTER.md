# Metro Demand Explorer — README writing guide

**Important:** Your course requires your README to be in your own writing. Use the prompts below to draft it yourself. Do not submit this guide as your README.

## Step 1 — Dataset and decision-maker
- Name the specific dataset and provide its **Kaggle link** (required by the course). The original navi-complexity GitHub repository by itself does NOT meet the Kaggle-source requirement.
- Original research source: Jiang et al. (2022), "Quantifying navigation complexity in transportation networks," PNAS Nexus. https://github.com/Jzjsnow/navi-complexity
- Shenzhen records: October 2017. Each CSV row is a combination of origin station, destination station and observed journey duration, with `count` giving the number of trips. No per-day or rush-hour information.
- Explain how/why your final CSV was selected or aggregated to stay below 25 MB; record the actual file size and count of rows.
- Target one role: metro service planning manager.

## Step 2 — Recurring decision
- Who consults this dashboard, and on what schedule?
- What action follows if a station/OD corridor has persistently high demand?
- Why use a recurring dashboard instead of a one-off report?
- What is today's alternative workflow, and its cost?

## Step 3 — Show vs cut
- Up to three KPIs: weighted trips, weighted journey time, share of trips starting at busiest origin.
- Chart 1: busiest stations, inbound and outbound movements, for where demand is concentrated.
- Chart 2: largest directed OD corridors, colored by count-weighted journey time.
- Explain why hourly patterns were CUT (the data has no trip date or clock time).
- Explain why a geographic network map was CUT (line/station IDs are not coordinates; adding map files makes workflow heavier without changing today's resource review).
- Caveats: stations can be represented by line-specific IDs; movements count origin and destination separately; historical snapshot not real-time crowding; top routes don't control for distance/transfers.
- Mention at least a brief EDA (shape, missingness, types, outliers) performed separately before design decisions.

## Step 4 — Refresh policy
- This historic file does not update. For a real production system: ingest new OD aggregates nightly and review weekly.
- Describe one action threshold that your operator could track over successive weeks, and how you would verify it, given no actual time-series in this snapshot.
- Describe consequence of stale data.

## Step 5 — Deployment
- Put `data/metro.csv` beside app.py inside `data/`; ensure its actual size is <25 MB.
- Install `pip install -r requirements.txt`; run `streamlit run app.py`.
- Publish repository under YOUR OWN GitHub account; deploy from YOUR OWN Streamlit Cloud account and select Python 3.14 as specified by class.
- Replace `TEAM` in app.py with your actual team name. Write README.md in your own words.
- Submit your own deployed app URL + your own GitHub repository URL.
