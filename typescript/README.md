# Frisk

Pre-transaction risk screening for autonomous AI agents.

Before your agent pays an x402 seller or calls an unfamiliar tool, ask Frisk
whether the counterparty is trustworthy and whether the transaction fits your
policy. Frisk returns a verdict — `allow`, `review`, or `block` — with a
trust score and human-readable reasons. It is advisory: your agent stays in
control of the decision.

## Install

```bash
npm install frisk-screen
```

## Usage

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
  // hold the payment for review
}
```

## Lite mode vs. hosted

| | Lite (default) | Hosted (API key) |
| --- | --- | --- |
| Runs | Locally, offline | Frisk API |
| Signals | Public, structural checks only | Reputation graph, trained models, live threat feed |
| Confidence | Always `low` | Rises with coverage |
| Cost | Free | Free in early access |

Lite mode catches obvious problems — malformed counterparties, `payTo` swaps,
insecure endpoints, policy violations, and a small seed blocklist. For
reputation history and continuously updated threat intelligence, pass an API
key:

```ts
const client = new Client({ apiKey: "..." });
```

## Design

- **Zero runtime dependencies.** Built on the platform `fetch` API, so it runs
  on Node, Bun, Deno, Cloudflare Workers, and the browser.
- **Advisory, not in-path.** Frisk never holds your funds or blocks a
  payment itself; it returns a verdict and your code decides.
- **Typed.** Ships with TypeScript declarations.

## Development

```bash
pnpm install
pnpm test
pnpm build
```

## License

MIT — see [LICENSE](LICENSE). Security disclosures: see [SECURITY.md](SECURITY.md).
