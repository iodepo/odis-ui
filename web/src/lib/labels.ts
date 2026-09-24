export function formatTypeLabel(value: string): string {
  const bare = value.replace(/^schema:/, "").replace(/^sc:/, "");
  const key = bare.toLowerCase();
  // Deliberate rename; every other label is derived from the @type as indexed.
  if (key === "boattrip") return "Cruise";
  return bare.replace(/([a-z])([A-Z])/g, "$1 $2").replace(/([A-Z]+)([A-Z][a-z])/g, "$1 $2");
}

export function sourceLabel(id: string, name?: string | null): string {
  return name ?? id;
}
