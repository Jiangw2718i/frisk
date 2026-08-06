"""Re-resolve every npm+stdio MCP server, keeping the full package name set.

Same instrument as ../mcp-dependency-census/measure.py — `npm install
--package-lock-only`, no tarballs fetched, scripts ignored, optional entries
gated on the host os/cpu — with two additions:

1. The resolved name->version map is persisted rather than only counted, so a
   tree can be checked against an arbitrary package set after the fact.
2. `hasInstallScript` is recorded. That is npm's own account of which entries
   would execute code at install time, which is the surface the August 2026
   `keyv` worm was delivered through.

The population comes from ../mcp-dependency-census/npm_stdio.json: one row per
distinct npm identifier, at the version the MCP registry declared when that
file was pulled (2026-07-29).

Limit of the instrument, stated up front because it governs how the output can
be read: resolution reflects the npm registry on the day it runs, which is
after the malicious versions were removed. A tree containing a name from the
compromised set therefore means that package is reachable, not that the server
ever shipped malware. Set membership is the durable signal; the resolved
version is recorded as context only.

Usage:
    python3 resolve_trees.py [limit]
    WORKERS=12 OUT=trees.jsonl python3 resolve_trees.py
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
POPULATION = os.environ.get(
    "POPULATION",
    os.path.join(HERE, os.pardir, "mcp-dependency-census", "npm_stdio.json"),
)
WORKERS = int(os.environ.get("WORKERS", "12"))
OUT = os.environ.get("OUT", os.path.join(HERE, "trees.jsonl"))

HOST_OS = os.environ.get("HOST_OS", "darwin")
HOST_CPU = os.environ.get("HOST_CPU", "arm64")


def _allowed(constraint, host):
    """npm os/cpu semantics: a bare list allows, a '!'-prefixed list denies."""
    if not constraint:
        return True
    allow = [c for c in constraint if not c.startswith("!")]
    deny = [c[1:] for c in constraint if c.startswith("!")]
    if host in deny:
        return False
    return host in allow if allow else True


def installs_here(meta):
    if not meta.get("optional"):
        return True
    return _allowed(meta.get("os"), HOST_OS) and _allowed(meta.get("cpu"), HOST_CPU)


def measure(entry):
    ident = entry["identifier"]
    version = entry.get("version")
    spec = f"{ident}@{version}" if version else ident
    tmp = tempfile.mkdtemp(prefix="mcp-reach-")
    try:
        with open(os.path.join(tmp, "package.json"), "w") as f:
            json.dump({"name": "probe", "version": "1.0.0", "private": True}, f)
        proc = subprocess.run(
            ["npm", "install", spec, "--omit=dev", "--package-lock-only",
             "--no-audit", "--no-fund", "--ignore-scripts"],
            cwd=tmp, capture_output=True, text=True, timeout=180,
        )
        lock = os.path.join(tmp, "package-lock.json")
        if proc.returncode != 0 or not os.path.exists(lock):
            code = ""
            for line in (proc.stderr or "").splitlines():
                if "npm error code" in line:
                    code = line.split("code")[-1].strip()
                    break
            return {"name": entry["name"], "spec": spec, "ok": False,
                    "error": code or f"exit {proc.returncode}"}
        with open(lock) as f:
            data = json.load(f)

        names = {}
        script_pkgs = []
        for key, meta in data.get("packages", {}).items():
            if not key.startswith("node_modules/"):
                continue
            if not installs_here(meta):
                continue
            pkg = key.split("node_modules/")[-1]
            names[pkg] = meta.get("version")
            if meta.get("hasInstallScript"):
                script_pkgs.append(pkg)

        return {
            "name": entry["name"],
            "spec": spec,
            "ok": True,
            "total": len(names),
            "packages": names,
            "install_scripts": sorted(set(script_pkgs)),
        }
    except subprocess.TimeoutExpired:
        return {"name": entry["name"], "spec": spec, "ok": False, "error": "timeout"}
    except Exception as exc:  # noqa: BLE001
        return {"name": entry["name"], "spec": spec, "ok": False, "error": str(exc)[:200]}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def targets():
    """One row per distinct npm identifier, chosen deterministically."""
    with open(POPULATION) as f:
        entries = json.load(f)
    best = {}
    for e in sorted(entries, key=lambda e: (e.get("identifier") or "", e.get("version") or "")):
        if e.get("identifier"):
            best.setdefault(e["identifier"], e)
    return list(best.values())


def main():
    todo = targets()
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else len(todo)
    todo = todo[:limit]
    print(f"resolving {len(todo)} distinct packages with {WORKERS} workers", flush=True)
    done = ok = 0
    with open(OUT, "w") as out, ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(measure, t): t for t in todo}
        for fut in as_completed(futures):
            row = fut.result()
            out.write(json.dumps(row) + "\n")
            done += 1
            ok += 1 if row.get("ok") else 0
            if done % 250 == 0:
                out.flush()
                print(f"  {done}/{len(todo)}  ok={ok}", flush=True)
    print(f"wrote {OUT}: {done} rows, {ok} resolved")


if __name__ == "__main__":
    main()
