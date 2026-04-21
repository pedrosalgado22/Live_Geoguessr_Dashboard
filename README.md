# Live GeoGuessr Dashboard

![Dashboard](https://geoguessrdashboard-kajzyegitrpucxqnvrshpb.streamlit.app/)

A personal data engineering and analytics project built on top of my own GeoGuessr Duels history — 540+ ranked games, fully automated, live at the click of a link.

GeoGuessr's native statistics are sparse and surface-level. This project builds everything that's missing: per-country accuracy, distance delta against opponents, regional breakdowns within large countries, and a data-driven training priority system — all updated automatically as new games are played.

**Live dashboard →** [geoguessrdashboard-kajzyegitrpucxqnvrshpb.streamlit.app](https://geoguessrdashboard-kajzyegitrpucxqnvrshpb.streamlit.app/)

---

## Repository Contents

| File | Description |
|---|---|
| `gitdashboard.py` | Streamlit dashboard application |
| `dataprocessing.py` | Full data processing pipeline — cleans, aggregates and builds all output tables |
| `Data_visualizations.ipynb` | Exploratory analysis and visualizations |
| `games.csv` | Game-level aggregation (result, avg distances, game mode) |
| `roundsfinal.csv` | Processed round-level data |
| `country_summary.csv` | Per-country performance metrics |
| `country_training_ranking.csv` | Training priority rankings with component scores |
| `requirements.txt` | Python dependencies |

> The data pipeline runs automatically on a schedule and commits updated CSVs to this repository. The dashboard reads directly from these files — no manual intervention required.

---

## Data

**Source:** Personal GeoGuessr Duels game history  
**Scope:** 540+ ranked games across Standard, No Move and NMPZ modes  
**Granularity:** Individual round-level data — coordinates, guess distances, health deltas, timing

The raw data is obtained through a private pipeline that is not part of this repository. What lives here is everything downstream: the processing, the analysis, and the dashboard.

---

## Data Processing Pipeline

`dataprocessing.py` takes the raw round data and produces the four CSV files above. The steps:

### 1. Cleaning
- Drops Street View metadata columns irrelevant to performance analysis
- Removes rows with missing coordinates or scores — essential fields for distance metrics
- Imputes missing country codes via reverse geocoding from lat/lng coordinates
- Standardises timestamps to UTC

### 2. Derived Columns
- `guessed_correctly` — boolean flag: player's guessed country matches real country
- `opp_correct` — same for the opponent
- `dist_delta_km` — player distance minus opponent distance; negative = you were closer

### 3. Game-Level Aggregation
Rounds grouped by game to produce:
- Final health for both players → `result` (W/L)
- Average guess distances in metres and kilometres
- Game mode, rated status, team duels flag

### 4. Geographic Region Assignment

For nine countries with sufficient round volume, rounds are assigned to sub-national regions using bounding box logic. First match wins — specific boxes are ordered before broader ones.

| Country | Regions |
|---|---|
| 🇷🇺 Russia | Leningrad MD, Moscow MD, Southern MD, Central MD, Eastern MD |
| 🇺🇸 United States | Northeast, South, Midwest, West, Alaska, Hawaii |
| 🇦🇺 Australia | Western Australia, Northern Australia, Southern Australia, Queensland, Eastern Australia |
| 🇧🇷 Brazil | Norte, Nordeste, Centro-Oeste, Sudeste, Sul |
| 🇲🇽 Mexico | North, South |
| 🇮🇩 Indonesia | Sumatra, Java & Nusa Tenggara, Kalimantan, Sulawesi, New Guinea & Banda |
| 🇨🇦 Canada | British Columbia, Prairie Provinces, Ontario, Quebec, Atlantic Provinces, North |
| 🇦🇷 Argentina | Norte Grande, Nuevo Cuyo, Centro, Buenos Aires, Patagonia |
| 🇮🇳 India | Northern, Western, Central, Eastern, Southern, North Eastern Zone |

This surfaces sub-country weaknesses that whole-country averages hide — e.g. strong in Southern Brazil, poor in Norte.

### 5. Country Summary
Per country (≥3 rounds):
- `accuracy_pct` — correct guess rate
- `avg_dist_km` — mean distance error
- `avg_delta_km` — mean distance delta vs opponent
- `biggest_confusion` — most common wrong guess
- `worst_region` — region with highest average distance error

### 6. Training Priority Ranking

A weighted scoring model that answers: *which countries should I train next?*

```
train_priority_score = 0.40 × rounds_imp
                     + 0.55 × delta_imp
                     + 0.02 × distance_imp
                     + 0.03 × accuracy_imp
```

| Component | Weight | Reasoning |
|---|---|---|
| `delta_imp` | 55% | Primary driver — countries where opponent outguesses you most |
| `rounds_imp` | 40% | Frequent countries have reliable metrics and high gameplay impact |
| `distance_imp` | 2% | Low weight — avoids bias toward structurally hard countries (Russia vs. Malta) |
| `accuracy_imp` | 3% | Correlates with delta; minimal independent signal |

All components are min-max scaled to 0–100 before weighting. Output includes a rank and a quintile bucket (Very High → Very Low).

---

## Dashboard

Built with Streamlit. Sections:

- **Win rate by mode** — Standard, No Move, NMPZ win rates with animated bars
- **All Time / Last 2 Weeks gauges** — overall performance at a glance
- **Best & Worst by accuracy** — top and bottom 5 countries by correct guess rate
- **Best & Worst by delta** — where you beat or lose to opponents on distance
- **Strongpoints & Need Improvement** — training priority extremes

Each panel is clickable and opens a full top-10 table with detailed metrics.

---

## Automation

The data pipeline runs on a schedule via GitHub Actions on a separate private repository. On each run:

1. New game IDs are discovered from recent activity
2. Round data is fetched for new games only (incremental)
3. All four CSVs are rebuilt
4. Updated files are committed to this repository

Streamlit Cloud detects the new commit and the dashboard refreshes automatically.

---

## Visualizations

<!-- Win rate by mode -->

<!-- Country accuracy breakdown -->

<!-- Distance delta vs opponent -->

<!-- Training priority ranking -->

---

## Tech Stack

| Tool | Purpose |
|---|---|
| Python 3.11 | Core language |
| `streamlit` | Dashboard framework |
| `pandas` / `numpy` | Data processing |
| `plotly` | Interactive charts and gauges |
| `pycountry` | Country code to name mapping |
| `reverse_geocoder` | Coordinate → country code imputation |
| GitHub Actions | Scheduled pipeline automation |
| Streamlit Community Cloud | Dashboard hosting |

---

## Automation

This is the part that makes the project live rather than static.

A scheduled pipeline runs every few hours via GitHub Actions — entirely without manual intervention. Every day, without touching a single file or running a single script locally:

1. New games played since the last run are discovered automatically
2. Round data is fetched incrementally — only new games, never re-fetching what already exists
3. All four CSVs are rebuilt with the latest data
4. Updated files are committed and pushed to this repository
5. Streamlit Cloud detects the new commit and the dashboard updates

The result: play a game, wait a few hours, refresh the dashboard — your new results are there. No pipelines to trigger, no files to upload, no local environment needed.

---

## Disclaimer

This project does not publish, distribute or condone the use of any tooling that accesses GeoGuessr's internal infrastructure in violation of their Terms of Service. The data collection layer is intentionally kept private. Any such methods used in personal projects should be done ethically, without malicious intent, and without causing server overload. This project was built for personal learning and analytical purposes only.

---

## Design Philosophy

Country accuracy is the most intuitive metric but distance delta is the most actionable. Guessing eastern Czechia for Slovakia costs almost nothing. Guessing Oregon for Massachusetts costs thousands of kilometres. The training priority system is built around delta — closing the gap against opponents, not just improving raw accuracy.

Regional analysis exists because large-country averages lie. A 60% accuracy rate in Russia tells you nothing about whether you're losing on Siberian roads or Moscow suburbs.

---

*Pedro Salgado*
