"""
routers.receipts
----------------
Endpoints for browsing receipt records:
  GET /receipts                  — list with optional filters
  GET /receipts/companies        — distinct company names
  GET /receipts/categories       — distinct product categories
  GET /receipts/{receipt_id}     — single receipt by ID

Note: the static-path routes (/companies, /categories) MUST be registered
before the dynamic {receipt_id} route so FastAPI matches them first.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from receipts_api.data_loader import RECEIPTS
from receipts_api.utils import apply_filters, serialise

router = APIRouter(prefix="/receipts", tags=["receipts"])


@router.get(
    "/companies",
    summary="List distinct companies",
    response_description="Sorted list of company names in the dataset",
)
def list_companies() -> list[str]:
    """Return every unique company name across all loaded receipts."""
    return sorted({r["company"] for r in RECEIPTS})


@router.get(
    "/categories",
    summary="List distinct product categories",
    response_description="Sorted list of product categories in the dataset",
)
def list_categories() -> list[str]:
    """Return every unique product category across all loaded receipts."""
    return sorted({r["product_category"] for r in RECEIPTS})


@router.get(
    "",
    summary="List receipts",
    response_description="Array of receipt objects matching applied filters",
)
def list_receipts(
    company: str | None = Query(None, description="Filter by company (case-insensitive)"),
    product_category: str | None = Query(None, description="Filter by product category"),
    date_from: date | None = Query(None, description="Earliest receipt date (ISO, inclusive)"),
    date_to: date | None = Query(None, description="Latest receipt date (ISO, inclusive)"),
    status: str | None = Query(None, description="Filter by status, e.g. Paid"),
) -> list[dict[str, Any]]:
    """Return all receipts, optionally narrowed by filters."""
    results = apply_filters(
        RECEIPTS,
        company=company,
        product_category=product_category,
        date_from=date_from,
        date_to=date_to,
        status=status,
    )
    return [serialise(r) for r in results]


@router.get(
    "/{receipt_id}",
    summary="Get receipt by ID",
    response_description="Single receipt object",
)
def get_receipt(receipt_id: str) -> dict[str, Any]:
    """Fetch a single receipt by its receipt_id (e.g. 2025-01-001)."""
    for r in RECEIPTS:
        if r["receipt_id"] == receipt_id:
            return serialise(r)
    raise HTTPException(status_code=404, detail=f"Receipt '{receipt_id}' not found")
