declare global {
  interface Window {
    dataLayer?: unknown[];
    gtag?: (...args: unknown[]) => void;
  }
}

export type SearchAnalyticsParams = {
  search_term: string;
  result_count?: number;
  types?: string[];
  sources?: string[];
};

/** Fire a GA4 recommended `search` event after a successful query. */
export function trackSearch(params: SearchAnalyticsParams): void {
  const term = params.search_term.trim();
  if (!term || typeof window.gtag !== "function") {
    return;
  }

  window.gtag("event", "search", {
    search_term: term,
    result_count: params.result_count,
    search_types: params.types?.join(",") || undefined,
    search_sources: params.sources?.join(",") || undefined,
  });
}
