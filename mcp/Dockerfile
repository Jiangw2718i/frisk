# Container image for directories that verify an MCP server by starting it and
# sending an introspection request. The server speaks stdio, so the container
# runs it in the foreground and does not expose a port.

FROM node:22-alpine AS build
WORKDIR /app
RUN npm install --global pnpm@11
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml .npmrc ./
RUN pnpm install --frozen-lockfile
COPY tsconfig.json tsup.config.ts ./
COPY scripts ./scripts
COPY src ./src
RUN pnpm build

# The build bundles every dependency into dist/index.js, so the runtime image
# needs nothing but that one file.
FROM node:22-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app/dist/index.js ./dist/index.js
USER node
ENTRYPOINT ["node", "dist/index.js"]
