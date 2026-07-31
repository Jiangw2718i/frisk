"""Quantify the instrument's residual error with real installs on a random sample.

measure.py resolves trees without downloading tarballs, which is the only way to
cover 6,139 packages. This runs actual installs on a random subset and reports
where the two disagree, so the article can state a measured error bound instead
of claiming exactness it has not earned.
"""

import json
import os
import random
import shutil
import statistics
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor

from measure import measure, targets

N = int(os.environ.get("N", "150"))
SEED = 20260730


def real_install(spec):
    tmp = tempfile.mkdtemp(prefix="mcpreal-")
    try:
        with open(os.path.join(tmp, "package.json"), "w") as f:
            json.dump({"name": "probe", "version": "1.0.0", "private": True}, f)
        proc = subprocess.run(
            ["npm", "install", spec, "--omit=dev", "--no-audit", "--no-fund",
             "--silent", "--ignore-scripts"],
            cwd=tmp, capture_output=True, text=True, timeout=900,
        )
        if proc.returncode != 0:
            return None
        listing = subprocess.run(
            ["npm", "ls", "--omit=dev", "--all", "--parseable"],
            cwd=tmp, capture_output=True, text=True, timeout=300,
        )
        return sum(1 for line in listing.stdout.splitlines() if "node_modules" in line)
    except subprocess.TimeoutExpired:
        return None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def one(entry):
    got = measure(entry)
    if not got.get("ok"):
        return None
    real = real_install(got["spec"])
    if real is None:
        return None
    return {
        "spec": got["spec"],
        "measured": got["total"],
        "real": real,
        "optional_entries": got["optional_entries"],
    }


random.seed(SEED)
sample = random.sample(targets(), N)
print(f"real-installing {N} random packages (seed {SEED})", flush=True)

with ThreadPoolExecutor(max_workers=6) as pool:
    results = [r for r in pool.map(one, sample) if r]

print(f"comparable: {len(results)}\n")

exact = [r for r in results if r["measured"] == r["real"]]
over = [r for r in results if r["measured"] > r["real"]]
under = [r for r in results if r["measured"] < r["real"]]

print(f"exact       : {len(exact)}/{len(results)} ({100*len(exact)/len(results):.1f}%)")
print(f"overcounts  : {len(over)}")
print(f"undercounts : {len(under)}")

no_opt = [r for r in results if r["optional_entries"] == 0]
with_opt = [r for r in results if r["optional_entries"] > 0]
for label, group in (("no optional entries", no_opt), ("has optional entries", with_opt)):
    if not group:
        continue
    ex = sum(1 for r in group if r["measured"] == r["real"])
    print(f"  {label:22} n={len(group):4}  exact {ex:4} ({100*ex/len(group):5.1f}%)")

if over:
    errs = sorted(100 * (r["measured"] - r["real"]) / r["real"] for r in over)
    print(f"\novercount magnitude: median {statistics.median(errs):.1f}%  worst {errs[-1]:.1f}%")
    for r in sorted(over, key=lambda r: -(r["measured"] - r["real"]))[:5]:
        print(f"    {r['spec']:44} {r['measured']:5} vs {r['real']:5}")
if under:
    for r in under[:5]:
        print(f"  UNDER {r['spec']:44} {r['measured']:5} vs {r['real']:5}")

m = [r["measured"] for r in results]
rl = [r["real"] for r in results]
print(f"\nsample median: measured {int(statistics.median(m))}  real {int(statistics.median(rl))}")
json.dump(results, open("sample_real.json", "w"), indent=1)
