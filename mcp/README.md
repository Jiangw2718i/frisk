# frisk-mcp

An [MCP](https://modelcontextprotocol.io) server for [Frisk](https://github.com/Jiangw2718i/frisk):
screen the counterparty of an x402 payment before an agent pays it.

It exposes one tool, `screen_payment`, which runs Frisk's deterministic checks —
address sanity, dynamic-`payTo` comparison, transport safety, and your own
spending policy — and returns `allow` / `review` / `block` with reasons.

## Where this belongs, and where it does not

An MCP tool runs when a model decides to call it. A payment check that the model
can skip is a weaker guarantee than the same check on the code path that signs
the payment.

So:

- **Use the library** — [`frisk-screen`](https://www.npmjs.com/package/frisk-screen) —
  where the money actually moves. It is MIT, dependency-free, and runs locally.
- **Use this server** for inspection ("is this address safe to pay?"), and for
  agents that cannot import a library.

Frisk is advisory in both cases: it returns a verdict and your code decides. It
never holds funds and cannot stop a payment by itself.

## Install

```bash
npx frisk-mcp
```

In any MCP client's server configuration:

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

No API key, no account, no network call: with no configuration the server
screens entirely on your machine.

## Hosted mode (optional)

Set `FRISK_API_KEY` to have the same tool answered by the hosted service, which
adds reputation-graph signals and returns higher-confidence verdicts:

```json
{
  "mcpServers": {
    "frisk": {
      "command": "npx",
      "args": ["-y", "frisk-mcp"],
      "env": { "FRISK_API_KEY": "..." }
    }
  }
}
```

The hosted tier is in early access — email support@tryfrisk.dev. Everything
above works without it.

| variable | default | meaning |
| --- | --- | --- |
| `FRISK_API_KEY` | unset | Enables hosted screening. Unset means fully offline. |
| `FRISK_BASE_URL` | `https://api.tryfrisk.dev` | Override the hosted endpoint. |

## The tool

`screen_payment`

| argument | type | notes |
| --- | --- | --- |
| `counterparty` | string, required | The address the agent intends to pay. |
| `endpoint` | string | URL that quoted the payment; checked for plaintext transport. |
| `amount` | number | Amount about to be paid. |
| `asset` | string | Asset symbol, e.g. `USDC`. |
| `observedPayTo` | string | The `payTo` the endpoint actually returned. If it differs from `counterparty`, that is the dynamic-`payTo` swap. |
| `strictness` | number 0–1 | 0 permissive, 1 paranoid. Default 0.3. |
| `maxPerCall` | number | Spending ceiling for one call. |
| `allowedAssets` | string[] | Assets the agent may pay in. |

Returns `verdict`, `trustScore`, `confidence`, `reasons`, `policyHits`,
`source` (`lite` or `hosted`), and `allowed`.

## What it does not do

It does not detect Sybil clusters, and offline it has no view of an address's
history — lite screening always reports `"low"` confidence for that reason. It
also cannot repair the protocol underneath a payment: replay, settlement races,
and facilitator trust live in x402 itself, not in the request being signed.
Those limits are discussed in
[Five ways an x402 payment can go wrong](https://tryfrisk.dev/blog/screening-x402-payments).

## License

MIT
