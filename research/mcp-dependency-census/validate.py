"""Validate the metric measure.py actually reports, against a real install.

The previous round validated one counting rule and then reported a different
one. This calls measure.measure() itself, so there is no second definition to
drift from. Samples include @modelcontextprotocol/sdk, whose tree installs
content-type at three locations — the case that exposed the discrepancy.
"""

import json
import os
import shutil
import subprocess
import tempfile

from measure import measure

SAMPLES = [
    # No optional dependencies: the original six.
    "@modelcontextprotocol/sdk@1.30.0",
    "@modelcontextprotocol/server@2.0.0",
    "frisk-screen@0.0.2",
    "pretrip-mcp@1.0.1",
    "@ankimcp/anki-mcp-server@0.22.5",
    "cortex-rmcp@3.9.1",
    # Heavy in platform-specific optionalDependencies. The first six all have
    # zero of these, so they could not detect the one failure mode this metric
    # has: --package-lock-only lists every platform variant, a real install
    # unpacks only the matching ones.
    "esbuild@0.25.0",
    "kubernetes-mcp-server@0.0.65",
    "@printr/mcp@0.4.1",
    "live-translate-mcp@0.1.6",
    "appium-mcp@1.90.0",
]


def real_install(spec):
    tmp = tempfile.mkdtemp(prefix="mcpreal-")
    try:
        with open(os.path.join(tmp, "package.json"), "w") as f:
            json.dump({"name": "probe", "version": "1.0.0", "private": True}, f)
        subprocess.run(
            ["npm", "install", spec, "--omit=dev", "--no-audit", "--no-fund",
             "--silent", "--ignore-scripts"],
            cwd=tmp, capture_output=True, text=True, timeout=600,
        )
        listing = subprocess.run(
            ["npm", "ls", "--omit=dev", "--all", "--parseable"],
            cwd=tmp, capture_output=True, text=True, timeout=300,
        )
        return sum(1 for line in listing.stdout.splitlines() if "node_modules" in line)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


print(f"{'package':42} {'measured':>9} {'real':>7}  match")
bad = 0
for spec in SAMPLES:
    ident, version = spec.rsplit("@", 1)
    got = measure({"name": spec, "identifier": ident, "version": version})
    measured = got.get("total")
    real = real_install(spec)
    ok = measured == real
    bad += 0 if ok else 1
    print(f"{spec:42} {str(measured):>9} {real:>7}  {'OK' if ok else 'MISMATCH'}")

print(f"\n{len(SAMPLES) - bad}/{len(SAMPLES)} agree")
raise SystemExit(1 if bad else 0)
