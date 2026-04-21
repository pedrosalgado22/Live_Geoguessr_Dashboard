import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import timedelta, datetime
from pathlib import Path

st.set_page_config(page_title="Geoguessr Dashboard", page_icon="🌍", layout="wide",
                   initial_sidebar_state="collapsed")

st.markdown("""
<style>
html, body, [class*="css"], .stApp {
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", "Helvetica Neue", Helvetica, Arial, sans-serif;
    background-color: #0f0d3d !important;
    color: #ffffff;
}
.block-container { padding: 2.1rem 2rem 2rem !important; max-width: 1350px !important; }
section[data-testid="stSidebar"] { display:none; }
[data-testid="stAppViewContainer"] { background-color: #0f0d3d; }
[data-testid="stHeader"] { background-color: #0f0d3d; }

/* remove default column padding */
div[data-testid="column"] { padding: 0 6px !important; }

/* flag buttons — large emoji, no box */
.stButton > button {
    background: transparent !important;
    border: none !important;
    color: white !important;
    font-size: 38px !important;
    line-height: 1 !important;
    padding: 4px !important;
    min-height: 0 !important;
    width: auto !important;
    box-shadow: none !important;
    transition: transform 0.15s !important;
}
.stButton > button:hover { transform: scale(1.15) !important; background: transparent !important; }
.stButton > button:focus { box-shadow: none !important; }

/* top-10 trigger button */
.top10-btn > button {
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    font-size: 11px !important;
    padding: 3px 10px !important;
    border-radius: 20px !important;
    color: rgba(255,255,255,0.6) !important;
    letter-spacing: 0.05em !important;
}
.top10-btn > button:hover {
    background: rgba(255,255,255,0.15) !important;
    color: white !important;
}

/* section containers */
.section-box {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 14px;
    padding: 16px 20px 14px;
    margin-bottom: 16px;
    transition: border-color 0.18s ease, transform 0.18s ease;
}
.section-box:hover {
    border-color: rgba(255,255,255,0.22);
    transform: translateY(-1px);
}

/* Key-targeted invisible overlay buttons to make each box clickable. */
div[class*="st-key-panel_"] {
    margin-top: -142px !important;
    margin-bottom: 16px !important;
    position: relative;
    z-index: 5;
}
div[class*="st-key-panel_"] button {
    width: 100% !important;
    height: 126px !important;
    opacity: 0 !important;
    border: none !important;
    box-shadow: none !important;
    background: transparent !important;
    padding: 0 !important;
    transform: none !important;
}
div[class*="st-key-panel_"] button p { display: none !important; }
div[class*="st-key-panel_"] button:hover,
div[class*="st-key-panel_"] button:focus {
    box-shadow: none !important;
    outline: none !important;
    transform: none !important;
}
.section-title {
    font-size: 14px;
    font-weight: 600;
    letter-spacing: 0.03em;
    text-transform: none;
    color: rgba(255,255,255,0.5);
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 6px;
}
.panel-title {
    font-size: 14px;
    font-weight: 600;
    letter-spacing: 0.03em;
    text-transform: none;
    color: rgba(255,255,255,0.5);
    margin-bottom: 16px;
}
.badge-up   { color: #4ade80; font-size: 16px; }
.badge-down { color: #f97316; font-size: 16px; }
.badge-plus { color: #4ade80; font-size: 14px; font-weight: 700; }
.badge-warn { color: #facc15; font-size: 14px; }

/* mode bars */
.mode-row {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 12px;
}
.mode-tag {
    font-size: 12px;
    font-weight: 500;
    background: rgba(255,255,255,0.12);
    padding: 4px 12px;
    border-radius: 6px;
    min-width: 80px;
    text-align: center;
}
.mode-pct { font-size: 18px; font-weight: 700; min-width: 52px; }
.bar-track {
    flex: 1;
    background: rgba(255,255,255,0.07);
    border-radius: 4px;
    height: 6px;
    overflow: hidden;
}
.bar-fill {
    height: 6px;
    border-radius: 4px;
    width: 0;
    animation-name: barGrow;
    animation-duration: 2.2s;
    animation-timing-function: ease-out;
    animation-fill-mode: forwards;
}
@keyframes barGrow {
    from { width: 0; }
    to   { width: var(--target-w); }
}

/* dialog table */
[data-testid="stDialog"] {
    background: #1a1760 !important;
}
[data-testid="stDialogBody"] {
    background: #1a1760 !important;
}
</style>
""", unsafe_allow_html=True)

# ── LOAD DATA ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800)
def load():
    rounds = pd.read_csv("roundsfinal.csv")
    games  = pd.read_csv("games.csv")
    cs     = pd.read_csv("country_summary.csv")
    tr     = pd.read_csv("country_training_ranking.csv")

    rounds["round_start"] = pd.to_datetime(rounds["round_start"], utc=True, errors="coerce")
    games["start_time"]   = pd.to_datetime(games["start_time"],   utc=True, errors="coerce")
    rounds["guessed_correctly"] = rounds["guessed_correctly"].map(
        {"True": True, "False": False, True: True, False: False}
    )
    if "dist_delta_km" not in rounds.columns:
        rounds["dist_delta_km"] = rounds["my_dist_km"] - rounds["opp_dist_km"]
    return rounds, games, cs, tr

rounds, games, cs, tr = load()

# ── HELPERS ───────────────────────────────────────────────────────────────────
def flag(cc):
    if not isinstance(cc, str) or len(cc) != 2:
        return "🏳"
    try:
        return chr(ord(cc[0].upper()) + 127397) + chr(ord(cc[1].upper()) + 127397)
    except:
        return "🏳"

cc_map = (
    rounds[["real_country","real_country_name"]].dropna()
    .drop_duplicates().set_index("real_country_name")["real_country"].to_dict()
)

def enrich(df_in):
    df_in = df_in.copy()
    df_in["cc"]   = df_in["real_country_name"].map(cc_map)
    df_in["flag"] = df_in["cc"].apply(flag)
    return df_in

MODE_LABELS = {"StandardDuels":"Move","NoMoveDuels":"No Move","NmpzDuels":"NMPZ"}

# ── GAME STATS ────────────────────────────────────────────────────────────────
total  = len(games)
wins   = (games["result"]=="W").sum()
wr_all = wins/total*100 if total else 0
two_w  = pd.Timestamp.now(tz="UTC") - timedelta(weeks=2)
g2w    = games[games["start_time"] >= two_w]
wr_2w  = (g2w["result"]=="W").sum()/len(g2w)*100 if len(g2w) else 0

mode_stats = {}
for code, label in MODE_LABELS.items():
    sub = games[(games["game_mode"]==code)&(games["result"].isin(["W","L"]))]
    mode_stats[label] = round((sub["result"]=="W").sum()/len(sub)*100,1) if len(sub) else 0.0

# ── COUNTRY SETS ──────────────────────────────────────────────────────────────
cs_v = cs[cs["rounds"]>=3].copy()
cs_v = enrich(cs_v)

tr_v = tr[tr["rounds"]>5].copy()
tr_v = enrich(tr_v)

# Ensure training views can display worst region by country.
if "worst_region" not in tr_v.columns and "worst_region" in cs_v.columns:
    tr_v = tr_v.merge(
        cs_v[["real_country_name", "worst_region"]].drop_duplicates(subset=["real_country_name"]),
        on="real_country_name",
        how="left",
    )

best_acc    = cs_v.nlargest(5,  "accuracy_pct").reset_index(drop=True)
worst_acc   = cs_v.nsmallest(5, "accuracy_pct").reset_index(drop=True)
best_delta  = cs_v.dropna(subset=["avg_delta_km"]).nsmallest(5,"avg_delta_km").reset_index(drop=True)
worst_delta = cs_v.dropna(subset=["avg_delta_km"]).nlargest(5, "avg_delta_km").reset_index(drop=True)
strongpoints= tr_v.nsmallest(5,"train_priority_score").reset_index(drop=True)
need_imp    = tr_v.nlargest(5, "train_priority_score").reset_index(drop=True)

# ── GAUGE ─────────────────────────────────────────────────────────────────────
def gauge(value, title):
    c = "#4ade80" if value>=55 else "#facc15" if value>=45 else "#f87171"
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={"suffix":"%","font":{"size":30,"color":"white","family":"Inter"}},
        gauge={
            "axis":{"range":[0,100],"tickwidth":1,"tickcolor":"rgba(255,255,255,0.2)",
                    "tickfont":{"color":"rgba(255,255,255,0.35)","size":9},"nticks":6},
            "bar":{"color":c,"thickness":0.22},
            "bgcolor":"rgba(0,0,0,0)","borderwidth":0,
            "steps":[
                {"range":[0,45], "color":"rgba(248,113,113,0.1)"},
                {"range":[45,55],"color":"rgba(250,204,21,0.1)"},
                {"range":[55,100],"color":"rgba(74,222,128,0.1)"},
            ],
            "threshold":{"line":{"color":c,"width":3},"thickness":0.75,"value":value},
        },
        title={"text":title,"font":{"size":13,"color":"rgba(255,255,255,0.55)","family":"Inter"}},
        domain={"x":[0,1],"y":[0,1]},
    ))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                      margin=dict(t=25,b=0,l=10,r=10),height=195,font={"color":"white"})
    return fig


# ── MODAL DIALOG ──────────────────────────────────────────────────────────────
@st.dialog(" ", width="large")
def show_top10(title, rows, sort_col, ascending, fmt_col=None):
    st.markdown(f"""
    <div style="font-size:26px;font-weight:700;
                letter-spacing:0.05em;margin-bottom:1rem;color:white">{title}</div>
    """, unsafe_allow_html=True)

    display = rows.sort_values(sort_col, ascending=ascending).head(10).copy()
    display.insert(0, "  ", display["flag"])

    title_l = title.lower()
    if "accuracy" in title_l:
        cols_show = [
            "  ", "real_country_name", "accuracy_pct", "avg_dist_km", "avg_delta_km", "biggest_confusion"
        ]
        col_names = {
            "  ": "",
            "real_country_name": "Country",
            "accuracy_pct": "Accuracy %",
            "avg_dist_km": "Average Distance (km)",
            "avg_delta_km": "Average Delta (km)",
            "biggest_confusion": "Biggest Confusion",
        }
    elif "delta" in title_l:
        cols_show = [
            "  ", "real_country_name", "avg_delta_km", "accuracy_pct", "biggest_confusion", "worst_region"
        ]
        col_names = {
            "  ": "",
            "real_country_name": "Country",
            "avg_delta_km": "Average Delta (km)",
            "accuracy_pct": "Accuracy %",
            "biggest_confusion": "Biggest Confusion",
            "worst_region": "Worst Region",
        }
    else:
        cols_show = [
            "  ", "real_country_name", "rounds", "train_priority_score", "avg_delta_km", "accuracy_pct", "worst_region"
        ]
        col_names = {
            "  ": "",
            "real_country_name": "Country",
            "rounds": "Rounds",
            "train_priority_score": "Training Score",
            "avg_delta_km": "Average Delta (km)",
            "accuracy_pct": "Accuracy %",
            "worst_region": "Worst Region",
        }

    display = display[[c for c in cols_show if c in display.columns]]
    display = display.rename(columns=col_names)

    if "Worst Region" in display.columns:
        display["Worst Region"] = display["Worst Region"].fillna("-").replace("", "-")

    for num_col in ["Accuracy %", "Average Distance (km)", "Average Delta (km)", "Training Score"]:
        if num_col in display.columns:
            display[num_col] = pd.to_numeric(display[num_col], errors="coerce").round(1)

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "": st.column_config.TextColumn(width=40),
            "Country": st.column_config.TextColumn(width=160),
        }
    )

# ── SECTION RENDERER ─────────────────────────────────────────────────────────
def section(badge, label, df_flags, modal_title, sort_col, ascending, modal_df=None):
    if modal_df is None:
        modal_df = df_flags

    flags_html = "".join(
        f'<span style="font-size:34px;margin-right:8px;cursor:default">{r["flag"]}</span>'
        for _, r in df_flags.iterrows()
    )

    st.markdown(f"""
    <div class="section-box">
      <div class="section-title">
        <span class="{badge}">{'↑' if badge=='badge-up' else '↓' if badge=='badge-down' else '+' if badge=='badge-plus' else '⚠'}</span>
        {label}
      </div>
      <div style="display:flex;align-items:center;justify-content:space-between">
        <div>{flags_html}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    btn_key = f"panel_{label}_{modal_title}_{sort_col}_{badge}".replace(" ", "_").lower()
    if st.button(" ", key=btn_key, use_container_width=True):
        show_top10(modal_title, modal_df, sort_col, ascending)

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="display:flex;align-items:flex-end;justify-content:space-between;gap:14px;margin-bottom:0.1rem">
    <div style="display:flex;align-items:baseline;gap:12px">
        <span style="font-size:44px;font-weight:700;line-height:1.15;
                                                                 letter-spacing:0.01em;color:white">GeoGuessr Dashboard</span>
        <span style="font-size:14px;font-weight:500;line-height:1.1;
                                                                 color:rgba(255,255,255,0.85)">Pedro Salgado</span>
    </div>
  <span style="font-size:11px;color:rgba(255,255,255,0.3);
               letter-spacing:0.14em;text-transform:uppercase">{total} games · GeoGuessr Duels</span>
</div>
<hr style="border:none;border-top:1px solid rgba(255,255,255,0.07);margin:0.3rem 0 1.2rem">
""", unsafe_allow_html=True)

left, right = st.columns([1, 1.3], gap="large")

# ── LEFT ──────────────────────────────────────────────────────────────────────
with left:
    bars_html = ""
    for i, (label, pct) in enumerate(mode_stats.items()):
        c = "#4ade80" if pct>=55 else "#facc15" if pct>=45 else "#f87171"
        bars_html += (
            f'<div class="mode-row">'
            f'<span class="mode-tag">{label}</span>'
            f'<span class="mode-pct" style="color:{c}">{pct}%</span>'
            f'<div class="bar-track">'
            f'<div class="bar-fill" style="--target-w:{int(pct)}%;background:{c};animation-delay:{0.15 * i:.2f}s"></div>'
            f'</div>'
            f'</div>'
        )

    mode_block_html = (
        '<div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);'
        'border-radius:16px;padding:20px 22px 8px">'
        '<div class="panel-title">Win rate by mode</div>'
        f'{bars_html}'
        '</div>'
    )
    st.markdown(mode_block_html, unsafe_allow_html=True)

    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

    g1, g2 = st.columns(2)
    with g1:
        st.plotly_chart(gauge(round(wr_all,1),"All Time"),
                        use_container_width=True, config={"displayModeBar":False})
    with g2:
        st.plotly_chart(gauge(round(wr_2w,1),"Last 2 Weeks"),
                        use_container_width=True, config={"displayModeBar":False})

# ── RIGHT ─────────────────────────────────────────────────────────────────────
with right:
    r1, r2 = st.columns(2, gap="medium")

    with r1:
        section("badge-up",   "By country guess",  best_acc,    "Best accuracy",  "accuracy_pct", False, cs_v)
        section("badge-up",   "By delta",          best_delta,  "Best delta",     "avg_delta_km", True,  cs_v)

    with r2:
        section("badge-down", "By country guess",  worst_acc,   "Worst accuracy", "accuracy_pct", True,  cs_v)
        section("badge-down", "By delta",          worst_delta, "Worst delta",     "avg_delta_km", False, cs_v)

    s1, s2 = st.columns(2, gap="medium")
    with s1:
        section("badge-plus", "Strongpoints", strongpoints, "Strongpoints", "train_priority_score", True, tr_v)
    with s2:
        section("badge-warn", "Need Improvement", need_imp, "Need Improvement", "train_priority_score", False, tr_v)

# ── FOOTER ───────────────────────────────────────────────────────────────────
update_candidates = [
    Path("roundsfinal.csv"),
    Path("games.csv"),
    Path("country_summary.csv"),
    Path("country_training_ranking.csv"),
]
existing_updates = [p for p in update_candidates if p.exists()]
if existing_updates:
    last_update_dt = datetime.fromtimestamp(max(p.stat().st_mtime for p in existing_updates))
    last_update_str = last_update_dt.strftime("%Y-%m-%d %H:%M")
else:
    last_update_str = datetime.now().strftime("%Y-%m-%d %H:%M")

st.markdown(
    f"""
        <div style="position:fixed;right:18px;bottom:10px;color:rgba(255,255,255,0.55);font-size:14px;z-index:9999;">
      Last updated: {last_update_str}
    </div>
    """,
    unsafe_allow_html=True,
)
