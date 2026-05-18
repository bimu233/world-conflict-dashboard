"""
Fetch World Bank WDI indicators for all countries, 1989-2024.
Outputs: wdi_indicators.csv  (long format: iso3, country, year, indicator, value)
         wdi_indicators.json (wide format: { ISO3: [{year, gdp_growth, fdi_pct_gdp, trade_pct_gdp}] })
"""

import requests, json, csv, time
from pathlib import Path

OUT_DIR = Path(__file__).parent

INDICATORS = {
    "NY.GDP.MKTP.KD.ZG": "gdp_growth",       # GDP growth (annual %)
    "BX.KLT.DINV.WD.GD.ZS": "fdi_pct_gdp",  # FDI net inflows (% of GDP)
    "NE.TRD.GNFS.ZS": "trade_pct_gdp",       # Trade (% of GDP)
}

DATE_RANGE = "1989:2024"
PER_PAGE   = 10000


def fetch_indicator(code):
    url = (
        f"https://api.worldbank.org/v2/country/all/indicator/{code}"
        f"?format=json&date={DATE_RANGE}&per_page={PER_PAGE}"
    )
    rows = []
    page = 1
    while True:
        for attempt in range(4):
            try:
                r = requests.get(url + f"&page={page}", timeout=90)
                r.raise_for_status()
                break
            except Exception as e:
                if attempt == 3:
                    raise
                print(f"  retry {attempt+1} after error: {e}", flush=True)
                time.sleep(5 * (attempt + 1))
        data = r.json()
        meta, records = data[0], data[1]
        if not records:
            break
        rows.extend(records)
        print(f"  page {page}/{meta['pages']}  ({len(rows)} so far)", flush=True)
        if page >= meta["pages"]:
            break
        page += 1
        time.sleep(0.5)
    return rows


def main():
    # { iso3 -> { year -> { col: value } } }
    wide = {}

    all_rows = []  # for CSV

    for code, col in INDICATORS.items():
        print(f"Fetching {col} ({code}) ...", flush=True)
        records = fetch_indicator(code)
        print(f"  {len(records)} records", flush=True)

        for rec in records:
            if rec["value"] is None:
                continue
            iso3    = rec["countryiso3code"]
            country = rec["country"]["value"]
            year    = int(rec["date"])
            value   = float(rec["value"])

            # skip aggregate regions (iso3 codes are 2-char for aggregates in WB)
            if len(iso3) != 3:
                continue

            all_rows.append({
                "iso3": iso3,
                "country": country,
                "year": year,
                "indicator": col,
                "value": value,
            })

            if iso3 not in wide:
                wide[iso3] = {}
            if year not in wide[iso3]:
                wide[iso3][year] = {"country": country}
            wide[iso3][year][col] = value

    # ── CSV (long format) ─────────────────────────────────────────────────────
    csv_path = OUT_DIR / "wdi_indicators.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["iso3","country","year","indicator","value"])
        writer.writeheader()
        writer.writerows(sorted(all_rows, key=lambda r: (r["iso3"], r["year"], r["indicator"])))
    print(f"\nWrote {csv_path}  ({len(all_rows)} rows)")

    # ── JSON (wide format) ────────────────────────────────────────────────────
    json_out = {}
    for iso3, years in wide.items():
        json_out[iso3] = sorted(
            [{"year": yr, **vals} for yr, vals in years.items()],
            key=lambda d: d["year"]
        )

    json_path = OUT_DIR / "wdi_indicators.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_out, f, separators=(",", ":"))
    print(f"Wrote {json_path}  ({len(json_out)} countries)")


if __name__ == "__main__":
    main()
