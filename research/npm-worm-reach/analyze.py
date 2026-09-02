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


def load_versions():
    """name -> malicious versions, from the merged list."""
    with open(os.path.join(HERE, "compromised.json"), encoding="utf-8") as f:
        return {p["name"]: p.get("versions", []) for p in json.load(f)["packages"]}


def major(v):
    try:
        return int(str(v).lstrip("^~=v").split(".")[0])
    except (ValueError, AttributeError):
        return None


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
    versions = load_versions()
    ok = [r for r in rows if r.get("ok")]
    failed = [r for r in rows if not r.get("ok")]

    for r in ok:
        r["hits"] = sorted(set(r["packages"]) & bad)
        # A hit is only reachable if the resolved version shares a major with a
        # malicious one. A caret range cannot cross a major, so a tree sitting on
        # keyv 5.6.0 could never have received the malicious 6.0.0.
        r["reachable"] = sorted(
            n for n in r["hits"]
            if major(r["packages"][n]) in {major(v) for v in versions.get(n, [])}
        )
    exposed = [r for r in ok if r["hits"]]
    reachable = [r for r in ok if r["reachable"]]

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
    print("(one entry per installed copy, so a tree holding two versions of the")
    print(" same dependency counts both; the 2026-07-31 census run of the same")
    print(" population gave 94 over 6,030 resolved, on the same definition)")

    rule("Name-level match vs semver reachability")
    print(f"compromised names checked against      {len(bad)}")
    print(f"trees carrying a compromised NAME      {len(exposed)} / {len(ok)}"
          f"  = {len(exposed) / len(ok) * 100:.2f}%")
    print(f"trees where a caret could reach it     {len(reachable)} / {len(ok)}"
          f"  = {len(reachable) / len(ok) * 100:.2f}%")
    print("\n  per name: malicious version vs what resolves here")
    seen = {}
    for r in ok:
        for n in r["hits"]:
            seen.setdefault(n, Counter())[r["packages"][n]] += 1
    for n, c in sorted(seen.items(), key=lambda x: -sum(x[1].values())):
        mal = versions.get(n, [])
        majs = {major(v) for v in mal}
        # Verdict is per resolved version, not per name: one package can be
        # reachable in one tree and a major behind in another.
        got = ", ".join(
            f"{v} x{k} {'[reachable]' if major(v) in majs else '[major gap]'}"
            for v, k in c.most_common(3)
        )
        n_reach = sum(k for v, k in c.items() if major(v) in majs)
        print(f"    {n:<22} malicious {','.join(mal):<9} -> {got}")
        print(f"    {'':<22} reachable in {n_reach} of {sum(c.values())} trees")

    print(f"\n  MCP packages that were themselves compromised: "
          f"{sum(1 for r in ok if r['spec'].rsplit('@', 1)[0] in bad)}")
    kv = {r["spec"] for r in ok if "keyv" in r["packages"]}
    print(f"  names appearing in any tree: {len(seen)} of {len(bad)}; "
          f"grepping 'keyv' alone gives {len(kv)} servers "
          f"({'same set' if kv == {r['spec'] for r in exposed} else 'different set'})")

    rule("Reachable trees by size")
    buckets = [(0, 25), (25, 50), (50, 100), (100, 200), (200, 400), (400, 10 ** 9)]
    for lo, hi in buckets:
        grp = [r for r in ok if lo <= r["total"] < hi]
        if not grp:
            continue
        n = sum(1 for r in grp if r["reachable"])
        label = f"<{hi}" if lo == 0 else (f"{lo}-<{hi}" if hi < 10 ** 9 else f"{lo}+")
        print(f"  {label:>10} packages  {len(grp):>5} servers  {n:>3} reachable"
              f"  {n / len(grp) * 100:>5.1f}%")

    med = st.median(totals)
    for cut, label in ((med, f"median ({med:.0f})"), (160, "160")):
        lo_g = [r for r in ok if r["total"] <= cut]
        hi_g = [r for r in ok if r["total"] > cut]
        print(f"\n  cut at {label}:")
        for grp, side in ((lo_g, "at or below"), (hi_g, "above     ")):
            print(f"    {side}  reachable {sum(1 for r in grp if r['reachable']):>3}"
                  f" / {len(grp):<5}  name-level {sum(1 for r in grp if r['hits']):>3}")

    rule("How many distinct trees is that, really")
    def deps(r):
        return frozenset(set(r["packages"]) - {r["spec"].rsplit("@", 1)[0]})
    below = [r for r in ok if r["total"] <= med]
    shapes = Counter(deps(r) for r in below)
    print(f"servers at or below the median         {len(below)}")
    print(f"distinct dependency sets among them    {len(shapes)}")
    for s, n in shapes.most_common(2):
        print(f"  one shape of {len(s):>3} packages accounts for {n} servers")
    print(f"distinct dependency sets, whole population  "
          f"{len(set(deps(r) for r in ok))} for {len(ok)} servers")

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
    print("set is reachable in that tree as resolved on 2026-08-31, after the")
    print("malicious versions were pulled. It is not a finding that the server")
    print("shipped malware, and it is not a defect in that server.")


if __name__ == "__main__":
    main()
