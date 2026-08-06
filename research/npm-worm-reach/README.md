# How far the August 2026 npm worm reached into MCP

On 2026-08-04 the GitHub account behind `keyv` was taken over and used to
publish a self-replicating credential stealer, delivered through a `preinstall`
hook. It spread to more than 440 npm packages.

This directory measures how far that reached into the MCP server population
already measured in [`../mcp-dependency-census`](../mcp-dependency-census):
**36 of 6,012 npm-packaged stdio servers reach at least one compromised
package, and every one of them installs more than the population median.**

Accompanies the post *Every MCP server the npm worm reached was above the
median install size*. Running `analyze.py` reprints every figure in that post,
labelled as it appears there.

## What "reach" means, and what it does not

Trees were resolved on **2026-08-06**, after npm removed the malicious
versions. So a match does **not** mean a server shipped malware, and it is not
a defect in that server.

It means the named package is reachable in that server's production install
tree. The consequence is narrower and, for this question, the useful one:
anyone who installed that server while the bad versions were live would have
received the payload, and the server's author had no way to know, because in
most cases they never named the package — it arrived through a caret range
several levels down.

Treat the per-server rows as evidence for the aggregate, not as a list of
compromised projects. The post deliberately publishes the aggregate rather than
the names for that reason.

## Files

| File | What it is |
|---|---|
| `resolve_trees.py` | Re-resolves the population, keeping full package name sets and `hasInstallScript` |
| `analyze.py` | Reprints every figure in the post from the shipped data. No network |
| `trees.jsonl.gz` | One row per npm identifier: resolved name->version map, install-script entries |
| `compromised.json` | 463 package names with versions and the source that lists each |
| `compromised-names.txt` | The same names, one per line, for `grep -Ff` |
| `wiz-keyv-packages.csv` | Wiz's published IOC list (443 names), retrieved 2026-08-06, for the gap comparison |

## Method

Identical to the census instrument, so the two runs are comparable:

```bash
npm install <package>@<version> \
  --omit=dev --package-lock-only --no-audit --ignore-scripts
```

`--package-lock-only` resolves the whole tree without downloading a tarball,
which makes 6,139 packages feasible and means nothing from the compromised set
is ever written to disk. Optional dependencies are gated on the host `os`/`cpu`
so the count reflects what would actually be unpacked. The population is one
row per distinct npm identifier, pinned to the version the MCP registry
declared on 2026-07-29.

## Reproducing

```bash
python3 analyze.py                     # every figure, from the shipped data
gunzip -k trees.jsonl.gz               # if you want the raw rows

python3 resolve_trees.py               # re-resolve from scratch (~45 min, 12 workers)
```

A fresh resolution will **not** reproduce these numbers exactly, and that is
the point rather than a defect. The same population resolved on 2026-07-31 gave
a median of 94 packages over 6,030 successes; on 2026-08-06 it gives 92 over
6,012. Nothing in the registry changed between those runs. Transitive caret
ranges did.

## The compromised list

Merged from JFrog, SafeDep, Wiz, Palo Alto Unit 42 and four community mirrors,
then cross-checked against OSV. 463 names, against the 443-444 most vendors
publish.

The extra 20 are 19 `@keyv/*` scoped packages plus `@nebula.js/cli-serve`.
The `@keyv/*` set is absent from Wiz's CSV and from the community scanners that
mirror it, but the advisories are real: `@keyv/redis` is `MAL-2026-12020`,
`@keyv/postgres` is `MAL-2026-12019`, `@keyv/sqlite` is `MAL-2026-12023`, all
published 2026-08-04 between 13:01 and 13:02 UTC.

In this population the gap has no practical consequence — the four servers that
reach a `@keyv/*` package also reach bare `keyv`, which every list contains, so
a scan against the short list still flags them. `analyze.py` prints that check
rather than asserting it.

Vendor lists were still being updated when this was collected. Treat 463 as a
floor.
