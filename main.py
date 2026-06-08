"""
Receipts Statistics API
-----------------------
Loads monthly receipt CSVs from assets/data/ and exposes a FastAPI server
with endpoints for browsing receipts and retrieving SQL-style grouped statistics.

Endpoints
---------
GET /receipts                  — List receipts with optional filters
GET /receipts/stats            — Grouped statistics (group_by, filters)
GET /receipts/companies        — Distinct company list
GET /receipts/categories       — Distinct product-category list
GET /receipts/{receipt_id}     — Single receipt by ID

Filters (shared across /receipts and /receipts/stats)
------------------------------------------------------
  company          exact match (case-insensitive)
  product_category exact match (case-insensitive)
  date_from        ISO date  e.g. 2025-01-01
  date_to          ISO date  e.g. 2025-01-31
  status           exact match (case-insensitive)  e.g. Paid

Grouping (/receipts/stats only)
---------------------------------
  group_by  comma-separated field names from: company, product_category
            default: company
            examples:
              ?group_by=company
              ?group_by=product_category
              ?group_by=company,product_category
"""

from __future__ import annotations

import csv
import os
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).parent / "assets" / "data"

VALID_GROUP_FIELDS = {"company", "product_category"}

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def _parse_row(row: dict[str, str]) -> dict[str, Any]:
    """Cast CSV string fields to their proper Python types."""
    return {
        "receipt_id": row["receipt_id"],
        "receipt_date": date.fromisoformat(row["receipt_date"]),
        "company": row["company"],
        "product_category": row["product_category"],
        "service_name": row["service_name"],
        "description": row["description"],
        "quantity": int(row["quantity"]),
        "unit_price_usd": float(row["unit_price_usd"]),
        "discount_usd": float(row["discount_usd"]),
        "tax_usd": float(row["tax_usd"]),
        "total_usd": float(row["total_usd"]),
        "status": row["status"],
    }


def load_receipts(data_dir: Path = DATA_DIR) -> list[dict[str, Any]]:
    """Read all *.csv files from *data_dir* in alphabetical order."""
    records: list[dict[str, Any]] = []
    csv_files = sorted(data_dir.glob("*.csv"))
    if not csv_files:
        raise RuntimeError(f"No CSV files found in {data_dir}")
    for path in csv_files:
        with path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                records.append(_parse_row(row))
    return records


# Load once at import time so every request shares the same in-memory dataset.
RECEIPTS: list[dict[str, Any]] = load_receipts()

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Receipts Statistics API",
    description=(
        "Browse receipt records and retrieve SQL-style grouped statistics "
        "loaded from monthly CSV exports."
    ),
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _r2(value: float) -> float:
    """Round to 2 decimal places."""
    return round(value, 2)


def _serialise(record: dict[str, Any]) -> dict[str, Any]:
    """Convert a receipt dict to a JSON-safe dict (date → ISO string)."""
    return {**record, "receipt_date": record["receipt_date"].isoformat()}


def _apply_filters(
    records: list[dict[str, Any]],
    *,
    company: Optional[str],
    product_category: Optional[str],
    date_from: Optional[date],
    date_to: Optional[date],
    status: Optional[str],
) -> list[dict[str, Any]]:
    """Return a filtered subset of *records*."""
    if company:
        records = [r for r in records if r["company"].lower() == company.lower()]
    if product_category:
        records = [
            r
            for r in records
            if r["product_category"].lower() == product_category.lower()
        ]
    if date_from:
        records = [r for r in records if r["receipt_date"] >= date_from]
    if date_to:
        records = [r for r in records if r["receipt_date"] <= date_to]
    if status:
        records = [r for r in records if r["status"].lower() == status.lower()]
    return records


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get(
    "/receipts",
    summary="List receipts",
    response_description="Array of receipt objects matching the applied filters",
)
def list_receipts(
    company: Optional[str] = Query(None, description="Filter by company name (case-insensitive)"),
    product_category: Optional[str] = Query(None, description="Filter by product category (case-insensitive)"),
    date_from: Optional[date] = Query(None, description="Earliest receipt date (inclusive), ISO format"),
    date_to: Optional[date] = Query(None, description="Latest receipt date (inclusive), ISO format"),
    status: Optional[str] = Query(None, description="Filter by status, e.g. Paid"),
) -> list[dict[str, Any]]:
    """
    Return all receipts, optionally narrowed by company, product_category,
    date range, and/or status.
    """
    results = _apply_filters(
        RECEIPTS,
        company=company,
        product_category=product_category,
        date_from=date_from,
        date_to=date_to,
        status=status,
    )
    return [_serialise(r) for r in results]


@app.get(
    "/receipts/stats",
    summary="Grouped receipt statistics",
    response_description="SQL-style aggregated statistics per group",
)
def get_stats(
    group_by: str = Query(
        "company",
        description=(
            "Comma-separated grouping fields. "
            "Allowed values: company, product_category. "
            "Example: company,product_category"
        ),
    ),
    company: Optional[str] = Query(None, description="Filter by company name (case-insensitive)"),
    product_category: Optional[str] = Query(None, description="Filter by product category (case-insensitive)"),
    date_from: Optional[date] = Query(None, description="Earliest receipt date (inclusive)"),
    date_to: Optional[date] = Query(None, description="Latest receipt date (inclusive)"),
    status: Optional[str] = Query(None, description="Filter by status, e.g. Paid"),
) -> dict[str, Any]:
    """
    Return SQL-style grouped statistics over receipts.

    **Aggregate columns returned per group**

    | Column | Description |
    |---|---|
    | `receipt_count` | COUNT(*) |
    | `total_quantity` | SUM(quantity) |
    | `sum_unit_price_usd` | SUM(unit_price_usd) |
    | `sum_discount_usd` | SUM(discount_usd) |
    | `sum_tax_usd` | SUM(tax_usd) |
    | `sum_total_usd` | SUM(total_usd) |
    | `avg_total_usd` | AVG(total_usd) |
    | `min_total_usd` | MIN(total_usd) |
    | `max_total_usd` | MAX(total_usd) |
    """
    # Validate group_by
    group_keys = [g.strip() for g in group_by.split(",") if g.strip()]
    invalid = [g for g in group_keys if g not in VALID_GROUP_FIELDS]
    if invalid:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Invalid group_by value(s): {invalid}. "
                f"Allowed: {sorted(VALID_GROUP_FIELDS)}"
            ),
        )

    # Apply filters
    results = _apply_filters(
        RECEIPTS,
        company=company,
        product_category=product_category,
        date_from=date_from,
        date_to=date_to,
        status=status,
    )

    # Accumulate aggregates keyed by the group tuple
    buckets: dict[tuple, dict[str, Any]] = defaultdict(
        lambda: {
            "receipt_count": 0,
            "total_quantity": 0,
            "sum_unit_price_usd": 0.0,
            "sum_discount_usd": 0.0,
            "sum_tax_usd": 0.0,
            "sum_total_usd": 0.0,
            "min_total_usd": None,
            "max_total_usd": None,
            "_totals": [],
        }
    )

    for row in results:
        key = tuple(row[k] for k in group_keys)
        b = buckets[key]
        b["receipt_count"] += 1
        b["total_quantity"] += row["quantity"]
        b["sum_unit_price_usd"] += row["unit_price_usd"]
        b["sum_discount_usd"] += row["discount_usd"]
        b["sum_tax_usd"] += row["tax_usd"]
        b["sum_total_usd"] += row["total_usd"]
        b["_totals"].append(row["total_usd"])
        if b["min_total_usd"] is None or row["total_usd"] < b["min_total_usd"]:
            b["min_total_usd"] = row["total_usd"]
        if b["max_total_usd"] is None or row["total_usd"] > b["max_total_usd"]:
            b["max_total_usd"] = row["total_usd"]

    # Build sorted output
    groups: list[dict[str, Any]] = []
    for key in sorted(buckets):
        b = buckets[key]
        totals = b.pop("_totals")
        entry: dict[str, Any] = {k: key[i] for i, k in enumerate(group_keys)}
        entry["receipt_count"] = b["receipt_count"]
        entry["total_quantity"] = b["total_quantity"]
        entry["sum_unit_price_usd"] = _r2(b["sum_unit_price_usd"])
        entry["sum_discount_usd"] = _r2(b["sum_discount_usd"])
        entry["sum_tax_usd"] = _r2(b["sum_tax_usd"])
        entry["sum_total_usd"] = _r2(b["sum_total_usd"])
        entry["avg_total_usd"] = _r2(sum(totals) / len(totals)) if totals else 0.0
        entry["min_total_usd"] = _r2(b["min_total_usd"]) if b["min_total_usd"] is not None else None
        entry["max_total_usd"] = _r2(b["max_total_usd"]) if b["max_total_usd"] is not None else None
        groups.append(entry)

    return {
        "group_by": group_keys,
        "filters_applied": {
            "company": company,
            "product_category": product_category,
            "date_from": date_from.isoformat() if date_from else None,
            "date_to": date_to.isoformat() if date_to else None,
            "status": status,
        },
        "total_records_matched": len(results),
        "groups": groups,
    }


@app.get(
    "/receipts/companies",
    summary="List distinct companies",
    response_description="Sorted list of company names present in the dataset",
)
def list_companies() -> list[str]:
    """Return every unique company name found across all loaded receipts."""
    return sorted({r["company"] for r in RECEIPTS})


@app.get(
    "/receipts/categories",
    summary="List distinct product categories",
    response_description="Sorted list of product categories present in the dataset",
)
def list_categories() -> list[str]:
    """Return every unique product category found across all loaded receipts."""
    return sorted({r["product_category"] for r in RECEIPTS})


@app.get(
    "/receipts/{receipt_id}",
    summary="Get receipt by ID",
    response_description="Single receipt object",
)
def get_receipt(receipt_id: str) -> dict[str, Any]:
    """Fetch a single receipt by its `receipt_id` field (e.g. `2025-01-001`)."""
    for r in RECEIPTS:
        if r["receipt_id"] == receipt_id:
            return _serialise(r)
    raise HTTPException(status_code=404, detail=f"Receipt '{receipt_id}' not found")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
