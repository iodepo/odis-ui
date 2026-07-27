export function formatTypeLabel(value: string): string {
  const bare = value.replace(/^schema:/, "").replace(/^sc:/, "");
  const key = bare.toLowerCase();
  if (key === "creativework") return "Creative Work";
  if (key === "researchproject") return "Research Project";
  if (key === "boattrip") return "Cruise";
  if (key === "course") return "Course";
  if (key === "datadownload") return "Data Download";
  if (key === "contactpoint") return "Contact Point";
  if (key === "geoshape") return "Geo Shape";
  if (key === "datacatalog") return "Data Catalog";
  return bare.replace(/([a-z])([A-Z])/g, "$1 $2").replace(/([A-Z]+)([A-Z][a-z])/g, "$1 $2");
}

export function sourceLabel(id: string, name?: string | null): string {
  return name ? `${name} (${id})` : id;
}
