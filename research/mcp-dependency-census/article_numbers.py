"""Recompute every figure the write-up states, from the measured data.

Each line prints the number and the label it appears under in the post, so a
reader can diff this output against the prose instead of taking it on trust.

Needs measurements.jsonl and npm_stdio.json. Figures that also need
registry_servers.json are printed only when that file is present, since it is
an 18 MB crawl of someone else's service and is not checked in — regenerate it
with fetch_registry.py.
"""

import json
import os
import statistics
from collections import Counter

rows = [json.loads(line) for line in open("measurements.jsonl")]
by_ident = {}
for r in rows:
    by_ident.setdefault(r["spec"].rsplit("@", 1)[0], r)
rows = list(by_ident.values())
ok = [r for r in rows if r["ok"]]
bad = [r for r in rows if not r["ok"]]
totals = sorted(r["total"] for r in ok)


def line(label, value):
    print(f"{value:>10}  {label}")


print("== population ==")
line("distinct npm+stdio packages measured", len(rows))
line("resolved", len(ok))
line("did not resolve", len(bad))
for err, n in Counter(b.get("error", "?") for b in bad).most_common():
    line(f"    failure: {err}", n)

entries = json.load(open("npm_stdio.json"))
per_ident = Counter(e["identifier"] for e in entries if e.get("identifier"))
line("packages listed under >1 server name", sum(1 for v in per_ident.values() if v > 1))

print("\n== distribution ==")
line("median packages installed", int(statistics.median(totals)))
q = statistics.quantiles(totals, n=4)
line("p25", int(q[0]))
line("p75", int(q[2]))
line("heaviest single install", totals[-1])
for lo, hi in [(1, 1), (2, 5), (6, 20), (21, 50), (51, 100), (101, 250), (251, 10**9)]:
    n = sum(1 for t in totals if lo <= t <= hi)
    label = f"{lo}" if lo == hi else (f"{lo}-{hi}" if hi < 10**9 else f"{lo}+")
    print(f"{n:>10}  bucket {label:<9} ({100 * n / len(totals):.1f}%)")

med = int(statistics.median(totals))
line(f"resolve to exactly {med}", sum(1 for t in totals if t == med))
near = sum(1 for t in totals if abs(t - med) <= 5)
print(f"{near:>10}  within five packages of the median ({100 * near / len(totals):.1f}%)")

print("\n== HTTP frameworks in stdio servers ==")
with_fw = [r for r in ok if r["frameworks"]]
print(f"{len(with_fw):>10}  install a framework ({100 * len(with_fw) / len(ok):.1f}%)")
for name, n in Counter(f for r in with_fw for f in r["frameworks"]).most_common():
    line(f"    {name}", n)
v1_share_of_fw = sum(1 for r in with_fw if r["sdk_v1"])
print(f"{v1_share_of_fw:>10}  of those also carry SDK v1 "
      f"({100 * v1_share_of_fw / len(with_fw):.1f}%)")

print("\n== which SDK ==")
v1 = [r for r in ok if r["sdk_v1"]]
v2 = [r for r in ok if r["sdk_v2"]]
neither = [r for r in ok if not r["sdk_v1"] and not r["sdk_v2"]]
print(f"{len(v1):>10}  have SDK v1 ({100 * len(v1) / len(ok):.1f}%)")
line("    median install for that cohort", int(statistics.median([r["total"] for r in v1])))
print(f"{len(v2):>10}  have SDK v2 ({100 * len(v2) / len(ok):.1f}%)")
both = [r for r in v2 if r["sdk_v1"]]
line("    of those, still carrying v1 too", len(both))
if both:
    t = sorted(r["total"] for r in both)
    line("        their installs range from", t[0])
    line("        to", t[-1])
line("have neither SDK in the prod tree", len(neither))
if neither:
    line("    their median install", int(statistics.median([r["total"] for r in neither])))
line("install exactly one package", sum(1 for t in totals if t == 1))

# The wall: packages on the current v1 SDK that add nothing npm has to unpack
# beyond it. 1 (themselves) + the SDK's own resolved tree.
cur = Counter(r["sdk_v1_version"] for r in v1 if r.get("sdk_v1_version")).most_common(1)
if cur:
    version, n_cur = cur[0]
    at_wall = [r for r in v1 if r.get("sdk_v1_version") == version and r["total"] == med]
    print(f"\n{n_cur:>10}  resolve SDK v1 at its current version ({version})")
    print(f"{len(at_wall):>10}  of those land on exactly {med} "
          f"({100 * len(at_wall) / n_cur:.1f}%)")

if os.path.exists("registry_servers.json"):
    print("\n== registry shape ==")
    servers = json.load(open("registry_servers.json"))
    official = "io.modelcontextprotocol.registry/official"
    active = [s for s in servers if s["_meta"][official].get("status") == "active"]
    line("servers in the registry", len(servers))
    line("marked active", len(active))
    http_too = paired = 0
    stdio_ids = set()
    for s in active:
        pkgs = s["server"].get("packages") or []
        kinds = {(p.get("transport") or {}).get("type") for p in pkgs}
        npm_stdio_here = [
            p for p in pkgs
            if p.get("registryType") == "npm"
            and (p.get("transport") or {}).get("type") == "stdio"
        ]
        if npm_stdio_here and "streamable-http" in kinds:
            http_too += 1
            stdio_ids.update(p.get("identifier") for p in npm_stdio_here)
        if npm_stdio_here and (s["server"].get("remotes") or []):
            paired += 1
    line("npm+stdio packages that also ship a streamable-http entry", len(stdio_ids))
    line("active entries pairing an npm stdio package with a remote endpoint", paired)
else:
    print("\n(registry_servers.json absent — run fetch_registry.py for registry-shape figures)")
