"""Read the pieces of the MBTA GTFS feed that the map uses.

The GTFS zip is read member by member with zipfile; nothing is extracted to disk.
Rapid transit means GTFS route_type 0 (light rail, Green and Mattapan) and 1 (subway: Red, Orange, Blue).
"""
import zipfile

import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, Point

RAPID_TYPES = {"0", "1"}


def _read(z: zipfile.ZipFile, name: str, **kw) -> pd.DataFrame:
    return pd.read_csv(z.open(name), dtype=str, **kw)


def load_stops(zip_path) -> dict:
    """Return rapid transit stations, commuter rail stations and bus stops as point GeoDataFrames."""
    with zipfile.ZipFile(zip_path) as z:
        s = _read(z, "stops.txt")
    s["location_type"] = s["location_type"].fillna("0")
    s["lat"] = s["stop_lat"].astype(float)
    s["lon"] = s["stop_lon"].astype(float)
    platforms = s[s.location_type == "0"]

    def stations(vehicle_types):
        parents = set(platforms[platforms.vehicle_type.isin(vehicle_types)]["parent_station"].dropna())
        st = s[(s.location_type == "1") & s.stop_id.isin(parents)]
        return gpd.GeoDataFrame(st[["stop_id", "stop_name", "municipality"]],
                                geometry=[Point(x, y) for x, y in zip(st.lon, st.lat)], crs=4326)

    bus = platforms[platforms.vehicle_type == "3"]
    return {
        "rapid": stations({"0", "1"}),
        "commuter": stations({"2"}),
        "bus": gpd.GeoDataFrame(bus[["stop_id", "stop_name", "municipality"]],
                                geometry=[Point(x, y) for x, y in zip(bus.lon, bus.lat)], crs=4326),
    }


def load_rapid_lines(zip_path) -> gpd.GeoDataFrame:
    """One line per rapid transit route and direction, using the most-used shape of each."""
    with zipfile.ZipFile(zip_path) as z:
        routes = _read(z, "routes.txt")
        trips = _read(z, "trips.txt", usecols=["route_id", "direction_id", "shape_id"])
        rapid = routes[routes.route_type.isin(RAPID_TYPES)].set_index("route_id")
        trips = trips[trips.route_id.isin(rapid.index)]
        top = (trips.groupby(["route_id", "direction_id", "shape_id"]).size().rename("n").reset_index()
               .sort_values("n", ascending=False).drop_duplicates(["route_id", "direction_id"]))
        shapes = _read(z, "shapes.txt")
    shapes = shapes[shapes.shape_id.isin(top.shape_id)].copy()
    shapes["seq"] = shapes["shape_pt_sequence"].astype(int)
    rows = []
    for _, t in top.iterrows():
        pts = shapes[shapes.shape_id == t.shape_id].sort_values("seq")
        coords = list(zip(pts.shape_pt_lon.astype(float), pts.shape_pt_lat.astype(float)))
        r = rapid.loc[t.route_id]
        rows.append({"route_id": t.route_id, "name": r.route_long_name, "color": "#" + r.route_color,
                     "geometry": LineString(coords)})
    return gpd.GeoDataFrame(rows, crs=4326)
