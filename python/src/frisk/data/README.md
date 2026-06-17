# Seed blocklist

`blocklist_seed.json` is a small, offline subset of known-bad counterparties
shipped with the package so that lite mode can flag the most obvious cases
without a network call.

It is **not** the authoritative list. The live, continuously updated
blocklist and reputation data are served by the hosted API. Entries here are
only added when independently verifiable from public sources.
