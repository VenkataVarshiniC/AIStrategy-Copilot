import { useCallback, useState } from "react";
import { runAnalysis } from "../api/analysis.js";
import { ApiError } from "../api/client.js";

/**
 * Encapsulates the analysis request lifecycle: idle -> loading -> success | error.
 * Keeps App.jsx focused on layout rather than fetch/error plumbing.
 */
export function useAnalysis() {
  const [status, setStatus] = useState("idle"); // idle | loading | success | error
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const submit = useCallback(async (payload) => {
    setStatus("loading");
    setError(null);
    try {
      const response = await runAnalysis(payload);
      setResult(response);
      setStatus("success");
    } catch (e) {
      const message =
        e instanceof ApiError
          ? typeof e.detail === "string"
            ? e.detail
            : e.message
          : "Something went wrong while running the analysis. Check that the backend is running.";
      setError(message);
      setStatus("error");
    }
  }, []);

  const reset = useCallback(() => {
    setStatus("idle");
    setResult(null);
    setError(null);
  }, []);

  return { status, result, error, submit, reset };
}
