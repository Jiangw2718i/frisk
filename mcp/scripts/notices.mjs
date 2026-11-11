// Writes THIRD_PARTY_NOTICES.md: the license of every package bundled into
// dist/index.js. The list comes from the esbuild metafile, so it always matches
// what the build actually included. Runs after tsup as part of `pnpm build`.
import { readdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const meta = JSON.parse(readFileSync("dist/metafile-esm.json", "utf8"));
const roots = new Map();
const pattern = /node_modules\/((?:@[^/]+\/)?[^/]+)\//g;

for (const input of Object.keys(meta.inputs)) {
  // The innermost node_modules segment names the package the file belongs to.
  const last = [...input.matchAll(pattern)].at(-1);
  if (last) {
    roots.set(last[1], input.slice(0, last.index + last[0].length));
  }
}

const sections = [...roots.keys()].sort().map((name) => {
  const root = roots.get(name);
  const pkg = JSON.parse(readFileSync(join(root, "package.json"), "utf8"));
  const files = readdirSync(root).filter((file) =>
    /^(licen[cs]e|copying|notice)/i.test(file),
  );
  if (files.length === 0) {
    throw new Error(`no license file found for bundled package ${name}`);
  }
  const texts = files
    .sort()
    .map((file) => readFileSync(join(root, file), "utf8").trim());
  return [
    `## ${name} ${pkg.version}`,
    "",
    `License: ${pkg.license ?? "see below"}`,
    "",
    "```",
    texts.join("\n\n"),
    "```",
  ].join("\n");
});

writeFileSync(
  "THIRD_PARTY_NOTICES.md",
  [
    "# Third-party notices",
    "",
    "frisk-mcp bundles the following packages into dist/index.js.",
    "",
    sections.join("\n\n"),
    "",
  ].join("\n"),
);
console.log(`THIRD_PARTY_NOTICES.md: ${roots.size} bundled package(s)`);
