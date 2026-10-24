/**
 * API Client for AI News Scraper Backend
 * REST endpoints + WebSocket connection management
 */

function getApiBase() {
  const envBase = process.env.NEXT_PUBLIC_API_URL;
  if (envBase) return envBase;

  if (typeof window !== "undefined") {
    if (
      window.location.hostname === "localhost" ||
      window.location.hostname === "127.0.0.1"
    ) {
      return "http://127.0.0.1:8000";
    }
    return window.location.origin;
  }

  return "http://127.0.0.1:8000";
}

function getWsBase() {
  const envBase = process.env.NEXT_PUBLIC_WS_URL;
  if (envBase) return envBase;

  if (typeof window !== "undefined") {
    if (
      window.location.hostname === "localhost" ||
      window.location.hostname === "127.0.0.1"
    ) {
      return "ws://127.0.0.1:8000";
    }
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${protocol}//${window.location.host}`;
  }

  return "ws://127.0.0.1:8000";
}

const API_BASE = getApiBase();
const WS_BASE = getWsBase();

/* ---------- REST helpers ---------- */

async function request(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    const message =
      err?.error_message ||
      err?.detail ||
      res.statusText ||
      `API error ${res.status}`;
    const apiError = new Error(message);
    apiError.errorCode = err?.error_code || "HTTP_ERROR";
    apiError.suggestedFix =
      err?.suggested_fix || "Check the backend logs and request payload.";
    apiError.details = err?.details;
    throw apiError;
  }
  return res.json();
}

/* ---------- Health ---------- */
export const getHealth = () => request("/health");
export const getMinioHealth = () => request("/health/minio");
export const getPostgresHealth = () => request("/health/postgres");

/* ---------- Data Lake Counts ---------- */
export const getBronzeCount = () => request("/datalake/bronze/count");
export const getSilverCount = () => request("/datalake/silver/count");
export const getGoldCount = () => request("/datalake/gold/count");

/* ---------- Scraping ---------- */
export const scrapeArticles = (scraperType = "both", limitPerSource = 5) =>
  request("/scrape", {
    method: "POST",
    body: JSON.stringify({
      scraper_type: scraperType,
      limit_per_source: limitPerSource,
    }),
  });

/* ---------- Analytics ---------- */
export const generateAnalytics = (articles, days = 7) =>
  request(`/analytics/generate?days=${days}`, {
    method: "POST",
    body: JSON.stringify(articles),
  });

export const getTrends = (days = 7) =>
  request(`/analytics/trends?days=${days}`);

export const getArticles = (limit = null, days = null) => {
  const params = new URLSearchParams();
  if (limit !== null && limit !== undefined) {
    params.set("limit", String(limit));
  }
  if (days !== null && days !== undefined) {
    params.set("days", String(days));
  }
  const query = params.toString();
  return request(`/analytics/articles${query ? `?${query}` : ""}`);
};

/* ---------- Ingestion ---------- */
export const ingestArticles = (articles, sourceType = "mixed") =>
  request("/ingest", {
    method: "POST",
    body: JSON.stringify({ articles, source_type: sourceType }),
  });

export const getIngestionStatus = () => request("/ingest/status");

/* ---------- Transformation ---------- */
export const cleanArticles = (articles) =>
  request("/transform/clean", {
    method: "POST",
    body: JSON.stringify(articles),
  });

export const filterLanguage = (articles) =>
  request("/transform/filter-language", {
    method: "POST",
    body: JSON.stringify(articles),
  });

/* ---------- Fetch all KPI data in parallel ---------- */
export async function fetchDashboardData(trendDays = 7, articleDays = null) {
  const [bronze, silver, gold, trends, articles] = await Promise.allSettled([
    getBronzeCount(),
    getSilverCount(),
    getGoldCount(),
    getTrends(trendDays),
    getArticles(null, articleDays),
  ]);

  return {
    bronze: bronze.status === "fulfilled" ? bronze.value : { count: 0 },
    silver: silver.status === "fulfilled" ? silver.value : { count: 0 },
    gold: gold.status === "fulfilled" ? gold.value : { count: 0 },
    trends:
      trends.status === "fulfilled"
        ? trends.value
        : { trends: [], sources: [], categories: [], keywords: [] },
    articles: articles.status === "fulfilled" ? articles.value.articles : [],
  };
}

export { API_BASE, WS_BASE };
