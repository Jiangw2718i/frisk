/**
 * A small, offline subset of known-bad counterparties shipped with the
 * package so that lite mode can flag the most obvious cases without a network
 * call.
 *
 * This is not authoritative. The live, continuously updated blocklist and
 * reputation data are served by the hosted API. Entries are added here only
 * when independently verifiable from public sources.
 */
export const SEED_BLOCKLIST: readonly string[] = [];
