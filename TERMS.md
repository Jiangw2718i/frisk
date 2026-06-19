# Frisk — Terms of Service & Disclaimer

> **Scope.** These Terms cover the *hosted* service at `api.tryfrisk.dev`. The
> open-source SDKs are separately governed by the MIT License in the public
> repository.

Last updated: 2026-06-19

## 1. The service

Frisk provides **advisory pre-transaction risk screening** for autonomous
agents and their operators. Given a counterparty (e.g. a blockchain address or
endpoint) and optional transaction context, Frisk returns a verdict
(`allow` / `review` / `block`), a trust score, and human-readable reasons.

These outputs are **signals to inform your own decision**. Frisk never holds,
moves, or blocks funds, and never executes or prevents any transaction. You
remain fully in control of, and solely responsible for, every action you take.

## 2. Acceptance

By accessing or using the hosted API (including with an API key) you agree to
these Terms. If you do not agree, do not use the service.

## 3. No warranty; accuracy

The service is provided **"as is" and "as available," without warranties of any
kind**, express or implied, including merchantability, fitness for a particular
purpose, and non-infringement.

Frisk draws on heuristics, machine-learning models, on-chain analysis, and
third-party and public data sources (for example, OFAC sanctions data). Such
data may be **incomplete, delayed, or inaccurate**. A verdict is a probabilistic
risk signal, **not a statement of fact** about any person or address, and
specifically:

- An `allow` verdict is **not** a guarantee that a counterparty is safe.
- A `review` / `block` verdict is **not** an accusation or a determination that
  a counterparty is unlawful, fraudulent, or sanctioned.

## 4. Not professional advice

Frisk does **not** provide legal, financial, investment, tax, or compliance
advice, and is **not** a substitute for your own sanctions screening, KYC/AML
program, or other regulatory obligations. You are responsible for meeting any
laws and regulations that apply to you.

## 5. Acceptable use

You agree not to:

- use the service for any unlawful purpose, or to facilitate the evasion of
  sanctions, money laundering, or other illegal activity;
- exceed published rate limits, or probe, overload, or disrupt the service;
- resell, redistribute, or bulk-extract the underlying data except as expressly
  permitted;
- misrepresent Frisk's output as a definitive or official determination.

We may suspend or revoke access (including API keys) at any time for suspected
abuse or violation of these Terms.

## 6. API keys

API keys are secrets. You are responsible for keeping your keys confidential and
for all activity under them. Notify us promptly if a key is compromised; we can
revoke and reissue keys. Keys may stop working shortly after revocation.

## 7. Availability

The service may change, be interrupted, or be discontinued at any time **without
notice and without any service-level guarantee.**

## 8. Limitation of liability

To the maximum extent permitted by law, Frisk and its contributors are **not
liable** for any indirect, incidental, special, consequential, or punitive
damages, or for any loss of funds, profits, data, or goodwill, arising from your
use of (or inability to use) the service or reliance on its output. To the
extent any liability cannot be excluded, it is limited to the greater of the
amount you paid for the service in the prior 3 months or USD 100.

## 9. Changes

We may update these Terms. Material changes will be reflected by the "last
updated" date. Continued use after changes constitutes acceptance.

## 10. Governing law & contact

These Terms are governed by the laws of Singapore, without regard to
conflict-of-laws rules. Questions: support@tryfrisk.dev.
