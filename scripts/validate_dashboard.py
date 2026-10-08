"""Validate dashboard structure before GitHub Actions commits refreshed data."""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "dashboard.json"

CORE_FIELDS = ["revenue", "operating_income", "net_income", "total_assets", "total_liabilities", "total_equity"]
TABLE_KEYS = ("annual", "half_year", "quarterly")

def fail(message: str) -> None:
    raise SystemExit(f"VALIDATION FAILED: {message}")

with DATA.open(encoding="utf-8") as f:
    d = json.load(f)

if d.get("collection_start_year") != 2010:
    fail("collection_start_year must be 2010")

tables = d.get("tables") or {}
missing = [key for key in TABLE_KEYS if key not in tables]
if missing:
    fail(f"missing tables: {missing}")

for key in TABLE_KEYS:
    rows = tables.get(key) or []
    if not rows:
        fail(f"{key} table is empty")

    labels = [row.get("period_label") for row in rows]
    if any(not label for label in labels):
        fail(f"{key} has a blank period_label")
    if len(labels) != len(set(labels)):
        fail(f"{key} has duplicate period_label")

    for row in rows:
        for field in CORE_FIELDS:
            value = row.get(field)
            if value is not None and (not isinstance(value, (int, float)) or not math.isfinite(value)):
                fail(f"{key} contains invalid numeric value in {field}")

peers = d.get("peer_firms") or []
if len(peers) < 5:
    fail("peer_firms must contain at least five domestic peers")

print(
    "VALIDATION OK:",
    f"annual={len(tables['annual'])}",
    f"half_year={len(tables['half_year'])}",
    f"quarterly={len(tables['quarterly'])}",
    f"peers={len(peers)}",
)
