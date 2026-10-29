import urllib.request, hashlib, json, os, datetime
ROOT=r"D:\DBBun\Misc\NIHHIS Heat Challenge 2026\data_raw"
H={"User-Agent":"DBbun-research-script (uri.kartoun@dbbun.com)"}
Q="/0/query?where=1%3D1&outFields=*&outSR=4326&f=geojson"
ITEMS=[("02_community_centers.geojson","https://services.arcgis.com/sFnw0xNflSi8J0uh/arcgis/rest/services/Community_Centers/FeatureServer"+Q),
("02_community_center_pools.geojson","https://services.arcgis.com/sFnw0xNflSi8J0uh/arcgis/rest/services/Community_center_pools/FeatureServer"+Q)]
mp=os.path.join(ROOT,"manifest.json"); man=json.load(open(mp))
for name,url in ITEMS:
    try:
        data=urllib.request.urlopen(urllib.request.Request(url,headers=H),timeout=120).read()
        n=len(json.loads(data).get("features",[]))
        open(os.path.join(ROOT,name),"wb").write(data)
        man=[m for m in man if m["file"]!=name]
        man.append(dict(file=name,url=url,bytes=len(data),features=n,sha256=hashlib.sha256(data).hexdigest(),downloaded=datetime.datetime.now().isoformat(timespec="seconds"),status="ok"))
        print("OK",name,len(data),n,"features")
    except Exception as e: print("FAIL",name,str(e)[:150])
json.dump(man,open(mp,"w"),indent=1)
