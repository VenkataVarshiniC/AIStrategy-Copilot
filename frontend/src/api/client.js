/**
 * Base fetch wrapper. Every API module (analysis.js, ingestion.js) goes
 * through this so base URL, headers, and error normalization live in one place.
 */
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

export class ApiError extends Error {
  constructor(message, status, detail) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

async function request(path, options = {}) {
  const url = `${API_BASE_URL}${path}`;
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });

  if (!res.ok) {
    let detail = null;
    try {
      const body = await res.json();
      detail = body.detail || body;
    } catch {
      detail = res.statusText;
    }
    throw new ApiError(`Request to ${path} failed (${res.status})`, res.status, detail);
  }

  if (res.status === 204) return null;
  return res.json();
}

export const apiClient = {
  get: (path) => request(path, { method: "GET" }),
  post: (path, body) => request(path, { method: "POST", body: JSON.stringify(body) }),
  del: (path) => request(path, { method: "DELETE" }),
  postForm: async (path, formData) => {
    const url = `${API_BASE_URL}${path}`;
    const res = await fetch(url, { method: "POST", body: formData });
    if (!res.ok) {
      let detail = null;
      try {
        const body = await res.json();
        detail = body.detail || body;
      } catch {
        detail = res.statusText;
      }
      throw new ApiError(`Request to ${path} failed (${res.status})`, res.status, detail);
    }
    return res.json();
  },
};
