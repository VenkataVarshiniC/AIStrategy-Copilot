import { apiClient } from "./client.js";

export function ingestUrls(sourceUrls, tags = {}) {
  return apiClient.post("/api/ingest/urls", { source_urls: sourceUrls, tags });
}

export function ingestPdf(file) {
  const formData = new FormData();
  formData.append("file", file);
  return apiClient.postForm("/api/ingest/pdf", formData);
}

export function getIngestionStatus() {
  return apiClient.get("/api/ingest/status");
}

export function resetKnowledgeBase() {
  return apiClient.del("/api/ingest/reset");
}
