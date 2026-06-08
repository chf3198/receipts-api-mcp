"""
utils
-----
Shared helpers used by multiple routers.
"""

from __future__ import annotations

from datetime import date
from typing import Any


def serialise(record: dict[str, Any]) -> dict[str, Any]:
    """Convert a receipt dict to a JSON-safe dict (date → ISO string)."""
    return {**record, "receipt_date": record["receipt_date"].isoformat()}


def apply_filters(
    records: list[dict[str, Any]],
    *,
    company: str | None,
    product_category: str | None,
    date_from: date | None,
    date_to: date | None,
    status: str | None,
) -> list[dict[str, Any]]:
    """Return a filtered subset of *records*."""
    if company:
        records = [r for r in records if r["company"].lower() == company.lower()]
    if product_category:
        records = [
            r for r in records if r["product_category"].lower() == product_category.lower()
        ]
    if date_from:
        records = [r for r in records if r["receipt_date"] >= date_from]
    if date_to:
        records = [r for r in records if r["receipt_date"] <= date_to]
    if status:
        records = [r for r in records if r["status"].lower() == status.lower()]
    return records
