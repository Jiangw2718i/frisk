"""Pull every latest-version server from the official MCP registry.

Keeps the raw records so later analysis can be re-derived without re-crawling.
"""

import json
import time
import urllib.parse
import urllib.request

BASE = "https://registry.modelcontextprotocol.io/v0.1/servers"
OUT = "registry_servers.json"

servers = []
cursor = None
pages = 0

while True:
    url = f"{BASE}?limit=100&version=latest"
    if cursor:
        url += f"&cursor={urllib.parse.quote(cursor, safe='')}"
    with urllib.request.urlopen(url, timeout=30) as r:
        data = json.load(r)
    batch = data.get("servers", [])
    servers.extend(batch)
    pages += 1
    cursor = data.get("metadata", {}).get("nextCursor")
    print(f"page {pages}: +{len(batch)} (total {len(servers)})", flush=True)
    if not cursor or not batch:
        break
    time.sleep(0.2)

with open(OUT, "w") as f:
    json.dump(servers, f)

# Sanity: the registry returns one row per version; version=latest must have
# collapsed those. A duplicate name here means the filter did not work.
names = [s["server"]["name"] for s in servers]
dupes = len(names) - len(set(names))
active = sum(
    1
    for s in servers
    if s["_meta"]["io.modelcontextprotocol.registry/official"].get("status") == "active"
)
print(f"\ntotal rows      : {len(servers)}")
print(f"distinct names  : {len(set(names))}")
print(f"duplicate rows  : {dupes}")
print(f"status=active   : {active}")
