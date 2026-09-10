export const GRAPH_FRAGMENTS_STORAGE_KEY = "odis-search-include-graph-fragments";
export const RELATED_RECORDS_STORAGE_KEY = "odis-search-show-related-records";

export function parseGraphFragmentsParam(value: string | null): boolean {
  if (!value) return false;
  const normalized = value.trim().toLowerCase();
  return normalized === "1" || normalized === "true" || normalized === "yes";
}

export function readGraphFragmentsPreference(): boolean {
  try {
    return localStorage.getItem(GRAPH_FRAGMENTS_STORAGE_KEY) === "1";
  } catch {
    return false;
  }
}

export function writeGraphFragmentsPreference(enabled: boolean): void {
  try {
    if (enabled) {
      localStorage.setItem(GRAPH_FRAGMENTS_STORAGE_KEY, "1");
    } else {
      localStorage.removeItem(GRAPH_FRAGMENTS_STORAGE_KEY);
    }
  } catch {
    // ignore
  }
}

export function readRelatedRecordsPreference(): boolean {
  try {
    return localStorage.getItem(RELATED_RECORDS_STORAGE_KEY) === "1";
  } catch {
    return false;
  }
}

export function writeRelatedRecordsPreference(enabled: boolean): void {
  try {
    if (enabled) {
      localStorage.setItem(RELATED_RECORDS_STORAGE_KEY, "1");
    } else {
      localStorage.removeItem(RELATED_RECORDS_STORAGE_KEY);
    }
  } catch {
    // ignore
  }
}
