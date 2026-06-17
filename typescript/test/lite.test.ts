import { describe, expect, it } from "vitest";

import { Client, evaluateLite } from "../src/index.js";

const GOOD = `0x${"ab".repeat(20)}`;

describe("lite screening", () => {
  it("allows a clean transaction", async () => {
    const client = new Client();
    const result = await client.screen(GOOD, {
      endpoint: "https://api.example.x402/quote",
    });
    expect(result.source).toBe("lite");
    expect(result.confidence).toBe("low");
    expect(result.verdict).toBe("allow");
    expect(result.allowed).toBe(true);
  });

  it("flags an amount over policy", async () => {
    const client = new Client();
    const result = await client.screen(GOOD, {
      amount: 10,
      policy: { maxPerCall: 5 },
    });
    expect(result.policyHits.length).toBeGreaterThan(0);
    expect(["review", "block"]).toContain(result.verdict);
  });

  it("flags a disallowed asset", () => {
    const result = evaluateLite({
      counterparty: GOOD,
      asset: "DOGE",
      policy: { allowedAssets: ["USDC"] },
    });
    expect(result.policyHits.some((hit) => hit.includes("allowedAssets"))).toBe(
      true,
    );
  });

  it("flags a dynamic payTo swap", () => {
    const result = evaluateLite({
      counterparty: GOOD,
      observedPayTo: `0x${"cd".repeat(20)}`,
    });
    expect(result.reasons.some((reason) => reason.includes("payTo"))).toBe(
      true,
    );
  });

  it("flags an insecure endpoint", () => {
    const result = evaluateLite({
      counterparty: GOOD,
      endpoint: "http://insecure.example",
    });
    expect(result.reasons.some((reason) => reason.includes("HTTPS"))).toBe(
      true,
    );
  });

  it("blocks a seed-blocklisted counterparty", () => {
    const bad = `0x${"11".repeat(20)}`;
    const result = evaluateLite({ counterparty: bad }, [bad]);
    expect(result.verdict).toBe("block");
    expect(result.trustScore).toBe(0);
  });

  it("defaults to lite mode without an api key", () => {
    expect(new Client().mode).toBe("lite");
    expect(new Client({ apiKey: "k" }).mode).toBe("hosted");
  });
});

describe("baseUrl validation", () => {
  it("accepts an https baseUrl", () => {
    expect(
      () => new Client({ baseUrl: "https://api.tryfrisk.dev" }),
    ).not.toThrow();
  });

  it("rejects a non-HTTPS baseUrl so the key is never sent in plaintext", () => {
    expect(() => new Client({ baseUrl: "http://api.evil.test" })).toThrow();
  });

  it("allows http only for localhost", () => {
    expect(
      () => new Client({ baseUrl: "http://localhost:8787" }),
    ).not.toThrow();
    expect(
      () => new Client({ baseUrl: "http://127.0.0.1:8787" }),
    ).not.toThrow();
  });
});
