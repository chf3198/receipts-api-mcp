"""
routers.stats
-------------
Endpoint for SQL-style grouped receipt statistics:
  GET /receipts/stats  — aggregate metrics grouped by company and/or product_category

Aggregate columns per group:
  receipt_count, total_quantity,
  sum/avg/min/max of total_usd, sum of discount_usd, sum of tax_usd,
  sum of unit_price_usd
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from receipts_api.data_loader import RECEIPTS
from receipts_api.utils import apply_filters

router = APIRouter(prefix="/receipts", tags=["statistics"])

VALID_GROUP_FIELDS = {"company", "product_category"}


def _r2(value: float) -> float:
    return round(value, 2)


@router.get(
    "/stats",
    summary="Grouped receipt statistics",
    response_description="SQL-style aggregated statistics per group",
)
def get_stats(
    group_by: str = Query(
        "company",
        description=(
            "Comma-separated grouping fields. "
            "Allowed: company, product_category. "
            "Example: company,product_category"
        ),
    ),
    company: str | None = Query(None, description="Filter by company (case-insensitive)"),
    product_category: str | None = Query(None, description="Filter by product category"),
    date_from: date | None = Query(None, description="Earliest receipt date (ISO, inclusive)"),
    date_to: date | None = Query(None, description="Latest receipt date (ISO, inclusive)"),
    status: str | None = Query(None, description="Filter by status, e.g. Paid"),
) -> dict[str, Any]:
    """
    Return SQL-style grouped statistics over receipts.

    | Column | SQL equivalent |
    |---|---|
    | receipt_count | COUNT(*) |
    | total_quantity | SUM(quantity) |
    | sum_unit_price_usd | SUM(unit_price_usd) |
    | sum_discount_usd | SUM(discount_usd) |
    | sum_tax_usd | SUM(tax_usd) |
    | sum_total_usd | SUM(total_usd) |
    | avg_total_usd | AVG(total_usd) |
    | min_total_usd | MIN(total_usd) |
    | max_total_usd | MAX(total_usd) |
    """
    group_keys = [g.strip() for g in group_by.split(",") if g.strip()]
    invalid = [g for g in group_keys if g not in VALID_GROUP_FIELDS]
    if invalid:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid group_by value(s): {invalid}. Allowed: {sorted(VALID_GROUP_FIELDS)}",
        )

    results = apply_filters(
        RECEIPTS,
        company=company,
        product_category=product_category,
        date_from=date_from,
        date_to=date_to,
        status=status,
    )

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
