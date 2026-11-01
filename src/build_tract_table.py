"""Build one Boston table keyed by 2020 census tract from the public files in data_raw.

Usage: python src/build_tract_table.py [raw_dir] [out_dir]

Inputs (all public, see data_raw/manifest.json):
  04 TIGER 2024 MA tracts (2020 tract geography)   -> geometry and GEOID
  01 Climate Ready Boston Social Vulnerability     -> 2010 tracts, used for city boundary,
                                                      neighborhood name, vulnerability shares
  05 CDC SVI 2022, 06 CDC PLACES, 07 Census LACE 2023 (all 2020 tracts)
  02 Community centers and pools (points)

Outputs: boston_tracts.csv and boston_tracts.geojson in out_dir, plus a coverage report.
Everything here is real public data or a modeled estimate. LACE is experimental and modeled.
"""
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

RAW = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "data_raw"
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parents[1] / "data_processed"
OUT.mkdir(exist_ok=True)

SVI_COLS = ["E_TOTPOP", "EP_POV150", "EP_AGE65", "EP_AGE17", "EP_DISABL", "EP_NOVEH",
            "EP_LIMENG", "EP_MINRTY", "EP_MUNIT", "EP_NOINT", "RPL_THEMES", "RPL_THEME1",
            "RPL_THEME2", "RPL_THEME3", "RPL_THEME4"]
PLACES_COLS = ["casthma", "copd", "chd", "diabetes", "bphigh", "disability", "phlth", "loneliness"]
CRB_COUNTS = ["TotDis", "TotChild", "OlderAdult", "Low_to_No", "LEP", "POC2", "MedIllnes"]


def read_tracts() -> gpd.GeoDataFrame:
    t = gpd.read_file(f"zip://{RAW / '04_tiger2024_ma_tracts.zip'}")
    return t[t.COUNTYFP == "025"][["GEOID", "ALAND", "geometry"]].to_crs(4326)


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

    # Boston study tracts: 2020 tracts whose representative point lies inside the city outline.
    city = crb.geometry.union_all()
    pts = tracts.geometry.representative_point()
    boston = tracts[pts.within(city)].copy()

    # Neighborhood name and CRB shares: exact GEOID match, else the 2010 tract with most overlap.
    crb_attrs = crb.drop(columns="geometry").set_index("GEOID10")
    exact = boston["GEOID"].isin(crb_attrs.index)
    boston["crb_join"] = np.where(exact, "exact", "overlap")
    proj = 26986  # Massachusetts Mainland state plane, metres, for area math
    ov = gpd.overlay(boston[["GEOID", "geometry"]].to_crs(proj),
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
    pl = pd.read_csv(RAW / "06_cdc_places_tract_ma.csv", dtype={"tractfips": str},
                     usecols=["tractfips"] + [f"{c}_crudeprev" for c in PLACES_COLS])
    pl = pl.rename(columns={f"{c}_crudeprev": f"places_{c}_pct" for c in PLACES_COLS})
    boston = boston.merge(pl, left_on="GEOID", right_on="tractfips", how="left").drop(columns="tractfips")

    # Census LACE 2023 air conditioning (experimental, modeled)
    la = pd.read_csv(RAW / "07_lace2023_tract.csv", dtype={"GEO_ID": str},
                     usecols=["GEO_ID", "HSE_OCC_E", "AC_PE", "AC_PM", "NO_AC_E", "NO_AC_PE", "NO_AC_PM"])
    la["GEOID"] = la["GEO_ID"].str[-11:]
    la = la.drop(columns="GEO_ID").rename(columns={c: f"lace_{c}" for c in la.columns if c != "GEOID"})
    boston = boston.merge(la, on="GEOID", how="left")

    # Cooling-related facilities from the city (points inside each tract)
    for name, f in [("community_centers", "02_community_centers.geojson"),
                    ("pools", "02_community_center_pools.geojson")]:
        p = gpd.read_file(RAW / f).to_crs(4326)
        joined = gpd.sjoin(p, boston[["GEOID", "geometry"]], predicate="within")
        # Shoreline sites can fall just outside land-clipped tracts: snap them to a tract within 500 m.
        missed = p.loc[~p.index.isin(joined.index)]
        if len(missed):
            snap = gpd.sjoin_nearest(missed.to_crs(proj), boston[["GEOID", "geometry"]].to_crs(proj),
                                     max_distance=500)
            joined = pd.concat([joined[["GEOID"]], snap[["GEOID"]]])
        boston[f"n_{name}"] = boston["GEOID"].map(joined.groupby("GEOID").size()).fillna(0).astype(int)

    boston = boston.sort_values("GEOID").reset_index(drop=True)
    boston.drop(columns="geometry").to_csv(OUT / "boston_tracts.csv", index=False)
    boston.to_file(OUT / "boston_tracts.geojson", driver="GeoJSON")

    # Coverage report
    n = len(boston)
    print(f"Boston study tracts (2020 geography): {n}")
    print(f"  CRB join: {int(exact.sum())} exact, {n - int(exact.sum())} by largest overlap")
    for col in ["svi_RPL_THEMES", "places_casthma_pct", "lace_NO_AC_PE", "neighborhood"]:
        print(f"  {col}: {boston[col].notna().sum()}/{n} non-missing")
    print(f"  community centers placed: {boston['n_community_centers'].sum()}/35, "
          f"pools placed: {boston['n_pools'].sum()}/18")
    print(f"  total population (SVI 2022): {boston['svi_E_TOTPOP'].sum():,.0f}")
    print(f"Wrote {OUT / 'boston_tracts.csv'} and {OUT / 'boston_tracts.geojson'}")


if __name__ == "__main__":
    main()
