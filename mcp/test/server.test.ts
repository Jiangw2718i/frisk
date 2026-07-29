import { Client, InMemoryTransport } from "@modelcontextprotocol/client";
import { beforeEach, describe, expect, it } from "vitest";

import { createServer } from "../src/server.js";

const A = `0x${"ab".repeat(20)}`;
const B = `0x${"cd".repeat(20)}`;

async function connect() {
  const server = createServer();
  const client = new Client({ name: "test", version: "0.0.0" });
  const [clientTransport, serverTransport] =
    InMemoryTransport.createLinkedPair();
  await Promise.all([
    server.connect(serverTransport),
    client.connect(clientTransport),
  ]);
  return client;
}

describe("frisk mcp server", () => {
  let client: Client;

  beforeEach(async () => {
    client = await connect();
  });

  it("exposes exactly one screening tool", async () => {
    const { tools } = await client.listTools();
    expect(tools.map((t) => t.name)).toEqual(["screen_payment"]);
  });

  it("says it runs offline when no API key is configured", async () => {
    const { tools } = await client.listTools();
    expect(tools[0]?.description).toContain("entirely offline");
    // Nothing leaves the machine without a key, so the tool is not open-world.
    expect(tools[0]?.annotations?.openWorldHint).toBe(false);
  });

  it("allows a clean payment", async () => {
    const result = await client.callTool({
      name: "screen_payment",
      arguments: { counterparty: A, endpoint: "https://api.seller.x402/quote" },
    });
    expect(result.structuredContent).toMatchObject({
      verdict: "allow",
      allowed: true,
      source: "lite",
    });
  });

  it("flags a payTo that moved between quote and payment", async () => {
    const result = await client.callTool({
      name: "screen_payment",
      arguments: { counterparty: A, observedPayTo: B },
    });
    const structured = result.structuredContent as { reasons: string[] };
    expect(structured.reasons).toContain(
      "payTo differs from the expected counterparty",
    );
    // A swap alone is a review, not a block — the caller still decides.
    expect(result.structuredContent).toMatchObject({ verdict: "review" });
  });

  it("applies the caller's spending policy", async () => {
    const result = await client.callTool({
      name: "screen_payment",
      arguments: { counterparty: A, amount: 40, maxPerCall: 5 },
    });
    const structured = result.structuredContent as { policyHits: string[] };
    expect(structured.policyHits.length).toBeGreaterThan(0);
  });

  it("reports a malformed counterparty rather than passing it through", async () => {
    const result = await client.callTool({
      name: "screen_payment",
      arguments: { counterparty: "not-an-address" },
    });
    const structured = result.structuredContent as { reasons: string[] };
    expect(structured.reasons.join(" ")).toMatch(/address/i);
  });
});
