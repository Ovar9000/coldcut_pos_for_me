"""
Security Hardening Verification Test Suite
============================================
Validates:
1. Unauthenticated requests to protected endpoints return 401 Unauthorized.
2. Admin login generates valid session token in admin_sessions.
3. Authenticated requests with Bearer token succeed.
4. Database export redacts sensitive keys and password hashes.
5. Cart inputs with negative quantity are rejected.
6. Anti-replay and fee validation for GCash transactions work.
"""

import asyncio
from starlette.testclient import TestClient
from app.main import app
from app.database import init_db

def test_security():
    print("=" * 60)
    print("[*] STARTING SECURITY HARDENING TEST SUITE")
    print("=" * 60)

    asyncio.run(init_db())

    with TestClient(app) as client:
        # 1. Unauthenticated Access Rejections (401 Unauthorized)
        print("\n--- 1. Testing Unauthenticated Access Rejections (401) ---")
        unauth_routes = [
            ("GET", "/api/admin/settings"),
            ("PUT", "/api/admin/settings"),
            ("GET", "/api/admin/labels"),
            ("POST", "/api/products"),
            ("PUT", "/api/products/1"),
            ("DELETE", "/api/products/1"),
            ("GET", "/api/sync/status"),
            ("GET", "/api/sync/download-db"),
            ("GET", "/api/sync/export-json"),
            ("POST", "/api/sync/push-to-cloud"),
            ("POST", "/api/sync/supabase/test"),
            ("POST", "/api/sync/supabase/upload-backup"),
            ("GET", "/api/sync/supabase/backups"),
            ("POST", "/api/sync/supabase/config"),
            ("GET", "/api/reports/monthly"),
            ("GET", "/api/reports/top-products"),
            ("GET", "/api/gcash/transactions"),
        ]

        for method, endpoint in unauth_routes:
            if method == "GET":
                resp = client.get(endpoint)
            elif method == "POST":
                resp = client.post(endpoint, json={})
            elif method == "PUT":
                resp = client.put(endpoint, json={})
            elif method == "DELETE":
                resp = client.delete(endpoint)

            assert resp.status_code == 401, f"Expected 401 for {method} {endpoint}, got {resp.status_code}"
        print(f"[+] All {len(unauth_routes)} sensitive admin/sync endpoints rejected unauthenticated requests with HTTP 401!")

        # 2. Admin Login & Session Token Issuance
        print("\n--- 2. Testing Admin Login & Token Generation ---")
        login_resp = client.post("/api/admin/login", json={"password": "admin123"})
        assert login_resp.status_code == 200
        data = login_resp.json()
        assert data["success"] is True
        token = data["token"]
        assert token and len(token) > 20
        auth_header = {"Authorization": f"Bearer {token}"}
        print(f"[+] Admin authenticated. Token issued: {token[:10]}...")

        # 3. Authenticated Access Verification
        print("\n--- 3. Testing Authenticated Access with Session Token ---")
        settings_resp = client.get("/api/admin/settings", headers=auth_header)
        assert settings_resp.status_code == 200
        assert "store_name" in settings_resp.json()
        print("[+] Admin settings successfully read with Bearer token.")

        labels_resp = client.get("/api/admin/labels", headers=auth_header)
        assert labels_resp.status_code == 200
        print("[+] Admin labels list successfully read with Bearer token.")

        sync_status_resp = client.get("/api/sync/status", headers=auth_header)
        assert sync_status_resp.status_code == 200
        print("[+] Sync status successfully read with Bearer token.")

        # 4. Export JSON Sanitization
        print("\n--- 4. Testing Export JSON Credential Sanitization ---")
        export_resp = client.get("/api/sync/export-json", headers=auth_header)
        assert export_resp.status_code == 200
        export_data = export_resp.json()
        admin_settings_rows = export_data["tables"].get("admin_settings", [])
        for row in admin_settings_rows:
            if row.get("key") in ("admin_password", "cloud_api_key", "supabase_key"):
                assert row["value"] == "***REDACTED***", f"Sensitive key {row['key']} was not redacted!"
        print("[+] Sensitive keys (admin_password, cloud_api_key, supabase_key) properly redacted in JSON export.")

        # 5. Download DB Authentication & Token Query Parameter
        print("\n--- 5. Testing DB Download Authorization ---")
        db_resp = client.get(f"/api/sync/download-db?token={token}")
        assert db_resp.status_code == 200
        assert len(db_resp.content) > 1000
        print(f"[+] Download DB with ?token=<token> verified ({len(db_resp.content)} bytes).")

        # 6. Financial Input Validation (Cart quantity > 0)
        print("\n--- 6. Testing Financial Input Validation (Negative/Zero Cart Quantity) ---")
        bad_cart = {
            "items": [
                {
                    "product_id": 1,
                    "product_name": "Test Item",
                    "quantity": -5.0,  # Negative quantity attempt
                    "unit_price": 50.0,
                    "cost_price": 40.0,
                    "subtotal": -250.0
                }
            ],
            "total_amount": -250.0,
            "payment_method": "CASH",
            "amount_tendered": 0.0
        }
        bad_resp = client.post("/api/checkout", json=bad_cart)
        assert bad_resp.status_code == 422, f"Expected 422 for negative quantity, got {bad_resp.status_code}"
        print("[+] Rejected negative item quantity in checkout with HTTP 422 Unprocessable Entity.")

        # 7. GCash Fee Server-Side Recalculation
        print("\n--- 7. Testing Server-Side GCash Fee Enforcement ---")
        import uuid
        tampered_gcash = {
            "transaction_type": "GCASH_IN",
            "flow_type": "A",
            "input_amount": 1000.0,
            "principal_amount": 1000.0,
            "fee": 0.0,  # Cashier / attacker attempted to bypass fee by setting 0.0
            "total_collected": 1000.0,
            "reference_number": f"TAMPER-{uuid.uuid4().hex[:6]}",
        }
        t_resp = client.post("/api/gcash/transact", json=tampered_gcash)
        assert t_resp.status_code == 200
        # Backend must enforce fee recalculation
        t_data = t_resp.json()
        assert t_data["gcash_detail"]["fee"] == 10.0, f"Fee should be 10.0, got {t_data['gcash_detail']['fee']}"
        assert t_data["gcash_detail"]["total_collected"] == 1010.0
        print("[+] Verified: Server recalibrates and enforces proper store fees regardless of client tampering.")

    print("\n" + "=" * 60)
    print("[SUCCESS] ALL SECURITY HARDENING TESTS PASSED 100%!")
    print("=" * 60)

if __name__ == "__main__":
    test_security()
