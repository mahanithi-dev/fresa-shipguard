import datetime


def test_create_and_list_shipments(client, auth_headers):
    # Fetch carriers and routes to get IDs
    carriers_res = client.get("/api/v1/carriers", headers=auth_headers)
    routes_res = client.get("/api/v1/routes", headers=auth_headers)
    assert carriers_res.status_code == 200
    assert routes_res.status_code == 200

    carrier_id = carriers_res.json()[0]["carrier_id"]
    route = routes_res.json()[0]

    # Create shipment
    create_payload = {
        "shipment_ref": "SHP-UNIT-1001",
        "carrier_id": carrier_id,
        "route_id": route["route_id"],
        "mode": route["mode"],
        "cargo_type": "Reefer",
        "etd": "2026-09-01",
        "eta": "2026-09-26",
    }

    create_res = client.post("/api/v1/shipments", json=create_payload, headers=auth_headers)
    assert create_res.status_code == 200
    created = create_res.json()
    assert created["shipment_ref"] == "SHP-UNIT-1001"
    assert created["risk_tier"] in ("HIGH", "MEDIUM", "LOW")

    # List shipments and verify pagination/filtering
    list_res = client.get("/api/v1/shipments?mode=" + route["mode"], headers=auth_headers)
    assert list_res.status_code == 200
    data = list_res.json()
    assert data["total"] >= 1
    assert any(s["shipment_ref"] == "SHP-UNIT-1001" for s in data["items"])


def test_shipment_detail_retrieval(client, auth_headers):
    carriers_res = client.get("/api/v1/carriers", headers=auth_headers)
    routes_res = client.get("/api/v1/routes", headers=auth_headers)
    carrier_id = carriers_res.json()[0]["carrier_id"]
    route = routes_res.json()[0]

    create_payload = {
        "shipment_ref": "SHP-DETAIL-1002",
        "carrier_id": carrier_id,
        "route_id": route["route_id"],
        "mode": route["mode"],
        "cargo_type": "General",
        "etd": "2026-09-01",
        "eta": "2026-09-20",
    }
    create_res = client.post("/api/v1/shipments", json=create_payload, headers=auth_headers)
    shipment_id = create_res.json()["shipment_id"]

    detail_res = client.get(f"/api/v1/shipments/{shipment_id}", headers=auth_headers)
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["shipment_id"] == shipment_id
    assert "risk" in detail
    assert "history" in detail


def test_risk_summary_aggregation(client, auth_headers):
    res = client.get("/api/v1/risk/summary", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "high" in data
    assert "medium" in data
    assert "low" in data
    assert "total" in data
    assert data["total"] >= 0


def test_report_summary_aggregation(client, auth_headers):
    res = client.get("/api/v1/reports/summary", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "metrics" in data
    assert "total_shipments" in data["metrics"]
    assert "carrier_scorecards" in data
    assert "route_analytics" in data
    assert "high_risk_exceptions" in data


def test_csv_export_bounded_limit(client, auth_headers):
    res = client.get("/api/v1/reports/export/csv?limit=5", headers=auth_headers)
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/csv")
    lines = res.text.strip().split("\n")
    # Header + at most 5 data rows
    assert len(lines) <= 6


def test_pagination_max_bounds(client, auth_headers):
    # Valid page_size <= 200
    res_valid = client.get("/api/v1/shipments?page=1&page_size=200", headers=auth_headers)
    assert res_valid.status_code == 200

    # Invalid page_size > 200 should be rejected
    res_invalid = client.get("/api/v1/shipments?page=1&page_size=201", headers=auth_headers)
    assert res_invalid.status_code == 422
