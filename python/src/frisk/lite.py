"""Offline ("lite") screening.

The lite engine runs entirely on the caller's machine using only public,
locally available signals. It is intentionally weaker than the hosted
service and always reports LOW confidence: it has no reputation history, no
threat feed, and no trained models. Supply an API key to :class:`Client` to
use the hosted service for graph-, model-, and threat-feed-backed verdicts.
"""

from __future__ import annotations

import json
import os
from typing import Iterable, List, Optional, Set

from .types import Confidence, ScreenRequest, ScreenResult, Verdict

_SEED_BLOCKLIST_PATH = os.path.join(
    os.path.dirname(__file__), "data", "blocklist_seed.json"
)

_BASELINE_SCORE = 70  # lite cannot see reputation history, so it starts neutral


def _load_seed_blocklist() -> Set[str]:
    try:
        with open(_SEED_BLOCKLIST_PATH, "r", encoding="utf-8") as handle:
            return {str(entry).lower() for entry in json.load(handle)}
    except (OSError, ValueError):
        return set()


_SEED_BLOCKLIST = _load_seed_blocklist()


def evaluate_lite(
    request: ScreenRequest,
    blocklist: Optional[Iterable[str]] = None,
) -> ScreenResult:
    """Score a request using offline signals only."""
    block = (
        _SEED_BLOCKLIST
        if blocklist is None
        else {str(entry).lower() for entry in blocklist}
    )

    score = _BASELINE_SCORE
    reasons: List[str] = []
    counterparty = (request.counterparty or "").lower()

    # 1. Seed blocklist. The live, continuously updated list is hosted-only.
    if counterparty in block:
        score = 0
        reasons.append("counterparty on local seed blocklist")

    # 2. Address sanity.
    if not _looks_like_address(counterparty):
        score -= 15
        reasons.append("counterparty is not a well-formed address")

    # 3. Dynamic payTo swap (a documented x402 attack vector).
    if request.observed_pay_to and request.observed_pay_to.lower() != counterparty:
        score -= 30
        reasons.append("payTo differs from the expected counterparty")

    # 4. Insecure endpoint.
    if request.endpoint and not request.endpoint.lower().startswith("https://"):
        score -= 20
        reasons.append("endpoint is not served over HTTPS")

    # 5. Spending policy (deterministic, fully offline).
    policy_hits = _check_policy(request)
    if policy_hits:
        score -= 25

    score = max(0, min(100, score))
    return ScreenResult(
        verdict=_verdict_for(score, policy_hits),
        trust_score=score,
        confidence=Confidence.LOW,
        reasons=reasons,
        policy_hits=policy_hits,
        source="lite",
    )


def _check_policy(request: ScreenRequest) -> List[str]:
    hits: List[str] = []
    policy = request.policy
    if policy is None:
        return hits
    if policy.max_per_call is not None and request.amount is not None:
        if request.amount > policy.max_per_call:
            hits.append(
                f"amount {request.amount} exceeds max_per_call {policy.max_per_call}"
            )
    if policy.allowed_assets is not None and request.asset is not None:
        if request.asset not in policy.allowed_assets:
            hits.append(f"asset {request.asset} not in allowed_assets")
    return hits


def _verdict_for(score: int, policy_hits: List[str]) -> Verdict:
    if score < 20:
        return Verdict.BLOCK
    if policy_hits or score < 65:
        return Verdict.REVIEW
    return Verdict.ALLOW


def _looks_like_address(value: str) -> bool:
    if value.startswith("0x") and len(value) == 42:
        return all(character in "0123456789abcdef" for character in value[2:])
    # Non-EVM identifiers (e.g. Solana base58) — length heuristic only.
    return 32 <= len(value) <= 60
