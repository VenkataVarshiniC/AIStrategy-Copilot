import { apiClient } from "./client.js";

/**
 * @param {{
 *   question: string,
 *   company_name?: string,
 *   industry?: string,
 *   additional_context?: string,
 *   max_branches?: number,
 *   quant_params?: Record<string, number>
 * }} payload
 * @returns {Promise<import("../lib/types.js").AnalysisResponse>}
 */
export function runAnalysis(payload) {
  return apiClient.post("/api/analysis/run", payload);
}
