"""Describe the registry population before measuring anything."""

import collections
import json

servers = json.load(open("registry_servers.json"))
official = "io.modelcontextprotocol.registry/official"

active = [s for s in servers if s["_meta"][official].get("status") == "active"]

registry_types = collections.Counter()
transports = collections.Counter()
npm_stdio = []
shape = collections.Counter()

for s in active:
    srv = s["server"]
    pkgs = srv.get("packages") or []
    remotes = srv.get("remotes") or []
    if pkgs and remotes:
        shape["both packages and remotes"] += 1
    elif pkgs:
        shape["packages only"] += 1
    elif remotes:
        shape["remotes only"] += 1
    else:
        shape["neither"] += 1

    for p in pkgs:
        rt = p.get("registryType", "?")
        registry_types[rt] += 1
        tt = (p.get("transport") or {}).get("type", "?")
        transports[f"{rt}/{tt}"] += 1
        if rt == "npm" and tt == "stdio":
            npm_stdio.append({
                "name": srv["name"],
                "identifier": p.get("identifier"),
                "version": p.get("version"),
            })

print(f"active servers: {len(active)}\n")
print("shape:")
for k, v in shape.most_common():
    print(f"  {k:28} {v:6}")
print("\nregistryType (per package entry):")
for k, v in registry_types.most_common(10):
    print(f"  {k:28} {v:6}")
print("\nnpm transports:")
for k, v in transports.most_common(8):
    if k.startswith("npm/"):
        print(f"  {k:28} {v:6}")

ids = [e["identifier"] for e in npm_stdio if e["identifier"]]
print(f"\nnpm + stdio package entries : {len(npm_stdio)}")
print(f"distinct npm identifiers    : {len(set(ids))}")

json.dump(npm_stdio, open("npm_stdio.json", "w"))
