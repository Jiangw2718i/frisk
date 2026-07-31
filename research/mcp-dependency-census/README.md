# MCP dependency census

What does installing an MCP server actually put on your machine?

This is the code and the data behind [*The median MCP server installs 94
packages*](https://tryfrisk.dev/blog/the-median-mcp-server-installs-94-packages).
It measures every npm-packaged, stdio-transport server in the official MCP
registry — 6,139 distinct packages, 6,030 of which resolve — and reports what a
production install of each one costs.

Headline: **median 94 packages**, and **87.6% install an HTTP server framework**
into a process that only speaks over stdin and stdout.

It is checked in because the post makes claims about its own instrument, and a
claim about an instrument is worth nothing if you cannot run the instrument.

## Run it

Python 3.11+ and a working `npm`. Nothing else; no third-party packages.

```bash
python3 fetch_registry.py     # crawl the registry            -> registry_servers.json (~18 MB)
python3 profile_pop.py        # filter to npm + stdio         -> npm_stdio.json
python3 measure.py            # resolve every tree (~2 hours) -> measurements.jsonl
python3 analyze.py            # the distribution              -> summary.json
python3 article_numbers.py    # every figure quoted in the post
```

`npm_stdio.json` (the population), `measurements.jsonl` (the measurements) and
`sample_real.json` (the validation run) are committed, so everything from
`measure.py` onwards runs without re-crawling. The 18 MB registry snapshot is
not; regenerate it with `fetch_registry.py` if you want the registry-shape
figures too.

Two checks on the instrument itself:

```bash
python3 validate.py           # named packages vs real installs, incl. the cases that broke it
N=150 python3 sample_real.py  # 150 random real installs, error bound on the whole population
```

## The instrument, and how it was wrong twice

`measure.py` runs `npm install <spec> --omit=dev --package-lock-only` and counts
the `node_modules/…` entries in the resulting lockfile. No tarballs are
downloaded, which is the only reason 6,139 packages is feasible at all.

Two things went wrong, both found by comparing against real installs rather than
by reasoning about the code.

**1. Two counting rules.** *Install locations* counts every `node_modules/…`
entry — one package pinned at two versions occupies two directories. *Distinct
package names* collapses them. The validation measured one and the analysis
reported the other. The tell was an impossible result: servers appearing
*smaller* than the SDK they depend on. `validate.py` now calls `measure.measure()`
directly, so there is no second definition to drift from.

**2. Optional dependencies.** `--package-lock-only` writes an entry for every
platform variant of an `optionalDependency`; a real install unpacks only the
matching ones. For `kubernetes-mcp-server@0.0.65` that is 7 entries versus 2 real
directories. Entries are now gated on `os`/`cpu`.

The second bug survived a validation run that passed 6 out of 6 — because all
six sample packages had zero optional dependencies, so the check was
structurally incapable of finding it. That is why `sample_real.py` exists and
why its sample is drawn at random from the actual population.

`npm install --dry-run --json` was evaluated as an alternative and rejected: it
reported 671 packages for `appium-mcp@1.90.0` against 1,186 in a real install.

## Measured error

150 random packages (seed 20260730), real installs, `npm ls --omit=dev --all
--parseable`:

| | packages | exact match |
| --- | --- | --- |
| no optional entries | 128 | **128 (100%)** |
| has optional entries | 21 | 18 (86%) |
| **all** | **149** | **146 (98.0%)** |

Three overcounts, 1.5%–2.0%. **Zero undercounts.** Sample median 94 measured, 94
real. The residual overcount comes from pruning a platform variant without also
pruning its subtree, which this does not model.

The median is unaffected: the trees sitting at the median carry no optional
entries at all.

## Caveats

- Measured on darwin/arm64. `HOST_OS`/`HOST_CPU` in `measure.py` change that.
- One row per distinct npm package, not per server. 166 packages appear in the
  registry under two server names and are counted once.
- Each row is measured at the version its registry entry declares. `npx -y
  <package>` installs whatever is latest instead, which can resolve differently.
- **These numbers have a shelf life.** Of 400 sampled packages, 400 declared a
  caret range on the SDK and none pinned. The number therefore tracks whatever
  the SDK's dependencies are today, and re-running this after the next SDK
  release will not reproduce it. That is the finding, not a defect.
