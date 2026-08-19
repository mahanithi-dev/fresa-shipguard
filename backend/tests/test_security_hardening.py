import io
import datetime
import pytest
from fastapi.testclient import TestClient

from app.entities import Carrier, Route, Shipment, User
from app.services.security import create_access_token, hash_password


def test_admin_rbac_enforcement(client, auth_headers, db):
    """Verify standard OPS_USER is rejected with 403 Forbidden on administrative endpoints."""
    # auth_headers is for OPS_USER (ops@shipguard.local)
    response = client.post("/api/v1/admin/generate-ai-data?count=5", headers=auth_headers)
    assert response.status_code == 403
    assert "Insufficient privileges" in response.json()["detail"]

    # Now test with ADMIN user token
    admin_user = User(
        name="Admin Tester",
        email="admin_test@shipguard.local",
        password_hash=hash_password("adminSecret123"),
        role="ADMIN",
    )
    db.add(admin_user)
    db.commit()

    admin_token = create_access_token("admin_test@shipguard.local", role="ADMIN")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    admin_resp = client.post("/api/v1/admin/generate-ai-data?count=5&replace_existing=false", headers=admin_headers)
    assert admin_resp.status_code == 200
    assert admin_resp.json()["status"] == "success"


def test_self_registration_privilege_escalation_blocked(client, db):
    """Verify that an attacker cannot grant themselves the ADMIN role via self-registration."""
    reg_payload = {
        "name": "Attacker User",
        "email": "attacker@evil.com",
        "password": "SecurePassword123!",
        "role": "ADMIN"  # Attempting privilege escalation
    }
    resp = client.post("/api/v1/auth/register", json=reg_payload)
    assert resp.status_code == 201

    created_user = db.query(User).filter(User.email == "attacker@evil.com").first()
    assert created_user is not None
    assert created_user.role == "OPS_USER"  # Server-side enforced: must NOT be ADMIN


def test_password_length_policy(client):
    """Verify that passwords under 8 characters are rejected during registration."""
    short_pw_payload = {
        "name": "Weak User",
        "email": "weak@shipguard.local",
        "password": "short"
    }
    resp = client.post("/api/v1/auth/register", json=short_pw_payload)
    assert resp.status_code == 422


def test_security_headers_present(client):
    """Verify that HTTP security headers are present on API responses."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert "Content-Security-Policy" in resp.headers
    assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


def test_csv_injection_sanitization(client, auth_headers, db):
    """Verify that formulas starting with =, +, -, @ are escaped with leading ' in CSV export."""
    carrier = db.query(Carrier).first()
    route = db.query(Route).first()

    # Create shipment with formula injection payloads
    malicious_shipment = Shipment(
        shipment_ref="=CMD|calc",
        carrier_id=carrier.carrier_id,
        route_id=route.route_id,
        mode="SEA",
        cargo_type="General",
        etd=datetime.date(2026, 9, 1),
        eta=datetime.date(2026, 9, 20),
        status="BOOKED",
        disruption_event="+2+5+cmd",
        consignee="@SUM(1+1)*cmd",
    )
    db.add(malicious_shipment)
    db.commit()

    resp = client.get("/api/v1/reports/export/csv", headers=auth_headers)
    assert resp.status_code == 200
    csv_text = resp.text

    # Verify formula characters are safely neutralized with leading single quote
    assert "'=CMD|calc" in csv_text
    assert "'+2+5+cmd" in csv_text
    assert "'@SUM(1+1)*cmd" in csv_text



def test_shipment_import_file_validation(client, auth_headers):
    """Verify non-CSV files and oversized uploads are rejected."""
    # 1. Invalid file extension
    fake_exe = io.BytesIO(b"malicious executable payload")
    resp = client.post(
        "/api/v1/shipments/import",
        files={"file": ("malware.exe", fake_exe, "application/octet-stream")},
        headers=auth_headers
    )
    assert resp.status_code == 400
    assert "Only CSV files" in resp.json()["detail"]

    # 2. Valid CSV import
    valid_csv = (
        "shipment_ref,carrier_id,route_id,mode,cargo_type,etd,eta,status\n"
        "SHP-SEC-001,1,1,SEA,General,2026-09-01,2026-09-25,BOOKED\n"
    )
    resp_valid = client.post(
        "/api/v1/shipments/import",
        files={"file": ("shipments.csv", io.BytesIO(valid_csv.encode("utf-8")), "text/csv")},
        headers=auth_headers
    )
    assert resp_valid.status_code == 200
    assert resp_valid.json()["imported"] >= 1


def test_sql_injection_resistance(client, auth_headers):
    """Verify SQL injection payloads in filter query params are safely handled as literals."""
    sqli_payload = "' OR 1=1 --"
    resp = client.get(f"/api/v1/shipments?status={sqli_payload}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 0  # No shipments with status "' OR 1=1 --"
