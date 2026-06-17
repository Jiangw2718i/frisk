# Frisk

Pre-transaction risk screening for autonomous AI agents.

Before your agent pays an x402 seller or calls an unfamiliar tool, ask Frisk
whether the counterparty is trustworthy and whether the transaction fits your
policy. Frisk returns a verdict — `allow`, `review`, or `block` — with a
trust score and human-readable reasons. It is advisory: your agent stays in
control of the decision.

## Install

```bash
pip install frisk-screen
```

## Usage

```python
from frisk import Client, Policy

client = Client()  # lite mode, no key required

result = client.screen(
    "0x9a3f1b2c3d4e5f60718293a4b5c6d7e8f9a0bc12",
    endpoint="https://api.seller.x402/quote",
    amount=2.50,
    asset="USDC",
    policy=Policy(max_per_call=5.00),
)

if not result.allowed:
    print(result.verdict, result.trust_score, result.reasons)
    # hold the payment for review
```

## Lite mode vs. hosted

| | Lite (default) | Hosted (API key) |
| --- | --- | --- |
| Runs | Locally, offline | Frisk API |
| Signals | Public, structural checks only | Reputation graph, trained models, live threat feed |
| Confidence | Always `low` | Rises with coverage |
| Cost | Free | Usage-based |

Lite mode catches obvious problems — malformed counterparties, `payTo` swaps,
insecure endpoints, policy violations, and a small seed blocklist. For
reputation history and continuously updated threat intelligence, pass an API
key:

```python
client = Client(api_key="...")
```

## Design

- **Zero runtime dependencies.** The SDK uses only the standard library.
- **Advisory, not in-path.** Frisk never holds your funds or blocks a
  payment itself; it returns a verdict and your code decides.
- **Typed.** Ships with type hints (`py.typed`).

## Development

This project uses [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run pytest
```

## License

MIT — see [LICENSE](LICENSE). Security disclosures: see [SECURITY.md](SECURITY.md).
