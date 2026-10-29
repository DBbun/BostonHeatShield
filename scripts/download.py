import urllib.request, hashlib, json, os, datetime, sys
ROOT=r"D:\DBBun\Misc\NIHHIS Heat Challenge 2026\data_raw"
H={"User-Agent":"Mozilla/5.0 (DBbun research; uri.kartoun@dbbun.com)"}
B="https://data.boston.gov/dataset/"
ITEMS=[
("01_boston_social_vulnerability.geojson","https://bostonopendata-boston.opendata.arcgis.com/api/download/v1/items/34f2c48b670d4b43a617b1540f20efe3/geojson?layers=0"),
("01_boston_social_vulnerability.csv","https://bostonopendata-boston.opendata.arcgis.com/api/download/v1/items/34f2c48b670d4b43a617b1540f20efe3/csv?layers=0"),
("02_community_centers.geojson",B+"33f63508-d3d0-4cea-a6bf-94c487ad745e/resource/b3b8525f-af13-413a-a766-e70287df4bb3/download/community_centers.geojson"),
("02_community_center_pools.geojson",B+"321c0d5f-fade-4cd1-be50-4674419fd946/resource/b61ef2fd-1324-4482-8ccd-4228f17dc0d7/download/community_center_pools.geojson"),
("03_urban_forest_priority_zones.geojson",B+"c8c042fb-fa02-4662-a523-593c21bb3b87/resource/41bb1f69-18a8-4016-bd82-37267abea881/download/priority_zones.geojson"),
("03_urban_forest_ej_tracts.geojson",B+"c8c042fb-fa02-4662-a523-593c21bb3b87/resource/37163833-9fc4-4a83-a2ec-7250e4313467/download/priority_zone_indicators_priority_ej_census_tracts.geojson"),
("03_urban_forest_heat_event_hours.geojson",B+"c8c042fb-fa02-4662-a523-593c21bb3b87/resource/b6ed8b78-0778-4689-aeaa-dd640fc8d6cc/download/priority_zone_indicators_priority_heat_event_hours_.geojson"),
("03_urban_forest_holc.geojson",B+"c8c042fb-fa02-4662-a523-593c21bb3b87/resource/eda9e38e-04f4-4b64-9a28-a0368a9d9117/download/priority_zone_indicators_priority_holc_boundaries.geojson"),
("03_urban_forest_low_canopy_tracts.geojson",B+"c8c042fb-fa02-4662-a523-593c21bb3b87/resource/53e1312d-aded-42c6-96f0-7f257f3c914d/download/priority_zone_indicators_priority_low_canopy_census_tracts.geojson"),
("03_urban_forest_datadictionary.xlsx",B+"c8c042fb-fa02-4662-a523-593c21bb3b87/resource/58d4715d-29ca-4cb2-be79-1a329c74e0a5/download/datadictionary.xlsx"),
("04_tiger2024_ma_tracts.zip","https://www2.census.gov/geo/tiger/TIGER2024/TRACT/tl_2024_25_tract.zip"),
("05_cdc_svi2022_ma.csv","https://svi.cdc.gov/Documents/Data/2022/csv/states/Massachusetts.csv"),
("06_cdc_places_tract_ma.csv","https://data.cdc.gov/resource/yjkw-uj5s.csv?stateabbr=MA&$limit=50000"),
("07_lace2023_tract.csv","https://www2.census.gov/programs-surveys/demo/datasets/lace/2023/LACE_23_Tract.csv"),
("07_lace2023_county.csv","https://www2.census.gov/programs-surveys/demo/datasets/lace/2023/LACE_23_County.csv"),
("07_lace2023_quick_guide.pdf","https://www2.census.gov/programs-surveys/demo/technical-documentation/lace/2023-LACE-Quick-Guide.pdf"),
("08_mbta_gtfs.zip","https://cdn.mbta.com/MBTA_GTFS.zip"),
("09_massgis_hospitals_pt.zip","https://s3.us-east-1.amazonaws.com/download.massgis.digital.mass.gov/shapefiles/state/hospitals_pt.zip"),
]
man=[]
for name,url in ITEMS:
    p=os.path.join(ROOT,name)
    try:
        data=urllib.request.urlopen(urllib.request.Request(url,headers=H),timeout=180).read()
        open(p,"wb").write(data)
        man.append(dict(file=name,url=url,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),downloaded=datetime.datetime.now().isoformat(timespec="seconds"),status="ok"))
        print("OK  ",name,len(data))
    except Exception as e:
        man.append(dict(file=name,url=url,status="FAILED: "+str(e)[:120]))
        print("FAIL",name,str(e)[:120])
json.dump(man,open(os.path.join(ROOT,"manifest.json"),"w"),indent=1)
