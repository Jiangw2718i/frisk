import { evaluateLite } from "./lite.js";
import type {
  Confidence,
  Policy,
  ScreenRequest,
  ScreenResult,
  Verdict,
} from "./types.js";

export const DEFAULT_BASE_URL = "https://api.tryfrisk.dev";

/** Raised when a hosted screening request cannot be completed. */
export class ScreenError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ScreenError";
  }
}

export interface ClientOptions {
  apiKey?: string;
  baseUrl?: string;
  timeoutMs?: number;
}

export interface ScreenOptions {
  endpoint?: string;
  amount?: number;
  asset?: string;
  policy?: Policy;
  observedPayTo?: string;
  /** Screening "temperature" in [0, 1]: 0 = permissive, 1 = paranoid. Default 0.3. */
  strictness?: number;
}

/**
 * Screen agent transactions before they execute.
 *
 * Without an API key the client runs in offline `lite` mode. Supply an API key
 * to use the hosted service, which adds reputation-graph, model, and
 * threat-feed signals and returns higher-confidence verdicts.
 */
export class Client {
  private readonly apiKey?: string;
  private readonly baseUrl: string;
  private readonly timeoutMs: number;

  constructor(options: ClientOptions = {}) {
    this.apiKey = options.apiKey;
    this.baseUrl = normalizeBaseUrl(options.baseUrl ?? DEFAULT_BASE_URL);
    this.timeoutMs = options.timeoutMs ?? 5000;
  }

  get mode(): "lite" | "hosted" {
    return this.apiKey ? "hosted" : "lite";
  }

  async screen(
    counterparty: string,
    options: ScreenOptions = {},
  ): Promise<ScreenResult> {
    const request: ScreenRequest = { counterparty, ...options };
    if (this.apiKey) {
      return this.screenHosted(request);
    }
    return evaluateLite(request);
  }

  private async screenHosted(request: ScreenRequest): Promise<ScreenResult> {
    const payload: Record<string, unknown> = {
      counterparty: request.counterparty,
      endpoint: request.endpoint,
      amount: request.amount,
      asset: request.asset,
      observed_pay_to: request.observedPayTo,
      strictness: request.strictness,
    };
    if (request.policy) {
      payload.policy = {
        max_per_call: request.policy.maxPerCall,
        allowed_assets: request.policy.allowedAssets,
      };
    }

    let response: Response;
    try {
      response = await fetch(`${this.baseUrl}/v1/screen`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${this.apiKey}`,
        },
        body: JSON.stringify(payload),
        signal: AbortSignal.timeout(this.timeoutMs),
      });
    } catch (error) {
      throw new ScreenError(
        `hosted screening unreachable: ${(error as Error).message}`,
      );
    }
    if (!response.ok) {
      throw new ScreenError(`hosted screening failed: HTTP ${response.status}`);
    }
    return resultFromPayload(
      (await response.json()) as Record<string, unknown>,
    );
  }
}

/**
 * Validate and normalize a base URL. HTTPS is required so the API key in the
 * Authorization header is never sent in plaintext; http is allowed only for
 * localhost to support local development and tests.
 */
function normalizeBaseUrl(raw: string): string {
  const trimmed = raw.replace(/\/+$/, "");
  let url: URL;
  try {
    url = new URL(trimmed);
  } catch {
    throw new ScreenError(`invalid baseUrl: ${raw}`);
  }
  const isLocalhost =
    url.hostname === "localhost" ||
    url.hostname === "127.0.0.1" ||
    url.hostname === "[::1]" ||
    url.hostname === "::1";
  if (url.protocol === "https:") return trimmed;
  if (url.protocol === "http:" && isLocalhost) return trimmed;
  throw new ScreenError(
    "baseUrl must use HTTPS (http is allowed only for localhost)",
  );
}

function resultFromPayload(data: Record<string, unknown>): ScreenResult {
  const verdict = data.verdict as Verdict;
  return {
    verdict,
    trustScore: Number(data.trust_score ?? 0),
    confidence: (data.confidence as Confidence) ?? "low",
    reasons: (data.reasons as string[]) ?? [],
    policyHits: (data.policy_hits as string[]) ?? [],
    source: "hosted",
    allowed: verdict === "allow",
  };
}
