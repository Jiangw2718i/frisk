import { StdioServerTransport } from "@modelcontextprotocol/server/stdio";
import { createServer } from "./server.js";

async function main(): Promise<void> {
  const server = createServer({
    apiKey: process.env.FRISK_API_KEY,
    baseUrl: process.env.FRISK_BASE_URL,
  });
  await server.connect(new StdioServerTransport());
}

main().catch((error) => {
  // stdout carries the protocol, so diagnostics go to stderr.
  console.error(error);
  process.exit(1);
});
