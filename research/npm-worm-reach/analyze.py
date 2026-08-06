"""Reprint every figure in the post, labelled as it appears there.

Reads only trees.jsonl(.gz), compromised-names.txt and wiz-keyv-packages.csv.
Nothing here touches the network, so the numbers it prints are exactly the ones
the shipped data supports. The figures in the post that are not reproducible
from these files are the OSV advisory IDs, which are quoted from api.osv.dev
and named inline.

Usage:
    python3 analyze.py
"""

import csv
import gzip
import io
import json
import os
import statistics as st
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))


def load_trees():
    plain = os.path.join(HERE, "trees.jsonl")
    packed = plain + ".gz"
    if os.path.exists(plain):
        stream = open(plain, encoding="utf-8")
    else:
        stream = io.TextIOWrapper(gzip.open(packed, "rb"), encoding="utf-8")
    with stream as f:
        return [json.loads(line) for line in f if line.strip()]


def load_compromised():
    with open(os.path.join(HERE, "compromised-names.txt"), encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}


def load_wiz():
    names = set()
    with open(os.path.join(HERE, "wiz-keyv-packages.csv"), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            names.add(row["Package"].strip())
    return names


def rule(title):
    print(f"\n{title}\n{'-' * len(title)}")


def main():
    rows = load_trees()
    bad = load_compromised()
    wiz = load_wiz()
    ok = [r for r in rows if r.get("ok")]
    failed = [r for r in rows if not r.get("ok")]

    for r in ok:
        r["hits"] = sorted(set(r["packages"]) & bad)
    exposed = [r for r in ok if r["hits"]]

    rule("Population")
    print(f"rows (distinct npm identifiers)        {len(rows)}")
    print(f"resolved                               {len(ok)}")
    print(f"did not resolve                        {len(failed)}")
    errs = Counter(r.get("error", "?") for r in failed)
    for code, label in [
        ("ETARGET", "version no longer published"),
        ("E404", "package gone from npm"),
        ("EUNSUPPORTEDPROTOCOL", "identifier not parseable as a spec"),
        ("EBADPLATFORM", "refuses this platform"),
        ("timeout", "timed out"),
        ("exit 1", "exited non-zero"),
    ]:
        if errs.get(code):
            print(f"  {errs[code]:>4}  {label} ({code})")

    totals = [r["total"] for r in ok]
    rule("Install size")
    print(f"median packages per server             {st.median(totals):.0f}")
    print("(the 2026-07-31 census run of the same population gave 94, over 6,030 resolved;")
    print(" the drift is transitive caret ranges resolving against a newer registry)")

    rule("Compromised-set reach")
    print(f"compromised names checked against      {len(bad)}")
    print(f"servers reaching at least one          {len(exposed)} / {len(ok)}"
          f"  = {len(exposed) / len(ok) * 100:.2f}%")
    print(f"exposed median tree                    {st.median([r['total'] for r in exposed]):.0f}")
    print(f"exposed smallest tree                  {min(r['total'] for r in exposed)}")
    print(f"exposed largest tree                   {max(r['total'] for r in exposed)}")

    rule("Exposure by tree size")
    buckets = [(0, 25), (25, 50), (50, 100), (100, 200), (200, 400), (400, 10 ** 9)]
    for lo, hi in buckets:
        grp = [r for r in ok if lo <= r["total"] < hi]
        if not grp:
            continue
        n = sum(1 for r in grp if r["hits"])
        label = f"{lo}-{hi}" if hi < 10 ** 9 else f"{lo}+"
        print(f"  {label:>9} packages  {len(grp):>5} servers  {n:>3} exposed"
              f"  {n / len(grp) * 100:>6.2f}%")

    med = st.median(totals)
    at_or_below = [r for r in ok if r["total"] <= med]
    above = [r for r in ok if r["total"] > med]
    print(f"\n  at or below the median ({med:.0f})   "
          f"{sum(1 for r in at_or_below if r['hits'])} / {len(at_or_below)}")
    print(f"  above the median              "
          f"{sum(1 for r in above if r['hits'])} / {len(above)}")

    rule("How the exposed trees reach the set")
    for pkg in ("got", "cacheable-request", "eslint"):
        n = sum(1 for r in exposed if pkg in r["packages"])
        print(f"  {pkg:<20} {n:>3} / {len(exposed)}")
    print("\n  matched names, by how many trees carry them:")
    per = Counter(h for r in exposed for h in r["hits"])
    for name, n in per.most_common():
        print(f"    {name:<26} {n}")

    rule("Install-time execution surface")
    counts = [len(r["install_scripts"]) for r in ok]
    withs = [c for c in counts if c]
    print(f"trees with at least one install script {len(withs)} / {len(ok)}"
          f"  = {len(withs) / len(ok) * 100:.1f}%")
    print(f"population median                      {st.median(counts):.0f}")
    print(f"largest                                {max(counts)}")
    top = Counter(p for r in ok for p in r["install_scripts"])
    for name, n in top.most_common(4):
        print(f"  {name:<24} {n:>4} trees")

    rule("Gap in the most-mirrored IOC list")
    gap = bad - wiz
    print(f"names in wiz-keyv-packages.csv         {len(wiz)}")
    print(f"names in the merged list               {len(bad)}")
    print(f"in the merged list only                {len(gap)}")
    print("  " + ", ".join(sorted(gap)))
    blind = [r for r in exposed if (set(r["packages"]) & gap)
             and not (set(r["packages"]) & wiz)]
    reach_gap = [r for r in exposed if set(r["packages"]) & gap]
    print(f"\nservers reaching a gap-only name       {len(reach_gap)}")
    print(f"servers a wiz-list scan would miss     {len(blind)}")

    print("\nNote on reading trees.jsonl: a hit means a name from the compromised")
    print("set is reachable in that tree as resolved on 2026-08-06, after the")
    print("malicious versions were pulled. It is not a finding that the server")
    print("shipped malware, and it is not a defect in that server.")


if __name__ == "__main__":
    main()
