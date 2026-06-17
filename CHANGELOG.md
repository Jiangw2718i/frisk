# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Both SDKs (`frisk-screen` on npm and PyPI) are versioned together.

## [Unreleased]

## [0.0.1] - 2026-06-16

### Added

- Initial public release of the TypeScript and Python SDKs.
- `Client.screen()` for pre-transaction risk screening, returning an
  `allow` / `review` / `block` verdict with a trust score and reasons.
- Lite mode: local, zero-dependency structural checks (malformed
  counterparties, `payTo` swaps, insecure endpoints, policy violations, and a
  seed blocklist).
- Hosted mode via API key for reputation history and live threat intelligence.

[Unreleased]: https://github.com/Jiangw2718i/frisk/compare/v0.0.1...HEAD
[0.0.1]: https://github.com/Jiangw2718i/frisk/releases/tag/v0.0.1
