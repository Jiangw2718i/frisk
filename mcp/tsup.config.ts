import { defineConfig } from "tsup";

export default defineConfig({
  entry: ["src/index.ts"],
  format: ["esm"],
  clean: true,
  sourcemap: true,
  target: "node20",
  banner: { js: "#!/usr/bin/env node" },
  // Everything the server needs is bundled into dist (package.json lists no
  // runtime dependencies), so an install gets exactly the code that was tested
  // here instead of whatever is newest in range on that day. The metafile
  // records which packages went in, for THIRD_PARTY_NOTICES.md.
  metafile: true,
});
