import pytest

from frisk import Client, Confidence, Policy, Verdict
from frisk.lite import evaluate_lite
from frisk.types import ScreenRequest

GOOD = "0x" + "ab" * 20


def test_clean_transaction_allows():
    client = Client()
    result = client.screen(GOOD, endpoint="https://api.example.x402/quote")
    assert result.source == "lite"
    assert result.confidence is Confidence.LOW
    assert result.verdict is Verdict.ALLOW
    assert result.allowed


def test_amount_over_policy_is_flagged():
    client = Client()
    result = client.screen(GOOD, amount=10.0, policy=Policy(max_per_call=5.0))
    assert result.policy_hits
    assert result.verdict in (Verdict.REVIEW, Verdict.BLOCK)


def test_disallowed_asset_is_flagged():
    result = evaluate_lite(
        ScreenRequest(
            counterparty=GOOD, asset="DOGE", policy=Policy(allowed_assets=["USDC"])
        )
    )
    assert any("allowed_assets" in hit for hit in result.policy_hits)


def test_dynamic_pay_to_is_flagged():
    result = evaluate_lite(
        ScreenRequest(counterparty=GOOD, observed_pay_to="0x" + "cd" * 20)
    )
    assert any("payTo" in reason for reason in result.reasons)


def test_insecure_endpoint_is_flagged():
    result = evaluate_lite(
        ScreenRequest(counterparty=GOOD, endpoint="http://insecure.example")
    )
    assert any("HTTPS" in reason for reason in result.reasons)


def test_seed_blocklist_blocks():
    bad = "0x" + "11" * 20
    result = evaluate_lite(ScreenRequest(counterparty=bad), blocklist=[bad])
    assert result.verdict is Verdict.BLOCK
    assert result.trust_score == 0


def test_client_defaults_to_lite_mode():
    assert Client().mode == "lite"
    assert Client(api_key="k").mode == "hosted"


def test_https_base_url_is_accepted():
    assert Client(base_url="https://api.tryfrisk.dev").mode == "lite"


def test_non_https_base_url_is_rejected():
    with pytest.raises(ValueError):
        Client(base_url="http://api.evil.test")


def test_http_localhost_base_url_is_allowed():
    assert Client(base_url="http://localhost:8787").mode == "lite"
    assert Client(base_url="http://127.0.0.1:8787").mode == "lite"
