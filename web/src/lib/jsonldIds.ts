/** Collect unique JSON-LD `@id` URI strings, skipping blank nodes. */
export function extractAtIds(value: unknown, found: Set<string> = new Set()): string[] {
  if (value === null || value === undefined) {
    return [...found];
  }
  if (Array.isArray(value)) {
    for (const item of value) {
      extractAtIds(item, found);
    }
    return [...found];
  }
  if (typeof value === "object") {
    for (const [key, child] of Object.entries(value as Record<string, unknown>)) {
      if (key === "@id" && typeof child === "string") {
        const id = child.trim();
        if (id && !id.startsWith("_:")) {
          found.add(id);
        }
      } else {
        extractAtIds(child, found);
      }
    }
  }
  return [...found];
}

/**
 * TEMPORARY: OceanExpert OBIS links use `/institution/N` while indexed
 * OceanExpert records use `/institute/N`. Expand both so related-record
 * lookup can find either form. Remove once identifiers are aligned upstream.
 */
function withOceanExpertIdAliases(ids: string[]): string[] {
  const expanded = new Set(ids);
  for (const id of ids) {
    if (id.includes("oceanexpert.org/institution/")) {
      expanded.add(id.replace("/institution/", "/institute/"));
    } else if (id.includes("oceanexpert.org/institute/")) {
      expanded.add(id.replace("/institute/", "/institution/"));
    }
  }
  return [...expanded];
}

/** Prefer `jsonld` when present; otherwise walk the full raw document. */
export function extractRelatedIds(
  raw: Record<string, unknown> | null | undefined,
  selfId?: string | null,
): string[] {
  if (!raw) return [];
  const root =
    raw.jsonld !== undefined && raw.jsonld !== null
      ? raw.jsonld
      : raw;
  const ids = withOceanExpertIdAliases(extractAtIds(root));
  const skip = new Set<string>();
  if (selfId) skip.add(selfId);
  if (typeof raw.id === "string" && raw.id.trim()) skip.add(raw.id.trim());
  return ids.filter((id) => !skip.has(id));
}
