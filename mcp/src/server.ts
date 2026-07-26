import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { Client, type ScreenResult } from "frisk-screen";
import { z } from "zod";

export interface ServerOptions {
  /** Hosted API key. Without one the server screens entirely offline. */
  apiKey?: string;
  /** Override the hosted base URL. Only used when an API key is supplied. */
  baseUrl?: string;
}

const inputSchema = {
  counterparty: z
    .string()
    .describe("The address the agent intends to pay, e.g. an 0x EVM address."),
  endpoint: z
    .string()
    .optional()
    .describe("URL that quoted the payment. Used to check transport safety."),
  amount: z.number().optional().describe("Amount the agent is about to pay."),
  asset: z.string().optional().describe("Asset symbol, e.g. USDC."),
  observedPayTo: z
    .string()
    .optional()
    .describe(
      "The payTo address the endpoint actually returned for this request. If it differs from the counterparty, that is the dynamic-payTo swap.",
    ),
  strictness: z
    .number()
    .min(0)
    .max(1)
    .optional()
    .describe("0 is permissive, 1 is paranoid. Defaults to 0.3."),
  maxPerCall: z
    .number()
    .optional()
    .describe("Spending ceiling for a single call."),
  allowedAssets: z
    .array(z.string())
    .optional()
    .describe("Assets the agent is permitted to pay in."),
};

/**
 * The verdict is advisory. Frisk returns a recommendation and the caller
 * decides; it never holds funds and cannot stop a payment by itself.
 */
function describeResult(result: ScreenResult): string {
  const lines = [
    `verdict: ${result.verdict}`,
    `trust score: ${result.trustScore}`,
    `confidence: ${result.confidence}`,
    `source: ${result.source}`,
  ];
  if (result.reasons.length > 0) {
    lines.push(`reasons: ${result.reasons.join("; ")}`);
  }
  if (result.policyHits.length > 0) {
    lines.push(`policy hits: ${result.policyHits.join("; ")}`);
  }
  return lines.join("\n");
}

/**
 * Build the Frisk MCP server.
 *
 * One tool, deliberately. `screen_payment` is the whole deterministic floor:
 * counterparty sanity, dynamic-payTo comparison, transport check, and the
 * caller's own spending policy. With an API key the same call is answered by
 * the hosted service, which adds reputation signals.
 *
 * Note on where this belongs: an MCP tool runs when a model decides to call it,
 * so it is a weaker guarantee than calling `screen()` on the code path that
 * actually signs the payment. Use this for inspection and for agents that
 * cannot import the library; use the library where the money moves.
 */
export function createServer(options: ServerOptions = {}): McpServer {
  const client = new Client({
    apiKey: options.apiKey,
    baseUrl: options.baseUrl,
  });

  const server = new McpServer({
    name: "frisk",
    version: "0.0.1",
  });

  server.registerTool(
    "screen_payment",
    {
      title: "Screen a payment before paying",
      description:
        client.mode === "hosted"
          ? "Screen a counterparty an agent is about to pay. Runs the local deterministic checks and the hosted reputation graph, and returns allow / review / block with reasons. Advisory: the caller decides."
          : "Screen a counterparty an agent is about to pay. Runs entirely offline: address sanity, dynamic-payTo comparison, transport check, and your spending policy. Returns allow / review / block with reasons. Advisory: the caller decides. Set FRISK_API_KEY to add hosted reputation signals.",
      inputSchema,
      annotations: {
        readOnlyHint: true,
        openWorldHint: client.mode === "hosted",
      },
    },
    async ({ counterparty, maxPerCall, allowedAssets, ...rest }) => {
      const policy =
        maxPerCall === undefined && allowedAssets === undefined
          ? undefined
          : { maxPerCall, allowedAssets };
      try {
        const result = await client.screen(counterparty, { ...rest, policy });
        return {
          content: [{ type: "text" as const, text: describeResult(result) }],
          structuredContent: { ...result },
        };
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        return {
          isError: true,
          content: [
            {
              type: "text" as const,
              text: `screening failed: ${message}`,
            },
          ],
        };
      }
    },
  );

  return server;
}
