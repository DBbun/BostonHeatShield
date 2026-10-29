import json, urllib.request
H={"User-Agent":"Mozilla/5.0 (DBbun research; uri.kartoun@dbbun.com)"}
def get(u):
    return urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=60).read()
for pid in ["climate-ready-boston-social-vulnerability","community-centers","community-center-pools","boston-urban-forest-plan"]:
    try:
        d=json.loads(get(f"https://data.boston.gov/api/3/action/package_show?id={pid}"))["result"]
        print(pid, d.get("license_title"), d.get("metadata_modified"))
        for r in d["resources"]: print("  ",r["format"],r["url"],r.get("size"))
    except Exception as e: print(pid,"ERR",e)
