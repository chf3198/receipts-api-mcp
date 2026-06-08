"""
Smoke tests for the Receipts Statistics API.

Run with:  uv run pytest
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from receipts_api.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# /receipts/companies
# ---------------------------------------------------------------------------


def test_list_companies_returns_list():
    resp = client.get("/receipts/companies")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_list_companies_sorted():
    data = client.get("/receipts/companies").json()
    assert data == sorted(data)


def test_known_company_present():
    data = client.get("/receipts/companies").json()
    assert "Northstar Software Co." in data


# ---------------------------------------------------------------------------
# /receipts/categories
# ---------------------------------------------------------------------------


def test_list_categories_returns_list():
    resp = client.get("/receipts/categories")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


# ---------------------------------------------------------------------------
# /receipts  (list)
# ---------------------------------------------------------------------------


def test_list_receipts_all():
    resp = client.get("/receipts")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 40  # 20 records × 2 months


def test_list_receipts_filter_by_company():
    resp = client.get("/receipts", params={"company": "Northstar Software Co."})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 8
    assert all(r["company"] == "Northstar Software Co." for r in data)


def test_list_receipts_filter_by_date_range():
    resp = client.get("/receipts", params={"date_from": "2025-01-01", "date_to": "2025-01-31"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 20
    assert all(r["receipt_date"].startswith("2025-01") for r in data)


def test_list_receipts_filter_by_category():
    resp = client.get("/receipts", params={"product_category": "Cloud Platform"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 4
    assert all(r["product_category"] == "Cloud Platform" for r in data)


# ---------------------------------------------------------------------------
# /receipts/stats
# ---------------------------------------------------------------------------


def test_stats_group_by_company():
    resp = client.get("/receipts/stats", params={"group_by": "company"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["group_by"] == ["company"]
    assert body["total_records_matched"] == 40
    assert len(body["groups"]) == 5


def test_stats_group_by_category():
    resp = client.get("/receipts/stats", params={"group_by": "product_category"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["group_by"] == ["product_category"]
    assert len(body["groups"]) > 0


def test_stats_group_by_company_and_category():
    resp = client.get("/receipts/stats", params={"group_by": "company,product_category"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["group_by"] == ["company", "product_category"]


def test_stats_aggregate_fields_present():
    groups = client.get("/receipts/stats").json()["groups"]
    required = {
        "receipt_count", "total_quantity", "sum_unit_price_usd",
        "sum_discount_usd", "sum_tax_usd", "sum_total_usd",
        "avg_total_usd", "min_total_usd", "max_total_usd",
    }
    for g in groups:
        assert required.issubset(g.keys())


def test_stats_invalid_group_by_returns_422():
    resp = client.get("/receipts/stats", params={"group_by": "invalid_field"})
    assert resp.status_code == 422


def test_stats_date_filter():
    resp = client.get(
        "/receipts/stats",
        params={"group_by": "company", "date_from": "2025-01-01", "date_to": "2025-01-31"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_records_matched"] == 20


# ---------------------------------------------------------------------------
# /receipts/{receipt_id}
# ---------------------------------------------------------------------------


def test_get_receipt_by_id():
    resp = client.get("/receipts/2025-01-001")
    assert resp.status_code == 200
    data = resp.json()
    assert data["receipt_id"] == "2025-01-001"
    assert data["company"] == "Northstar Software Co."


def test_get_receipt_not_found():
    resp = client.get("/receipts/9999-99-999")
    assert resp.status_code == 404
