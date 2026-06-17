/** Recommended action for a screened transaction. */
export type Verdict = "allow" | "review" | "block";

/**
 * How much weight to place on the verdict. Offline (lite) screening always
 * reports `"low"`; the hosted service raises confidence as graph, model, and
 * threat-feed coverage improve.
 */
export type Confidence = "low" | "medium" | "high";

/** Caller-supplied spending policy. Every field is optional. */
export interface Policy {
  maxPerCall?: number;
  allowedAssets?: string[];
}

/** A transaction an agent is about to perform. */
export interface ScreenRequest {
  counterparty: string;
  endpoint?: string;
  amount?: number;
  asset?: string;
  policy?: Policy;
  /**
   * The payTo address the endpoint actually returned this request, if
   * observed. Used to detect dynamic-payTo swaps.
   */
  observedPayTo?: string;
  /** Screening "temperature" in [0, 1]: 0 = permissive, 1 = paranoid. Default 0.3. */
  strictness?: number;
}

/** The outcome of screening a transaction. */
export interface ScreenResult {
  verdict: Verdict;
  trustScore: number; // 0-100
  confidence: Confidence;
  reasons: string[];
  policyHits: string[];
  source: "lite" | "hosted";
  allowed: boolean;
}
