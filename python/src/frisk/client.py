"""Client entry point for screening agent transactions."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Optional
from urllib.parse import urlparse

from .lite import evaluate_lite
from .types import Confidence, Policy, ScreenRequest, ScreenResult, Verdict

DEFAULT_BASE_URL = "https://api.tryfrisk.dev"


class ScreenError(RuntimeError):
    """Raised when a hosted screening request cannot be completed."""


def _normalize_base_url(raw: str) -> str:
    """Validate and normalize a base URL.

    HTTPS is required so the API key in the Authorization header is never sent
    in plaintext; http is allowed only for localhost to support local
    development and tests.
    """
    trimmed = raw.rstrip("/")
    parsed = urlparse(trimmed)
    is_localhost = parsed.hostname in ("localhost", "127.0.0.1", "::1")
    if parsed.scheme == "https" or (parsed.scheme == "http" and is_localhost):
        return trimmed
    raise ValueError("base_url must use HTTPS (http is allowed only for localhost)")


class Client:
    """Screen agent transactions before they execute.

    Without an API key the client runs in offline ``lite`` mode. Supply an
    API key to use the hosted service, which adds reputation-graph, model,
    and threat-feed signals and returns higher-confidence verdicts.

    Example::

        client = Client()  # lite mode
        result = client.screen("0xabc...", amount=2.5, asset="USDC")
        if not result.allowed:
            ...  # hold the payment for review
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 5.0,
    ) -> None:
        self._api_key = api_key
        self._base_url = _normalize_base_url(base_url)
        self._timeout = timeout

    @property
    def mode(self) -> str:
        return "hosted" if self._api_key else "lite"

    def screen(
        self,
        counterparty: str,
        *,
        endpoint: Optional[str] = None,
        amount: Optional[float] = None,
        asset: Optional[str] = None,
        policy: Optional[Policy] = None,
        observed_pay_to: Optional[str] = None,
        strictness: Optional[float] = None,
    ) -> ScreenResult:
        request = ScreenRequest(
            counterparty=counterparty,
            endpoint=endpoint,
            amount=amount,
            asset=asset,
            policy=policy,
            observed_pay_to=observed_pay_to,
            strictness=strictness,
        )
        if self._api_key:
            return self._screen_hosted(request)
        return evaluate_lite(request)

    def _screen_hosted(self, request: ScreenRequest) -> ScreenResult:
        payload = {
            "counterparty": request.counterparty,
            "endpoint": request.endpoint,
            "amount": request.amount,
            "asset": request.asset,
            "observed_pay_to": request.observed_pay_to,
            "strictness": request.strictness,
        }
        if request.policy is not None:
            payload["policy"] = {
                "max_per_call": request.policy.max_per_call,
                "allowed_assets": request.policy.allowed_assets,
            }

        http_request = urllib.request.Request(
            f"{self._base_url}/v1/screen",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(
                http_request, timeout=self._timeout
            ) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise ScreenError(f"hosted screening failed: HTTP {exc.code}") from exc
        except urllib.error.URLError as exc:
            raise ScreenError(f"hosted screening unreachable: {exc.reason}") from exc
        return _result_from_payload(data)


def _result_from_payload(data: dict) -> ScreenResult:
    return ScreenResult(
        verdict=Verdict(data["verdict"]),
        trust_score=int(data["trust_score"]),
        confidence=Confidence(data.get("confidence", "low")),
        reasons=list(data.get("reasons", [])),
        policy_hits=list(data.get("policy_hits", [])),
        source="hosted",
    )
