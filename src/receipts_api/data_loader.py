"""
data_loader
-----------
Loads all *.csv receipt files from the project data/ directory into a
shared in-memory list.  Called once at import time; every request in the
process shares the same list without re-reading disk.
"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
from typing import Any

# Resolve data/ relative to the project root (two levels above this file:
#   src/receipts_api/data_loader.py → project root)
DATA_DIR: Path = Path(__file__).parent.parent.parent / "data"


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
        raise RuntimeError(f"No CSV receipt files found in {data_dir}")
    for path in csv_files:
        with path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                records.append(_parse_row(row))
    return records


# Shared dataset — loaded once at module import time.
RECEIPTS: list[dict[str, Any]] = load_receipts()
