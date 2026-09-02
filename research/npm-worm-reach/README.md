# How far the August 2026 npm worm could reach into MCP

On 2026-08-04 the GitHub account behind `keyv` was taken over and used to
publish a self-replicating credential stealer, delivered through a `preinstall`
hook. It is the third Shai-Hulud wave, tracked by some vendors as ChainDrop.
More than 440 npm packages were affected.

This directory measures how far that could reach into the MCP server population
already measured in [`../mcp-dependency-census`](../mcp-dependency-census).

**36 of 6,001 npm-packaged stdio servers carry a compromised package name.
Only 18 could have received a malicious version.**

The other 18 sit a major release behind. `keyv` — the name present in all 36,
and the only name needed to reproduce the whole name-level set — was malicious
at 6.0.0, while every tree here resolves 5.x or 4.x. A caret range cannot cross
a major, so those trees were never in range.

**Zero of the 6,139 MCP packages were themselves compromised. Every hit is
transitive.**

Accompanies the post *The npm worm could reach 18 MCP servers, not the 36 an
IOC name match reports*. `analyze.py` reprints every figure in that post,
labelled as it appears there.

## Two different questions

Conflating these is the mistake this directory exists to correct, and it is the
mistake the first draft of the post made.

| | question | answer |
|---|---|---|
| **name match** | is the package anywhere in the tree? | 36 servers |
| **semver reachable** | does the resolved version share a major with a malicious one, so a caret could have carried the payload? | 18 servers |

Trees were resolved on **2026-08-31**, after npm pulled the malicious versions,
so reachability is inferred from declared ranges rather than observed at the
time. Spot-checked against the ranges themselves: `cacheable-request@13.0.19`
declares `keyv: ^5.6.0`, which excludes 6.0.0 by construction — the major gap
is the constraint, not an artefact of the takedown.

A match on either measure is **not** a finding that a server shipped malware,
and it is not a defect in that server. Treat the per-server rows as evidence
for the aggregate, not as a list of compromised projects.

## Files

| File | What it is |
|---|---|
| `resolve_trees.py` | Re-resolves the population, keeping full package name sets and `hasInstallScript` |
| `analyze.py` | Reprints every figure in the post from the shipped data. No network |
| `trees.jsonl.gz` | One row per npm identifier: resolved name->version map, install-script entries |
| `compromised.json` | 463 package names with malicious versions and the source listing each |
| `compromised-names.txt` | The same names, one per line, for `grep -Fxf` |
| `wiz-keyv-packages.csv` | Wiz's published IOC list (443 names), retrieved 2026-08-06 |

## Method

Identical to the census instrument, so the two runs are comparable:

```bash
npm install <package>@<version> \
  --omit=dev --package-lock-only --no-audit --ignore-scripts
```

`--package-lock-only` resolves the whole tree without downloading a tarball,
which makes 6,139 packages feasible and means nothing from the compromised set
is ever written to disk. Optional dependencies are gated on the host `os`/`cpu`
so the count reflects what would actually be unpacked. The population is one row
per distinct npm identifier, pinned to the version the MCP registry declared on
2026-07-29.

Known limits, all of which bound how these numbers should be read:

- `--package-lock-only` is not an install. Validated in the previous post
  against 150 real installs: exact on 98%, never low, up to 2% high on trees
  carrying platform-specific optional dependencies.
- Resolved for **darwin/arm64**. A Windows or Linux tree differs wherever
  optional dependencies are platform-gated.
- `npx -y <server>` resolves `latest`, not the pinned version, and that is how
  most MCP clients install these. The real-world trees during the window may
  differ from the registry-declared ones measured here.
- No download weighting. 18 is a count of packages, not of affected users.

## Reproducing

```bash
python3 analyze.py                     # every figure, from the shipped data
gunzip -k trees.jsonl.gz               # if you want the raw rows

python3 resolve_trees.py               # re-resolve from scratch (~45 min, 12 workers)
```

A fresh resolution will **not** reproduce these numbers exactly, and that is the
point rather than a defect. The same population, read from the same 2026-07-29
snapshot, gave a median of 94 packages over 6,030 successes on 2026-07-31 and 95
over 6,001 on 2026-08-31: names leave npm, and transitive caret ranges resolve
against a registry that has moved.

An earlier version of this file read the same two runs as 94 and 92 and put the
gap down to caret ranges. That was an artefact: `resolve_trees.py` keyed its
package map on the name, so two installed copies of one dependency counted
once, while the census counted installed entries. `total` now counts entries,
matching the census.

## The compromised list

463 names, merged from JFrog, SafeDep, Wiz, Palo Alto Unit 42 and four community
mirrors, then cross-checked against OSV.

Worth being blunt about what that merge was worth here: **seven of the eight
sources contributed no unique name** — operationally this is JFrog's list — and
**452 of the 463 names appear in zero MCP trees**. Grepping for `keyv` alone
reproduces the identical 36-server name-level set. The merge changed no figure
in the post.

The 20 names JFrog carries that Wiz's 443-name CSV does not are 19 `@keyv/*`
scoped packages plus `@nebula.js/cli-serve`. The advisories are real —
`@keyv/redis` is `MAL-2026-12020`, `@keyv/postgres` is `MAL-2026-12019`,
`@keyv/sqlite` is `MAL-2026-12023`, all published 2026-08-04 between 13:01 and
13:02 UTC — so the gap is a genuine one in a widely-copied list. In this
population it costs nothing: the four servers reaching a `@keyv/*` name also
carry bare `keyv`, and after the version check none of them were reachable
through either. `analyze.py` prints that check rather than asserting it.

Vendor lists were still being updated when this was collected. Treat 463 as a
floor.
