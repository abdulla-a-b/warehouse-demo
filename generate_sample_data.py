#!/usr/bin/env python3
"""
GUDAM(TM) - Sample / bulk data generator.

Generates a gudam-kpi-records.json file that can be imported via
Admin -> KPI Records -> Import JSON, or pushed directly to the
Google Apps Script backend with --push <WEB_APP_URL>.

Usage:
    python generate_sample_data.py                     # 3 months of sample data
    python generate_sample_data.py --months 6
    python generate_sample_data.py --push https://script.google.com/macros/s/XXX/exec
    python generate_sample_data.py --from-csv mydata.csv   # bulk import a CSV
        CSV columns: warehouse,kpi_id,month,numerator,denominator,note
"""
import argparse, csv, json, random, sys, time, urllib.request
from datetime import date

# KPI catalog: id -> (type, realistic sample range for numerator ratio)
KPIS = {
    # RMW
    "rmw01": ("pct", 98.5, 100.0), "rmw02": ("pct", 99.0, 100.0),
    "rmw03": ("pct", 96.0, 100.0), "rmw04": ("hours", 1.2, 2.6),
    "rmw05": ("pct", 99.0, 100.0), "rmw06": ("pct", 99.5, 100.0),
    "rmw07": ("minutes", 20, 40),  "rmw08": ("pct", 98.0, 100.0),
    "rmw09": ("pct", 0.2, 1.8),    "rmw10": ("ratio", 4.0, 9.0),
    "rmw11": ("days", 2.5, 8.5),   "rmw12": ("pct", 98.0, 100.0),
    "rmw13": ("pct", 0.1, 0.9),    "rmw14": ("pct", 74.0, 94.0),
    "rmw15": ("pct", 98.0, 100.0), "rmw16": ("minutes", 5, 18),
    "rmw17": ("pct", 0.5, 3.0),    "rmw18": ("pct", 96.0, 100.0),
    "rmw19": ("pct", 92.0, 100.0), "rmw20": ("pct", 90.0, 100.0),
    # FGW
    "fgw01": ("pct", 98.5, 100.0), "fgw02": ("pct", 99.0, 100.0),
    "fgw03": ("pct", 99.4, 100.0), "fgw04": ("pct", 99.4, 100.0),
    "fgw05": ("pct", 96.0, 100.0), "fgw06": ("hours", 1.2, 2.6),
    "fgw07": ("pct", 98.0, 100.0), "fgw08": ("pct", 96.0, 100.0),
    "fgw09": ("pct", 99.0, 100.0), "fgw10": ("pct", 99.7, 100.0),
    "fgw11": ("days", 0.8, 3.8),   "fgw12": ("pct", 74.0, 94.0),
    "fgw13": ("pct", 0.05, 0.4),   "fgw14": ("pct", 98.0, 100.0),
    "fgw15": ("pct", 98.5, 100.0), "fgw16": ("hours", 4.0, 9.0),
    "fgw17": ("ratio", 6.0, 14.0), "fgw18": ("ratio", 20.0, 45.0),
    "fgw19": ("pct", 92.0, 100.0), "fgw20": ("pct", 90.0, 100.0),
}

def uid():
    return format(int(time.time() * 1000), "x") + format(random.randrange(16**5), "05x")

def last_months(n):
    y, m = date.today().year, date.today().month
    out = []
    for _ in range(n):
        out.append(f"{y:04d}-{m:02d}")
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    return list(reversed(out))

def sample_records(n_months):
    recs = []
    for month in last_months(n_months):
        for kid, (ktype, lo, hi) in KPIS.items():
            wh = "RMW" if kid.startswith("rmw") else "FGW"
            target = random.uniform(lo, hi)
            if ktype == "pct":
                den = random.randint(200, 5000)
                num = round(den * target / 100)
            else:  # hours / minutes / ratio / days -> num/den = target
                den = random.randint(50, 800)
                num = round(den * target, 1)
            recs.append({
                "id": uid(), "wh": wh, "kpi": kid, "month": month,
                "num": num, "den": den, "note": "sample",
                "ts": f"{month}-15T09:00:00Z",
            })
    return recs

def from_csv(path):
    recs = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            kid = row["kpi_id"].strip().lower()
            if kid not in KPIS:
                print(f"  ! skipping unknown kpi_id: {kid}", file=sys.stderr)
                continue
            recs.append({
                "id": uid(),
                "wh": row["warehouse"].strip().upper(),
                "kpi": kid,
                "month": row["month"].strip(),
                "num": float(row["numerator"]),
                "den": float(row["denominator"]),
                "note": row.get("note", "").strip(),
                "ts": f'{row["month"].strip()}-01T00:00:00Z',
            })
    return recs

def push(url, records):
    body = json.dumps({"action": "replaceAll", "records": records}).encode()
    req = urllib.request.Request(url, data=body,
                                 headers={"Content-Type": "text/plain;charset=utf-8"})
    with urllib.request.urlopen(req) as r:
        print("Server response:", r.read().decode()[:200])

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--months", type=int, default=3)
    ap.add_argument("--from-csv", dest="csv_path")
    ap.add_argument("--push", dest="push_url")
    ap.add_argument("--out", default="gudam-kpi-records.json")
    a = ap.parse_args()

    records = from_csv(a.csv_path) if a.csv_path else sample_records(a.months)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)
    print(f"Wrote {len(records)} records -> {a.out}")

    if a.push_url:
        push(a.push_url, records)
        print("Pushed to Google Sheet.")
