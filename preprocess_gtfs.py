# locally run to pre-generate the station data as a static file (avoids Streamlit Cloud timing out when trying to run stop_times.txt)
import os, re, pandas as pd

GTFS_DIR = "data"   # adjust if needed

routes = pd.read_csv(os.path.join(GTFS_DIR, "routes.txt"))
trips  = pd.read_csv(os.path.join(GTFS_DIR, "trips.txt"), low_memory=False)
stops = pd.read_csv(os.path.join(GTFS_DIR, "stops.txt"), dtype={"stop_id": str})

SUBWAY_IDS = [1, 2, 4]
subway_trips = trips[trips["route_id"].isin(SUBWAY_IDS)].copy()
subway_trips["trip_id"] = subway_trips["trip_id"].astype(str)
subway_trip_ids = set(subway_trips["trip_id"])

def clean_name(raw):
    n = re.sub(r"\s*-\s*(Northbound|Southbound|Eastbound|Westbound).*", "", raw)
    n = re.sub(r"\s*Platform.*",  "", n)
    n = re.sub(r"\s*-\s*Subway.*", "", n)
    return n.strip()

chunks = []
for chunk in pd.read_csv(
    os.path.join(GTFS_DIR, "stop_times.txt"),
    usecols=["trip_id", "stop_id"], chunksize=200_000, dtype=str,
):
    filtered = chunk[chunk["trip_id"].isin(subway_trip_ids)]
    if len(filtered):
        chunks.append(filtered)

sst = pd.concat(chunks, ignore_index=True).drop_duplicates()
sst = (
    sst
    .merge(subway_trips[["trip_id", "route_id"]], on="trip_id", how="left")
    [["route_id", "stop_id"]].drop_duplicates()
    .merge(stops[["stop_id", "stop_name", "stop_lat", "stop_lon"]], on="stop_id", how="left")
)
sst["station_name"] = sst["stop_name"].apply(clean_name)
sst["stop_lat"] = pd.to_numeric(sst["stop_lat"], errors="coerce")
sst["stop_lon"] = pd.to_numeric(sst["stop_lon"], errors="coerce")
result = sst.drop_duplicates(subset=["route_id", "station_name"]).dropna(subset=["stop_lat","stop_lon"])

result[["route_id","station_name","stop_lat","stop_lon"]].to_csv(
    os.path.join(GTFS_DIR, "stations_precomputed.csv"), index=False
)
print(f"Done — {len(result)} station rows written to data/stations_precomputed.csv")