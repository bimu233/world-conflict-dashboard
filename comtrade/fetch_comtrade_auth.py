import sys, os, time, json, requests
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ── config ─────────────────────────────────────────────────────────────────────


BASE_URL   = "https://comtradeapi.un.org/tools/v1/getTradeBalance/C/A/HS"
HEADERS    = {"Ocp-Apim-Subscription-Key": API_KEY}
YEAR_START = 1989
YEAR_END   = 2024
PAUSE      = 1.1   # seconds between calls (1 call/sec limit)
OUT_DIR    = os.path.dirname(os.path.abspath(__file__))

BILATERAL_OUT  = os.path.join(OUT_DIR, "bilateral_trade_auth.csv")
WORLD_OUT      = os.path.join(OUT_DIR, "world_totals_auth.csv")
CHECKPOINT     = os.path.join(OUT_DIR, "fetch_checkpoint.csv")

PERIOD_STR = ",".join(str(y) for y in range(YEAR_START, YEAR_END + 1))

# All 124 GED countries: name → ISO3
GED_TO_ISO3 = {
    "Afghanistan":                      "AFG",
    "Albania":                          "ALB",
    "Algeria":                          "DZA",
    "Angola":                           "AGO",
    "Argentina":                        "ARG",
    "Armenia":                          "ARM",
    "Australia":                        "AUS",
    "Austria":                          "AUT",
    "Azerbaijan":                       "AZE",
    "Bahrain":                          "BHR",
    "Bangladesh":                       "BGD",
    "Belgium":                          "BEL",
    "Benin":                            "BEN",
    "Bhutan":                           "BTN",
    "Bolivia":                          "BOL",
    "Bosnia-Herzegovina":               "BIH",
    "Botswana":                         "BWA",
    "Brazil":                           "BRA",
    "Burkina Faso":                     "BFA",
    "Burundi":                          "BDI",
    "Cambodia (Kampuchea)":             "KHM",
    "Cameroon":                         "CMR",
    "Canada":                           "CAN",
    "Central African Republic":         "CAF",
    "Chad":                             "TCD",
    "China":                            "CHN",
    "Colombia":                         "COL",
    "Comoros":                          "COM",
    "Congo":                            "COG",
    "Croatia":                          "HRV",
    "DR Congo (Zaire)":                 "COD",
    "Djibouti":                         "DJI",
    "Ecuador":                          "ECU",
    "Egypt":                            "EGY",
    "El Salvador":                      "SLV",
    "Eritrea":                          "ERI",
    "Ethiopia":                         "ETH",
    "France":                           "FRA",
    "Gambia":                           "GMB",
    "Georgia":                          "GEO",
    "Germany":                          "DEU",
    "Ghana":                            "GHA",
    "Guatemala":                        "GTM",
    "Guinea":                           "GIN",
    "Guinea-Bissau":                    "GNB",
    "Guyana":                           "GUY",
    "Haiti":                            "HTI",
    "Honduras":                         "HND",
    "India":                            "IND",
    "Indonesia":                        "IDN",
    "Iran":                             "IRN",
    "Iraq":                             "IRQ",
    "Israel":                           "ISR",
    "Italy":                            "ITA",
    "Ivory Coast":                      "CIV",
    "Jamaica":                          "JAM",
    "Jordan":                           "JOR",
    "Kenya":                            "KEN",
    "Kingdom of eSwatini (Swaziland)":  "SWZ",
    "Kuwait":                           "KWT",
    "Kyrgyzstan":                       "KGZ",
    "Laos":                             "LAO",
    "Lebanon":                          "LBN",
    "Lesotho":                          "LSO",
    "Liberia":                          "LBR",
    "Libya":                            "LBY",
    "Madagascar (Malagasy)":            "MDG",
    "Malaysia":                         "MYS",
    "Mali":                             "MLI",
    "Malta":                            "MLT",
    "Mauritania":                       "MRT",
    "Mexico":                           "MEX",
    "Moldova":                          "MDA",
    "Morocco":                          "MAR",
    "Mozambique":                       "MOZ",
    "Myanmar (Burma)":                  "MMR",
    "Namibia":                          "NAM",
    "Nepal":                            "NPL",
    "Netherlands":                      "NLD",
    "Nicaragua":                        "NIC",
    "Niger":                            "NER",
    "Nigeria":                          "NGA",
    "North Macedonia":                  "MKD",
    "Pakistan":                         "PAK",
    "Panama":                           "PAN",
    "Papua New Guinea":                 "PNG",
    "Paraguay":                         "PRY",
    "Peru":                             "PER",
    "Philippines":                      "PHL",
    "Poland":                           "POL",
    "Qatar":                            "QAT",
    "Romania":                          "ROU",
    "Russia (Soviet Union)":            "RUS",
    "Rwanda":                           "RWA",
    "Saudi Arabia":                     "SAU",
    "Senegal":                          "SEN",
    "Serbia (Yugoslavia)":              "SRB",
    "Sierra Leone":                     "SLE",
    "Solomon Islands":                  "SLB",
    "Somalia":                          "SOM",
    "South Africa":                     "ZAF",
    "South Sudan":                      "SSD",
    "Spain":                            "ESP",
    "Sri Lanka":                        "LKA",
    "Sudan":                            "SDN",
    "Sweden":                           "SWE",
    "Syria":                            "SYR",
    "Tajikistan":                       "TJK",
    "Tanzania":                         "TZA",
    "Thailand":                         "THA",
    "Togo":                             "TGO",
    "Trinidad and Tobago":              "TTO",
    "Tunisia":                          "TUN",
    "Turkey":                           "TUR",
    "Uganda":                           "UGA",
    "Ukraine":                          "UKR",
    "United Arab Emirates":             "ARE",
    "United Kingdom":                   "GBR",
    "United States of America":         "USA",
    "Uzbekistan":                       "UZB",
    "Venezuela":                        "VEN",
    "Yemen (North Yemen)":              "YEM",
    "Zambia":                           "ZMB",
    "Zimbabwe (Rhodesia)":              "ZWE",
}

ALL_ISO3 = sorted(set(GED_TO_ISO3.values()))


def log(msg):
    print(msg, flush=True)


def load_reporter_map():
    """Load ISO3 → Comtrade M49 numeric code from the existing map file."""
    map_path = os.path.join(os.path.dirname(OUT_DIR), "comtrade_reporter_map.csv")
    df = pd.read_csv(map_path)
    return dict(zip(df["iso3"], df["comtrade_code"].astype(str)))


def load_checkpoint():
    try:
        df = pd.read_csv(CHECKPOINT)
        done = set(df["reporter_code"].astype(str).tolist())
        log(f"  Resumed: {len(done)} countries already fetched.")
        return done
    except FileNotFoundError:
        return set()


def save_checkpoint(done_codes):
    pd.DataFrame({"reporter_code": sorted(done_codes)}).to_csv(CHECKPOINT, index=False)


def fetch_country(reporter_code):
    """Fetch all years for one reporter. Returns list of raw record dicts."""
    params = {
        "reporterCode": reporter_code,
        "period":       PERIOD_STR,
        "cmdCode":      "TOTAL",
    }
    for attempt in range(4):
        try:
            r = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=60)
            if r.status_code == 429:
                wait = 60 * (attempt + 1)
                log(f"    [rate-limit] waiting {wait}s...")
                time.sleep(wait)
                continue
            if r.status_code != 200:
                log(f"    [warn] HTTP {r.status_code} for code {reporter_code}")
                return []
            data = r.json()
            recs = data.get("data", [])
            # Handle potential truncation (shouldn't happen at 100k limit but guard anyway)
            count = data.get("count", len(recs))
            if count > len(recs):
                log(f"    [warn] truncated: got {len(recs)} of {count} records for {reporter_code}")
            return recs
        except Exception as e:
            log(f"    [warn] attempt {attempt+1} failed for {reporter_code}: {e}")
            time.sleep(5 * (attempt + 1))
    return []


def parse_records(recs, iso3, reporter_code):
    """Extract relevant fields from raw API records."""
    rows = []
    for r in recs:
        rows.append({
            "reporter_code":       reporter_code,
            "reporter_iso3":       iso3,
            "partner_code":        r.get("partnerCode"),
            "year":                r.get("refYear"),
            "exports_usd":         r.get("primaryValueX"),
            "imports_usd":         r.get("primaryValueM"),
            "trade_balance_usd":   r.get("primaryValueBal"),
        })
    return rows


# ── main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":

    log("Loading reporter code map...")
    iso3_to_code = load_reporter_map()

    # Resolve ISO3 → Comtrade code
    tasks, skipped = [], []
    for iso3 in ALL_ISO3:
        code = iso3_to_code.get(iso3)
        if code:
            tasks.append((iso3, code))
        else:
            skipped.append(iso3)
    if skipped:
        log(f"  No Comtrade code found for: {skipped}")

    done_codes = load_checkpoint()
    remaining  = [(iso3, code) for iso3, code in tasks if code not in done_codes]

    log(f"\nFetching authenticated bilateral trade (1989–2024):")
    log(f"  Total countries : {len(tasks)}")
    log(f"  Already done    : {len(tasks) - len(remaining)}")
    log(f"  To fetch        : {len(remaining)}")
    log(f"  Est. runtime    : ~{len(remaining) * PAUSE / 60:.1f} min")
    log("")

    bilateral_rows = []
    world_rows     = []

    # Load existing output files if resuming
    if done_codes:
        try:
            bilateral_rows = pd.read_csv(BILATERAL_OUT).to_dict("records")
            world_rows     = pd.read_csv(WORLD_OUT).to_dict("records")
            log(f"  Loaded existing: {len(bilateral_rows):,} bilateral + {len(world_rows):,} world rows")
        except FileNotFoundError:
            pass

    for i, (iso3, code) in enumerate(remaining, 1):
        recs = fetch_country(code)
        parsed = parse_records(recs, iso3, code)

        bilateral = [r for r in parsed if r["partner_code"] != 0]
        world      = [r for r in parsed if r["partner_code"] == 0]

        bilateral_rows.extend(bilateral)
        world_rows.extend(world)

        log(f"  [{i}/{len(remaining)}] {iso3} (code {code}): "
            f"{len(bilateral)} bilateral + {len(world)} world rows "
            f"({len(recs)} raw)")

        done_codes.add(code)

        # Save after every country
        pd.DataFrame(bilateral_rows).to_csv(BILATERAL_OUT, index=False)
        pd.DataFrame(world_rows).to_csv(WORLD_OUT, index=False)
        save_checkpoint(done_codes)

        time.sleep(PAUSE)

    # ── summary ────────────────────────────────────────────────────────────────

    df_b = pd.DataFrame(bilateral_rows)
    df_w = pd.DataFrame(world_rows)

    log(f"\n{'='*60}")
    log(f"DONE — output in comtrade/")
    log(f"  bilateral_trade_auth.csv")
    log(f"    Rows      : {len(df_b):,}")
    if not df_b.empty:
        log(f"    Reporters : {df_b['reporter_iso3'].nunique()}")
        log(f"    Partners  : {df_b['partner_code'].nunique()}")
        log(f"    Years     : {int(df_b['year'].min())}–{int(df_b['year'].max())}")
        log(f"    Has X+M   : {df_b['exports_usd'].notna().sum():,} exports, "
            f"{df_b['imports_usd'].notna().sum():,} imports")
    log(f"  world_totals_auth.csv")
    log(f"    Rows      : {len(df_w):,}")
    log(f"{'='*60}")
