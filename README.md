# Frisk

[![CI](https://github.com/Jiangw2718i/frisk/actions/workflows/ci.yml/badge.svg)](https://github.com/Jiangw2718i/frisk/actions/workflows/ci.yml)
[![npm](https://img.shields.io/npm/v/frisk-screen?label=npm)](https://www.npmjs.com/package/frisk-screen)
[![PyPI](https://img.shields.io/pypi/v/frisk-screen?label=PyPI)](https://pypi.org/project/frisk-screen/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Pre-transaction risk screening for autonomous AI agents.**

Before your agent pays an x402 seller or calls an unfamiliar tool, ask Frisk
whether the counterparty is trustworthy and whether the transaction fits your
policy. Frisk returns a verdict — `allow`, `review`, or `block` — with a trust
score and human-readable reasons. It is advisory: your agent stays in control
of the decision.

```ts
import { Client } from "frisk-screen";

const client = new Client(); // lite mode, no key required

const result = await client.screen("0x9a3f1b2c3d4e5f60718293a4b5c6d7e8f9a0bc12", {
  endpoint: "https://api.seller.x402/quote",
  amount: 2.5,
  asset: "USDC",
  policy: { maxPerCall: 5.0 },
});

if (!result.allowed) {
  console.log(result.verdict, result.trustScore, result.reasons);
}
```

## SDKs

| Language   | Package        | Source                             |
| ---------- | -------------- | ---------------------------------- |
| TypeScript | `frisk-screen` (npm)  | [`typescript/`](typescript/) |
| Python     | `frisk-screen` (PyPI) | [`python/`](python/)         |

Both expose the same model: a `Client` with a `screen()` call, a `lite` mode
that runs locally with zero dependencies, and an optional hosted mode for
reputation history and live threat intelligence.

## Lite mode vs. hosted

|            | Lite (default)                  | Hosted (API key)                              |
| ---------- | ------------------------------- | --------------------------------------------- |
| Runs       | Locally, offline                | Frisk API                                     |
| Signals    | Public, structural checks only  | Reputation graph, trained models, threat feed |
| Confidence | Always `low`                    | Rises with coverage                           |
| Cost       | Free                            | Usage-based                                   |

Lite mode catches obvious problems — malformed counterparties, `payTo` swaps,
insecure endpoints, policy violations, and a small seed blocklist — without a
network call. The hosted API (`https://api.tryfrisk.dev`) adds reputation
history and continuously updated threat intelligence.

## Design principles

- **Advisory, not in-path.** Frisk never holds your funds or blocks a payment
  itself; it returns a verdict and your code decides.
- **Zero runtime dependencies.** The TypeScript SDK is built on the platform
  `fetch` API (Node, Bun, Deno, Workers, browser); the Python SDK uses only the
  standard library.
- **Typed.** Both SDKs ship with full type information.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Security disclosures: [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE)
