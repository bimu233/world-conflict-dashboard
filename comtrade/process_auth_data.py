"""
Process authenticated Comtrade data into dashboard-ready JSON files.

Steps:
  1. Deduplicate bilateral_trade_auth.csv (multiple HS revisions per row)
     → keep row with highest (exports_usd + imports_usd) per reporter×partner×year
  2. Deduplicate world_totals_auth.csv same way
  3. Build trade_flows.json        → my-app/public/data/trade_flows.json
  4. Build world_trade_totals.json → my-app/public/data/world_trade_totals.json
"""

import sys, os, json
import pandas as pd
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE       = os.path.dirname(os.path.abspath(__file__))
ROOT       = os.path.dirname(HERE)
PUBLIC     = os.path.join(ROOT, "my-app", "public", "data")

BILATERAL  = os.path.join(HERE, "bilateral_trade_auth.csv")
WORLD      = os.path.join(HERE, "world_totals_auth.csv")
REP_MAP    = os.path.join(ROOT, "comtrade_reporter_map.csv")

FLOWS_OUT  = os.path.join(PUBLIC, "trade_flows.json")
TOTALS_OUT = os.path.join(PUBLIC, "world_trade_totals.json")

TOP_N = 15


def log(msg): print(msg, flush=True)


# ── load & deduplicate ─────────────────────────────────────────────────────────

log("Loading bilateral trade data...")
df = pd.read_csv(BILATERAL, dtype={"partner_code": "Int64"})
log(f"  Raw rows: {len(df):,}")

df["exports_usd"] = pd.to_numeric(df["exports_usd"], errors="coerce").fillna(0)
df["imports_usd"] = pd.to_numeric(df["imports_usd"], errors="coerce").fillna(0)
df["total_usd"]   = df["exports_usd"] + df["imports_usd"]

# Deduplicate: keep row with highest total_usd per reporter×partner×year
df = (
    df.sort_values("total_usd", ascending=False)
      .drop_duplicates(subset=["reporter_iso3", "partner_code", "year"], keep="first")
      .reset_index(drop=True)
)
log(f"  After dedup: {len(df):,} rows")
log(f"  Reporters: {df['reporter_iso3'].nunique()}  |  "
    f"Partners: {df['partner_code'].nunique()}  |  "
    f"Years: {int(df['year'].min())}–{int(df['year'].max())}")

# ── load & deduplicate world totals ───────────────────────────────────────────

log("\nLoading world totals...")
wdf = pd.read_csv(WORLD, dtype={"partner_code": "Int64"})
log(f"  Raw rows: {len(wdf):,}")

wdf["exports_usd"] = pd.to_numeric(wdf["exports_usd"], errors="coerce").fillna(0)
wdf["imports_usd"] = pd.to_numeric(wdf["imports_usd"], errors="coerce").fillna(0)
wdf["total_usd"]   = wdf["exports_usd"] + wdf["imports_usd"]

wdf = (
    wdf.sort_values("total_usd", ascending=False)
       .drop_duplicates(subset=["reporter_iso3", "year"], keep="first")
       .reset_index(drop=True)
)
log(f"  After dedup: {len(wdf):,} rows  |  "
    f"Reporters: {wdf['reporter_iso3'].nunique()}")

# ── partner code → ISO3 mapping ───────────────────────────────────────────────

log("\nBuilding partner code → ISO3 map...")
rep_map = pd.read_csv(REP_MAP)
code_to_iso3 = dict(zip(rep_map["comtrade_code"].astype(int), rep_map["iso3"]))

df["partner_iso3"] = df["partner_code"].astype(int).map(code_to_iso3)
unmapped = df["partner_iso3"].isna().sum()
log(f"  Unmapped partner codes: {unmapped:,} rows dropped")
df = df.dropna(subset=["partner_iso3"])

# Exclude world total (partner_code == 0) from bilateral
df_bilateral = df[df["partner_code"] != 0].copy()
log(f"  Bilateral rows (partner≠0): {len(df_bilateral):,}")

# ── build trade_flows.json ────────────────────────────────────────────────────

log("\nBuilding trade_flows.json...")
flows = {}
groups = df_bilateral.groupby(["reporter_iso3", "year"])
for (iso3, year), grp in groups:
    top = grp.nlargest(TOP_N, "total_usd")
    key = f"{iso3}_{int(year)}"
    flows[key] = [
        {
            "partner_iso3": row["partner_iso3"],
            "total_usd":    round(row["total_usd"]),
            "exports_usd":  round(row["exports_usd"]) if row["exports_usd"] > 0 else None,
            "imports_usd":  round(row["imports_usd"]) if row["imports_usd"] > 0 else None,
        }
        for _, row in top.iterrows()
    ]

with open(FLOWS_OUT, "w", encoding="utf-8") as f:
    json.dump(flows, f, separators=(",", ":"))

size = os.path.getsize(FLOWS_OUT) / 1e6
log(f"  Saved {FLOWS_OUT}")
log(f"  {len(flows):,} country-year keys  |  {size:.1f} MB")
log(f"  Year range: {min(int(k.split('_')[1]) for k in flows)}–"
    f"{max(int(k.split('_')[1]) for k in flows)}")

# ── build world_trade_totals.json ─────────────────────────────────────────────

log("\nBuilding world_trade_totals.json...")
totals = {}
for iso3, grp in wdf.groupby("reporter_iso3"):
    totals[iso3] = [
        {
            "year":        int(r["year"]),
            "exports_usd": round(r["exports_usd"]) if r["exports_usd"] > 0 else None,
            "imports_usd": round(r["imports_usd"]) if r["imports_usd"] > 0 else None,
        }
        for _, r in grp.sort_values("year").iterrows()
    ]

with open(TOTALS_OUT, "w", encoding="utf-8") as f:
    json.dump(totals, f, separators=(",", ":"))

size = os.path.getsize(TOTALS_OUT) / 1e6
log(f"  Saved {TOTALS_OUT}")
log(f"  {len(totals)} countries  |  {size:.1f} MB")

# ── coverage summary ──────────────────────────────────────────────────────────

log("\n" + "="*60)
log("DONE. Dashboard data updated:")
log(f"  trade_flows.json        — {len(flows):,} keys (1989–2024)")
log(f"  world_trade_totals.json — {len(totals)} countries (1989–2024)")

# Check key countries
for iso3 in ["USA", "IND", "MEX", "SYR", "CHN"]:
    keys_for = [k for k in flows if k.startswith(iso3 + "_")]
    yrs = sorted(int(k.split("_")[1]) for k in keys_for)
    if yrs:
        log(f"  {iso3}: {len(yrs)} years ({yrs[0]}–{yrs[-1]})")
    else:
        log(f"  {iso3}: no data")
log("="*60)
