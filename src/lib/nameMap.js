// Normalizes CSV country names → GeoJSON feature names.
// The two datasets use different naming conventions for ~14 countries.
export const nameMap = {
  "Bosnia-Herzegovina":              "Bosnia and Herz.",
  "Cambodia (Kampuchea)":            "Cambodia",
  "Central African Republic":        "Central African Rep.",
  "DR Congo (Zaire)":                "Dem. Rep. Congo",
  "Ivory Coast":                     "Côte d'Ivoire",
  "Kingdom of eSwatini (Swaziland)": "eSwatini",
  "Madagascar (Malagasy)":           "Madagascar",
  "Myanmar (Burma)":                 "Myanmar",
  "Russia (Soviet Union)":           "Russia",
  "Serbia (Yugoslavia)":             "Serbia",
  "Solomon Islands":                 "Solomon Is.",
  "South Sudan":                     "S. Sudan",
  "Yemen (North Yemen)":             "Yemen",
  "Zimbabwe (Rhodesia)":             "Zimbabwe",
};

// CSV country name → GeoJSON name
export function csvToGeo(name) {
  return nameMap[name] ?? name;
}

// GeoJSON name → CSV country name (reverse lookup)
export const geoToCSV = Object.fromEntries(
  Object.entries(nameMap).map(([csv, geo]) => [geo, csv])
);

export function geoNameToCSV(geoName) {
  return geoToCSV[geoName] ?? geoName;
}
