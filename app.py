"""
TTC Transit Equity Explorer
Transit Data Challenge 2026
"""

import os, re, io, zipfile, tempfile
import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from folium import plugins
from streamlit_folium import st_folium


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Transit Equity Explorer",
    page_icon="icon.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

_HERE = os.path.dirname(os.path.abspath(__file__))
_DATA = os.path.join(_HERE, "data")

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

/* Collapse toolbar so it doesn't steal vertical space */
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

/* Sidebar */
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

/* Sidebar collapse/expand toggle */
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

/* File status row in sidebar */
.file-row {
    display: flex; align-items: center; gap: 8px;
    padding: 6px 0; font-size: 13px;
    border-bottom: 1px solid #f0f0f5; color: #1d1d1f;
}
.file-row .dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.dot-ok  { background: #34c759; }
.dot-err { background: #ff3b30; }

/* Main content area */
.block-container { padding: 32px 40px !important; max-width: 1400px; }

/* Page header */
.page-header { margin-bottom: 32px; padding-bottom: 24px; border-bottom: 1px solid #e0e0e5; }
.page-header h1 { font-size: 28px; font-weight: 600; color: #1d1d1f !important; margin: 0 0 6px; letter-spacing: -0.5px; }
.page-header p  { font-size: 15px; color: #6e6e73; margin: 0; max-width: 680px; line-height: 1.5; }

/* Four-cell stat strip under the header */
.stat-strip {
    display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 1px; background: #e0e0e5;
    border: 1px solid #e0e0e5; border-radius: 12px;
    overflow: hidden; margin-bottom: 28px;
}
.stat-cell { background: #ffffff; padding: 18px 22px; }
.stat-cell .num { font-size: 26px; font-weight: 600; color: #1d1d1f; letter-spacing: -0.5px; line-height: 1; margin-bottom: 4px; }
.stat-cell .lbl { font-size: 12px; color: #6e6e73; font-weight: 400; }

/* Tabs */
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

/* Selectbox */
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

/* Checkboxes */
[data-testid="stCheckbox"]       { background: transparent !important; }
[data-testid="stCheckbox"] label { background: transparent !important; color: #1d1d1f !important; }
[data-testid="stCheckbox"] input[type="checkbox"] { accent-color: #C8102E !important; }

/* Control panel labels */
.ctrl-label {
    font-size: 11px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.06em; color: #6e6e73; margin-bottom: 8px; margin-top: 20px;
}
.ctrl-label:first-child { margin-top: 0; }

.desc-card {
    background: #f5f5f7; border-radius: 8px; padding: 12px 14px;
    font-size: 13px; color: #6e6e73; line-height: 1.5; margin-top: 8px;
}

/* Transit line legend */
.legend-grid { display: flex; flex-direction: column; gap: 6px; margin-top: 8px; }
.legend-row  { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #1d1d1f; }
.legend-line { width: 20px; height: 3px; border-radius: 2px; flex-shrink: 0; }

/* Instructional note blocks */
.note {
    background: #f5f5f7; border-radius: 8px; padding: 12px 16px;
    font-size: 13px; color: #6e6e73; line-height: 1.6; margin: 16px 0;
}

/* Numbered step list (Extension Simulator) */
.step-list { display: flex; flex-direction: column; gap: 8px; margin: 12px 0; }
.step-row  { display: flex; align-items: flex-start; gap: 12px; font-size: 13px; color: #1d1d1f; line-height: 1.5; }
.step-num  {
    width: 22px; height: 22px; border-radius: 50%;
    background: #C8102E; color: #ffffff;
    font-size: 11px; font-weight: 600;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0; margin-top: 1px;
}

/* Buttons */
.stButton > button {
    background: #ffffff; color: #1d1d1f;
    border: 1px solid #e0e0e5;
    border-radius: 8px; font-size: 13px; font-weight: 500;
    padding: 8px 18px; font-family: inherit;
}
.stButton > button:hover { background: #f5f5f7; border-color: #C8102E; color: #C8102E; }

/* DataFrames */
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

/* Vega-Lite charts */
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

/* File upload expander in sidebar */
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

/* Misc */
h2, h3 { color: #1d1d1f !important; font-weight: 600; }
.stSelectbox > label, .stCheckbox > label { font-size: 13px !important; }
hr { border-color: #e0e0e5; }
[data-testid="stAlert"] { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# DataFrame rendering — custom HTML table so the theme stays consistent
# ---------------------------------------------------------------------------

def styled_df(df, index=True):
    """Render a DataFrame as an HTML table that matches the app's light theme."""
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
# Data loading — all three sources are cached separately
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def load_census(path):
    """
    Parse the census Excel file and pull out the rows we care about.
    Returns a dict of metric name → single-row DataFrame, keyed by neighbourhood.
    """
    df = pd.read_excel(path, engine="openpyxl")
    df = df.set_index(df.columns[0])
    df.index = df.index.astype(str)

    return {
        "Public Transit %":        df.loc[df.index.str.contains("Public transit",                   na=False)],
        "Commute 60+ Min %":       df.loc[df.index.str.contains("60 minutes and over",              na=False)],
        "Depart 7–8 AM %":         df.loc[df.index.str.contains("Between 7 a.m. and 7:59 a.m.",    na=False)],
        "Depart 6–7 AM %":         df.loc[df.index.str.contains("Between 6 a.m. and 6:59 a.m.",    na=False)],
        "Depart 5–6 AM %":         df.loc[df.index.str.contains("Between 5 a.m. and 5:59 a.m.",    na=False)],
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
    """
    Build route polylines and station lists from a GTFS feed directory.
    Subway lines (routes 1, 2, 4) come from shapes.txt.
    Station names are cleaned up and deduplicated from stop_times.txt,
    which we read in chunks to keep memory reasonable.
    Bus and streetcar polylines use the longest shape per route.
    """
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
        """Pick the shape with the most points — usually the full-length trip."""
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
        """Strip direction suffixes and platform noise from station names."""
        n = re.sub(r"\s*-\s*(Northbound|Southbound|Eastbound|Westbound).*", "", raw)
        n = re.sub(r"\s*Platform.*",  "", n)
        n = re.sub(r"\s*-\s*Subway.*", "", n)
        return n.strip()

    stops["stop_id"] = stops["stop_id"].astype(str)

    # stop_times.txt is huge — only keep rows that belong to subway trips
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
        """Return a dict of route_id → {coords, label} using the longest shape per route."""
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

    return route_polylines, stations, bus_lines, streetcar_lines


# ---------------------------------------------------------------------------
# Constants — line geometry, colours, metric metadata
# ---------------------------------------------------------------------------

# Line 3 was decommissioned in 2023 and is absent from current GTFS feeds,
# so we hardcode its stops and approximate alignment here.
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

# Choropleth colour scales — picked to feel distinct per metric category
METRIC_COLORS = {
    "Public Transit %":        "YlOrRd",
    "Commute 60+ Min %":       "OrRd",
    "Depart 7–8 AM %":         "PuRd",
    "Depart 6–7 AM %":         "RdPu",
    "Depart 5–6 AM %":         "BuPu",
    "Median After-Tax Income": "RdYlGn",
    "Low Income (LIM-AT) %":   "YlOrBr",
    "Shelter Cost Burden %":   "Reds",
    "Seniors (65+) %":         "Blues",
    "Recent Immigrants %":     "Greens",
    "Visible Minority %":      "PuBuGn",
    "Renters %":               "BuGn",
}

# These metrics come from census counts, so we convert them to % of city total.
# Median After-Tax Income is already a dollar value and is excluded.
PERCENT_METRICS = {
    "Public Transit %", "Commute 60+ Min %",
    "Depart 7–8 AM %", "Depart 6–7 AM %", "Depart 5–6 AM %",
    "Low Income (LIM-AT) %", "Shelter Cost Burden %",
    "Seniors (65+) %", "Recent Immigrants %",
    "Visible Minority %", "Renters %",
}

METRIC_DESCRIPTIONS = {
    "Public Transit %":        "Share of commuters whose main mode is public transit.",
    "Commute 60+ Min %":       "Share of commuters spending 60+ minutes commuting one-way.",
    "Depart 7–8 AM %":         "Share of workers leaving home between 7:00–7:59 AM.",
    "Depart 6–7 AM %":         "Share of workers leaving home between 6:00–6:59 AM.",
    "Depart 5–6 AM %":         "Share of workers leaving home between 5:00–5:59 AM.",
    "Median After-Tax Income": "Median after-tax household income in the neighbourhood.",
    "Low Income (LIM-AT) %":   "Share of residents below Statistics Canada's Low-Income Measure after tax (poverty threshold based on household size).",
    "Shelter Cost Burden %":   "Share of households spending 30%+ of income on housing.",
    "Seniors (65+) %":         "Share of residents aged 65 and over.",
    "Recent Immigrants %":     "Share of residents who immigrated 2011–2021.",
    "Visible Minority %":      "Share of residents identifying as a visible minority.",
    "Renters %":               "Share of households that rent their dwelling.",
}

# Subset shown in the Equity Analysis tab — the most policy-relevant metrics
EQUITY_METRICS = [
    "Public Transit %", "Low Income (LIM-AT) %", "Median After-Tax Income",
    "Shelter Cost Burden %", "Visible Minority %", "Recent Immigrants %",
    "Renters %", "Seniors (65+) %",
]


# ---------------------------------------------------------------------------
# Helpers — census data wrangling
# ---------------------------------------------------------------------------

def melt_metric_raw(df_metric):
    """Unpivot a single-metric census DataFrame into (Neighbourhood, RawValue) rows."""
    df = df_metric.copy().reset_index()
    df = df.melt(id_vars=df.columns[0], var_name="Neighbourhood", value_name="RawValue")
    df = df.iloc[:, [1, 2]]
    df.columns = ["Neighbourhood", "RawValue"]
    df["RawValue"] = pd.to_numeric(df["RawValue"], errors="coerce")
    return df


def get_melted(metric_name, metrics_dict):
    """
    Return a neighbourhood-level DataFrame with both the raw census count
    and, for count metrics, each neighbourhood's share of the city total.
    """
    df = melt_metric_raw(metrics_dict[metric_name])
    if metric_name in PERCENT_METRICS:
        total = df["RawValue"].sum()
        df["Value"] = (df["RawValue"] / total * 100).round(3) if total else df["RawValue"]
    else:
        df["Value"] = df["RawValue"]
    return df


# ---------------------------------------------------------------------------
# Map helper — draw all four subway lines + station markers
# ---------------------------------------------------------------------------

def add_subway_to_map(m, route_polylines, stations):
    """Add each subway line as a FeatureGroup so users can toggle them independently."""
    for route_id, cfg in LINE_CONFIG.items():
        layer = folium.FeatureGroup(name=cfg["name"], show=True)

        # Draw the polyline — Line 3 uses hardcoded coords since it's gone from GTFS
        if route_id == 3:
            folium.PolyLine(
                locations=LINE3_POLYLINE,
                color=cfg["color"], weight=cfg["weight"],
                opacity=0.85,
                tooltip="Line 3 · Scarborough RT (Closed 2023)",
            ).add_to(layer)
        elif route_id in route_polylines and route_polylines[route_id]:
            folium.PolyLine(
                locations=route_polylines[route_id],
                color=cfg["color"], weight=cfg["weight"],
                opacity=0.85, tooltip=cfg["name"],
            ).add_to(layer)

        # Station dots
        if route_id == 3:
            for s in LINE3_STATIONS:
                folium.CircleMarker(
                    location=[s["lat"], s["lon"]], radius=5,
                    color="white", weight=2, fill=True,
                    fill_color=cfg["color"], fill_opacity=1.0,
                    tooltip=f"{s['name']} (Line 3 – Closed 2023)",
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


# ---------------------------------------------------------------------------
# Sidebar — data file status + map layer toggles
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <h2>Transit Equity Explorer</h2>
        <p>Toronto Transit Commission (TTC)</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">Data files</div>', unsafe_allow_html=True)

    def _frow(label, path, upload_key, accept):
        """Show a coloured dot (green = found, red = missing) and a file-replace expander."""
        uploaded = st.session_state.get(upload_key)
        ok       = (uploaded is not None) or os.path.exists(path)
        cls      = "dot-ok" if ok else "dot-err"
        suffix   = " ✦" if uploaded is not None else ""
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
    _frow("routes.txt / trips.txt / …",   os.path.join(GTFS_DIR, "routes.txt"), "upload_gtfs_zip", ["zip"])
    _frow("ttc-subway-shapefile-wgs84.zip", SUBWAY_ZIP,                          "upload_subway",   ["zip"])

    st.markdown('<div class="sidebar-section" style="margin-top:24px">Map layers</div>', unsafe_allow_html=True)
    show_subway    = st.checkbox("Subway lines",     value=True)
    show_bus       = st.checkbox("Bus routes",       value=True)
    show_streetcar = st.checkbox("Streetcar routes", value=True)

    st.markdown("---")
    st.markdown(
        '<p style="font-size:12px;color:#6e6e73;line-height:1.6">'
        'Data: Statistics Canada · TTC GTFS · City of Toronto Open Data.<br/>'
        'All data is open/public — no PII used.</p>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Load data — try uploaded file first, then fall back to disk
# ---------------------------------------------------------------------------

data_ok = {"census": False, "geo": False, "gtfs": False}
metrics         = {}
gdf             = None
route_polylines = {}
stations        = pd.DataFrame()
bus_lines       = {}
streetcar_lines = {}

with st.spinner("Loading data…"):

    # Census
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

    # GeoJSON
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

    # GTFS — accept either a zip upload or a pre-extracted directory
    gtfs_upload = st.session_state.get("upload_gtfs_zip")
    if gtfs_upload is not None:
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                with zipfile.ZipFile(io.BytesIO(gtfs_upload.getvalue())) as zf:
                    zf.extractall(tmpdir)
                gtfs_root = tmpdir
                # Some zips have a single subdirectory rather than files at the root
                if not os.path.exists(os.path.join(tmpdir, "routes.txt")):
                    for entry in os.listdir(tmpdir):
                        candidate = os.path.join(tmpdir, entry)
                        if os.path.isdir(candidate) and os.path.exists(os.path.join(candidate, "routes.txt")):
                            gtfs_root = candidate
                            break
                route_polylines, stations, bus_lines, streetcar_lines = load_gtfs(gtfs_root)
            data_ok["gtfs"] = True
        except Exception as e:
            st.sidebar.error(f"GTFS (uploaded): {e}")
    elif os.path.exists(os.path.join(GTFS_DIR, "routes.txt")):
        try:
            route_polylines, stations, bus_lines, streetcar_lines = load_gtfs(GTFS_DIR)
            data_ok["gtfs"] = True
        except Exception as e:
            st.sidebar.error(f"GTFS: {e}")


# ---------------------------------------------------------------------------
# Page header + stat strip
# ---------------------------------------------------------------------------

st.markdown("""
<div class="page-header">
    <h1>Transit Equity Explorer (Toronto Transit Commission)</h1>
    <p>Compare Toronto neighbourhood demographics with TTC transit infrastructure.
    Identify service gaps, assess equity needs, and sketch future subway extensions.</p>
</div>
""", unsafe_allow_html=True)

n_sta   = len(stations["station_name"].unique()) if len(stations) > 0 else "—"
n_neigh = len(gdf) if gdf is not None else "—"
n_met   = len(metrics) if metrics else "—"
n_lines = len(route_polylines) + 1   # +1 for the hardcoded Line 3

st.markdown(f"""
<div class="stat-strip">
    <div class="stat-cell" style="border-top:3px solid #C8102E"><div class="num">{n_sta}</div><div class="lbl">Subway stations</div></div>
    <div class="stat-cell" style="border-top:3px solid #FFCD00"><div class="num">{n_neigh}</div><div class="lbl">Neighbourhoods</div></div>
    <div class="stat-cell" style="border-top:3px solid #00A650"><div class="num">{n_met}</div><div class="lbl">Census indicators</div></div>
    <div class="stat-cell" style="border-top:3px solid #0054A6"><div class="num">{n_lines}</div><div class="lbl">Subway lines</div></div>
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

tab1, tab2, tab3, tab4 = st.tabs(["Census Map", "Equity Analysis", "Extension Simulator", "About"])


# ── Tab 1: Census Map ─────────────────────────────────────────────────────

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
            df_m = get_melted(selected_metric, metrics)
            is_pct = selected_metric in PERCENT_METRICS
            legend_name = (
                f"{selected_metric} (% of city total)" if is_pct else selected_metric
            )

            folium.Choropleth(
                geo_data=gdf.to_json(),
                data=df_m,
                columns=["Neighbourhood", "Value"],
                key_on="feature.properties.AREA_NAME",
                fill_color=METRIC_COLORS.get(selected_metric, "YlGnBu"),
                fill_opacity=0.7,
                line_opacity=0.2,
                line_color="#999",
                name=selected_metric,
                legend_name=legend_name,
                nan_fill_color="transparent",
            ).add_to(m)

            # Transparent GeoJson overlay just for the hover tooltips
            merged = gdf.merge(df_m, left_on="AREA_NAME", right_on="Neighbourhood", how="left")
            tooltip_fields  = ["AREA_NAME", "Value", "RawValue"] if is_pct else ["AREA_NAME", "Value"]
            tooltip_aliases = (
                ["Neighbourhood", f"{selected_metric} (% of city)", "Number of individuals"]
                if is_pct else
                ["Neighbourhood", selected_metric]
            )

            folium.GeoJson(
                merged,
                style_function=lambda _: {
                    "fillColor": "transparent", "color": "transparent",
                    "weight": 0, "fillOpacity": 0,
                },
                tooltip=folium.GeoJsonTooltip(
                    fields=tooltip_fields,
                    aliases=tooltip_aliases,
                    localize=True, sticky=True,
                    style=(
                        "background:#fff;color:#1d1d1f;"
                        "font-family:-apple-system,sans-serif;"
                        "font-size:13px;border:1px solid #e0e0e5;border-radius:6px;"
                        "padding:8px 12px;box-shadow:0 2px 8px rgba(0,0,0,0.1);"
                    ),
                ),
            ).add_to(m)

        if show_bus and bus_lines:
            bl = folium.FeatureGroup(name="Bus Routes", show=True)
            for rid, info in bus_lines.items():
                folium.PolyLine(
                    info["coords"], color="#E8871E", weight=1.5,
                    opacity=0.45, tooltip=f"Bus {info['label']}",
                ).add_to(bl)
            bl.add_to(m)

        if show_streetcar and streetcar_lines:
            sl = folium.FeatureGroup(name="Streetcar Routes", show=True)
            for rid, info in streetcar_lines.items():
                folium.PolyLine(
                    info["coords"], color="#C8102E", weight=2,
                    opacity=0.6, tooltip=f"Streetcar {info['label']}",
                ).add_to(sl)
            sl.add_to(m)

        if show_subway:
            add_subway_to_map(m, route_polylines, stations)

        folium.LayerControl(collapsed=True).add_to(m)
        plugins.MousePosition(position="bottomright", separator=" | ", prefix="").add_to(m)

        st_folium(m, width="100%", height=560, returned_objects=[])


# ── Tab 2: Equity Analysis ────────────────────────────────────────────────

with tab2:
    if not data_ok["census"] or not data_ok["geo"]:
        st.info("Census and GeoJSON data required for this view.", icon="ℹ️")
    else:
        eq_metric = st.selectbox("Equity indicator", EQUITY_METRICS)

        if eq_metric in metrics:
            df_eq     = get_melted(eq_metric, metrics).dropna(subset=["Value"])
            is_pct_eq = eq_metric in PERCENT_METRICS

            col_a, col_b = st.columns(2, gap="large")

            with col_a:
                st.markdown("**Highest 10 neighbourhoods**")
                top10 = df_eq.nlargest(10, "Value").reset_index(drop=True)
                top10.index += 1
                if is_pct_eq:
                    display_top = top10[["Neighbourhood", "RawValue", "Value"]].copy()
                    display_top.columns = ["Neighbourhood", "Number of individuals", "% of city total"]
                else:
                    display_top = top10[["Neighbourhood", "Value"]].copy()
                    display_top.columns = ["Neighbourhood", eq_metric]
                styled_df(display_top)

            with col_b:
                st.markdown("**Lowest 10 neighbourhoods**")
                bot10 = df_eq.nsmallest(10, "Value").reset_index(drop=True)
                bot10.index += 1
                if is_pct_eq:
                    display_bot = bot10[["Neighbourhood", "RawValue", "Value"]].copy()
                    display_bot.columns = ["Neighbourhood", "Number of individuals", "% of city total"]
                else:
                    display_bot = bot10[["Neighbourhood", "Value"]].copy()
                    display_bot.columns = ["Neighbourhood", eq_metric]
                styled_df(display_bot)

            st.markdown("**Distribution across all neighbourhoods**")
            chart_df = (
                df_eq[["Neighbourhood", "Value"]]
                .sort_values("Value", ascending=False)
                .reset_index(drop=True)
            )
            st.vega_lite_chart(chart_df, {
                "mark": {"type": "bar", "color": "#C8102E", "opacity": 0.75},
                "encoding": {
                    "x": {
                        "field": "Neighbourhood", "type": "nominal", "sort": "-y",
                        "axis": {
                            "labelAngle": -45, "labelFontSize": 10, "labelColor": "#6e6e73",
                            "tickColor": "#e0e0e5", "domainColor": "#e0e0e5", "title": None,
                        },
                    },
                    "y": {
                        "field": "Value", "type": "quantitative",
                        "axis": {
                            "labelFontSize": 10, "labelColor": "#6e6e73",
                            "gridColor": "#f0f0f2", "domainColor": "#e0e0e5",
                            "title": "% of city total" if is_pct_eq else eq_metric,
                            "titleColor": "#6e6e73", "titleFontSize": 11,
                        },
                    },
                    "tooltip": [
                        {"field": "Neighbourhood", "type": "nominal"},
                        {
                            "field": "Value", "type": "quantitative", "format": ".3f",
                            "title": "% of city total" if is_pct_eq else eq_metric,
                        },
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
                    "style": {
                        "guide-label": {"fill": "#6e6e73"},
                        "guide-title": {"fill": "#6e6e73"},
                    },
                },
                "height": 260,
            }, use_container_width=True)

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
        st.markdown("**Neighbourhood profile**")
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
                        rows.append({
                            "Indicator":             mname,
                            "Number of individuals": f"{int(raw_val):,}" if pd.notna(raw_val) else "—",
                            "% of city total":       f"{pct_val:.3f}%" if pd.notna(pct_val) else "—",
                        })
                    else:
                        rows.append({
                            "Indicator":             mname,
                            "Number of individuals": f"${int(raw_val):,}" if pd.notna(raw_val) else "—",
                            "% of city total":       "—",
                        })
            if rows:
                styled_df(pd.DataFrame(rows).set_index("Indicator"))
            else:
                st.info("No data available for this neighbourhood.")


# ── Tab 3: Extension Simulator ────────────────────────────────────────────

with tab3:
    left2, right2 = st.columns([1, 3], gap="large")

    with left2:
        st.markdown("**How to use**")
        st.markdown("""
        <div class="step-list">
            <div class="step-row"><span class="step-num">1</span><span>Select the <b>polyline tool</b> and click on the map to draw a proposed route. Double-click to finish.</span></div>
            <div class="step-row"><span class="step-num">2</span><span>Use the <b>marker tool</b> to place proposed station stops.</span></div>
            <div class="step-row"><span class="step-num">3</span><span>Use the <b>circle tool</b> to visualise ~500 m walking catchment zones.</span></div>
            <div class="step-row"><span class="step-num">4</span><span>Use the <b>measure tool</b> (top-right) to estimate route distances.</span></div>
            <div class="step-row"><span class="step-num">5</span><span>Click <b>Export</b> to download your proposal as GeoJSON.</span></div>
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
        Drawings are not saved between sessions. Export GeoJSON to preserve your proposal.
        </div>
        """, unsafe_allow_html=True)

    with right2:
        sm = folium.Map(
            location=[43.700, -79.420], zoom_start=11,
            tiles="CartoDB positron", control_scale=True,
        )

        if sim_overlay and sim_metric and data_ok["census"] and data_ok["geo"]:
            ds = get_melted(sim_metric, metrics)
            folium.Choropleth(
                geo_data=gdf.to_json(), data=ds,
                columns=["Neighbourhood", "Value"],
                key_on="feature.properties.AREA_NAME",
                fill_color=METRIC_COLORS.get(sim_metric, "YlGnBu"),
                fill_opacity=0.5, line_opacity=0.15,
                legend_name=(
                    f"{sim_metric} (% of city total)"
                    if sim_metric in PERCENT_METRICS else sim_metric
                ),
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

        st_folium(sm, width="100%", height=560, returned_objects=[])


# ── Tab 4: About ──────────────────────────────────────────────────────────

with tab4:
    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("#### Purpose")
        st.markdown(
            "The TTC Transit Equity Explorer helps planners, policymakers, and transit riders "
            "understand how TTC infrastructure aligns with the needs of Toronto's most transit-dependent "
            "communities — and where investment could have the greatest equity impact."
        )
        st.markdown("#### Core questions")
        st.markdown(
            "Which neighbourhoods rely most on transit, and are they well-served? "
            "Where are concentrations of low-income residents or seniors who depend on transit? "
            "Where would a new station create the most benefit?"
        )

    with col2:
        st.markdown("#### Data sources")
        styled_df(pd.DataFrame([
            {"Dataset": "Census data",              "Source": "Statistics Canada, 2021",          "Licence": "Open Government Licence"},
            {"Dataset": "Neighbourhood boundaries", "Source": "City of Toronto Open Data",        "Licence": "Open Government Licence"},
            {"Dataset": "GTFS feed",                "Source": "TTC (Toronto Transit Commission)", "Licence": "Open Data"},
            {"Dataset": "Subway shapefile",         "Source": "TTC / OpenStreetMap",              "Licence": "Open Data"},
        ]), index=False)

        st.markdown("#### Privacy compliance")
        st.markdown(
            "All datasets are open/public with no personally identifiable information. "
            "No individual travel records, smartcard data, or device identifiers are used. "
            "This project complies with the Transit Data Challenge Privacy-First Principle."
        )

    st.markdown("---")
    st.markdown("#### Census indicators reference")
    styled_df(
        pd.DataFrame([{"Indicator": k, "Description": v} for k, v in METRIC_DESCRIPTIONS.items()]),
        index=False,
    )

    st.markdown("#### Methodological notes")
    st.markdown(
        "**Percentage calculation:** For count-based census metrics (all except Median After-Tax Income), "
        "each neighbourhood's value is divided by the sum across all neighbourhoods and multiplied by 100. "
        "This gives each neighbourhood's true share of the city-wide total — e.g. a value of 2.4% means "
        "that neighbourhood accounts for 2.4% of all public transit commuters in Toronto. "
        "Median After-Tax Income is displayed as a raw dollar value.\n\n"
        "Census values are joined to City of Toronto neighbourhood polygons by name. "
        "GTFS line geometry uses the longest shape per route from shapes.txt, whereas "
        "stop_times.txt is read only for station locations, in subway-filtered chunks for speed. "
        "Line 3 (Scarborough RT, closed 2023) uses hardcoded coordinates as it is absent from the current GTFS feed. "
        "Six neighbourhoods with name mismatches between the census and GeoJSON may appear unshaded."
    )

    st.markdown(
        "Built for the **[Transit Data Challenge 2026](https://www.transitdata2026.ca)** "
        "· Transit Data Symposium · Toronto · June 2026."
    )
    
    st.markdown(
        "Developed by "
        "Anitra Roy, Maggie Wu, Sameha Tasnim"
    )