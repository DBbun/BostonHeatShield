"""Download the Census county subdivision (city and town) boundaries for Massachusetts.

Used to tell which census tracts belong to Boston, Cambridge and Somerville.
Appends an entry to data_raw/manifest.json. Honest client name; no workarounds if the server refuses.
"""
import datetime
import hashlib
import json
import urllib.request
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data_raw"
H = {"User-Agent": "DBbun-BostonHeatShield (uri.kartoun@dbbun.com)"}
NAME = "10_tiger2024_ma_cousub.zip"
URL = "https://www2.census.gov/geo/tiger/TIGER2024/COUSUB/tl_2024_25_cousub.zip"

data = urllib.request.urlopen(urllib.request.Request(URL, headers=H), timeout=180).read()
(RAW / NAME).write_bytes(data)
man_path = RAW / "manifest.json"
man = [m for m in json.loads(man_path.read_text()) if m["file"] != NAME]
man.append(dict(file=NAME, url=URL, bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                downloaded=datetime.datetime.now().isoformat(timespec="seconds"), status="ok"))
man_path.write_text(json.dumps(man, indent=1))
print("OK", NAME, len(data), "bytes")
