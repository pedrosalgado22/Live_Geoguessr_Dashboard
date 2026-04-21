import pandas as pd
import numpy as np
import pycountry
import reverse_geocoder as rg

INPUT_FILE = "rounds.csv"


print("Loading rounds.csv ...")
df = pd.read_csv(INPUT_FILE)
for col in ["my_dist_m", "my_dist_km", "opp_dist_m", "opp_dist_km", "dist_delta_km",
            "my_score", "opp_score", "real_lat", "real_lng", "my_lat", "my_lng"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")



df = df.drop(columns=[c for c in ["healing_rounds","pano_id","pano_heading","pano_pitch"] if c in df.columns])

df = df.dropna(subset=["game_id", "round_number"])

def fill_country(row):
    if pd.isna(row["real_country"]) and pd.notna(row.get("real_lat")) and pd.notna(row.get("real_lng")):
        try:
            result = rg.search((row["real_lat"], row["real_lng"]), verbose=False)
            return result[0]["cc"].lower() if result else None
        except:
            return None
    return row["real_country"]

df["real_country"] = df.apply(fill_country, axis=1)
df["round_start"] = pd.to_datetime(df["round_start"], utc=True, errors="coerce").fillna(pd.Timestamp("2025-01-01", tz="UTC"))
df["round_end"]   = pd.to_datetime(df["round_end"],   utc=True, errors="coerce").fillna(pd.Timestamp("2025-01-01", tz="UTC"))

df["guessed_correctly"] = df.apply(
    lambda r: r["my_guessed_country"] == r["real_country"]
    if pd.notna(r.get("my_guessed_country")) and pd.notna(r["real_country"]) else None,
    axis=1,
)
df["opp_correct"] = df.apply(
    lambda r: r["opp_guessed_country"] == r["real_country"]
    if pd.notna(r.get("opp_guessed_country")) and pd.notna(r["real_country"]) else None,
    axis=1,
)


def cc_to_name(cc):
    if not isinstance(cc, str) or len(cc) != 2:
        return None
    try:
        return pycountry.countries.get(alpha_2=cc.upper()).name
    except:
        return None

df["real_country_name"]        = df["real_country"].apply(cc_to_name)
df["my_guessed_country_name"]  = df["my_guessed_country"].apply(cc_to_name) if "my_guessed_country" in df.columns else None
df["opp_guessed_country_name"] = df["opp_guessed_country"].apply(cc_to_name) if "opp_guessed_country" in df.columns else None

REPLACE_MAP = {"Isle of Man": "United Kingdom", "im": "gb"}
for col in ["real_country_name","real_country","my_guessed_country_name",
            "my_guessed_country","opp_guessed_country_name","opp_guessed_country"]:
    if col in df.columns:
        df[col] = df[col].replace(REPLACE_MAP)

print("Building games.csv ...")
df_sorted = df.sort_values(["game_id","round_number"])
games = df_sorted.groupby("game_id").agg(
    rounds_played   = ("round_number",  "count"),
    start_time      = ("round_start",   "min"),
    end_time        = ("round_end",     "max"),
    my_health       = ("my_hp_after",   "last"),
    opp_health      = ("opp_hp_after",  "last"),
    my_avg_dist_m   = ("my_dist_m",     "mean"),
    opp_avg_dist_m  = ("opp_dist_m",    "mean"),
    my_avg_dist_km  = ("my_dist_km",    "mean"),
    opp_avg_dist_km = ("opp_dist_km",   "mean"),
    game_mode       = ("game_mode",     "first"),
    is_rated        = ("is_rated",      "first"),
    is_team_duels   = ("is_team_duels", "first"),
).reset_index()

games["result"] = games.apply(
    lambda r: "W" if r["my_health"] > r["opp_health"]
              else ("L" if r["my_health"] < r["opp_health"] else "?"),
    axis=1,
)
for c in ["my_avg_dist_m","opp_avg_dist_m","my_avg_dist_km","opp_avg_dist_km"]:
    games[c] = games[c].round(2)

games.to_csv("games_private.csv", index=False)
games.drop(columns=["game_id"], errors="ignore").to_csv("games.csv", index=False)
total = len(games[games["result"].isin(["W","L"])])
print(f"  Games: {len(games)}  W: {(games.result=='W').sum()}  L: {(games.result=='L').sum()}")


REGIONS = {
    "ru": [
        (54.0,72.0, 19.0, 45.0,"Leningrad MD"),
        (50.0,60.0, 30.0, 46.0,"Moscow MD"),
        (41.0,52.0, 36.0, 55.0,"Southern MD"),
        (48.0,72.0, 45.0, 90.0,"Central MD"),
        (42.0,78.0, 90.0,180.0,"Eastern MD"),
    ],
    "us": [
        (51.0,72.0,-180.0,-130.0,"Alaska"),
        (18.0,23.0,-161.0,-154.0,"Hawaii"),
        (36.5,48.0,  -80.5, -66.0,"Northeast"),
        (24.0,40.0, -100.0, -75.0,"South"),
        (36.0,49.5,  -97.5, -80.5,"Midwest"),
        (31.0,49.0, -125.0, -97.5,"West"),
    ],
    "au": [
        (-35.5,-13.5,112.0,129.0,"Western Australia"),
        (-26.0,-10.5,129.0,138.0,"Northern Australia"),
        (-38.5,-26.0,129.0,141.0,"Southern Australia"),
        (-29.5,-10.0,138.0,154.0,"Queensland"),
        (-44.0,-28.0,140.0,154.0,"Eastern Australia"),
    ],
    "br": [
        (-12.0, 5.5,-74.0,-44.0,"Norte"),
        (-18.5, 5.0,-48.0,-34.0,"Nordeste"),
        (-24.0,-5.0,-61.0,-44.0,"Centro-Oeste"),
        (-25.0,-14.0,-48.0,-39.0,"Sudeste"),
        (-34.0,-22.5,-58.0,-48.0,"Sul"),
    ],
    "mx": [
        (21.0,33.0,-118.0,-97.0,"North"),
        (14.0,22.5,-105.0,-86.0,"South"),
    ],
    "id": [
        ( -6.0, 6.0, 95.0,109.0,"Sumatra"),
        (-11.0,-5.0,105.0,125.0,"Java & Nusa Tenggara"),
        ( -4.5, 4.5,108.0,119.0,"Kalimantan"),
        ( -6.0, 2.0,119.0,128.5,"Sulawesi"),
        ( -9.0, 0.5,128.0,141.0,"New Guinea & Banda"),
    ],
    "ca": [
        (48.0,60.0,-140.0,-114.0,"British Columbia"),
        (48.5,60.0,-120.0, -95.0,"Prairie Provinces"),
        (41.5,57.0, -95.0, -74.0,"Ontario"),
        (44.5,63.0, -80.0, -57.0,"Quebec"),
        (43.0,54.0, -67.0, -52.0,"Atlantic Provinces"),
        (55.0,84.0,-141.0, -52.0,"North"),
    ],
    "ar": [
        (-32.0,-21.0,-68.0,-53.0,"Norte Grande"),
        (-38.5,-27.0,-72.0,-64.0,"Nuevo Cuyo"),
        (-36.0,-27.0,-65.0,-57.5,"Centro"),
        (-41.0,-33.0,-63.5,-56.5,"Buenos Aires"),
        (-55.5,-37.0,-73.5,-62.0,"Patagonia"),
    ],
    "in": [
        (23.0,37.5,68.0,81.0,"Northern Zone"),
        (15.0,24.5,68.0,78.0,"Western Zone"),
        (17.5,26.5,74.0,84.5,"Central Zone"),
        (19.0,27.5,82.0,89.5,"Eastern Zone"),
        ( 7.5,20.0,74.0,83.5,"Southern Zone"),
        (21.5,29.5,88.0,97.5,"North Eastern Zone"),
    ],
}

def assign_region(row):
    cc = row["real_country"]
    if cc not in REGIONS or pd.isna(row.get("real_lat")) or pd.isna(row.get("real_lng")):
        return None
    lat, lng = row["real_lat"], row["real_lng"]
    for box in REGIONS[cc]:
        mn_lat,mx_lat,mn_lng,mx_lng,region = box
        if mn_lat <= lat <= mx_lat and mn_lng <= lng <= mx_lng:
            return region
    return None

df["region"] = df.apply(assign_region, axis=1)

df["dist_delta_km"] = df["my_dist_km"] - df["opp_dist_km"]

print("Building country_summary.csv ...")
base = df.groupby("real_country_name").agg(
    rounds       = ("guessed_correctly","count"),
    correct      = ("guessed_correctly","sum"),
    avg_dist_km  = ("my_dist_km","mean"),
    avg_delta_km = ("dist_delta_km","mean"),
).reset_index()
base["accuracy_pct"] = (base["correct"] / base["rounds"] * 100).round(1)
base["avg_dist_km"]  = base["avg_dist_km"].round(1)
base["avg_delta_km"] = base["avg_delta_km"].round(1)
base = base[base["rounds"] >= 8]

wrong = df[df["guessed_correctly"] == False].copy()
confusion = (
    wrong.groupby(["real_country_name","my_guessed_country_name"])
    .size().reset_index(name="n")
    .sort_values("n", ascending=False)
    .groupby("real_country_name").first().reset_index()
    [["real_country_name","my_guessed_country_name"]]
    .rename(columns={"my_guessed_country_name":"biggest_confusion"})
)

region_dist = (
    df[df["region"].notna()]
    .groupby(["real_country_name","region"])["my_dist_km"].mean()
    .reset_index()
    .sort_values("my_dist_km", ascending=False)
    .groupby("real_country_name").first().reset_index()
    [["real_country_name","region","my_dist_km"]]
    .rename(columns={"region":"worst_region","my_dist_km":"worst_region_avg_km"})
)
region_dist["worst_region_avg_km"] = region_dist["worst_region_avg_km"].round(1)

country_summary = (
    base
    .merge(confusion,   on="real_country_name", how="left")
    .merge(region_dist, on="real_country_name", how="left")
    [["real_country_name","rounds","accuracy_pct","avg_dist_km",
      "avg_delta_km","biggest_confusion","worst_region","worst_region_avg_km"]]
    .sort_values("accuracy_pct", ascending=False)
    .reset_index(drop=True)
)
country_summary.to_csv("country_summary.csv", index=False)
print(f"  Countries: {len(country_summary)}")

print("Building country_training_ranking.csv ...")
priority_base = df.groupby("real_country_name", dropna=True).agg(
    rounds       = ("guessed_correctly","count"),
    correct      = ("guessed_correctly","sum"),
    avg_dist_km  = ("my_dist_km","mean"),
    avg_delta_km = ("dist_delta_km","mean"),
).reset_index()
priority_base = priority_base[priority_base["rounds"] > 8].copy()
priority_base["accuracy_pct"] = (priority_base["correct"] / priority_base["rounds"] * 100).fillna(0)

def minmax(s):
    s = pd.to_numeric(s, errors="coerce")
    lo, hi = s.min(), s.max()
    if pd.isna(lo) or pd.isna(hi) or hi == lo:
        return pd.Series(50.0, index=s.index)
    return ((s - lo) / (hi - lo) * 100).clip(0,100)

priority_base["rounds_imp"]   = minmax(priority_base["rounds"])
priority_base["delta_imp"]    = minmax(priority_base["avg_delta_km"])
priority_base["distance_imp"] = minmax(priority_base["avg_dist_km"])
priority_base["accuracy_imp"] = (100 - priority_base["accuracy_pct"]).clip(0,100)

priority_base["train_priority_score"] = (
    0.40 * priority_base["rounds_imp"]
  + 0.55 * priority_base["delta_imp"]
  + 0.02 * priority_base["distance_imp"]
  + 0.03 * priority_base["accuracy_imp"]
).round(2)

priority_base = priority_base.sort_values("train_priority_score", ascending=False).reset_index(drop=True)
priority_base["train_priority_rank"] = np.arange(1, len(priority_base)+1)
priority_base["train_bucket"] = pd.qcut(
    priority_base["train_priority_score"], q=5,
    labels=["Very Low","Low","Medium","High","Very High"], duplicates="drop",
)

country_training_ranking = priority_base[[
    "train_priority_rank","real_country_name","train_priority_score","train_bucket",
    "rounds","avg_delta_km","accuracy_pct","avg_dist_km",
    "rounds_imp","delta_imp","accuracy_imp","distance_imp",
]].copy()
country_training_ranking.to_csv("country_training_ranking.csv", index=False)
print(f"  Countries ranked: {len(country_training_ranking)}")

print("Writing roundsfinal.csv ...")
# Keep both private and public round-level outputs.
df.to_csv("roundsfinal_private.csv", index=False)
df.drop(columns=["game_id"], errors="ignore").to_csv("roundsfinal.csv", index=False)

print("\n─ ALL DONE ─")
print(f"  rounds      : {len(df)}")
print(f"  games       : {len(games)}")
print(f"  countries   : {len(country_summary)}")
