# TTC Transit Equity Explorer

An interactive Streamlit dashboard that layers TTC transit infrastructure over Toronto neighbourhood census data. Built for the Transit Data Challenge 2026.

The goal is to make it easy to see which communities are most transit-dependent, where service gaps exist, and where a new station would do the most good.

---

## Quick start

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app expects its data files under a `data/` subdirectory (see below). If a file is missing, a red dot appears in the sidebar — you can also upload replacements directly through the UI without restarting.

---

## Data files

| File | What it is |
|---|---|
| `data/census_data.xlsx` | Statistics Canada 2021 census metrics by Toronto neighbourhood |
| `data/Neighbourhoods.geojson` | City of Toronto neighbourhood boundary polygons |
| `data/routes.txt`, `trips.txt`, `stops.txt`, `shapes.txt`, `stop_times.txt` | TTC GTFS feed (drop the extracted files directly into `data/`) |
| `data/ttc-subway-shapefile-wgs84.zip` | TTC subway shapefile — only needed if you want to replace the hardcoded Line 3 geometry |

All sources are open/public data with no PII. See the About tab for licences.

> **Note on Line 3:** The Scarborough RT was closed in 2023 and is no longer in TTC's GTFS feed. The app uses hardcoded coordinates for its alignment and stations, so you won't need a shapefile for it.

---

## What's in each tab

### Census Map
Choropleth of any of 12 census metrics — transit use, income, low-income rate, shelter cost burden, renters, seniors, recent immigrants, visible minority share, and departure time bands. Subway lines render in official TTC colours; bus and streetcar overlays are toggleable from the sidebar. Hover any neighbourhood for its value and underlying count.

### Equity Analysis
Ranked top/bottom-10 tables for each equity-relevant metric, a distribution bar chart across all 158 neighbourhoods, and a per-neighbourhood profile lookup that shows every indicator at once. Useful for spotting where multiple disadvantages overlap.

### Extension Simulator
A freehand drawing tool on top of the census choropleth. Draw a proposed route with the polyline tool, drop station markers, sketch 500 m catchment circles, measure distances, and export the whole thing as GeoJSON. Nothing persists between sessions, so export before you close.

### About
Data source table, privacy compliance note, full metric definitions, and methodology notes (how percentages are calculated, why some neighbourhoods appear unshaded, how GTFS geometry is selected).

---

## Notes

- `stop_times.txt` is very large. The app reads it in 200k-row chunks and filters to subway trips only, so initial load takes a few seconds but subsequent loads are cached.
- Neighbourhood name matching between the census and GeoJSON is done by string equality. About six neighbourhoods have minor naming mismatches and will appear unshaded on the choropleth.
- Percentage values shown in the app represent each neighbourhood's share of the city-wide total for that metric, not the neighbourhood-internal rate. A value of 2.4% for "Public Transit %" means that neighbourhood accounts for 2.4% of all transit commuters in Toronto.