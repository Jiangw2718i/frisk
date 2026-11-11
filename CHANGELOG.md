# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Both SDKs (`frisk-screen` on npm and PyPI) are versioned together.

## [Unreleased]

## [0.0.3] - 2026-11-11

### Changed

- Docs: the README now says how to get a hosted API key: one request to
  `https://api.tryfrisk.dev/keys`, with no account.
- Python: `frisk.__version__` reports the package version again; it had been
  left at 0.0.1.

### frisk-mcp 0.0.2

- Requires `@modelcontextprotocol/server` 2.3.1 or newer, which carries the
  October 2026 security fixes. Those advisories are in the HTTP transport,
  which frisk-mcp does not use (it speaks stdio), so this only keeps installs
  off the affected versions.
- Docs: the README says how to get a hosted API key instead of pointing at an
  email address.
- The server reports its version as 0.0.2 (it said 0.0.1).

## [0.0.2] - 2026-06-22

### Changed

- Docs: the hosted tier's cost is now described as "Free in early access"
  rather than "Usage-based", reflecting that the hosted API is free to start.

## [0.0.1] - 2026-06-16

### Added

- Initial public release of the TypeScript and Python SDKs.
- `Client.screen()` for pre-transaction risk screening, returning an
  `allow` / `review` / `block` verdict with a trust score and reasons.
- Lite mode: local, zero-dependency structural checks (malformed
  counterparties, `payTo` swaps, insecure endpoints, policy violations, and a
  seed blocklist).
- Hosted mode via API key for reputation history and live threat intelligence.

[Unreleased]: https://github.com/Jiangw2718i/frisk/compare/v0.0.2...HEAD
[0.0.2]: https://github.com/Jiangw2718i/frisk/releases/tag/v0.0.2
[0.0.1]: https://github.com/Jiangw2718i/frisk/releases/tag/v0.0.1
