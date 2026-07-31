"""Measure what installing each npm+stdio MCP server puts on disk.

Instrument: `npm install <spec> --omit=dev --package-lock-only`, counting the
node_modules entries npm would actually unpack on this machine (darwin/arm64).
No tarballs are downloaded, which is what makes 6,139 packages feasible.

Two corrections over the naive count, both found by checking against real
installs rather than by reasoning:

1. Entries are install locations, not distinct package names. A package pinned
   at two versions occupies two directories.
2. --package-lock-only writes an entry for every platform variant of an
   optionalDependency. A real install unpacks only matching ones, so optional
   entries are gated on os/cpu here.

Residual error is measured, not assumed: sample_real.py runs real installs on a
random sample and reports where this instrument disagrees. It is exact for trees
with no platform-specific optional dependencies and overcounts slightly
otherwise, because pruning a variant should also prune its subtree and this does
not model that.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed

WORKERS = int(os.environ.get("WORKERS", "12"))
OUT = os.environ.get("OUT", "measurements.jsonl")

WEB_FRAMEWORKS = {
    "express", "fastify", "koa", "@hapi/hapi", "hono",
    "@hono/node-server", "connect", "restify", "polka",
}
SDK_V1 = "@modelcontextprotocol/sdk"
SDK_V2 = {"@modelcontextprotocol/server", "@modelcontextprotocol/core"}

HOST_OS = "darwin"
HOST_CPU = "arm64"


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
    tmp = tempfile.mkdtemp(prefix="mcpmeas-")
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

        total = optional_entries = 0
        names = {}
        for key, meta in data.get("packages", {}).items():
            if not key.startswith("node_modules/"):
                continue
            if meta.get("optional"):
                optional_entries += 1
            if not installs_here(meta):
                continue
            total += 1
            names[key.split("node_modules/")[-1]] = meta.get("version")

        return {
            "name": entry["name"],
            "spec": spec,
            "ok": True,
            "total": total,
            # Non-zero means this row is subject to the residual overcount.
            "optional_entries": optional_entries,
            "frameworks": sorted(set(names) & WEB_FRAMEWORKS),
            "sdk_v1": SDK_V1 in names,
            "sdk_v1_version": names.get(SDK_V1),
            "sdk_v2": bool(set(names) & SDK_V2),
        }
    except subprocess.TimeoutExpired:
        return {"name": entry["name"], "spec": spec, "ok": False, "error": "timeout"}
    except Exception as exc:  # noqa: BLE001
        return {"name": entry["name"], "spec": spec, "ok": False, "error": str(exc)[:200]}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def targets():
    """One row per distinct npm identifier, chosen deterministically."""
    entries = json.load(open("npm_stdio.json"))
    best = {}
    for e in sorted(entries, key=lambda e: (e.get("identifier") or "", e.get("version") or "")):
        if e.get("identifier"):
            best.setdefault(e["identifier"], e)
    return list(best.values())


def main():
    todo = targets()
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else len(todo)
    todo = todo[:limit]
    print(f"measuring {len(todo)} distinct packages with {WORKERS} workers", flush=True)
    done = 0
    with open(OUT, "w") as out, ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(measure, t): t for t in todo}
        for fut in as_completed(futures):
            out.write(json.dumps(fut.result()) + "\n")
            done += 1
            if done % 200 == 0:
                out.flush()
                print(f"  {done}/{len(todo)}", flush=True)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
