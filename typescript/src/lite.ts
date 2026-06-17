/**
 * Offline ("lite") screening.
 *
 * The lite engine runs entirely on the caller's machine using only public,
 * locally available signals. It is intentionally weaker than the hosted
 * service and always reports `"low"` confidence: it has no reputation history,
 * no threat feed, and no trained models. Supply an API key to `Client` to use
 * the hosted service for graph-, model-, and threat-feed-backed verdicts.
 */

import { SEED_BLOCKLIST } from "./data/blocklistSeed.js";
import type { ScreenRequest, ScreenResult, Verdict } from "./types.js";

const BASELINE_SCORE = 70; // lite cannot see reputation history, so it starts neutral

export function evaluateLite(
  request: ScreenRequest,
  blocklist?: Iterable<string>,
): ScreenResult {
  const block = new Set(
    [...(blocklist ?? SEED_BLOCKLIST)].map((entry) => entry.toLowerCase()),
  );

  let score = BASELINE_SCORE;
  const reasons: string[] = [];
  const counterparty = (request.counterparty ?? "").toLowerCase();

  // 1. Seed blocklist. The live, continuously updated list is hosted-only.
  if (block.has(counterparty)) {
    score = 0;
    reasons.push("counterparty on local seed blocklist");
  }

  // 2. Address sanity.
  if (!looksLikeAddress(counterparty)) {
    score -= 15;
    reasons.push("counterparty is not a well-formed address");
  }

  // 3. Dynamic payTo swap (a documented x402 attack vector).
  if (
    request.observedPayTo &&
    request.observedPayTo.toLowerCase() !== counterparty
  ) {
    score -= 30;
    reasons.push("payTo differs from the expected counterparty");
  }

  // 4. Insecure endpoint.
  if (
    request.endpoint &&
    !request.endpoint.toLowerCase().startsWith("https://")
  ) {
    score -= 20;
    reasons.push("endpoint is not served over HTTPS");
  }

  // 5. Spending policy (deterministic, fully offline).
  const policyHits = checkPolicy(request);
  if (policyHits.length > 0) {
    score -= 25;
  }

  score = Math.max(0, Math.min(100, score));
  const verdict = verdictFor(score, policyHits);
  return {
    verdict,
    trustScore: score,
    confidence: "low",
    reasons,
    policyHits,
    source: "lite",
    allowed: verdict === "allow",
  };
}

function checkPolicy(request: ScreenRequest): string[] {
  const hits: string[] = [];
  const policy = request.policy;
  if (!policy) {
    return hits;
  }
  if (policy.maxPerCall !== undefined && request.amount !== undefined) {
    if (request.amount > policy.maxPerCall) {
      hits.push(
        `amount ${request.amount} exceeds maxPerCall ${policy.maxPerCall}`,
      );
    }
  }
  if (policy.allowedAssets !== undefined && request.asset !== undefined) {
    if (!policy.allowedAssets.includes(request.asset)) {
      hits.push(`asset ${request.asset} not in allowedAssets`);
    }
  }
  return hits;
}

function verdictFor(score: number, policyHits: string[]): Verdict {
  if (score < 20) {
    return "block";
  }
  if (policyHits.length > 0 || score < 65) {
    return "review";
  }
  return "allow";
}

function looksLikeAddress(value: string): boolean {
  if (value.startsWith("0x") && value.length === 42) {
    return /^[0-9a-f]+$/.test(value.slice(2));
  }
  // Non-EVM identifiers (e.g. Solana base58) — length heuristic only.
  return value.length >= 32 && value.length <= 60;
}
