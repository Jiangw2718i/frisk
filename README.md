# Frisk

[![CI](https://github.com/Jiangw2718i/frisk/actions/workflows/ci.yml/badge.svg)](https://github.com/Jiangw2718i/frisk/actions/workflows/ci.yml)
[![npm](https://img.shields.io/npm/v/frisk-screen?label=frisk-screen)](https://www.npmjs.com/package/frisk-screen)
[![PyPI](https://img.shields.io/pypi/v/frisk-screen?label=PyPI)](https://pypi.org/project/frisk-screen/)
[![npm](https://img.shields.io/npm/v/frisk-mcp?label=frisk-mcp)](https://www.npmjs.com/package/frisk-mcp)
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

## Surfaces

| Surface        | Package                | Source                       |
| -------------- | ---------------------- | ---------------------------- |
| TypeScript SDK | `frisk-screen` (npm)   | [`typescript/`](typescript/) |
| Python SDK     | `frisk-screen` (PyPI)  | [`python/`](python/)         |
| MCP server     | `frisk-mcp` (npm)      | [`mcp/`](mcp/)               |

Both SDKs expose the same model: a `Client` with a `screen()` call, a `lite`
mode that runs locally with zero dependencies, and an optional hosted mode for
reputation history and live threat intelligence.

## MCP server

For agents that cannot import a library, and for asking the question
interactively, the same checks are available as an MCP server exposing one
tool, `screen_payment`:

```json
{
  "mcpServers": {
    "frisk": {
      "command": "npx",
      "args": ["-y", "frisk-mcp"]
    }
  }
}
```

No API key and no account: with no configuration it screens entirely on your
machine. It is listed in the MCP registry as `dev.tryfrisk/frisk`.

An MCP tool runs only when a model chooses to call it, so a check the model can
skip is a weaker guarantee than the same check on the code path that signs the
payment. Where the money actually moves, prefer the SDK. Details in
[`mcp/`](mcp/).

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

## What a verdict covers

Frisk screens who you are paying. An `allow` means nothing disqualifying was
found by the checks you gave it enough information to run: the counterparty
parses as an address and is not on the blocklist, the `payTo` the endpoint
asked for matches the counterparty you named, the endpoint is served over
HTTPS, and the amount and asset fall inside the policy you supplied. A check
whose input you leave out does not run and does not fail — omit
`observedPayTo` and no `payTo` comparison happens. In hosted mode an `allow`
also means no adverse reputation history was found.

It says nothing about what comes back. Whether the response matches the shape
you expected, contains the data you paid for, or is worth the price is a
separate question, and Frisk deliberately does not answer it. Verifying the
response contract is worth doing; it belongs after the call, on the buyer's
side, against the buyer's own definition of a satisfactory answer.

An `allow` is not a claim of safety in general either. In lite mode confidence
is always `low`, because the checks are structural: a counterparty with no
history and no defects screens the same as one with a long clean record. The
verdict is one input to your decision, which is why it is advisory.

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

The hosted API at `api.tryfrisk.dev` is additionally governed by the
[Terms of Service](TERMS.md).
