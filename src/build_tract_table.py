"""Build one Boston table keyed by 2020 census tract from the public files in data_raw.

Usage: python src/build_tract_table.py [raw_dir] [out_dir]

Inputs (all public, see data_raw/manifest.json):
  04 TIGER 2024 MA tracts (2020 tract geography)   -> geometry and GEOID
  01 Climate Ready Boston Social Vulnerability     -> 2010 tracts, used for city boundary,
                                                      neighborhood name, vulnerability shares
  05 CDC SVI 2022, 06 CDC PLACES, 07 Census LACE 2023 (all 2020 tracts)
  02 Community centers and pools (points)
  08 MBTA GTFS (stations and bus stops, counted per tract)

Outputs: boston_tracts.csv and boston_tracts.geojson in out_dir, plus a coverage report.
Everything here is real public data or a modeled estimate. LACE is experimental and modeled.
"""
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

from gtfs_utils import load_stops

RAW = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "data_raw"
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parents[1] / "data_processed"
OUT.mkdir(exist_ok=True)

SVI_COLS = ["E_TOTPOP", "EP_POV150", "EP_AGE65", "EP_AGE17", "EP_DISABL", "EP_NOVEH",
            "EP_LIMENG", "EP_MINRTY", "EP_MUNIT", "EP_NOINT", "RPL_THEMES", "RPL_THEME1",
            "MP_POV150", "MP_AGE65", "MP_DISABL", "MP_NOVEH", "MP_LIMENG",   # margins of error (90%)
            "RPL_THEME2", "RPL_THEME3", "RPL_THEME4"]
PLACES_COLS = ["casthma", "copd", "chd", "diabetes", "bphigh", "disability", "phlth", "loneliness"]
CRB_COUNTS = ["TotDis", "TotChild", "OlderAdult", "Low_to_No", "LEP", "POC2", "MedIllnes"]


def read_tracts() -> gpd.GeoDataFrame:
    t = gpd.read_file(f"zip://{RAW / '04_tiger2024_ma_tracts.zip'}")
    return t[t.COUNTYFP.isin(["025", "017"])][["GEOID", "ALAND", "geometry"]].to_crs(4326)


def read_crb() -> gpd.GeoDataFrame:
    crb = gpd.read_file(RAW / "01_boston_social_vulnerability.geojson").to_crs(4326)
    pop = crb["POP100_RE"].replace(0, np.nan)
    for c in CRB_COUNTS:
        crb[f"crb_{c}_share"] = (crb[c] / pop).round(4)
    crb["crb_pop2010based"] = crb["POP100_RE"]
    keep = ["GEOID10", "Name", "crb_pop2010based"] + [f"crb_{c}_share" for c in CRB_COUNTS]
    return crb[keep + ["geometry"]]


def main() -> None:
    tracts = read_tracts()
    crb = read_crb()

    # Study tracts: Boston (2020 tracts whose representative point lies inside the city outline),
    # plus Cambridge and Somerville (inside the Census county subdivision for each city).
    outline = crb.geometry.union_all()
    pts = tracts.geometry.representative_point()
    tracts["city"] = np.where(pts.within(outline), "Boston", None)
    cousub = gpd.read_file(f"zip://{RAW / '10_tiger2024_ma_cousub.zip'}").to_crs(4326)
    for name in ("Cambridge", "Somerville"):
        poly = cousub[(cousub.NAME == name) & (cousub.COUNTYFP == "017")].geometry.union_all()
        tracts.loc[pts.within(poly) & tracts["city"].isna(), "city"] = name
    boston = tracts[tracts["city"].notna()].copy()

    # Neighborhood name and CRB shares: exact GEOID match, else the 2010 tract with most overlap.
    crb_attrs = crb.drop(columns="geometry").set_index("GEOID10")
    exact = boston["GEOID"].isin(crb_attrs.index)
    is_bos = boston["city"] == "Boston"
    boston["crb_join"] = np.where(exact, "exact", np.where(is_bos, "overlap", "n/a"))
    proj = 26986  # Massachusetts Mainland state plane, metres, for area math
    ov = gpd.overlay(boston.loc[is_bos, ["GEOID", "geometry"]].to_crs(proj),
                     crb[["GEOID10", "geometry"]].to_crs(proj), how="intersection")
    ov["area"] = ov.geometry.area
    best = ov.sort_values("area", ascending=False).drop_duplicates("GEOID").set_index("GEOID")["GEOID10"]
    boston["crb_geoid10"] = np.where(exact, boston["GEOID"], boston["GEOID"].map(best))
    boston = boston.join(crb_attrs, on="crb_geoid10").rename(columns={"Name": "neighborhood"})

    # CDC SVI 2022 (-999 means missing)
    svi = pd.read_csv(RAW / "05_cdc_svi2022_ma.csv", dtype={"FIPS": str}, usecols=["FIPS"] + SVI_COLS)
    svi = svi.replace(-999, np.nan).rename(columns={c: f"svi_{c}" for c in SVI_COLS})
    boston = boston.merge(svi, left_on="GEOID", right_on="FIPS", how="left").drop(columns="FIPS")

    # CDC PLACES (crude prevalence, model-based small-area estimates)
    ci_cols = [f"{c}_crude95ci" for c in PLACES_COLS]
    pl = pd.read_csv(RAW / "06_cdc_places_tract_ma.csv", dtype={"tractfips": str},
                     usecols=["tractfips"] + [f"{c}_crudeprev" for c in PLACES_COLS] + ci_cols)
    pl = pl.rename(columns={f"{c}_crudeprev": f"places_{c}_pct" for c in PLACES_COLS})
    for c in PLACES_COLS:  # 95% confidence interval arrives as text like "( 9.6, 12.3)"
        ci = pl.pop(f"{c}_crude95ci").str.extract(r"\(\s*([\d.]+)\s*,\s*([\d.]+)\s*\)").astype(float)
        pl[f"places_{c}_lo"], pl[f"places_{c}_hi"] = ci[0], ci[1]
    boston = boston.merge(pl, left_on="GEOID", right_on="tractfips", how="left").drop(columns="tractfips")

    # Census LACE 2023 air conditioning (experimental, modeled)
    la = pd.read_csv(RAW / "07_lace2023_tract.csv", dtype={"GEO_ID": str},
                     usecols=["GEO_ID", "HSE_OCC_E", "AC_PE", "AC_PM", "NO_AC_E", "NO_AC_PE", "NO_AC_PM"])
    num_cols = [c for c in la.columns if c not in ("GEO_ID",)]
    # Census codes for "not available" (-666666666 estimate, -222222222 margin of error) are not values
    la[num_cols] = la[num_cols].where(la[num_cols] > -100)
    la["GEOID"] = la["GEO_ID"].str[-11:]
    la = la.drop(columns="GEO_ID").rename(columns={c: f"lace_{c}" for c in la.columns if c != "GEOID"})
    boston = boston.merge(la, on="GEOID", how="left")

    is_bos = boston["city"] == "Boston"  # recomputed: merges above reset the index
    # Cooling-related facilities from the city (points inside each tract)
    for name, f in [("community_centers", "02_community_centers.geojson"),
                    ("pools", "02_community_center_pools.geojson")]:
        p = gpd.read_file(RAW / f).to_crs(4326)
        bos_only = boston.loc[is_bos, ["GEOID", "geometry"]]
        joined = gpd.sjoin(p, bos_only, predicate="within")
        # Shoreline sites can fall just outside land-clipped tracts: snap them to a tract within 500 m.
        missed = p.loc[~p.index.isin(joined.index)]
        if len(missed):
            snap = gpd.sjoin_nearest(missed.to_crs(proj), bos_only.to_crs(proj), max_distance=500)
            joined = pd.concat([joined[["GEOID"]], snap[["GEOID"]]])
        counts = boston["GEOID"].map(joined.groupby("GEOID").size()).fillna(0).astype("Int64")
        counts[~is_bos] = pd.NA  # the city lists cover Boston only; "not loaded" is not the same as zero
        boston[f"n_{name}"] = counts

    # MBTA stops and stations from the GTFS feed (rapid transit = subway and Green/Mattapan light rail)
    transit = load_stops(RAW / "08_mbta_gtfs.zip")
    for key, col in [("rapid", "n_rapid_stations"), ("commuter", "n_commuter_rail_stations"),
                     ("bus", "n_bus_stops")]:
        joined = gpd.sjoin(transit[key], boston[["GEOID", "geometry"]], predicate="within")
        boston[col] = boston["GEOID"].map(joined.groupby("GEOID").size()).fillna(0).astype(int)

    boston = boston.sort_values("GEOID").reset_index(drop=True)
    # Guard: no agency "missing value" code may survive into the table
    numeric = boston.drop(columns="geometry").select_dtypes("number")
    assert not (numeric <= -100).fillna(False).any().any(), "sentinel missing-value code left in table"
    boston.drop(columns="geometry").to_csv(OUT / "boston_tracts.csv", index=False)
    boston.to_file(OUT / "boston_tracts.geojson", driver="GeoJSON")

    # Coverage report
    n = len(boston)
    print(f"Study tracts (2020 geography): {n}")
    for c, g in boston.groupby("city"):
        print(f"  {c}: {len(g)} tracts, population {g['svi_E_TOTPOP'].sum():,.0f}")
    print(f"  CRB join (Boston only): {int(exact.sum())} exact, {int((boston['crb_join'] == 'overlap').sum())} by largest overlap")
    for col in ["svi_RPL_THEMES", "places_casthma_pct", "lace_NO_AC_PE", "neighborhood"]:
        print(f"  {col}: {boston[col].notna().sum()}/{n} non-missing")
    print(f"  community centers placed: {int(boston['n_community_centers'].sum())}/35, "
          f"pools placed: {int(boston['n_pools'].sum())}/18")
    print(f"  rapid transit stations: {boston['n_rapid_stations'].sum()}, commuter rail stations: "
          f"{boston['n_commuter_rail_stations'].sum()}, bus stops: {boston['n_bus_stops'].sum()}; "
          f"tracts with no bus stop or station: "
          f"{int(((boston['n_bus_stops'] + boston['n_rapid_stations'] + boston['n_commuter_rail_stations']) == 0).sum())}")
    print(f"  total population (SVI 2022): {boston['svi_E_TOTPOP'].sum():,.0f}")
    print(f"Wrote {OUT / 'boston_tracts.csv'} and {OUT / 'boston_tracts.geojson'}")


if __name__ == "__main__":
    main()
