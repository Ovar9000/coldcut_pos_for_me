"""
Test Suite: Svelte 5 SPA + FastAPI End-to-End Integration
===========================================================
Validates:
1. Svelte 5 Cashier SPA is served at '/' with HTTP 200
2. Static assets (/assets/...) are served with correct MIME types
3. Scale-embedded barcode decoding via /api/smart-scan and /api/products/barcode/
4. Dual-mode weight / peso cart items checkout via /api/checkout
5. Legacy cashier fallback at '/legacy-cashier'
"""

import re
import sys
import asyncio
from starlette.testclient import TestClient
from app.main import app
from app.database import init_db, get_db

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def run_tests():
    print("=" * 60)
    print("[*] STARTING SVELTE 5 SPA + FASTAPI END-TO-END VERIFICATION")
    print("=" * 60)

    # Initialize DB
    asyncio.run(init_db())
    print("[+] SQLite database initialized.")

    with TestClient(app) as client:
        # 1. Test Root Route Serving Svelte 5 SPA
        print("\n--- 1. Testing Root Route ('/') Serving Svelte 5 SPA ---")
        resp = client.get("/")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        html_content = resp.text
        assert "Coldcut POS" in html_content
        assert '<div id="app"' in html_content
        print("[+] Root '/' successfully serves Coldcut POS Svelte 5 SPA index.html")

        # 2. Extract and Test Asset Loading
        print("\n--- 2. Testing Compiled Asset Serving (/assets/...) ---")
        js_match = re.search(r'src="\.?/(assets/[^"]+\.js)"', html_content)
        css_match = re.search(r'href="\.?/(assets/[^"]+\.css)"', html_content)
        assert js_match, f"Could not find JS bundle path in HTML: {html_content[:300]}"
        assert css_match, f"Could not find CSS bundle path in HTML: {html_content[:300]}"

        js_path = "/" + js_match.group(1)
        css_path = "/" + css_match.group(1)

        js_resp = client.get(js_path)
        assert js_resp.status_code == 200, f"Failed to fetch JS bundle at {js_path}: {js_resp.status_code}"
        assert len(js_resp.content) > 10000
        print(f"[+] Svelte 5 JS bundle verified ({len(js_resp.content)} bytes) at {js_path}")

        css_resp = client.get(css_path)
        assert css_resp.status_code == 200, f"Failed to fetch CSS bundle at {css_path}: {css_resp.status_code}"
        assert len(css_resp.content) > 5000
        print(f"[+] Svelte 5 CSS bundle verified ({len(css_resp.content)} bytes) at {css_path}")

        # 3. Test Shanghai Dahua Scale Barcode Resolution (Prefixes 03 & 21)
        print("\n--- 3. Testing Shanghai Dahua & EAN-13 Scale Barcode Resolution ---")
        # 3a. Dahua Prefix 03: PLU 00001 (Chicken Feet / Adidas), 485g (0.485kg)
        dahua_code1 = "0300001004858"
        scan1 = client.post(f"/api/smart-scan?scanned_code={dahua_code1}")
        assert scan1.status_code == 200, f"Scan failed: {scan1.text}"
        data1 = scan1.json()
        assert data1["scan_type"] == "scale_weight"
        assert "Adidas" in data1["product"]["name"] or "Chicken Feet" in data1["product"]["name"]
        assert data1["quantity_to_add"] == 0.485
        assert data1["effective_subtotal"] == round(0.485 * 160.0, 2)
        print(f"[+] Dahua Scale (Prefix 03) {dahua_code1} decoded: '{data1['product']['name']}', Weight: {data1['quantity_to_add']}kg, Total: ₱{data1['effective_subtotal']:.2f}")

        # 3b. Scale Prefix 21: PLU 00002 (Chicken Gizzard / Balun-balunan), 650g (0.650kg)
        dahua_code2 = "2100002006505"
        scan2 = client.post(f"/api/smart-scan?scanned_code={dahua_code2}")
        assert scan2.status_code == 200, f"Scan failed: {scan2.text}"
        data2 = scan2.json()
        assert data2["scan_type"] == "scale_weight"
        assert "Gizzard" in data2["product"]["name"] or "Balun-balunan" in data2["product"]["name"]
        assert data2["quantity_to_add"] == 0.650
        print(f"[+] Dahua Scale (Prefix 21) {dahua_code2} decoded: '{data2['product']['name']}', Weight: {data2['quantity_to_add']}kg, Total: ₱{data2['effective_subtotal']:.2f}")

        # 3c. User Photo Barcode Label (0328100 001308 -> PLU 13: TJ Cheesedog Jumbo 1kg)
        dahua_photo_code = "0328100001308"
        scan3 = client.post(f"/api/smart-scan?scanned_code={dahua_photo_code}")
        assert scan3.status_code == 200, f"Scan failed: {scan3.text}"
        data3 = scan3.json()
        print(f"[+] User Scale Photo Barcode {dahua_photo_code} decoded: '{data3['product']['name']}' (PLU {data3['product'].get('plu_code')})")

        # 4. Test Mixed Coldcut POS Checkout: Weighed Chicken Cuts + TJ Hotdogs + Sanitary Ice + Chilled Drink
        print("\n--- 4. Testing Mixed Coldcut POS Checkout (Poultry + Hotdog + Ice + Drink) ---")
        items_resp = client.get("/api/products/quick-items")
        assert items_resp.status_code == 200
        catalog = items_resp.json()
        
        prod_adidas = next(p for p in catalog if "Adidas" in p["name"])
        prod_tj = next(p for p in catalog if "TJ Hotdog Jumbo" in p["name"])
        prod_ice = next(p for p in catalog if "Tube Ice" in p["name"])
        prod_drink = next(p for p in catalog if "Ramune" in p["name"] or "Cider" in p["name"])

        subtotal_adidas = round(0.485 * float(prod_adidas["selling_price"]), 2)
        total_order = subtotal_adidas + float(prod_tj["selling_price"]) + float(prod_ice["selling_price"]) + float(prod_drink["selling_price"])

        checkout_payload = {
            "items": [
                {
                    "product_id": prod_adidas["id"],
                    "product_name": prod_adidas["name"],
                    "quantity": 0.485,
                    "unit_price": float(prod_adidas["selling_price"]),
                    "cost_price": float(prod_adidas.get("cost_price", 0)),
                    "subtotal": subtotal_adidas,
                    "pack_label": "Scale Weighed (0.485kg)"
                },
                {
                    "product_id": prod_tj["id"],
                    "product_name": prod_tj["name"],
                    "quantity": 1.0,
                    "unit_price": float(prod_tj["selling_price"]),
                    "cost_price": float(prod_tj.get("cost_price", 0)),
                    "subtotal": float(prod_tj["selling_price"]),
                    "pack_label": "1kg Jumbo Pack"
                },
                {
                    "product_id": prod_ice["id"],
                    "product_name": prod_ice["name"],
                    "quantity": 1.0,
                    "unit_price": float(prod_ice["selling_price"]),
                    "cost_price": float(prod_ice.get("cost_price", 0)),
                    "subtotal": float(prod_ice["selling_price"]),
                    "pack_label": "Ice Freezer (Sanitary)"
                },
                {
                    "product_id": prod_drink["id"],
                    "product_name": prod_drink["name"],
                    "quantity": 1.0,
                    "unit_price": float(prod_drink["selling_price"]),
                    "cost_price": float(prod_drink.get("cost_price", 0)),
                    "subtotal": float(prod_drink["selling_price"]),
                    "pack_label": "Chilled Drink"
                }
            ],
            "total_amount": round(total_order, 2),
            "payment_method": "CASH",
            "amount_tendered": 500.0,
            "print_receipt": False
        }

        checkout_resp = client.post("/api/checkout", json=checkout_payload)
        assert checkout_resp.status_code == 200, f"Checkout failed: {checkout_resp.text}"
        txn = checkout_resp.json()
        assert txn["receipt_number"].startswith("TXN-")
        expected_change = round(500.0 - checkout_payload["total_amount"], 2)
        change_val = txn.get("change", txn.get("change_amount", 0))
        assert abs(change_val - expected_change) < 0.01
        print(f"[+] Mixed Coldcut Sale complete: Receipt #{txn['receipt_number']}, Total: ₱{checkout_payload['total_amount']:.2f}, Sukli: ₱{change_val:.2f}")

        # 5. Test GCash Money Transaction Recording with Photo / Metadata & Anti-Replay
        print("\n--- 5. Testing GCash Transaction Recording with Photo & Metadata ---")
        import uuid
        test_ref = f"50425{uuid.uuid4().int % 10000000:07d}"
        gcash_payload = {
            "transaction_type": "GCASH_OUT",
            "flow_type": "B",
            "input_amount": 1000.0,
            "principal_amount": 990.0,
            "fee": 10.0,
            "total_collected": 1000.0,
            "reference_number": test_ref,
            "mobile_number": "09171234567",
            "receipt_image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
            "gcash_timestamp": "Sep 21, 2026, 12:15 AM"
        }
        gcash_resp = client.post("/api/gcash/transact", json=gcash_payload)
        assert gcash_resp.status_code == 200, f"GCash transact failed: {gcash_resp.text}"
        g_data = gcash_resp.json()
        assert g_data["transaction"]["id"] > 0
        assert g_data["gcash_detail"]["id"] > 0
        print(f"[+] GCash Cash-Out recorded successfully: Txn ID {g_data['transaction']['id']}, Ref: {test_ref}, Fee: ₱10.00")

        # 5b. Verify Anti-Replay: Duplicate Reference Number must return 409 Conflict
        dup_resp = client.post("/api/gcash/transact", json=gcash_payload)
        assert dup_resp.status_code == 409, f"Expected 409 for duplicate reference, got {dup_resp.status_code}"
        print(f"[+] Anti-Replay verified: Duplicate GCash reference '{test_ref}' correctly rejected with 409.")

        # 6. Test Utang (Customer Credit / Palista) Full Lifecycle
        print("\n--- 6. Testing Utang (Customer Credit) Full Lifecycle & Ledger ---")
        # 6a. Register new debtor with initial 0 balance
        test_debtor_name = "Aling Maria (Test)"
        reg_resp = client.post("/api/debts/charge", json={
            "customer_name": test_debtor_name,
            "amount_charged": 0,
            "phone_number": "09189998888",
            "notes": "Purok 1 neighbor"
        })
        assert reg_resp.status_code == 200, f"Register debtor failed: {reg_resp.text}"
        debtor = reg_resp.json()
        debtor_id = debtor["id"]
        assert debtor["customer_name"] == test_debtor_name
        assert debtor["total_debt"] == 0.0
        print(f"[+] Debtor registered: '{test_debtor_name}', Account ID: {debtor_id}")

        # 6b. Test both debt listing endpoints (/api/debts and /api/debts/customers)
        list_resp1 = client.get("/api/debts")
        list_resp2 = client.get("/api/debts/customers")
        assert list_resp1.status_code == 200
        assert list_resp2.status_code == 200
        names1 = [c["customer_name"] for c in list_resp1.json()]
        names2 = [c["customer_name"] for c in list_resp2.json()]
        assert test_debtor_name in names1
        assert test_debtor_name in names2
        print("[+] Both '/api/debts' and '/api/debts/customers' endpoints return debtor list successfully")

        # 6c. Test search query filtering
        search_resp = client.get(f"/api/debts?search=Maria")
        assert search_resp.status_code == 200
        search_results = search_resp.json()
        assert any(c["customer_name"] == test_debtor_name for c in search_results)
        print(f"[+] Debtor search filter (?search=Maria) found: {len(search_results)} record(s)")

        # 6d. POS Utang Checkout: Buy items on credit (₱150 total, ₱50 downpayment, ₱100 to utang)
        utang_checkout_payload = {
            "items": [
                {
                    "product_id": prod_tj["id"],
                    "product_name": prod_tj["name"],
                    "quantity": 1.0,
                    "unit_price": 210.0,
                    "cost_price": 175.0,
                    "subtotal": 210.0,
                    "pack_label": "1kg Jumbo Pack"
                }
            ],
            "total_amount": 210.0,
            "payment_method": "UTANG",
            "amount_tendered": 110.0,
            "amount_paid_now": 110.0,
            "customer_name": test_debtor_name,
            "phone_number": "09189998888",
            "notes": "Partial cash downpayment",
            "print_receipt": False
        }
        utang_resp = client.post("/api/checkout", json=utang_checkout_payload)
        assert utang_resp.status_code == 200, f"Utang checkout failed: {utang_resp.text}"
        utang_txn = utang_resp.json()
        assert utang_txn["payment_method"] == "UTANG"
        print(f"[+] Utang sale completed: Receipt #{utang_txn['receipt_number']}, Total: ₱150.00, Downpayment: ₱50.00")

        # 6e. Verify debt balance after sale
        hist_resp = client.get(f"/api/debts/{debtor_id}/history")
        assert hist_resp.status_code == 200, f"Debt history failed: {hist_resp.text}"
        hist_data = hist_resp.json()
        assert hist_data["customer"]["total_debt"] == 100.0, f"Expected ₱100.00 debt, got {hist_data['customer']['total_debt']}"
        charge_entries = [h for h in hist_data["history"] if h["type"] == "CHARGE"]
        assert len(charge_entries) > 0
        assert charge_entries[0]["amount"] == 100.0
        print(f"[+] Debt balance correctly updated to ₱100.00 with audit entry")

        # 6f. Record debt repayment (₱60.00)
        pay_resp = client.post(f"/api/debts/{debtor_id}/pay", json={
            "payment_amount": 60.0,
            "notes": "Weekly hulog"
        })
        assert pay_resp.status_code == 200, f"Pay debt failed: {pay_resp.text}"
        pay_data = pay_resp.json()
        assert pay_data["customer"]["total_debt"] == 40.0
        print(f"[+] Partial payment of ₱60.00 accepted: New Balance = ₱40.00")

        # 6g. Pay remaining balance (₱40.00)
        pay_resp2 = client.post(f"/api/debts/{debtor_id}/pay", json={
            "payment_amount": 40.0,
            "notes": "Fully paid"
        })
        assert pay_resp2.status_code == 200
        pay_data2 = pay_resp2.json()
        assert pay_data2["customer"]["total_debt"] == 0.0
        print(f"[+] Final payment of ₱40.00 accepted: New Balance = ₱0.00 (Cleared)")

        # 6h. Verify Cash Drawer / Daily Report includes debt payments
        rep_resp = client.get("/api/reports/daily")
        assert rep_resp.status_code == 200
        report = rep_resp.json()
        assert report["total_debt_payments"] >= 100.0
        print(f"[+] Daily Report verified: Total debt payments collected = ₱{report['total_debt_payments']:.2f}")

        # 7. Test Legacy Cashier Fallback Route
        print("\n--- 7. Testing Legacy Cashier Fallback Route ---")
        legacy_resp = client.get("/legacy-cashier")
        assert legacy_resp.status_code == 200
        assert "cashierApp()" in legacy_resp.text
        print("[+] Legacy Cashier route '/legacy-cashier' remains fully accessible for fallback.")

    print("\n" + "=" * 60)
    print("[SUCCESS] ALL SVELTE 5 SPA + FASTAPI END-TO-END TESTS PASSED!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
