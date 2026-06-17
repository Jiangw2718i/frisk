# Contributing to Frisk

Thanks for your interest in improving Frisk. This repository is a monorepo
containing two SDKs that track the same API surface:

- [`typescript/`](typescript/) — the `frisk-screen` npm package
- [`python/`](python/) — the `frisk-screen` PyPI package

## Development setup

### TypeScript

```bash
cd typescript
pnpm install
pnpm test        # vitest
pnpm typecheck   # tsc --noEmit
pnpm lint        # biome check
pnpm build       # tsup
```

### Python

This project uses [uv](https://docs.astral.sh/uv/).

```bash
cd python
uv sync
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

## Pull requests

1. Fork the repository and create a branch from `main`.
2. Keep changes focused; one logical change per pull request.
3. Add or update tests for any behavior change.
4. Run the lint, type, and test steps above before pushing — CI runs the same
   checks and must pass.
5. If your change touches both SDKs, keep their behavior and public API in sync.
6. Update [`CHANGELOG.md`](CHANGELOG.md) under the `Unreleased` heading.

## Keeping the SDKs in parity

Frisk's value depends on the two SDKs behaving identically. A change to the lite
screening logic, the verdict model, or the request/response shape in one
language should be mirrored in the other within the same pull request.

## Reporting bugs

Open an issue with a minimal reproduction, the SDK version, and the runtime
(Node/Bun/Deno version, or Python version). For security issues, do **not** open
a public issue — see [SECURITY.md](SECURITY.md).

## License

By contributing, you agree that your contributions will be licensed under the
[MIT License](LICENSE).
