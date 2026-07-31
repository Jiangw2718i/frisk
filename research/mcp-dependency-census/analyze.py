"""Analyse the measured dependency trees.

Every count is "install locations npm resolves for a production install". The
error bound on that is measured, not asserted: sample_real.py real-installs 150
random packages and compares. See the README for what that found, and for the
two bugs the earlier, weaker validation could not have caught.

One row per distinct npm identifier; where the registry lists the same package
under several versions, the first measured row wins.
"""

import json
import statistics
from collections import Counter

rows = [json.loads(line) for line in open("measurements.jsonl")]

by_ident = {}
for r in rows:
    ident = r["spec"].rsplit("@", 1)[0]
    by_ident.setdefault(ident, r)
rows = list(by_ident.values())

ok = [r for r in rows if r["ok"]]
bad = [r for r in rows if not r["ok"]]
totals = sorted(r["total"] for r in ok)

print(f"measured        : {len(rows)} distinct npm packages")
print(f"resolved        : {len(ok)}")
print(f"failed          : {len(bad)}")
if bad:
    for err, n in Counter(b["error"].split(":")[0][:60] for b in bad).most_common(5):
        print(f"    {n:5}  {err}")

print("\n--- packages installed per MCP server ---")
q = statistics.quantiles(totals, n=4)
print(f"min / median / max : {totals[0]} / {int(statistics.median(totals))} / {totals[-1]}")
print(f"quartiles          : p25={int(q[0])}  p50={int(q[1])}  p75={int(q[2])}")
print(f"mean               : {statistics.mean(totals):.1f}")

buckets = [(1, 1), (2, 5), (6, 20), (21, 50), (51, 100), (101, 250), (251, 10**9)]
print("\ndistribution:")
for lo, hi in buckets:
    n = sum(1 for t in totals if lo <= t <= hi)
    label = f"{lo}" if lo == hi else (f"{lo}-{hi}" if hi < 10**9 else f"{lo}+")
    bar = "#" * round(60 * n / len(totals))
    print(f"  {label:>8} {n:5} ({100*n/len(totals):4.1f}%) {bar}")

print("\n--- an HTTP framework inside a stdio-only server ---")
with_fw = [r for r in ok if r["frameworks"]]
print(f"servers shipping one : {len(with_fw)} / {len(ok)} ({100*len(with_fw)/len(ok):.1f}%)")
fw_count = Counter(f for r in with_fw for f in r["frameworks"])
for name, n in fw_count.most_common():
    print(f"    {name:22} {n:5}")

print("\n--- which SDK ---")
v1 = [r for r in ok if r["sdk_v1"]]
v2 = [r for r in ok if r["sdk_v2"]]
neither = [r for r in ok if not r["sdk_v1"] and not r["sdk_v2"]]
print(f"SDK v1 (@modelcontextprotocol/sdk)    : {len(v1)} ({100*len(v1)/len(ok):.1f}%)")
print(f"SDK v2 (@modelcontextprotocol/server) : {len(v2)} ({100*len(v2)/len(ok):.1f}%)")
print(f"neither in the prod tree              : {len(neither)}")

for label, group in (("on SDK v1", v1), ("on SDK v2", v2), ("neither", neither)):
    if not group:
        continue
    t = sorted(r["total"] for r in group)
    fw = sum(1 for r in group if r["frameworks"])
    print(f"  {label:10} median {int(statistics.median(t)):4}  "
          f"framework in tree {100*fw/len(group):5.1f}%")

# How much of a v1 server's tree is the SDK itself? The SDK alone resolves to 93.
if v1:
    t = sorted(r["total"] for r in v1)
    print(f"\n  SDK v1 alone resolves to 93 packages; median v1 server is {int(statistics.median(t))}.")

print("\n--- heaviest ---")
for r in sorted(ok, key=lambda r: -r["total"])[:8]:
    print(f"  {r['total']:5}  {r['spec']}")

print("\n--- leanest (single-package installs) ---")
solo = [r for r in ok if r["total"] == 1]
print(f"  {len(solo)} servers install exactly one package (themselves, no dependencies)")

json.dump(
    {
        "measured": len(rows), "resolved": len(ok), "failed": len(bad),
        "median": int(statistics.median(totals)),
        "p25": int(q[0]), "p75": int(q[2]), "max": totals[-1],
        "with_framework": len(with_fw), "framework_pct": 100 * len(with_fw) / len(ok),
        "sdk_v1": len(v1), "sdk_v2": len(v2),
        "solo": len(solo),
    },
    open("summary.json", "w"), indent=1,
)
