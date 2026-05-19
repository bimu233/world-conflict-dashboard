"""
Retry fetch for:
  USA  (code 842, not 841)
  IND  (code 699, not 356)
  DEU  (code 276)  — year-by-year due to large dataset
  ESP  (code 724)  — year-by-year
  TUR  (code 792)  — year-by-year

Appends to bilateral_trade_auth.csv and world_totals_auth.csv,
then rebuilds trade_flows.json and world_trade_totals.json.
"""

import sys, os, time, json, requests
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

API_KEY  = "4907f4211ea847b4b2b1689b2eeeb6c3"
BASE_URL = "https://comtradeapi.un.org/tools/v1/getTradeBalance/C/A/HS"
HEADERS  = {"Ocp-Apim-Subscription-Key": API_KEY}
PAUSE    = 1.1

HERE   = os.path.dirname(os.path.abspath(__file__))
ROOT   = os.path.dirname(HERE)
PUBLIC = os.path.join(ROOT, "my-app", "public", "data")

BILATERAL = os.path.join(HERE, "bilateral_trade_auth.csv")
WORLD_OUT = os.path.join(HERE, "world_totals_auth.csv")
CKPT      = os.path.join(HERE, "fetch_retry_checkpoint.csv")

# Countries to fetch: (iso3, comtrade_code, batch_all_years)
TARGETS = [
    ("USA", 842, True),
    ("IND", 699, True),
    ("DEU", 276, False),   # year-by-year
    ("ESP", 724, False),
    ("TUR", 792, False),
]

YEARS = list(range(1989, 2025))


def log(msg): print(msg, flush=True)


def load_checkpoint():
    try:
        df = pd.read_csv(CKPT)
        done = set(zip(df["iso3"], df["year"].astype(str)))
        log(f"  Resumed: {len(done)} (iso3,year) pairs already done.")
        return done
    except FileNotFoundError:
        return set()


def save_checkpoint(done):
    rows = [{"iso3": iso3, "year": yr} for iso3, yr in done]
    pd.DataFrame(rows).to_csv(CKPT, index=False)


def fetch_one(reporter_code, period_str, label=""):
    params = {"reporterCode": reporter_code, "period": period_str, "cmdCode": "TOTAL"}
    for attempt in range(4):
        try:
            r = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=90)
            if r.status_code == 429:
                wait = 60 * (attempt + 1)
                log(f"    [rate-limit] waiting {wait}s...")
                time.sleep(wait)
                continue
            if r.status_code != 200:
                log(f"    [warn] HTTP {r.status_code} {label}")
                return []
            recs = r.json().get("data", [])
            return recs
        except Exception as e:
            log(f"    [warn] attempt {attempt+1} failed {label}: {e}")
            time.sleep(5 * (attempt + 1))
    return []


def parse(recs, iso3, reporter_code):
    rows = []
    for r in recs:
        rows.append({
            "reporter_code":     reporter_code,
            "reporter_iso3":     iso3,
            "partner_code":      r.get("partnerCode"),
            "year":              r.get("refYear"),
            "exports_usd":       r.get("primaryValueX"),
            "imports_usd":       r.get("primaryValueM"),
            "trade_balance_usd": r.get("primaryValueBal"),
        })
    return rows


if __name__ == "__main__":

    done = load_checkpoint()
    new_bilateral, new_world = [], []

    for iso3, code, batch in TARGETS:
        if batch:
            # Single call with all years
            key = (iso3, "ALL")
            if key in done:
                log(f"  {iso3}: already done, skipping.")
                continue
            log(f"  Fetching {iso3} (code {code}) — all years batched...")
            period_str = ",".join(str(y) for y in YEARS)
            recs = fetch_one(code, period_str, f"{iso3}")
            parsed = parse(recs, iso3, code)
            new_bilateral.extend([r for r in parsed if r["partner_code"] != 0])
            new_world.extend([r for r in parsed if r["partner_code"] == 0])
            log(f"    {iso3}: {len([r for r in parsed if r['partner_code']!=0])} bilateral + "
                f"{len([r for r in parsed if r['partner_code']==0])} world rows")
            done.add(key)
            save_checkpoint(done)
            time.sleep(PAUSE)
        else:
            # Year-by-year
            years_needed = [y for y in YEARS if (iso3, str(y)) not in done]
            log(f"  Fetching {iso3} (code {code}) — {len(years_needed)} years one-by-one...")
            for year in years_needed:
                recs = fetch_one(code, str(year), f"{iso3} {year}")
                parsed = parse(recs, iso3, code)
                new_bilateral.extend([r for r in parsed if r["partner_code"] != 0])
                new_world.extend([r for r in parsed if r["partner_code"] == 0])
                done.add((iso3, str(year)))
                save_checkpoint(done)
                time.sleep(PAUSE)
            total_b = len([r for r in new_bilateral if r["reporter_iso3"] == iso3])
            log(f"    {iso3}: done — {total_b} bilateral rows total")

    if not new_bilateral and not new_world:
        log("Nothing new to add.")
        sys.exit(0)

    log(f"\nNew rows: {len(new_bilateral):,} bilateral + {len(new_world):,} world")

    # ── append to existing CSVs ────────────────────────────────────────────────

    existing_b = pd.read_csv(BILATERAL)
    existing_w = pd.read_csv(WORLD_OUT)

    # Remove any old rows for these countries (replace with fresh data)
    retry_iso3 = {t[0] for t in TARGETS}
    existing_b = existing_b[~existing_b["reporter_iso3"].isin(retry_iso3)]
    existing_w = existing_w[~existing_w["reporter_iso3"].isin(retry_iso3)]

    combined_b = pd.concat([existing_b, pd.DataFrame(new_bilateral)], ignore_index=True)
    combined_w = pd.concat([existing_w, pd.DataFrame(new_world)],     ignore_index=True)

    combined_b.to_csv(BILATERAL, index=False)
    combined_w.to_csv(WORLD_OUT, index=False)
    log(f"Updated bilateral_trade_auth.csv: {len(combined_b):,} rows, "
        f"{combined_b['reporter_iso3'].nunique()} reporters")

    # ── rebuild JSON files ─────────────────────────────────────────────────────

    log("\nRebuilding dashboard JSON files...")
    import subprocess, sys as _sys
    result = subprocess.run(
        [_sys.executable, os.path.join(HERE, "process_auth_data.py")],
        cwd=ROOT
    )
    if result.returncode != 0:
        log("process_auth_data.py failed — run it manually.")
    else:
        log("Done.")
