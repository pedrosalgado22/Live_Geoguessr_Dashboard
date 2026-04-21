# Live GeoGuessr Dashboard


<img width="1882" height="791" alt="Image" src="https://github.com/user-attachments/assets/d6f8acc0-b633-444d-8ed1-8e127c96d928" />



---

A data engineering and analytics project built on top of my own GeoGuessr Duels history, with 500+ ranked games, fully automated and updated every day.

GeoGuessr's native statistics are sparse and surface-level. This project builds everything that's missing: per-country scores, distance delta against opponents, regional breakdowns within large countries, and a data-driven training priority system.

[**Live dashboard**](https://geoguessrdashboard-kajzyegitrpucxqnvrshpb.streamlit.app/)


---

## Disclaimer

This project does not publish, distribute or condone the use of any tooling that accesses GeoGuessr's internal infrastructure in violation of their Terms of Service. 

---

## Repository Contents

| File | Description |
|---|---|
| `gitdashboard.py` | Streamlit dashboard application |
| `dataprocessing.py` | Full data processing pipeline: cleaning, aggregation and building of all output tables |
| `Data_visualizations.ipynb` | Exploratory analysis and visualizations |
| `games.csv` | Game-level aggregation (result, avg distances, game mode) |
| `roundsfinal.csv` | Processed round-level data |
| `country_summary.csv` | Per-country performance metrics |
| `country_training_ranking.csv` | Training priority rankings with component scores |
| `requirements.txt` | Python dependencies |

> The data pipeline runs automatically on a schedule and commits updated CSVs to this repository. The dashboard reads directly from these files.


---

<img width="1136" height="1450" alt="Image" src="https://github.com/user-attachments/assets/de7d0798-6268-4a65-9c86-0f83bea75bf6" />

---

## Automation

A scheduled pipeline runs every day via GitHub Actions entirely without manual intervention. On each run:

1. New games played since the last run are detected automatically
2. Round data is fetched incrementally (only new games)
3. All four CSVs are rebuilt with the latest data
4. Updated files are committed and pushed to this repository
5. Streamlit Cloud detects the new commit and the dashboard updates

---

## Design Philosophy

Geoguessr is based on distance, not borders, so average distance and average delta are much more important when dictating a game than "guessed country X right". However, per-country analysis is better for immediate conclusions, as well as the most enjoyable, and it is still particularly important as well as heavily correlated with distance and winning. A player who gets all countries right will win an absolute majority of their games. 

In conclusion, country accuracy is the most intuitive metric but distance delta is the most actionable. For example, guessing eastern Czechia for Slovakia costs almost nothing, while guessing Oregon for Massachusetts costs thousands of kilometres. 

Thus, both metrics and analyses were maintained with the training priority system built around delta, the most important metric when identifying the most important areas for closing the gap against opponents, followed by round frequency (how many times a country atually shows up, as the mainstream countries even if "boring" rounds will decide 8/10 games).

Regional analysis for the 9 larger countries in the game was added for additional metrics and to help analysis in these larger countries. A 60% accuracy rate in Russia tells you nothing about whether you're losing on Siberian roads or Moscow suburbs.

## Data Processing Pipeline

`dataprocessing.py` takes the raw round data and produces the four CSV files above:

### 1. Cleaning
- Drops Street View metadata columns irrelevant to performance analysis
- Removes rows with missing coordinates or scores
- Imputes missing country codes via reverse geocoding from lat/lng coordinates
- Standardises timestamps to UTC

### 2. Derived Columns
- `guessed_correctly` — boolean flag: player's guessed country matches real country
- `opp_correct` — same for the opponent
- `dist_delta_km` — player distance minus opponent distance; negative = you were closer

### 3. Game-Level Aggregation
Rounds grouped by game to produce:
- Final health for both players and final `result` (W/L)
- Average guess distances in metres and kilometres
- Game mode, rated status, team duels flag

### 4. Geographic Region Assignment

For nine countries with sufficient round volume, rounds are assigned to sub-national regions using bounding box logic.


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


### 5. Country Summary
Per country (≥5 rounds):
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
| `delta_imp` | 55% | Primary driver: countries where opponent outguesses you most |
| `rounds_imp` | 40% | Frequent countries have reliable metrics and high gameplay impact |
| `distance_imp` | 2% | Low weight, avoids bias toward structurally hard countries |
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



## Visualizations

<img width="1136" height="2508" alt="Image" src="https://github.com/user-attachments/assets/298efa92-49ee-44b2-8a3b-35c50c93d890" />

---
<img width="1136" height="450" alt="Image" src="https://github.com/user-attachments/assets/6ad1f993-131d-4f95-8297-551313707699" />

---
<img width="1308" height="1314" alt="Image" src="https://github.com/user-attachments/assets/cd8d3c5f-82e7-4cd8-87d2-854f98df36f6" />

---


<img width="1308" height="1634" alt="Image" src="https://github.com/user-attachments/assets/73a2b9be-4386-47e7-840e-f1e124b5de1e" />


---


<img width="1308" height="1444" alt="Image" src="https://github.com/user-attachments/assets/7a053630-a3e2-4fb0-9534-f261c8dad459" />

---

<img width="1308" height="1334" alt="Image" src="https://github.com/user-attachments/assets/d0fac82e-8cc0-41be-8679-2f0680684268" />

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
