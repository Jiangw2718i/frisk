"""Core data types for the screening SDK."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class Verdict(str, Enum):
    """Recommended action for a screened transaction."""

    ALLOW = "allow"
    REVIEW = "review"
    BLOCK = "block"


class Confidence(str, Enum):
    """How much weight to place on the verdict.

    Offline (lite) screening always reports ``LOW``; the hosted service
    raises confidence as graph, model, and threat-feed coverage improve.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True)
class Policy:
    """Caller-supplied spending policy. Every field is optional."""

    max_per_call: Optional[float] = None
    allowed_assets: Optional[List[str]] = None


@dataclass(frozen=True)
class ScreenRequest:
    """A transaction an agent is about to perform."""

    counterparty: str
    endpoint: Optional[str] = None
    amount: Optional[float] = None
    asset: Optional[str] = None
    policy: Optional[Policy] = None
    # The payTo address the endpoint actually returned this request, if
    # observed. Used to detect dynamic-payTo swaps.
    observed_pay_to: Optional[str] = None
    # Screening "temperature" in [0, 1]: 0 = permissive, 1 = paranoid. Default 0.3.
    strictness: Optional[float] = None


@dataclass(frozen=True)
class ScreenResult:
    """The outcome of screening a transaction."""

    verdict: Verdict
    trust_score: int  # 0-100
    confidence: Confidence
    reasons: List[str] = field(default_factory=list)
    policy_hits: List[str] = field(default_factory=list)
    source: str = "lite"  # "lite" | "hosted"

    @property
    def allowed(self) -> bool:
        return self.verdict is Verdict.ALLOW
