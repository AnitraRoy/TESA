"""
Transit Equity Scenario Analyzer (TESA)
Transit Data Challenge 2026
"""

import os, re, io, json, zipfile, tempfile
import streamlit as st
import pandas as pd
import numpy as np
import geopandas as gpd
import folium
from folium import plugins
from streamlit_folium import st_folium


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="TESA",
    page_icon="icon.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

_HERE = os.path.dirname(os.path.abspath(__file__))
_DATA = os.path.join(_HERE, "data")

# unzip data.zip into data/
zip_path = os.path.join(_HERE, "data.zip")

with zipfile.ZipFile(zip_path, "r") as zip_ref:
    zip_ref.extractall(_HERE)

CENSUS_PATH  = os.path.join(_DATA, "census_data.xlsx")
GEOJSON_PATH = os.path.join(_DATA, "Neighbourhoods.geojson")
GTFS_DIR     = _DATA
SUBWAY_ZIP   = os.path.join(_DATA, "ttc-subway-shapefile-wgs84.zip")


# ---------------------------------------------------------------------------
# CSS — light theme, TTC-inspired colours
# ---------------------------------------------------------------------------

st.markdown("""
<style>
*, *::before, *::after { box-sizing: border-box; }

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewBlockContainer"],
[data-testid="stMain"],
.main, .main > div,
[data-testid="block-container"],
[class*="css"] {
    background-color: #f5f5f7 !important;
    color: #1d1d1f !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif !important;
    font-size: 14px;
}

[data-testid="stHeader"],
[data-testid="stToolbar"] { background-color: #f5f5f7 !important; }

[data-testid="stToolbar"] {
    height: 0 !important;
    min-height: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
}

section[data-testid="stSidebar"] > div:first-child {
    padding-top: 0 !important;
    margin-top: 0 !important;
}

[data-testid="stSidebarContent"] {
    padding-top: 0 !important;
    margin-top: 0 !important;
}

[data-testid="stSidebarContent"] > div:first-child {
    margin-top: 0 !important;
    padding-top: 0 !important;
}

.sidebar-logo { padding-top: 0 !important; margin-top: 0 !important; }

[data-testid="stMainBlockContainer"] { padding-top: 1rem !important; }

:root {
    --background-color: #f5f5f7 !important;
    --secondary-background-color: #ffffff !important;
    --text-color: #1d1d1f !important;
}

section[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div {
    background-color: #ffffff !important;
    border-right: 1px solid #e0e0e5;
}
section[data-testid="stSidebar"] * { color: #1d1d1f !important; }
section[data-testid="stSidebar"] [data-testid="stCheckbox"],
section[data-testid="stSidebar"] [data-testid="stCheckbox"] label {
    background: transparent !important;
}

section[data-testid="stSidebar"] > div:first-child { padding-top: 1rem !important; }
[data-testid="stSidebarContent"]                   { padding-top: 0.5rem !important; }

.sidebar-logo {
    padding: 12px 0 16px;
    border-bottom: 1px solid #e0e0e5;
    margin-bottom: 20px;
}
.sidebar-logo h2 { font-size: 15px; font-weight: 600; color: #1d1d1f !important; margin: 0 0 2px; letter-spacing: -0.2px; }
.sidebar-logo p  { font-size: 12px; color: #6e6e73 !important; margin: 0; }

.sidebar-section {
    font-size: 11px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.06em; color: #6e6e73 !important; margin: 20px 0 10px;
}

[data-testid="stSidebarCollapsedControl"] button {
    background: #ffffff !important;
    border: 1px solid #e0e0e5 !important;
    border-radius: 8px !important;
    color: #1d1d1f !important;
}
[data-testid="stSidebarCollapsedControl"] button:hover {
    border-color: #C8102E !important;
    color: #C8102E !important;
}
[data-testid="stSidebarCollapsedControl"] svg              { fill: #1d1d1f !important; color: #1d1d1f !important; }
[data-testid="stSidebarCollapsedControl"] button:hover svg { fill: #C8102E !important; color: #C8102E !important; }

.file-row {
    display: flex; align-items: center; gap: 8px;
    padding: 6px 0; font-size: 13px;
    border-bottom: 1px solid #f0f0f5; color: #1d1d1f;
}
.file-row .dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.dot-ok  { background: #34c759; }
.dot-err { background: #ff3b30; }

.block-container { padding: 32px 40px !important; max-width: 1400px; }

.page-header { margin-bottom: 32px; padding-bottom: 24px; border-bottom: 1px solid #e0e0e5; }
.page-header h1 { font-size: 28px; font-weight: 600; color: #1d1d1f !important; margin: 0 0 6px; letter-spacing: -0.5px; }
.page-header p  { font-size: 15px; color: #6e6e73; margin: 0; max-width: 680px; line-height: 1.5; }

.stat-strip {
    display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 1px; background: #e0e0e5;
    border: 1px solid #e0e0e5; border-radius: 12px;
    overflow: hidden; margin-bottom: 28px;
}
.stat-cell { background: #ffffff; padding: 18px 22px; }
.stat-cell .num { font-size: 26px; font-weight: 600; color: #1d1d1f; letter-spacing: -0.5px; line-height: 1; margin-bottom: 4px; }
.stat-cell .lbl { font-size: 12px; color: #6e6e73; font-weight: 400; }

.stTabs [data-baseweb="tab-list"] {
    background: transparent; border-bottom: 1px solid #e0e0e5;
    gap: 0; padding: 0; margin-bottom: 24px;
}
.stTabs [data-baseweb="tab"] {
    font-size: 14px; font-weight: 400; color: #6e6e73;
    padding: 10px 18px; border-radius: 0;
    border-bottom: 2px solid transparent; margin-bottom: -1px;
}
.stTabs [aria-selected="true"] {
    color: #1d1d1f !important; font-weight: 500;
    border-bottom: 2px solid #C8102E !important;
    background: transparent !important;
}

[data-testid="stSelectbox"] { position: relative; }
[data-baseweb="select"] > div {
    background-color: #ffffff !important;
    border-color: #d1d1d6 !important;
    color: #1d1d1f !important;
}
[data-baseweb="select"] > div:hover { border-color: #b0b0b8 !important; }
[data-baseweb="select"] [data-testid="stMarkdownContainer"],
[data-baseweb="select"] span,
[data-baseweb="select"] div {
    color: #1d1d1f !important;
    background-color: transparent !important;
}
[data-baseweb="select"] svg { fill: #6e6e73 !important; color: #6e6e73 !important; display: block !important; opacity: 1 !important; }
[data-baseweb="select"] > div:focus-within { border-color: #aaa !important; box-shadow: none !important; }

[data-baseweb="popover"],
[data-baseweb="popover"] > div,
[data-baseweb="popover"] > div > div {
    background-color: #ffffff !important;
    border: 1px solid #e0e0e5 !important;
    border-radius: 8px !important;
    box-shadow: 0 4px 16px rgba(0,0,0,0.10) !important;
}
[data-baseweb="menu"], [data-baseweb="menu"] ul, [data-baseweb="menu"] li,
[role="listbox"], [role="option"] {
    background-color: #ffffff !important; color: #1d1d1f !important; border-color: #e0e0e5 !important;
}
[data-baseweb="menu"] li:hover, [role="option"]:hover {
    background-color: #f0f0f2 !important; color: #1d1d1f !important;
}
[role="option"][aria-selected="true"],
[data-baseweb="option"][aria-selected="true"] {
    background-color: #f0f0f2 !important; color: #1d1d1f !important;
}
[data-baseweb="popover"] * { color: #1d1d1f !important; background-color: transparent !important; }
[data-baseweb="popover"],
[data-baseweb="popover"] > div,
[data-baseweb="menu"],
[role="listbox"]              { background-color: #ffffff !important; }
div[class*="popover"], div[class*="Popover"], div[class*="dropdown"],
div[class*="Dropdown"], div[class*="menu"], div[class*="Menu"] {
    background-color: #ffffff !important; color: #1d1d1f !important;
}
div[class*="popover"] *, div[class*="Popover"] *,
div[class*="dropdown"] *, div[class*="Dropdown"] * { color: #1d1d1f !important; }

[data-testid="stCheckbox"]       { background: transparent !important; }
[data-testid="stCheckbox"] label { background: transparent !important; color: #1d1d1f !important; }
[data-testid="stCheckbox"] input[type="checkbox"] { accent-color: #C8102E !important; }

.ctrl-label {
    font-size: 11px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.06em; color: #6e6e73; margin-bottom: 8px; margin-top: 20px;
}
.ctrl-label:first-child { margin-top: 0; }

.desc-card {
    background: #f5f5f7; border-radius: 8px; padding: 12px 14px;
    font-size: 13px; color: #6e6e73; line-height: 1.5; margin-top: 8px;
}

.legend-grid { display: flex; flex-direction: column; gap: 6px; margin-top: 8px; }
.legend-row  { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #1d1d1f; }
.legend-line { width: 20px; height: 3px; border-radius: 2px; flex-shrink: 0; }

.note {
    background: #f5f5f7; border-radius: 8px; padding: 12px 16px;
    font-size: 13px; color: #6e6e73; line-height: 1.6; margin: 16px 0;
}

.step-list { display: flex; flex-direction: column; gap: 8px; margin: 12px 0; }
.step-row  { display: flex; align-items: flex-start; gap: 12px; font-size: 13px; color: #1d1d1f; line-height: 1.5; }
.step-num  {
    width: 22px; height: 22px; border-radius: 50%;
    background: #C8102E; color: #ffffff;
    font-size: 11px; font-weight: 600;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0; margin-top: 1px;
}

.stButton > button {
    background: #ffffff; color: #1d1d1f;
    border: 1px solid #e0e0e5;
    border-radius: 8px; font-size: 13px; font-weight: 500;
    padding: 8px 18px; font-family: inherit;
}
.stButton > button:hover { background: #f5f5f7; border-color: #C8102E; color: #C8102E; }

.stDataFrame,
[data-testid="stDataFrame"],
[data-testid="stDataFrame"] > div,
[data-testid="stDataFrame"] iframe,
[data-testid="stDataFrame"] canvas {
    background-color: #ffffff !important;
    border: 1px solid #e0e0e5 !important;
    border-radius: 8px !important;
    overflow: hidden; color: #1d1d1f !important;
}
[data-testid="stDataFrame"] [role="grid"],
[data-testid="stDataFrame"] [role="gridcell"],
[data-testid="stDataFrame"] [role="columnheader"],
[data-testid="stDataFrame"] [role="rowheader"] {
    background-color: #ffffff !important; color: #1d1d1f !important; border-color: #f0f0f2 !important;
}
[data-testid="stDataFrame"] [role="columnheader"] {
    background-color: #f5f5f7 !important; color: #6e6e73 !important; font-weight: 600;
}
[data-testid="stDataFrame"] tr:nth-child(even) td { background-color: #fafafa !important; }
[data-testid="stDataFrame"] [data-testid="data-grid-canvas"] { filter: none !important; }
[data-testid="stDataFrame"] > div                             { background-color: #ffffff !important; }

[data-testid="stArrowVegaLiteChart"], [data-testid="stArrowVegaLiteChart"] > div,
[data-testid="stVegaLiteChart"],      [data-testid="stVegaLiteChart"] > div,
.vega-embed, .vega-embed canvas, .vega-embed svg {
    background: #ffffff !important; background-color: #ffffff !important;
    color: #1d1d1f !important; border-radius: 8px;
}
.vega-embed .background    { fill: #ffffff !important; }
.vega-embed text           { fill: #1d1d1f !important; }
.vega-embed .role-axis path,
.vega-embed .role-axis line { stroke: #d1d1d6 !important; }
.vega-embed .role-grid line  { stroke: #f0f0f2 !important; }
.vega-embed, .vega-embed details, .vega-embed summary, .vega-embed canvas,
.vega-embed svg, .vega-bindings,
div[data-testid="stVegaLiteChart"] > div { background-color: #ffffff !important; color: #1d1d1f !important; }
.js-plotly-plot, .plotly, svg.main-svg   { background-color: #ffffff !important; }

/* Expander — white, consistent on all pages */
[data-testid="stExpander"] {
    border: 1px solid #e0e0e5 !important;
    border-radius: 8px !important;
    background: #ffffff !important;
    margin: 2px 0 6px !important;
}
[data-testid="stExpander"] summary {
    font-size: 13px !important;
    color: #1d1d1f !important;
    padding: 10px 14px !important;
    background: #ffffff !important;
}
[data-testid="stExpander"] summary * { color: #1d1d1f !important; background: transparent !important; }
[data-testid="stExpander"] > div { background: #ffffff !important; padding: 0 14px 12px !important; }

[data-testid="stSidebar"] [data-testid="stExpander"] {
    border: 0.5px solid #e0e0e5 !important;
    border-radius: 8px !important;
    background: #f5f5f7 !important;
    margin: 2px 0 6px !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] summary {
    font-size: 12px !important; color: #6e6e73 !important; padding: 6px 10px !important;
}
[data-testid="stSidebar"] [data-testid="stFileUploader"]         { background: transparent !important; }
[data-testid="stSidebar"] [data-testid="stFileUploader"] label   { font-size: 11px !important; color: #6e6e73 !important; }
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
    background: #ffffff !important;
    border: 1px dashed #d1d1d6 !important;
    border-radius: 6px !important;
    padding: 6px 8px !important;
    font-size: 11px !important;
    color: #6e6e73 !important;
}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] * { color: #6e6e73 !important; }

[data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInput"] + div button,
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {
    background: #ffffff !important;
    color: #1d1d1f !important;
    border: 1px solid #d1d1d6 !important;
    border-radius: 6px !important;
    font-size: 12px !important;
}
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover {
    background: #f5f5f7 !important;
    border-color: #C8102E !important;
    color: #C8102E !important;
}

/* File uploader — white on all pages */
[data-testid="stFileUploader"] { background: transparent !important; }
[data-testid="stFileUploader"] label { font-size: 13px !important; color: #1d1d1f !important; }
[data-testid="stFileUploaderDropzone"] {
    background: #ffffff !important;
    border: 1px dashed #d1d1d6 !important;
    border-radius: 8px !important;
    padding: 16px !important;
    font-size: 13px !important;
    color: #1d1d1f !important;
}
[data-testid="stFileUploaderDropzone"] * { color: #1d1d1f !important; background: transparent !important; }
[data-testid="stFileUploaderDropzone"] svg { fill: #6e6e73 !important; }

/* Alert/success/info boxes — white background, dark text */
[data-testid="stAlert"] {
    border-radius: 8px !important;
    background: #ffffff !important;
    border: 1px solid #e0e0e5 !important;
    color: #1d1d1f !important;
}
[data-testid="stAlert"] * { color: #1d1d1f !important; }
[data-testid="stAlert"] p { color: #1d1d1f !important; }
/* Success alert specifically */
[data-testid="stAlert"][data-baseweb="notification"] { background: #ffffff !important; }
div[class*="stAlert"] p { color: #1d1d1f !important; }

h2, h3 { color: #1d1d1f !important; font-weight: 600; }
.stSelectbox > label, .stCheckbox > label { font-size: 13px !important; }
hr { border-color: #e0e0e5; }

/* FIX 2: Slider styling — neutral white/grey, no red */
[data-testid="stSlider"] { background: transparent !important; }
[data-testid="stSlider"] > div { background: transparent !important; }
[data-testid="stSlider"] label { font-size: 13px !important; color: #1d1d1f !important; }
[data-testid="stSlider"] [data-baseweb="slider"] { background: transparent !important; }
[data-testid="stSlider"] [data-baseweb="slider"] > div { background: #d1d1d6 !important; }
[data-testid="stSlider"] [data-baseweb="slider"] [role="slider"] {
    background: #ffffff !important;
    border: 2px solid #6e6e73 !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.15) !important;
}
[data-testid="stSlider"] [data-baseweb="slider"] [role="slider"]:hover {
    border-color: #1d1d1f !important;
}
div[data-testid="stSlider"] > label + div { background: transparent !important; }

/* Impact indicator cards */
.impact-card {
    background: #ffffff; border: 1px solid #e0e0e5; border-radius: 12px;
    padding: 20px 24px; text-align: center;
}
.impact-card .impact-num {
    font-size: 32px; font-weight: 600; letter-spacing: -0.5px; line-height: 1; margin-bottom: 4px;
}
.impact-card .impact-lbl { font-size: 12px; color: #6e6e73; }
.impact-pos { color: #34c759; }
.impact-neg { color: #ff3b30; }
.impact-neu { color: #6e6e73; }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# DataFrame rendering
# ---------------------------------------------------------------------------

def styled_df(df, index=True):
    if index:
        df = df.reset_index()
    cols = df.columns.tolist()
    headers   = "".join(f'<th>{c}</th>' for c in cols)
    rows_html = ""
    for i, row in df.iterrows():
        row_class = "even" if int(i) % 2 == 0 else ""
        cells     = "".join(f'<td>{v}</td>' for v in row)
        rows_html += f'<tr class="{row_class}">{cells}</tr>'
    html = f"""
    <style>
    .lttable {{
        width: 100%; border-collapse: collapse;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        font-size: 13px; background: #ffffff;
        border: 1px solid #e0e0e5; border-radius: 8px; overflow: hidden;
    }}
    .lttable th {{
        background: #f5f5f7; color: #6e6e73; font-weight: 600;
        font-size: 12px; padding: 8px 12px; text-align: left;
        border-bottom: 1px solid #e0e0e5;
    }}
    .lttable td {{
        background: #ffffff; color: #1d1d1f;
        padding: 7px 12px; border-bottom: 1px solid #f5f5f7;
    }}
    .lttable tr.even td {{ background: #fafafa; }}
    .lttable tr:hover td {{ background: #f0f0f5; color: #1d1d1f; }}
    </style>
    <div style="border-radius:8px;overflow:hidden;border:1px solid #e0e0e5;margin-bottom:8px">
    <table class="lttable">
      <thead><tr>{headers}</tr></thead>
      <tbody>{rows_html}</tbody>
    </table></div>
    """
    st.markdown(html, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def load_census(path):
    df = pd.read_excel(path, engine="openpyxl")
    df = df.rename(columns={
        "O`Connor Parkview": "O'Connor-Parkview",
        "Danforth-East York": "Danforth East York",
        "Taylor Massey": "Taylor-Massey",
        "East End Danforth": "East End-Danforth",
        "Yonge-St. Clair": "Yonge-St.Clair",
        "North St. James Town": "North St.James Town",
        "Cabbagetown-South St. James Town": "Cabbagetown-South St.James Town"
    })
    df = df.set_index(df.columns[0])
    df.index = df.index.astype(str)
    return {
        "Public Transit %":        df.loc[df.index.str.contains("Public transit",                   na=False)],
        "Commute 60+ Min %":       df.loc[df.index.str.contains("60 minutes and over",              na=False)],
        "Depart 7-8 AM %":         df.loc[df.index.str.contains("Between 7 a.m. and 7:59 a.m.",    na=False)],
        "Depart 6-7 AM %":         df.loc[df.index.str.contains("Between 6 a.m. and 6:59 a.m.",    na=False)],
        "Depart 5-6 AM %":         df.loc[df.index.str.contains("Between 5 a.m. and 5:59 a.m.",    na=False)],
        "Median After-Tax Income": df.loc[df.index.str.contains("Median after-tax income",          na=False)],
        "Low Income (LIM-AT) %":   df.loc[df.index.str.contains("LIM-AT",                          na=False)],
        "Shelter Cost Burden %":   df.loc[df.index.str.contains("30% or more",                     na=False)],
        "Seniors (65+) %":         df.loc[df.index.str.contains("65 years and over",               na=False)],
        "Recent Immigrants %":     df.loc[df.index.str.contains("2011 to 2021",                    na=False)],
        "Visible Minority %":      df.loc[df.index.str.contains("Total visible minority population", na=False)],
        "Renters %":               df.loc[df.index.str.contains("Renter",                          na=False)],
    }


@st.cache_data(show_spinner=False)
def load_geojson(path):
    return gpd.read_file(path)


@st.cache_data(show_spinner=False)
def load_gtfs(gtfs_dir):
    def rd(fname, **kw):
        return pd.read_csv(os.path.join(gtfs_dir, fname), **kw)
    routes     = rd("routes.txt")
    trips      = rd("trips.txt", low_memory=False)
    stops      = rd("stops.txt")
    shapes_raw = rd("shapes.txt", dtype=str)
    shapes_raw["shape_pt_lat"]      = shapes_raw["shape_pt_lat"].astype(float)
    shapes_raw["shape_pt_lon"]      = shapes_raw["shape_pt_lon"].astype(float)
    shapes_raw["shape_pt_sequence"] = shapes_raw["shape_pt_sequence"].astype(int)
    SUBWAY_IDS   = [1, 2, 4]
    subway_trips = trips[trips["route_id"].isin(SUBWAY_IDS)].copy()
    subway_trips["trip_id"] = subway_trips["trip_id"].astype(str)
    def longest_shape(route_id):
        ids = subway_trips[subway_trips["route_id"] == route_id]["shape_id"].dropna().unique()
        if len(ids) == 0:
            return None
        return max(ids, key=lambda sid: len(shapes_raw[shapes_raw["shape_id"] == sid]))
    route_polylines = {}
    for rid in SUBWAY_IDS:
        sid = longest_shape(rid)
        if sid is None:
            continue
        pts = shapes_raw[shapes_raw["shape_id"] == sid].sort_values("shape_pt_sequence")
        route_polylines[rid] = list(zip(pts["shape_pt_lat"], pts["shape_pt_lon"]))
    subway_trip_ids = set(subway_trips["trip_id"])
    def clean_name(raw):
        n = re.sub(r"\s*-\s*(Northbound|Southbound|Eastbound|Westbound).*", "", raw)
        n = re.sub(r"\s*Platform.*",  "", n)
        n = re.sub(r"\s*-\s*Subway.*", "", n)
        return n.strip()
    stops["stop_id"] = stops["stop_id"].astype(str)
    chunks = []
    for chunk in pd.read_csv(
        os.path.join(gtfs_dir, "stop_times.txt"),
        usecols=["trip_id", "stop_id"],
        chunksize=200_000,
        dtype=str,
    ):
        filtered = chunk[chunk["trip_id"].isin(subway_trip_ids)]
        if len(filtered):
            chunks.append(filtered)
    stations = pd.DataFrame(columns=["route_id", "station_name", "stop_lat", "stop_lon"])
    if chunks:
        sst = pd.concat(chunks, ignore_index=True).drop_duplicates()
        sst = (
            sst
            .merge(subway_trips[["trip_id", "route_id"]], on="trip_id", how="left")
            [["route_id", "stop_id"]].drop_duplicates()
            .merge(stops[["stop_id", "stop_name", "stop_lat", "stop_lon"]], on="stop_id", how="left")
        )
        sst["station_name"] = sst["stop_name"].apply(clean_name)
        sst["stop_lat"]     = pd.to_numeric(sst["stop_lat"], errors="coerce")
        sst["stop_lon"]     = pd.to_numeric(sst["stop_lon"], errors="coerce")
        stations = sst.drop_duplicates(subset=["route_id", "station_name"]).reset_index(drop=True)
    bus_routes       = routes[routes["route_type"] == 3][["route_id", "route_short_name", "route_long_name"]].copy()
    streetcar_routes = routes[routes["route_type"] == 0][["route_id", "route_short_name", "route_long_name"]].copy()
    def get_polylines(route_subset):
        result = {}
        for _, row in route_subset.iterrows():
            rid    = row["route_id"]
            r_sids = trips[trips["route_id"] == rid]["shape_id"].dropna().unique()
            if len(r_sids) == 0:
                continue
            best   = max(r_sids, key=lambda sid: len(shapes_raw[shapes_raw["shape_id"] == sid]))
            pts    = shapes_raw[shapes_raw["shape_id"] == best].sort_values("shape_pt_sequence")
            coords = list(zip(pts["shape_pt_lat"], pts["shape_pt_lon"]))
            if len(coords) >= 2:
                result[rid] = {
                    "coords": coords,
                    "label":  f"{row['route_short_name']} · {row['route_long_name']}",
                }
        return result
    bus_lines       = get_polylines(bus_routes)
    streetcar_lines = get_polylines(streetcar_routes)
    return route_polylines, stations, bus_lines, streetcar_lines, routes, trips, stops, shapes_raw


# ---------------------------------------------------------------------------
# Transit Access Score computation
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def compute_transit_access(_routes_hash, _trips_hash, _stops_hash, _shapes_hash, gtfs_dir, geojson_path):
    routes     = pd.read_csv(os.path.join(gtfs_dir, "routes.txt"))
    trips      = pd.read_csv(os.path.join(gtfs_dir, "trips.txt"), low_memory=False)
    stops      = pd.read_csv(os.path.join(gtfs_dir, "stops.txt"))

    express_route_ids   = set(routes[routes["route_short_name"].astype(str).str.match(r"^9\d{2}")]["route_id"])
    streetcar_route_ids = set(routes[routes["route_type"] == 0]["route_id"])
    bus_route_ids       = set(routes[routes["route_type"] == 3]["route_id"]) - express_route_ids

    all_trip_route = trips[["trip_id", "route_id"]].astype(str)
    stop_route_map = {}
    for chunk in pd.read_csv(
        os.path.join(gtfs_dir, "stop_times.txt"),
        usecols=["trip_id", "stop_id"], chunksize=200_000, dtype=str,
    ):
        merged_chunk = chunk.merge(all_trip_route, on="trip_id", how="left")
        for stop_id, grp in merged_chunk.groupby("stop_id"):
            rids = set(grp["route_id"].dropna().astype(int))
            if stop_id in stop_route_map:
                stop_route_map[stop_id].update(rids)
            else:
                stop_route_map[stop_id] = rids

    def classify_stop(route_ids):
        if route_ids & express_route_ids:   return "express"
        if route_ids & streetcar_route_ids: return "streetcar"
        if route_ids & bus_route_ids:       return "local"
        return None

    stops["stop_id"] = stops["stop_id"].astype(str)
    stops["mode"]    = stops["stop_id"].map(lambda sid: classify_stop(stop_route_map.get(sid, set())))
    stops_classified = stops[stops["mode"].notna()].copy()
    stops_classified["stop_lat"] = stops_classified["stop_lat"].astype(float)
    stops_classified["stop_lon"] = stops_classified["stop_lon"].astype(float)

    def to_gdf_utm(df, lat_col="stop_lat", lon_col="stop_lon"):
        return gpd.GeoDataFrame(
            df,
            geometry=gpd.points_from_xy(df[lon_col], df[lat_col]),
            crs="EPSG:4326",
        ).to_crs("EPSG:32617")

    stops_gdf = to_gdf_utm(stops_classified)

    SUBWAY_IDS   = [1, 2, 4]
    subway_trips = trips[trips["route_id"].isin(SUBWAY_IDS)].copy()
    subway_trips["trip_id"] = subway_trips["trip_id"].astype(str)
    subway_trip_ids = set(subway_trips["trip_id"])

    chunks = []
    for chunk in pd.read_csv(
        os.path.join(gtfs_dir, "stop_times.txt"),
        usecols=["trip_id", "stop_id"], chunksize=200_000, dtype=str,
    ):
        filt = chunk[chunk["trip_id"].isin(subway_trip_ids)]
        if len(filt):
            chunks.append(filt)

    stations_for_access = pd.DataFrame(columns=["stop_lat", "stop_lon"])
    if chunks:
        sst = pd.concat(chunks, ignore_index=True).drop_duplicates()
        sst = (
            sst.merge(subway_trips[["trip_id", "route_id"]], on="trip_id", how="left")
            [["route_id", "stop_id"]].drop_duplicates()
            .merge(stops[["stop_id", "stop_lat", "stop_lon"]], on="stop_id", how="left")
        )
        sst["stop_lat"] = pd.to_numeric(sst["stop_lat"], errors="coerce")
        sst["stop_lon"] = pd.to_numeric(sst["stop_lon"], errors="coerce")
        stations_for_access = sst.drop_duplicates(subset=["route_id", "stop_id"]).dropna(subset=["stop_lat", "stop_lon"])

    line3 = pd.DataFrame([
        {"stop_lat": 43.73205, "stop_lon": -79.26473},
        {"stop_lat": 43.75090, "stop_lon": -79.27044},
        {"stop_lat": 43.76708, "stop_lon": -79.27742},
        {"stop_lat": 43.77059, "stop_lon": -79.27214},
        {"stop_lat": 43.77450, "stop_lon": -79.25791},
        {"stop_lat": 43.77513, "stop_lon": -79.25183},
    ])
    stations_for_access = pd.concat([stations_for_access, line3], ignore_index=True)
    stations_gdf = to_gdf_utm(stations_for_access)

    gdf_utm = gpd.read_file(geojson_path).to_crs("EPSG:32617")
    gdf_utm["area_km2"] = gdf_utm.geometry.area / 1e6

    BUFFER = {"local": 400, "express": 1200, "streetcar": 400, "subway": 800}
    WEIGHT = {"local": 1.0, "express": 1.5,  "streetcar": 1.5,  "subway": 3.0}

    def count_within(geom, pts_gdf, buf_m):
        return int(pts_gdf.geometry.within(geom.buffer(buf_m)).sum())

    scores = []
    for _, row in gdf_utm.iterrows():
        geom = row.geometry
        area = row["area_km2"]
        name = row["AREA_NAME"]
        n_local   = count_within(geom, stops_gdf[stops_gdf["mode"] == "local"],     BUFFER["local"])
        n_express = count_within(geom, stops_gdf[stops_gdf["mode"] == "express"],   BUFFER["express"])
        n_sc      = count_within(geom, stops_gdf[stops_gdf["mode"] == "streetcar"], BUFFER["streetcar"])
        n_subway  = count_within(geom, stations_gdf, BUFFER["subway"])
        raw   = (n_local * WEIGHT["local"] + n_express * WEIGHT["express"] +
                 n_sc * WEIGHT["streetcar"] + n_subway * WEIGHT["subway"])
        score = raw / area if area > 0 else 0
        scores.append({
            "Neighbourhood":   name,
            "local_stops":     n_local,
            "express_stops":   n_express,
            "streetcar_stops": n_sc,
            "subway_stations": n_subway,
            "area_km2":        round(area, 3),
            "transit_raw":     round(raw, 2),
            "transit_access":  round(score, 4),
        })

    transit_df = pd.DataFrame(scores)
    mn, mx = transit_df["transit_access"].min(), transit_df["transit_access"].max()
    transit_df["transit_access_norm"] = ((transit_df["transit_access"] - mn) / (mx - mn) * 100).round(1)
    transit_df["_access_min"] = mn
    transit_df["_access_max"] = mx
    return transit_df


# ---------------------------------------------------------------------------
# Census helpers
# ---------------------------------------------------------------------------

def metric_to_series(df_metric):
    d = df_metric.copy().reset_index()
    melted = d.melt(id_vars=d.columns[0], var_name="Neighbourhood", value_name="Value")
    melted = melted.iloc[:, [1, 2]]
    melted.columns = ["Neighbourhood", "Value"]
    melted["Value"] = pd.to_numeric(melted["Value"], errors="coerce")
    return melted.groupby("Neighbourhood")["Value"].mean()


def norm_col(s):
    mn, mx = s.min(), s.max()
    if mx == mn:
        return s * 0
    return ((s - mn) / (mx - mn) * 100).fillna(0)


NEED_FACTOR_OPTIONS = {
    "Low Income (%)":           "low_income",
    "Seniors (%)":              "seniors",
    "Renters (%)":              "renters",
    "Low Median Income":        "income",
    "Shelter Burden (%)":       "shelter_burden",
    "Visible Minority (%)":     "visible_minority",
    "Recent Immigrants (%)":    "immigrants",
    "High Commute 60+ min (%)": "commute_60plus",
    "Public Transit Use (%)":   "public_transit",
}

NEED_FACTOR_DEFAULTS = {"Low Income (%)", "Seniors (%)", "Renters (%)", "Low Median Income"}


def build_census_table(metrics_dict):
    return pd.DataFrame({
        "public_transit":   metric_to_series(metrics_dict["Public Transit %"]),
        "commute_60plus":   metric_to_series(metrics_dict["Commute 60+ Min %"]),
        "income":           metric_to_series(metrics_dict["Median After-Tax Income"]),
        "low_income":       metric_to_series(metrics_dict["Low Income (LIM-AT) %"]),
        "shelter_burden":   metric_to_series(metrics_dict["Shelter Cost Burden %"]),
        "seniors":          metric_to_series(metrics_dict["Seniors (65+) %"]),
        "immigrants":       metric_to_series(metrics_dict["Recent Immigrants %"]),
        "visible_minority": metric_to_series(metrics_dict["Visible Minority %"]),
        "renters":          metric_to_series(metrics_dict["Renters %"]),
    })


def compute_need_score(census_df, factor_weights):
    components = []
    for label, weight in factor_weights.items():
        if weight == 0:
            continue
        col = NEED_FACTOR_OPTIONS.get(label)
        if col not in census_df.columns:
            continue
        s = census_df[col].copy()
        normed = (100 - norm_col(s)) if label == "Low Median Income" else norm_col(s)
        components.append(normed * weight)
    if not components:
        return pd.Series(0, index=census_df.index)
    total_weight = sum(w for w in factor_weights.values() if w > 0)
    need = pd.concat(components, axis=1).sum(axis=1) / total_weight
    return need.round(1)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LINE3_STATIONS = [
    {"name": "Kennedy Station",            "lat": 43.73205, "lon": -79.26473},
    {"name": "Lawrence East Station",      "lat": 43.75090, "lon": -79.27044},
    {"name": "Ellesmere Station",          "lat": 43.76708, "lon": -79.27742},
    {"name": "Midland Station",            "lat": 43.77059, "lon": -79.27214},
    {"name": "Scarborough Centre Station", "lat": 43.77450, "lon": -79.25791},
    {"name": "McCowan Station",            "lat": 43.77513, "lon": -79.25183},
]

LINE3_POLYLINE = [
    (43.73205, -79.26473), (43.73480, -79.26520), (43.73900, -79.26640),
    (43.74500, -79.26820), (43.75090, -79.27044), (43.75600, -79.27220),
    (43.76200, -79.27520), (43.76708, -79.27742), (43.77059, -79.27214),
    (43.77200, -79.26850), (43.77380, -79.26250), (43.77450, -79.25791),
    (43.77513, -79.25183),
]

LINE_CONFIG = {
    1: {"name": "Line 1 · Yonge-University", "color": "#FFCD00", "weight": 5},
    2: {"name": "Line 2 · Bloor-Danforth",   "color": "#00A650", "weight": 5},
    3: {"name": "Line 3 · Scarborough RT",   "color": "#0054A6", "weight": 4},
    4: {"name": "Line 4 · Sheppard",         "color": "#B000B0", "weight": 5},
}

METRIC_COLORS = {
    "Public Transit %":        "YlOrRd",
    "Commute 60+ Min %":       "OrRd",
    "Depart 7-8 AM %":         "PuRd",
    "Depart 6-7 AM %":         "RdPu",
    "Depart 5-6 AM %":         "BuPu",
    "Median After-Tax Income": "RdYlGn",
    "Low Income (LIM-AT) %":   "YlOrBr",
    "Shelter Cost Burden %":   "Reds",
    "Seniors (65+) %":         "Blues",
    "Recent Immigrants %":     "Greens",
    "Visible Minority %":      "PuBuGn",
    "Renters %":               "BuGn",
}

PERCENT_METRICS = {
    "Public Transit %", "Commute 60+ Min %",
    "Depart 7-8 AM %", "Depart 6-7 AM %", "Depart 5-6 AM %",
    "Low Income (LIM-AT) %", "Shelter Cost Burden %",
    "Seniors (65+) %", "Recent Immigrants %",
    "Visible Minority %", "Renters %",
}

METRIC_DESCRIPTIONS = {
    "Public Transit %":        "Share of commuters whose main mode is public transit.",
    "Commute 60+ Min %":       "Share of commuters spending 60+ minutes commuting one-way.",
    "Depart 7-8 AM %":         "Share of workers leaving home between 7:00-7:59 AM.",
    "Depart 6-7 AM %":         "Share of workers leaving home between 6:00-6:59 AM.",
    "Depart 5-6 AM %":         "Share of workers leaving home between 5:00-5:59 AM.",
    "Median After-Tax Income": "Median after-tax household income in the neighbourhood.",
    "Low Income (LIM-AT) %":   "Share of residents below Statistics Canada's Low-Income Measure after tax.",
    "Shelter Cost Burden %":   "Share of households spending 30%+ of income on housing.",
    "Seniors (65+) %":         "Share of residents aged 65 and over.",
    "Recent Immigrants %":     "Share of residents who immigrated 2011-2021.",
    "Visible Minority %":      "Share of residents identifying as a visible minority.",
    "Renters %":               "Share of households that rent their dwelling.",
}

EQUITY_METRICS = [
    "Public Transit %", "Low Income (LIM-AT) %", "Median After-Tax Income",
    "Shelter Cost Burden %", "Visible Minority %", "Recent Immigrants %",
    "Renters %", "Seniors (65+) %",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def melt_metric_raw(df_metric):
    df = df_metric.copy().reset_index()
    df = df.melt(id_vars=df.columns[0], var_name="Neighbourhood", value_name="RawValue")
    df = df.iloc[:, [1, 2]]
    df.columns = ["Neighbourhood", "RawValue"]
    df["RawValue"] = pd.to_numeric(df["RawValue"], errors="coerce")
    return df


def get_melted(metric_name, metrics_dict):
    df = melt_metric_raw(metrics_dict[metric_name])
    if metric_name in PERCENT_METRICS:
        total = df["RawValue"].sum()
        df["Value"] = (df["RawValue"] / total * 100).round(3) if total else df["RawValue"]
    else:
        df["Value"] = df["RawValue"]
    return df


def add_subway_to_map(m, route_polylines, stations):
    for route_id, cfg in LINE_CONFIG.items():
        layer = folium.FeatureGroup(name=cfg["name"], show=True)
        if route_id == 3:
            folium.PolyLine(
                locations=LINE3_POLYLINE,
                color=cfg["color"], weight=cfg["weight"], opacity=0.85,
                tooltip="Line 3 · Scarborough RT (Closed 2023)",
            ).add_to(layer)
        elif route_id in route_polylines and route_polylines[route_id]:
            folium.PolyLine(
                locations=route_polylines[route_id],
                color=cfg["color"], weight=cfg["weight"], opacity=0.85,
                tooltip=cfg["name"],
            ).add_to(layer)
        if route_id == 3:
            for s in LINE3_STATIONS:
                folium.CircleMarker(
                    location=[s["lat"], s["lon"]], radius=5,
                    color="white", weight=2, fill=True,
                    fill_color=cfg["color"], fill_opacity=1.0,
                    tooltip=f"{s['name']} (Line 3 - Closed 2023)",
                ).add_to(layer)
        elif stations is not None and len(stations) > 0:
            for _, row in stations[stations["route_id"] == route_id].iterrows():
                folium.CircleMarker(
                    location=[row["stop_lat"], row["stop_lon"]], radius=5,
                    color="white", weight=2, fill=True,
                    fill_color=cfg["color"], fill_opacity=1.0,
                    tooltip=f"{row['station_name']} — {cfg['name']}",
                ).add_to(layer)
        layer.add_to(m)


def vega_bar_chart(df, x_field, y_field, color, y_title, height=260):
    return {
        "mark": {"type": "bar", "color": color, "opacity": 0.82},
        "encoding": {
            "x": {
                "field": x_field, "type": "nominal", "sort": "-y",
                "axis": {
                    "labelAngle": -45, "labelFontSize": 10, "labelColor": "#6e6e73",
                    "tickColor": "#e0e0e5", "domainColor": "#e0e0e5", "title": None,
                },
            },
            "y": {
                "field": y_field, "type": "quantitative",
                "axis": {
                    "labelFontSize": 10, "labelColor": "#6e6e73",
                    "gridColor": "#f0f0f2", "domainColor": "#e0e0e5",
                    "title": y_title, "titleColor": "#6e6e73", "titleFontSize": 11,
                },
            },
            "tooltip": [
                {"field": x_field, "type": "nominal"},
                {"field": y_field, "type": "quantitative", "format": ".1f"},
            ],
        },
        "config": {
            "background": "#ffffff",
            "view": {"stroke": "transparent", "fill": "#ffffff"},
            "axis": {
                "labelFont": "-apple-system, sans-serif",
                "titleFont": "-apple-system, sans-serif",
                "labelColor": "#6e6e73", "titleColor": "#6e6e73",
                "domainColor": "#d1d1d6", "tickColor": "#d1d1d6", "gridColor": "#f0f0f2",
            },
        },
        "height": height,
    }


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <h2>Transit Equity Scenario Analyzer (TESA)</h2>
        <p>Toronto, ON</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">Data files</div>', unsafe_allow_html=True)

    def _frow(label, path, upload_key, accept):
        uploaded = st.session_state.get(upload_key)
        ok       = (uploaded is not None) or os.path.exists(path)
        cls      = "dot-ok" if ok else "dot-err"
        suffix   = " +" if uploaded is not None else ""
        st.markdown(
            f'<div class="file-row">'
            f'<span class="dot {cls}"></span>'
            f'<span>{label}{suffix}</span></div>',
            unsafe_allow_html=True,
        )
        with st.expander("Replace", expanded=False):
            f = st.file_uploader(
                label, type=accept,
                key=f"_upload_widget_{upload_key}",
                label_visibility="collapsed",
            )
            if f is not None:
                st.session_state[upload_key] = f
                st.rerun()
            if uploaded is not None:
                if st.button("Restore default", key=f"_reset_{upload_key}"):
                    st.session_state[upload_key] = None
                    st.rerun()

    _frow("census_data.xlsx",              CENSUS_PATH,                          "upload_census",   ["xlsx"])
    _frow("Neighbourhoods.geojson",        GEOJSON_PATH,                         "upload_geojson",  ["geojson", "json"])
    _frow("routes.txt / trips.txt / ...", os.path.join(GTFS_DIR, "routes.txt"), "upload_gtfs_zip", ["zip"])
    _frow("ttc-subway-shapefile-wgs84.zip", SUBWAY_ZIP,                          "upload_subway",   ["zip"])

    st.markdown('<div class="sidebar-section" style="margin-top:24px">Map layers</div>', unsafe_allow_html=True)
    show_subway    = st.checkbox("Subway lines",     value=True)
    show_bus       = st.checkbox("Bus routes",       value=True)
    show_streetcar = st.checkbox("Streetcar routes", value=True)

    st.markdown("---")
    st.markdown(
        '<p style="font-size:12px;color:#6e6e73;line-height:1.6">'
        'All data is open/public — no PII used.<br/>'
        'Check About page for more details.</p>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

data_ok = {"census": False, "geo": False, "gtfs": False}
metrics         = {}
gdf             = None
route_polylines = {}
stations        = pd.DataFrame()
bus_lines       = {}
streetcar_lines = {}
_gtfs_dir_loaded = None

with st.spinner("Loading data..."):
    census_upload = st.session_state.get("upload_census")
    if census_upload is not None:
        try:
            metrics = load_census(io.BytesIO(census_upload.getvalue()))
            data_ok["census"] = True
        except Exception as e:
            st.sidebar.error(f"Census (uploaded): {e}")
    elif os.path.exists(CENSUS_PATH):
        try:
            metrics = load_census(CENSUS_PATH)
            data_ok["census"] = True
        except Exception as e:
            st.sidebar.error(f"Census: {e}")

    geo_upload = st.session_state.get("upload_geojson")
    if geo_upload is not None:
        try:
            gdf = gpd.read_file(io.BytesIO(geo_upload.getvalue()))
            data_ok["geo"] = True
        except Exception as e:
            st.sidebar.error(f"GeoJSON (uploaded): {e}")
    elif os.path.exists(GEOJSON_PATH):
        try:
            gdf = load_geojson(GEOJSON_PATH)
            data_ok["geo"] = True
        except Exception as e:
            st.sidebar.error(f"GeoJSON: {e}")

    gtfs_upload = st.session_state.get("upload_gtfs_zip")
    if gtfs_upload is not None:
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                with zipfile.ZipFile(io.BytesIO(gtfs_upload.getvalue())) as zf:
                    zf.extractall(tmpdir)
                gtfs_root = tmpdir
                if not os.path.exists(os.path.join(tmpdir, "routes.txt")):
                    for entry in os.listdir(tmpdir):
                        candidate = os.path.join(tmpdir, entry)
                        if os.path.isdir(candidate) and os.path.exists(os.path.join(candidate, "routes.txt")):
                            gtfs_root = candidate
                            break
                result = load_gtfs(gtfs_root)
                route_polylines, stations, bus_lines, streetcar_lines = result[:4]
                _gtfs_dir_loaded = gtfs_root
            data_ok["gtfs"] = True
        except Exception as e:
            st.sidebar.error(f"GTFS (uploaded): {e}")
    elif os.path.exists(os.path.join(GTFS_DIR, "routes.txt")):
        try:
            result = load_gtfs(GTFS_DIR)
            route_polylines, stations, bus_lines, streetcar_lines = result[:4]
            _gtfs_dir_loaded = GTFS_DIR
            data_ok["gtfs"] = True
        except Exception as e:
            st.sidebar.error(f"GTFS: {e}")


# ---------------------------------------------------------------------------
# Page header + stat strip
# ---------------------------------------------------------------------------

st.markdown("""
<div class="page-header">
    <h1>Transit Equity Scenario Analyzer</h1>
    <p>Compare Toronto neighbourhood demographics with Toronto Transit Commission infrastructure, as of 2021.
    <p>Identify service gaps, assess equity needs, and sketch future subway extensions.</p>
</div>
""", unsafe_allow_html=True)

n_sta   = len(stations["station_name"].unique()) if len(stations) > 0 else "—"
n_neigh = len(gdf) if gdf is not None else "—"
n_met   = len(metrics) if metrics else "—"
n_lines = len(route_polylines) + 1

st.markdown(f"""
<div class="stat-strip">
    <div class="stat-cell" style="border-top:3px solid #C8102E"><div class="num">{n_sta}</div><div class="lbl">Subway Stations</div></div>
    <div class="stat-cell" style="border-top:3px solid #FFCD00"><div class="num">{n_neigh}</div><div class="lbl">Neighbourhoods</div></div>
    <div class="stat-cell" style="border-top:3px solid #00A650"><div class="num">{n_met}</div><div class="lbl">Census Indicators</div></div>
    <div class="stat-cell" style="border-top:3px solid #0054A6"><div class="num">{n_lines}</div><div class="lbl">Subway Lines</div></div>
</div>
""", unsafe_allow_html=True)

if not all(data_ok.values()):
    missing = [k for k, v in data_ok.items() if not v]
    st.warning(
        f"Could not load: **{', '.join(missing)}**. "
        "Check the sidebar — files must be in the `data/` folder with the exact names shown.",
        icon="⚠️",
    )


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Census Map",
    "Census Analysis",
    "Equity Gap",
    "Extension Simulator",
    "Simulation Comparison",
    "About",
])


# ── Tab 1: Census Map ──────────────────────────────────────────────────────

with tab1:
    left, right = st.columns([1, 3], gap="large")

    with left:
        st.markdown('<div class="ctrl-label">Census layer</div>', unsafe_allow_html=True)
        metric_opts     = list(metrics.keys()) if metrics else list(METRIC_DESCRIPTIONS.keys())
        selected_metric = st.selectbox("metric", metric_opts, label_visibility="collapsed")

        if selected_metric in METRIC_DESCRIPTIONS:
            st.markdown(
                f'<div class="desc-card">{METRIC_DESCRIPTIONS[selected_metric]}</div>',
                unsafe_allow_html=True,
            )

        st.markdown('<div class="ctrl-label" style="margin-top:24px">Transit layers</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="legend-grid">
            <div class="legend-row"><div class="legend-line" style="background:#FFCD00"></div>Line 1 · Yonge-University</div>
            <div class="legend-row"><div class="legend-line" style="background:#00A650"></div>Line 2 · Bloor-Danforth</div>
            <div class="legend-row"><div class="legend-line" style="background:#0054A6"></div>Line 3 · Scarborough RT (closed)</div>
            <div class="legend-row"><div class="legend-line" style="background:#B000B0"></div>Line 4 · Sheppard</div>
            <div class="legend-row"><div class="legend-line" style="background:#E8871E;opacity:0.7"></div>Bus routes</div>
            <div class="legend-row"><div class="legend-line" style="background:#C8102E;opacity:0.7"></div>Streetcar routes</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="ctrl-label" style="margin-top:24px">How to use</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="desc-card">
        Hover over a neighbourhood to see its value and raw count.<br/><br/>
        Click a station marker for details.<br/><br/>
        Toggle layers with the control in the top-right of the map.<br/><br/>
        Darker shading = higher value for the selected metric.
        </div>
        """, unsafe_allow_html=True)

    with right:
        m = folium.Map(
            location=[43.700, -79.420], zoom_start=11,
            tiles="CartoDB positron", control_scale=True,
        )
        if data_ok["census"] and data_ok["geo"] and selected_metric in metrics:
            df_m    = get_melted(selected_metric, metrics)
            is_pct  = selected_metric in PERCENT_METRICS
            legend_name = (f"{selected_metric} (% of city total)" if is_pct else selected_metric)
            folium.Choropleth(
                geo_data=gdf.to_json(), data=df_m,
                columns=["Neighbourhood", "Value"],
                key_on="feature.properties.AREA_NAME",
                fill_color=METRIC_COLORS.get(selected_metric, "YlGnBu"),
                fill_opacity=0.7, line_opacity=0.2, line_color="#999",
                name=selected_metric, legend_name=legend_name,
                nan_fill_color="transparent",
            ).add_to(m)
            merged = gdf.merge(df_m, left_on="AREA_NAME", right_on="Neighbourhood", how="left")
            tooltip_fields  = ["AREA_NAME", "Value", "RawValue"] if is_pct else ["AREA_NAME", "Value"]
            tooltip_aliases = (
                ["Neighbourhood", f"{selected_metric} (% of city)", "Number of individuals"]
                if is_pct else ["Neighbourhood", selected_metric]
            )
            folium.GeoJson(
                merged,
                style_function=lambda _: {"fillColor": "transparent", "color": "transparent", "weight": 0, "fillOpacity": 0},
                tooltip=folium.GeoJsonTooltip(
                    fields=tooltip_fields, aliases=tooltip_aliases, localize=True, sticky=True,
                    style="background:#fff;color:#1d1d1f;font-family:-apple-system,sans-serif;font-size:13px;border:1px solid #e0e0e5;border-radius:6px;padding:8px 12px;box-shadow:0 2px 8px rgba(0,0,0,0.1);",
                ),
            ).add_to(m)
        if show_bus and bus_lines:
            bl = folium.FeatureGroup(name="Bus Routes", show=True)
            for rid, info in bus_lines.items():
                folium.PolyLine(info["coords"], color="#E8871E", weight=1.5, opacity=0.45, tooltip=f"Bus {info['label']}").add_to(bl)
            bl.add_to(m)
        if show_streetcar and streetcar_lines:
            sl = folium.FeatureGroup(name="Streetcar Routes", show=True)
            for rid, info in streetcar_lines.items():
                folium.PolyLine(info["coords"], color="#C8102E", weight=2, opacity=0.6, tooltip=f"Streetcar {info['label']}").add_to(sl)
            sl.add_to(m)
        if show_subway:
            add_subway_to_map(m, route_polylines, stations)
        folium.LayerControl(collapsed=True).add_to(m)
        plugins.MousePosition(position="bottomright", separator=" | ", prefix="").add_to(m)
        st_folium(m, width="100%", height=560, returned_objects=[])


# ── Tab 2: Census Analysis ─────────────────────────────────────────────────

with tab2:
    if not data_ok["census"] or not data_ok["geo"]:
        st.info("Census and GeoJSON data required for this view.", icon="ℹ️")
    else:
        eq_metric = st.selectbox("Census indicator", EQUITY_METRICS)
        if eq_metric in metrics:
            df_eq     = get_melted(eq_metric, metrics).dropna(subset=["Value"])
            is_pct_eq = eq_metric in PERCENT_METRICS
            col_a, col_b = st.columns(2, gap="large")
            with col_a:
                st.markdown("**Highest 10 Neighbourhoods**")
                top10 = df_eq.nlargest(10, "Value").reset_index(drop=True)
                top10.index += 1
                if is_pct_eq:
                    d = top10[["Neighbourhood", "RawValue", "Value"]].copy()
                    d.columns = ["Neighbourhood", "Number of individuals", "% of city total"]
                else:
                    d = top10[["Neighbourhood", "Value"]].copy()
                    d.columns = ["Neighbourhood", eq_metric]
                styled_df(d)
            with col_b:
                st.markdown("**Lowest 10 Neighbourhoods**")
                bot10 = df_eq.nsmallest(10, "Value").reset_index(drop=True)
                bot10.index += 1
                if is_pct_eq:
                    d = bot10[["Neighbourhood", "RawValue", "Value"]].copy()
                    d.columns = ["Neighbourhood", "Number of individuals", "% of city total"]
                else:
                    d = bot10[["Neighbourhood", "Value"]].copy()
                    d.columns = ["Neighbourhood", eq_metric]
                styled_df(d)
            st.markdown("**Distribution Across All Neighbourhoods**")
            chart_df = df_eq[["Neighbourhood", "Value"]].sort_values("Value", ascending=False).reset_index(drop=True)
            st.vega_lite_chart(chart_df, vega_bar_chart(
                chart_df, "Neighbourhood", "Value", "#C8102E",
                "% of city total" if is_pct_eq else eq_metric,
            ), use_container_width=True)
            s    = df_eq["Value"].describe()
            unit = "%" if is_pct_eq else ""
            st.markdown(f"""
            <div class="stat-strip" style="margin-top:16px">
                <div class="stat-cell"><div class="num">{s['mean']:.2f}{unit}</div><div class="lbl">Mean</div></div>
                <div class="stat-cell"><div class="num">{s['50%']:.2f}{unit}</div><div class="lbl">Median</div></div>
                <div class="stat-cell"><div class="num">{s['max']:.2f}{unit}</div><div class="lbl">Max</div></div>
                <div class="stat-cell"><div class="num">{s['min']:.2f}{unit}</div><div class="lbl">Min</div></div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("**Neighbourhood Profile**")
        if gdf is not None:
            hood = st.selectbox("Select neighbourhood", sorted(gdf["AREA_NAME"].dropna().unique()))
            rows = []
            for mname in metrics:
                dm  = get_melted(mname, metrics)
                row = dm[dm["Neighbourhood"] == hood]
                if not row.empty:
                    raw_val = row["RawValue"].values[0]
                    pct_val = row["Value"].values[0]
                    if mname in PERCENT_METRICS:
                        rows.append({"Indicator": mname, "Number of individuals": f"{int(raw_val):,}" if pd.notna(raw_val) else "—", "% of city total": f"{pct_val:.3f}%" if pd.notna(pct_val) else "—"})
                    else:
                        rows.append({"Indicator": mname, "Number of individuals": f"${int(raw_val):,}" if pd.notna(raw_val) else "—", "% of city total": "—"})
            if rows:
                styled_df(pd.DataFrame(rows).set_index("Indicator"))
            else:
                st.info("No data available for this neighbourhood.")


# ── Tab 3: Equity Gap ──────────────────────────────────────────────────────

with tab3:
    if not data_ok["census"] or not data_ok["geo"] or not data_ok["gtfs"]:
        st.info("Census, GeoJSON, and GTFS data are all required for this view.", icon="ℹ️")
    else:
        st.markdown("### Equity Gap")
        st.markdown(
            '<p style="font-size:14px;color:#6e6e73;margin-bottom:8px">'
            "This tab brings together two preliminary calculations to produce the Equity Gap:</p>",
            unsafe_allow_html=True,
        )

        # FIX 1: Numbered step rows instead of misleading + / = operators
        st.markdown("""
        <div style="display:flex;flex-direction:column;gap:10px;margin-bottom:20px">
            <div style="background:#ffffff;border:1px solid #e0e0e5;border-radius:10px;padding:14px 20px;display:flex;align-items:flex-start;gap:14px">
                <div style="width:26px;height:26px;border-radius:50%;background:#1d1d1f;color:#ffffff;font-size:12px;font-weight:600;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:1px">1</div>
                <div>
                    <div style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;color:#6e6e73;margin-bottom:3px">Transit Access Score</div>
                    <div style="font-size:13px;color:#1d1d1f;line-height:1.5">Counts stops and stations within walking distance of each neighbourhood, weighted by mode (bus, streetcar, subway) and normalized 0–100.</div>
                </div>
            </div>
            <div style="background:#ffffff;border:1px solid #e0e0e5;border-radius:10px;padding:14px 20px;display:flex;align-items:flex-start;gap:14px">
                <div style="width:26px;height:26px;border-radius:50%;background:#1d1d1f;color:#ffffff;font-size:12px;font-weight:600;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:1px">2</div>
                <div>
                    <div style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;color:#6e6e73;margin-bottom:3px">Need Score</div>
                    <div style="font-size:13px;color:#1d1d1f;line-height:1.5">Combines census vulnerability indicators (low income, seniors, renters, etc.) into a weighted composite score, normalized 0–100.</div>
                </div>
            </div>
            <div style="background:#f5f5f7;border:1px solid #e0e0e5;border-left:3px solid #C8102E;border-radius:10px;padding:14px 20px;display:flex;align-items:flex-start;gap:14px">
                <div style="width:26px;height:26px;border-radius:50%;background:#C8102E;color:#ffffff;font-size:12px;font-weight:600;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:1px">=</div>
                <div>
                    <div style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;color:#C8102E;margin-bottom:3px">Equity Gap</div>
                    <div style="font-size:13px;color:#1d1d1f;line-height:1.5"><b>Need Score minus Transit Access Score.</b> A positive gap means a neighbourhood has greater need than its current level of service.</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_ctrl, col_map = st.columns([1, 3], gap="large")

        # FIX 3: map_layer_base default — resolved from session_state so the selectbox
        # (rendered below the map) persists correctly across reruns
        map_layer_base = st.session_state.get("base_map_layer", "Equity Gap (Need − Access)")

        with col_ctrl:
            st.markdown('<div class="ctrl-label">Need Score factors</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="desc-card" style="margin-bottom:12px">Adjust the weight (0 = exclude, 1 = normal, 2 = double weight) for each factor. '
                'Median income is automatically inverted so lower income = higher need.</div>',
                unsafe_allow_html=True,
            )

            factor_weights = {}
            for label in NEED_FACTOR_OPTIONS:
                default_val = 1.0 if label in NEED_FACTOR_DEFAULTS else 0.0
                w = st.slider(
                    label, min_value=0.0, max_value=2.0, value=default_val, step=0.25,
                    key=f"w_base_{label}",
                )
                factor_weights[label] = w

        with col_map:
            with st.spinner("Computing transit access scores..."):
                transit_df = compute_transit_access(
                    None, None, None, None,
                    _gtfs_dir_loaded if _gtfs_dir_loaded else GTFS_DIR,
                    GEOJSON_PATH if not st.session_state.get("upload_geojson") else None,
                )

            census_df  = build_census_table(metrics)
            need_score = compute_need_score(census_df, factor_weights)

            equity = transit_df.set_index("Neighbourhood")[["transit_access_norm"]].copy()
            equity["need_score"] = need_score
            equity["equity_gap"] = (equity["need_score"] - equity["transit_access_norm"]).round(1)
            equity["need_score"] = equity["need_score"].round(1)
            equity = equity.round(1)

            eq_map = folium.Map(location=[43.700, -79.420], zoom_start=11, tiles="CartoDB positron", control_scale=True)

            def make_choro_df(series, name):
                d = series.reset_index()
                d.columns = ["Neighbourhood", "Value"]
                d["Value"] = pd.to_numeric(d["Value"], errors="coerce")
                return d

            layer_specs = {
                "Equity Gap (Need − Access)": (equity["equity_gap"],          "RdYlGn_r", "Equity Gap (positive = underserved)"),
                "Transit Access Score":       (equity["transit_access_norm"], "YlGnBu",   "Transit Access Score (0-100)"),
                "Need Score":                 (equity["need_score"],          "OrRd",     "Need Score (0-100)"),
            }

            for lname, (series, color, legend) in layer_specs.items():
                folium.Choropleth(
                    geo_data=gdf.to_json(),
                    data=make_choro_df(series, lname),
                    columns=["Neighbourhood", "Value"],
                    key_on="feature.properties.AREA_NAME",
                    fill_color=color, fill_opacity=0.75, line_opacity=0.15,
                    name=lname,
                    show=(lname == map_layer_base),
                    legend_name=legend,
                    nan_fill_color="transparent",
                ).add_to(eq_map)

            gdf_disp = gdf.copy().merge(
                equity.round(1),
                left_on="AREA_NAME", right_index=True, how="left",
            )
            folium.GeoJson(
                gdf_disp,
                style_function=lambda _: {"fillOpacity": 0, "weight": 0},
                highlight_function=lambda _: {"fillOpacity": 0.15, "weight": 2, "color": "#333"},
                tooltip=folium.GeoJsonTooltip(
                    fields=["AREA_NAME", "transit_access_norm", "need_score", "equity_gap"],
                    aliases=["Neighbourhood", "Transit Access Score (0-100)", "Need Score (0-100)", "Equity Gap"],
                    sticky=True,
                    style="background:#fff;color:#1d1d1f;font-family:-apple-system,sans-serif;font-size:13px;border:1px solid #e0e0e5;border-radius:6px;padding:8px 12px;",
                ),
            ).add_to(eq_map)

            if show_subway:
                add_subway_to_map(eq_map, route_polylines, stations)

            folium.LayerControl(collapsed=True).add_to(eq_map)
            st_folium(eq_map, width="100%", height=520, returned_objects=[])

            # FIX 3: Map layer selector + legend moved below the map
            map_ctrl_row = st.columns([1, 2], gap="medium")
            with map_ctrl_row[0]:
                st.markdown('<div class="ctrl-label" style="margin-top:10px">Map layer</div>', unsafe_allow_html=True)
                st.selectbox(
                    "Map layer",
                    ["Equity Gap (Need − Access)", "Transit Access Score", "Need Score"],
                    key="base_map_layer",
                    label_visibility="collapsed",
                )
            with map_ctrl_row[1]:
                st.markdown("""
                <div style="margin-top:14px;display:flex;flex-wrap:wrap;gap:10px 24px">
                    <div class="legend-row"><div class="legend-line" style="background:#FFCD00"></div>Line 1 · Yonge-University</div>
                    <div class="legend-row"><div class="legend-line" style="background:#00A650"></div>Line 2 · Bloor-Danforth</div>
                    <div class="legend-row"><div class="legend-line" style="background:#0054A6"></div>Line 3 · Scarborough RT (closed)</div>
                    <div class="legend-row"><div class="legend-line" style="background:#B000B0"></div>Line 4 · Sheppard</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### Top 15 Most Underserved Neighbourhoods")
        st.markdown(
            '<p style="font-size:13px;color:#6e6e73;margin-bottom:16px">'
            "Ranked by Equity Gap — a larger gap indicates greater unmet need relative to current service levels.</p>",
            unsafe_allow_html=True,
        )

        top15 = equity.sort_values("equity_gap", ascending=False).head(15).reset_index()
        top15.columns = ["Neighbourhood", "Transit Access Score", "Need Score", "Equity Gap"]

        c1, c2, c3 = st.columns(3, gap="large")

        with c1:
            st.markdown("**By Transit Access Score**")
            chart_acc = top15[["Neighbourhood", "Transit Access Score"]].sort_values("Transit Access Score")
            st.vega_lite_chart(chart_acc, vega_bar_chart(chart_acc, "Neighbourhood", "Transit Access Score", "#0054A6", "Transit Access Score"), use_container_width=True)

        with c2:
            st.markdown("**By Need Score**")
            chart_need = top15[["Neighbourhood", "Need Score"]].sort_values("Need Score", ascending=False)
            st.vega_lite_chart(chart_need, vega_bar_chart(chart_need, "Neighbourhood", "Need Score", "#FF9F0A", "Need Score"), use_container_width=True)

        with c3:
            st.markdown("**By Equity Gap**")
            chart_gap = top15[["Neighbourhood", "Equity Gap"]].copy()
            st.vega_lite_chart(chart_gap, vega_bar_chart(chart_gap, "Neighbourhood", "Equity Gap", "#C8102E", "Equity Gap"), use_container_width=True)

        st.markdown("**Top 15 Neighbourhoods by Equity Gap**")
        styled_df(top15.set_index("Neighbourhood"))

        st.session_state["baseline_equity"]    = equity
        st.session_state["baseline_transit_df"] = transit_df
        st.session_state["baseline_census_df"]  = census_df


# ── Tab 4: Extension Simulator ─────────────────────────────────────────────

with tab4:
    left2, right2 = st.columns([1, 3], gap="large")

    with left2:
        st.markdown("**How to Use**")
        # FIX 4: subway_proposal.geojson uses <em> italic instead of <code> black/green
        st.markdown("""
        <div class="step-list">
            <div class="step-row"><span class="step-num">1</span><span>Select the <b>polyline tool</b> and click on the map to draw a proposed route. Double-click to finish.</span></div>
            <div class="step-row"><span class="step-num">2</span><span>Use the <b>marker tool</b> to place proposed station stops. Each marker = one new station.</span></div>
            <div class="step-row"><span class="step-num">3</span><span>Use the <b>circle tool</b> to visualise ~500 m walking catchment zones.</span></div>
            <div class="step-row"><span class="step-num">4</span><span>Use the <b>measure tool</b> (top-right) to estimate route distances.</span></div>
            <div class="step-row"><span class="step-num">5</span><span>Click <b>Export</b> to download your proposal as <em>subway_proposal.geojson</em>. Upload this file in the <b>Simulation Comparison</b> tab to analyse the equity impact.</span></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div style="margin-top:20px"></div>', unsafe_allow_html=True)
        st.markdown('<style>[data-testid="stCheckbox"] p { color: #1d1d1f !important; }</style>', unsafe_allow_html=True)

        sim_overlay = st.checkbox("Show census overlay", value=True)
        sim_metric  = None
        if sim_overlay and metrics:
            sim_metric = st.selectbox("Metric", list(metrics.keys()), key="sim_m")

        st.markdown("""
        <div class="note" style="margin-top:16px">
        Drawings are not saved between sessions. Export GeoJSON to preserve your proposal, then upload it in the <b>Simulation Comparison</b> tab.
        </div>
        """, unsafe_allow_html=True)

    with right2:
        sm = folium.Map(location=[43.700, -79.420], zoom_start=11, tiles="CartoDB positron", control_scale=True)
        if sim_overlay and sim_metric and data_ok["census"] and data_ok["geo"]:
            ds = get_melted(sim_metric, metrics)
            folium.Choropleth(
                geo_data=gdf.to_json(), data=ds,
                columns=["Neighbourhood", "Value"],
                key_on="feature.properties.AREA_NAME",
                fill_color=METRIC_COLORS.get(sim_metric, "YlGnBu"),
                fill_opacity=0.5, line_opacity=0.15,
                legend_name=(f"{sim_metric} (% of city total)" if sim_metric in PERCENT_METRICS else sim_metric),
                nan_fill_color="transparent",
            ).add_to(sm)
        if show_bus and bus_lines:
            bl2 = folium.FeatureGroup(name="Bus Routes", show=True)
            for rid, info in bus_lines.items():
                folium.PolyLine(info["coords"], color="#E8871E", weight=1.5, opacity=0.45).add_to(bl2)
            bl2.add_to(sm)
        if show_streetcar and streetcar_lines:
            sl2 = folium.FeatureGroup(name="Streetcar Routes", show=True)
            for rid, info in streetcar_lines.items():
                folium.PolyLine(info["coords"], color="#C8102E", weight=2, opacity=0.6).add_to(sl2)
            sl2.add_to(sm)
        if show_subway:
            add_subway_to_map(sm, route_polylines, stations)
        plugins.Draw(
            export=True,
            filename="subway_proposal.geojson",
            position="topleft",
            draw_options={
                "polyline":     {"shapeOptions": {"color": "#FF3B30", "weight": 4}},
                "marker":       True,
                "circle":       {"shapeOptions": {"color": "#FF3B30", "fillOpacity": 0.08}},
                "polygon":      False,
                "rectangle":    False,
                "circlemarker": False,
            },
            edit_options={"edit": True, "remove": True},
        ).add_to(sm)
        plugins.MousePosition(position="bottomright", separator=" | ", prefix="").add_to(sm)
        plugins.MeasureControl(position="topright", primary_length_unit="kilometers").add_to(sm)
        folium.LayerControl(collapsed=True).add_to(sm)

        sm.get_root().html.add_child(folium.Element(
            '<div style="position:fixed;top:10px;left:50%;transform:translateX(-50%);'
            'background:rgba(20,20,20,0.82);color:white;border-radius:8px;'
            'padding:8px 20px;font-family:Arial,sans-serif;font-size:12px;'
            'z-index:9999;pointer-events:none;white-space:nowrap">'
            'Place <b>Markers</b> at each station &nbsp;·&nbsp; Draw a <b>Polyline</b> for the route &nbsp;·&nbsp;'
            'Click <b style="color:#7ec8e3">Export</b> (top-left) when done'
            '</div>'
        ))

        st_folium(sm, width="100%", height=560, returned_objects=[])


# ── Tab 5: Simulation Comparison ───────────────────────────────────────────

with tab5:
    st.markdown("### Simulation Comparison")
    st.markdown(
        '<p style="font-size:14px;color:#6e6e73;margin-bottom:16px">'
        "Upload the GeoJSON exported from the <b>Extension Simulator</b> tab. "
        "TESA re-computes the Transit Access Score with your proposed stations added, "
        "then recalculates the Equity Gap (Need Score minus updated Transit Access Score) "
        "and compares results side-by-side against the baseline.</p>",
        unsafe_allow_html=True,
    )

    upload_col, _ = st.columns([1, 2])
    with upload_col:
        geojson_file = st.file_uploader(
            "Upload your geojson file",
            type=["geojson", "json"],
            key="sim_geojson_upload",
            help="Export your drawing from the Extension Simulator tab, then upload it here.",
        )

    if geojson_file is None:
        # FIX 4: <em> italic instead of <code> black/green
        st.markdown("""
        <div class="note">
        No GeoJSON uploaded yet. Go to the <b>Extension Simulator</b> tab, draw your proposed extension,
        place <b>markers</b> at each new station, then click <b>Export</b> to download
        <em>subway_proposal.geojson</em>. Upload that file here to see the equity impact.
        </div>
        """, unsafe_allow_html=True)
    elif not data_ok["census"] or not data_ok["geo"] or not data_ok["gtfs"]:
        st.warning("Census, GeoJSON, and GTFS data must all be loaded before running the comparison.", icon="⚠️")
    else:
        try:
            geojson_data = json.loads(geojson_file.getvalue())
        except Exception as e:
            st.error(f"Could not parse GeoJSON: {e}")
            geojson_data = None

        if geojson_data is not None:
            new_station_coords = []
            for feat in geojson_data.get("features", []):
                if feat.get("geometry", {}).get("type") == "Point":
                    lon, lat = feat["geometry"]["coordinates"]
                    props = feat.get("properties") or {}
                    name  = props.get("name") or f"New Station ({lat:.4f}, {lon:.4f})"
                    new_station_coords.append({"station_name": name, "stop_lat": lat, "stop_lon": lon})

            if not new_station_coords:
                st.warning(
                    "No Point features (station markers) found in the GeoJSON. "
                    "Make sure you placed markers at each station using the marker tool before exporting.",
                    icon="⚠️",
                )
            else:
                st.markdown(
                    f'<div style="background:#ffffff;border:1px solid #34c759;border-left:4px solid #34c759;'
                    f'border-radius:8px;padding:12px 16px;font-size:13px;color:#1d1d1f;margin-bottom:16px">'
                    f'Found <b>{len(new_station_coords)}</b> new station(s) in the uploaded file.</div>',
                    unsafe_allow_html=True,
                )

                with st.expander("Need Score configuration", expanded=False):
                    sim_factor_weights = {}
                    for label in NEED_FACTOR_OPTIONS:
                        base_val = st.session_state.get(f"w_base_{label}", 1.0 if label in NEED_FACTOR_DEFAULTS else 0.0)
                        w = st.slider(
                            label, min_value=0.0, max_value=2.0, value=float(base_val), step=0.25,
                            key=f"w_sim_{label}",
                        )
                        sim_factor_weights[label] = w
                if not any(f"w_sim_{l}" in st.session_state for l in NEED_FACTOR_OPTIONS):
                    sim_factor_weights = {
                        l: st.session_state.get(f"w_base_{l}", 1.0 if l in NEED_FACTOR_DEFAULTS else 0.0)
                        for l in NEED_FACTOR_OPTIONS
                    }
                else:
                    sim_factor_weights = {l: st.session_state.get(f"w_sim_{l}", 1.0 if l in NEED_FACTOR_DEFAULTS else 0.0) for l in NEED_FACTOR_OPTIONS}

                with st.spinner("Computing simulation scores..."):
                    if "baseline_transit_df" in st.session_state:
                        transit_df_base = st.session_state["baseline_transit_df"]
                    else:
                        transit_df_base = compute_transit_access(
                            None, None, None, None,
                            _gtfs_dir_loaded if _gtfs_dir_loaded else GTFS_DIR,
                            GEOJSON_PATH,
                        )

                    census_df = build_census_table(metrics)
                    need_score = compute_need_score(census_df, sim_factor_weights)

                    equity_base = transit_df_base.set_index("Neighbourhood")[["transit_access_norm"]].copy()
                    equity_base["need_score"] = need_score
                    equity_base["equity_gap"] = (equity_base["need_score"] - equity_base["transit_access_norm"]).round(1)
                    equity_base = equity_base.round(1)

                    new_stations_df  = pd.DataFrame(new_station_coords)
                    new_stations_gdf = gpd.GeoDataFrame(
                        new_stations_df,
                        geometry=gpd.points_from_xy(new_stations_df["stop_lon"], new_stations_df["stop_lat"]),
                        crs="EPSG:4326",
                    ).to_crs("EPSG:32617")

                    gtfs_dir_use = _gtfs_dir_loaded if _gtfs_dir_loaded else GTFS_DIR

                    if len(stations) > 0:
                        existing_stn = stations.dropna(subset=["stop_lat", "stop_lon"]).copy()
                        existing_stn_gdf = gpd.GeoDataFrame(
                            existing_stn,
                            geometry=gpd.points_from_xy(existing_stn["stop_lon"], existing_stn["stop_lat"]),
                            crs="EPSG:4326",
                        ).to_crs("EPSG:32617")
                    else:
                        existing_stn_gdf = gpd.GeoDataFrame(
                            pd.DataFrame({"stop_lat": [], "stop_lon": []}),
                            geometry=[], crs="EPSG:32617",
                        )

                    line3_df = pd.DataFrame([
                        {"stop_lat": 43.73205, "stop_lon": -79.26473},
                        {"stop_lat": 43.75090, "stop_lon": -79.27044},
                        {"stop_lat": 43.76708, "stop_lon": -79.27742},
                        {"stop_lat": 43.77059, "stop_lon": -79.27214},
                        {"stop_lat": 43.77450, "stop_lon": -79.25791},
                        {"stop_lat": 43.77513, "stop_lon": -79.25183},
                    ])
                    line3_gdf = gpd.GeoDataFrame(
                        line3_df,
                        geometry=gpd.points_from_xy(line3_df["stop_lon"], line3_df["stop_lat"]),
                        crs="EPSG:4326",
                    ).to_crs("EPSG:32617")

                    stations_combined = pd.concat([existing_stn_gdf, line3_gdf, new_stations_gdf], ignore_index=True)

                    stops_raw  = pd.read_csv(os.path.join(gtfs_dir_use, "stops.txt"))
                    routes_raw = pd.read_csv(os.path.join(gtfs_dir_use, "routes.txt"))
                    trips_raw  = pd.read_csv(os.path.join(gtfs_dir_use, "trips.txt"), low_memory=False)

                    express_rids   = set(routes_raw[routes_raw["route_short_name"].astype(str).str.match(r"^9\d{2}")]["route_id"])
                    streetcar_rids = set(routes_raw[routes_raw["route_type"] == 0]["route_id"])
                    bus_rids       = set(routes_raw[routes_raw["route_type"] == 3]["route_id"]) - express_rids

                    all_tr = trips_raw[["trip_id", "route_id"]].astype(str)
                    stop_route_map2 = {}
                    for chunk in pd.read_csv(
                        os.path.join(gtfs_dir_use, "stop_times.txt"),
                        usecols=["trip_id", "stop_id"], chunksize=200_000, dtype=str,
                    ):
                        mc = chunk.merge(all_tr, on="trip_id", how="left")
                        for sid, grp in mc.groupby("stop_id"):
                            rids = set(grp["route_id"].dropna().astype(int))
                            if sid in stop_route_map2: stop_route_map2[sid].update(rids)
                            else: stop_route_map2[sid] = rids

                    def classify_stop2(rids):
                        if rids & express_rids:   return "express"
                        if rids & streetcar_rids: return "streetcar"
                        if rids & bus_rids:       return "local"
                        return None

                    stops_raw["stop_id"] = stops_raw["stop_id"].astype(str)
                    stops_raw["mode"]    = stops_raw["stop_id"].map(lambda s: classify_stop2(stop_route_map2.get(s, set())))
                    stops_cl = stops_raw[stops_raw["mode"].notna()].copy()
                    stops_cl["stop_lat"] = stops_cl["stop_lat"].astype(float)
                    stops_cl["stop_lon"] = stops_cl["stop_lon"].astype(float)

                    stops_gdf2 = gpd.GeoDataFrame(
                        stops_cl,
                        geometry=gpd.points_from_xy(stops_cl["stop_lon"], stops_cl["stop_lat"]),
                        crs="EPSG:4326",
                    ).to_crs("EPSG:32617")

                    gdf_utm2 = gdf.to_crs("EPSG:32617")
                    gdf_utm2["area_km2"] = gdf_utm2.geometry.area / 1e6

                    BUFFER = {"local": 400, "express": 1200, "streetcar": 400, "subway": 800}
                    WEIGHT = {"local": 1.0, "express": 1.5,  "streetcar": 1.5,  "subway": 3.0}

                    def count_within2(geom, pts_gdf, buf_m):
                        return int(pts_gdf.geometry.within(geom.buffer(buf_m)).sum())

                    sim_scores = []
                    for _, row in gdf_utm2.iterrows():
                        geom = row.geometry
                        area = row["area_km2"]
                        name = row["AREA_NAME"]
                        n_local   = count_within2(geom, stops_gdf2[stops_gdf2["mode"] == "local"],     BUFFER["local"])
                        n_express = count_within2(geom, stops_gdf2[stops_gdf2["mode"] == "express"],   BUFFER["express"])
                        n_sc      = count_within2(geom, stops_gdf2[stops_gdf2["mode"] == "streetcar"], BUFFER["streetcar"])
                        n_subway  = count_within2(geom, stations_combined, BUFFER["subway"])
                        raw   = (n_local * WEIGHT["local"] + n_express * WEIGHT["express"] +
                                 n_sc * WEIGHT["streetcar"] + n_subway * WEIGHT["subway"])
                        score = raw / area if area > 0 else 0
                        sim_scores.append({
                            "Neighbourhood":       name,
                            "subway_stations_sim": n_subway,
                            "transit_access_sim":  round(score, 4),
                        })

                    transit_df_sim = pd.DataFrame(sim_scores)
                    mn = transit_df_base["transit_access"].min()
                    mx = transit_df_base["transit_access"].max()
                    transit_df_sim["transit_access_sim_norm"] = (
                        (transit_df_sim["transit_access_sim"] - mn) / (mx - mn) * 100
                    ).clip(0, 100).round(1)

                    equity_sim = transit_df_sim.set_index("Neighbourhood")[["transit_access_sim_norm"]].copy()
                    equity_sim["need_score"]     = need_score.round(1)
                    equity_sim["equity_gap_sim"] = (equity_sim["need_score"] - equity_sim["transit_access_sim_norm"]).round(1)
                    equity_sim = equity_sim.round(1)

                    comparison = equity_base[["need_score", "transit_access_norm", "equity_gap"]].join(
                        equity_sim[["transit_access_sim_norm", "equity_gap_sim"]]
                    )
                    comparison["delta_access"] = (comparison["transit_access_sim_norm"] - comparison["transit_access_norm"]).round(1)
                    comparison["delta_gap"]    = (comparison["equity_gap_sim"]           - comparison["equity_gap"]).round(1)

                n_affected        = int((transit_df_sim["subway_stations_sim"].values !=
                                         transit_df_base["subway_stations"].values).sum())
                mean_delta_gap    = comparison["delta_gap"].mean()
                mean_delta_access = comparison["delta_access"].mean()
                improved  = int((comparison["delta_gap"] < 0).sum())
                worsened  = int((comparison["delta_gap"] > 0).sum())

                gap_class = "impact-pos" if mean_delta_gap < 0 else ("impact-neg" if mean_delta_gap > 0 else "impact-neu")
                acc_class = "impact-pos" if mean_delta_access > 0 else ("impact-neg" if mean_delta_access < 0 else "impact-neu")

                st.markdown(f"""
                <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:28px">
                    <div class="impact-card">
                        <div class="impact-num">{len(new_station_coords)}</div>
                        <div class="impact-lbl">New Subway Stations Added</div>
                    </div>
                    <div class="impact-card">
                        <div class="impact-num">{n_affected}</div>
                        <div class="impact-lbl">Neighbourhoods Affected</div>
                    </div>
                    <div class="impact-card">
                        <div class="impact-num {acc_class}">{mean_delta_access:+.1f}</div>
                        <div class="impact-lbl">Avg Change in Transit Access Score</div>
                    </div>
                    <div class="impact-card">
                        <div class="impact-num {gap_class}">{mean_delta_gap:+.1f}</div>
                        <div class="impact-lbl">Avg Change in Equity Gap</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("#### Side-by-Side Comparison")
                mc1, mc2 = st.columns(2, gap="medium")

                def build_comparison_map(title, choro_data, choro_color, choro_label, new_stations_gdf_wgs=None):
                    fm = folium.Map(location=[43.700, -79.420], zoom_start=11, tiles="CartoDB positron", control_scale=False)
                    folium.Choropleth(
                        geo_data=gdf.to_json(), data=choro_data,
                        columns=["Neighbourhood", "Value"],
                        key_on="feature.properties.AREA_NAME",
                        fill_color=choro_color, fill_opacity=0.75, line_opacity=0.15,
                        legend_name=choro_label, nan_fill_color="transparent",
                    ).add_to(fm)
                    if show_subway:
                        add_subway_to_map(fm, route_polylines, stations)
                    if new_stations_gdf_wgs is not None:
                        new_layer = folium.FeatureGroup(name="New Stations", show=True)
                        for _, s in new_stations_gdf_wgs.iterrows():
                            folium.CircleMarker(
                                location=[s.geometry.y, s.geometry.x],
                                radius=9, color="white", weight=2.5,
                                fill=True, fill_color="#E63946", fill_opacity=1.0,
                                tooltip=s.get("station_name", "New Station"),
                            ).add_to(new_layer)
                        new_layer.add_to(fm)
                    folium.map.Marker(
                        [43.845, -79.53],
                        icon=folium.DivIcon(html=f'<div style="font-family:Arial;font-size:13px;font-weight:600;color:#1d1d1f;background:rgba(255,255,255,0.92);padding:4px 10px;border-radius:6px;border:1px solid #e0e0e5;white-space:nowrap">{title}</div>'),
                    ).add_to(fm)
                    return fm

                base_choro_df = comparison.reset_index()[["Neighbourhood", "equity_gap"]].rename(columns={"equity_gap": "Value"})
                sim_choro_df  = comparison.reset_index()[["Neighbourhood", "equity_gap_sim"]].rename(columns={"equity_gap_sim": "Value"})
                new_stn_wgs84 = new_stations_gdf.to_crs("EPSG:4326")

                with mc1:
                    st.markdown("**Baseline**")
                    fm_base = build_comparison_map("Baseline", base_choro_df, "RdYlGn_r", "Equity Gap — Baseline")
                    st_folium(fm_base, width="100%", height=420, returned_objects=[], key="cmp_map_base")

                with mc2:
                    st.markdown("**Your Simulation**")
                    fm_sim = build_comparison_map("Simulated", sim_choro_df, "RdYlGn_r", "Equity Gap — Simulated", new_stn_wgs84)
                    st_folium(fm_sim, width="100%", height=420, returned_objects=[], key="cmp_map_sim")

                st.markdown(
                    '<p style="font-size:12px;color:#6e6e73;margin-top:4px">'
                    '<span style="color:#E63946">●</span> Red circles = new simulated stations. </p>',
                    unsafe_allow_html=True,
                )

                st.markdown("---")
                st.markdown("#### Top 15 Most Underserved — Baseline vs Simulation")

                top15_base = equity_base.sort_values("equity_gap", ascending=False).head(15).reset_index()
                top15_sim  = equity_sim.sort_values("equity_gap_sim", ascending=False).head(15).reset_index()

                ch1, ch2 = st.columns(2, gap="large")
                with ch1:
                    st.markdown("**Baseline**")
                    d = top15_base[["Neighbourhood", "equity_gap"]].rename(columns={"equity_gap": "Equity Gap"})
                    st.vega_lite_chart(d, vega_bar_chart(d, "Neighbourhood", "Equity Gap", "#C8102E", "Equity Gap"), use_container_width=True)

                with ch2:
                    st.markdown("**Simulation**")
                    d = top15_sim[["Neighbourhood", "equity_gap_sim"]].rename(columns={"equity_gap_sim": "Equity Gap"})
                    st.vega_lite_chart(d, vega_bar_chart(d, "Neighbourhood", "Equity Gap", "#0054A6", "Equity Gap"), use_container_width=True)

                st.markdown("**Change in Equity Gap per Neighbourhood (Top 20 Most Improved)**")
                delta_df = comparison.reset_index()[["Neighbourhood", "delta_gap"]].sort_values("delta_gap").head(20)
                delta_df_chart = delta_df.copy()
                delta_spec = {
                    "mark": {"type": "bar", "opacity": 0.85},
                    "encoding": {
                        "x": {
                            "field": "Neighbourhood", "type": "nominal", "sort": "y",
                            "axis": {"labelAngle": -45, "labelFontSize": 10, "labelColor": "#6e6e73", "title": None},
                        },
                        "y": {
                            "field": "delta_gap", "type": "quantitative",
                            "axis": {"labelFontSize": 10, "labelColor": "#6e6e73", "gridColor": "#f0f0f2",
                                     "title": "Change in Equity Gap (negative = improved)", "titleColor": "#6e6e73", "titleFontSize": 11},
                        },
                        "color": {
                            "condition": {"test": "datum.delta_gap < 0", "value": "#34c759"},
                            "value": "#ff3b30",
                        },
                        "tooltip": [
                            {"field": "Neighbourhood", "type": "nominal"},
                            {"field": "delta_gap", "type": "quantitative", "format": ".1f", "title": "Change in Equity Gap"},
                        ],
                    },
                    "config": {
                        "background": "#ffffff",
                        "view": {"stroke": "transparent", "fill": "#ffffff"},
                        "axis": {"labelFont": "-apple-system, sans-serif", "titleFont": "-apple-system, sans-serif"},
                    },
                    "height": 240,
                }
                st.vega_lite_chart(delta_df_chart, delta_spec, use_container_width=True)

                st.markdown("---")
                st.markdown("#### Full Neighbourhood Comparison Table")
                full_table = comparison.reset_index()
                full_table.columns = [
                    "Neighbourhood", "Need Score",
                    "Transit Access (Baseline)", "Equity Gap (Baseline)",
                    "Transit Access (Simulated)", "Equity Gap (Simulated)",
                    "Change in Transit Access", "Change in Equity Gap",
                ]
                full_table = full_table.sort_values("Change in Equity Gap").reset_index(drop=True)
                full_table.index += 1
                styled_df(full_table)


# ── Tab 6: About ────────────────────────────────────────────────────────────

with tab6:
    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown("#### Purpose")
        st.markdown(
            "TESA helps planners, policymakers, and transit riders "
            "understand how TTC infrastructure aligns with the needs of Toronto's most transit-dependent "
            "communities — and where investment could have the greatest equity impact."
        )
        st.markdown("#### Core Questions")
        st.markdown(
            "Which neighbourhoods rely most on transit, and are they well-served? "
            "Where are concentrations of low-income residents or seniors who depend on transit? "
            "Where would a new station create the most benefit?"
        )
    with col2:
        st.markdown("#### Data Sources")
        styled_df(pd.DataFrame([
            {"Dataset": "Census data",              "Source": "Statistics Canada, 2021",          "Licence": "Open Government Licence"},
            {"Dataset": "Neighbourhood boundaries", "Source": "City of Toronto Open Data",        "Licence": "Open Government Licence"},
            {"Dataset": "GTFS feed",                "Source": "TTC (Toronto Transit Commission)", "Licence": "Open Data"},
            {"Dataset": "Subway shapefile",         "Source": "TTC / OpenStreetMap",              "Licence": "Open Data"},
        ]), index=False)
        st.markdown("#### Privacy Compliance")
        st.markdown(
            "All datasets are open/public with no personally identifiable information. "
            "No individual travel records, smartcard data, or device identifiers are used. "
            "This project complies with the Transit Data Challenge Privacy-First Principle."
        )

    st.markdown("---")
    st.markdown("#### Census Indicators Reference")
    styled_df(pd.DataFrame([{"Indicator": k, "Description": v} for k, v in METRIC_DESCRIPTIONS.items()]), index=False)

    st.markdown("#### Need Score Factors")
    styled_df(pd.DataFrame([
        {"Factor": k, "Census column": v, "Note": "Inverted: lower income = higher need" if k == "Low Median Income" else ""}
        for k, v in NEED_FACTOR_OPTIONS.items()
    ]), index=False)

    st.markdown("#### Methodological Notes")
    st.markdown(
        "**Transit Access Score (Step 1):** Each neighbourhood is scored by counting stops/stations of each mode "
        "(local bus, express bus, streetcar, subway) within mode-specific buffers (400 m, 1200 m, 400 m, 800 m respectively), "
        "applying mode weights (1.0, 1.5, 1.5, 3.0), and dividing by neighbourhood area (km²). "
        "Scores are normalized 0-100 across all neighbourhoods.\n\n"
        "**Need Score (Step 2):** Each selected factor is normalized 0-100, then multiplied by its user-supplied weight. "
        "The weighted average gives the Need Score (0-100). Median income is inverted so lower income = higher need. "
        "Equal weights reproduce the simple average used in simulation_correlation_v2.py.\n\n"
        "**Equity Gap (Result):** Need Score minus Transit Access Score. Positive = underserved relative to need.\n\n"
        "**Simulation:** The GeoJSON exported from the Extension Simulator is parsed for Point features (station markers). "
        "Those stations are added to the existing station set, the Transit Access Score is re-computed, "
        "and the Equity Gap is recalculated using the same Need Score — normalized on the same baseline scale for direct comparability.\n\n"
        "**Limitations**: \n\nLine 3 (Scarborough RT, closed 2023) uses hardcoded coordinates. "
        "Six neighbourhoods with name mismatches between the census and GeoJSON may appear unshaded."
    )

    st.markdown("Developed by Anitra Roy, Maggie Wu, Sameha Tasnim")