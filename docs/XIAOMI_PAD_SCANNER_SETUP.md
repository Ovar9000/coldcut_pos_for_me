# Xiaomi Pad 11" & Presentation Barcode Scanner Setup Guide
## Standalone Cloud POS with Supabase & Starlink Wi-Fi

This guide details how to set up and operate your **Coldcut / Sari-Sari POS** directly on your **11-inch Xiaomi Pad (Android)** as an independent, standalone cashier terminal connected to **Supabase** in the cloud over **Starlink Wi-Fi**, without needing a PC or local server running.

---

## 1. Hardware Connection Architecture

Your 640×480 CMOS presentation barcode scanner draws **5V DC @ 175mA** over USB. To prevent battery drain and maintain 24/7 store operation, connect the hardware as follows:

```
                  ┌───────────────────────────────┐
                  │    Xiaomi Fast Wall Charger   │
                  └───────────────┬───────────────┘
                                  │ USB-C Power Cable
                                  ▼
┌─────────────────────────┐  (PD Port)  ┌───────────────────────────────┐
│     Xiaomi Pad 11"      │◄────────────┤   USB-C Hub with Power        │
│  (MIUI / HyperOS Pad)   │  USB-C Host │   Delivery (PD Pass-Through)  │
└─────────────────────────┘             └───────────────┬───────────────┘
                                                        │ USB-A Port
                                                        ▼
                                        ┌───────────────────────────────┐
                                        │  CMOS Presentation Scanner    │
                                        │  (USB HID Keyboard Emulation) │
                                        └───────────────────────────────┘
```

### Hardware Checklist:
1. **Xiaomi Pad 11"** (8GB RAM / 256GB Storage).
2. **USB-C Multiport Hub with Power Delivery (PD 60W/100W pass-through)**:
   - *Note*: Ensure the hub has at least one USB-C PD input port and one USB-A female port.
3. **Omnidirectional CMOS Barcode Scanner**:
   - Plug the scanner's USB cable directly into the USB-A port of the hub.
   - Plug the tablet's charger into the USB-C PD port of the hub.
   - Connect the hub's main USB-C cable to the tablet.

---

## 2. Essential Android Tablet Settings

When Android detects a USB barcode scanner, it identifies it as an external physical keyboard. To prevent Android from hiding the on-screen soft keyboard when typing custom prices or customer names:

1. On your Xiaomi Pad, open **Settings**.
2. Go to **Additional Settings** > **Languages & Input**.
3. Under **Physical Keyboard**, turn **ON** the switch for:
   - **"Show on-screen keyboard"** (or *"Keep virtual keyboard on screen"*).
4. *(Optional Kiosk Mode)*: In **Display**, set screen timeout to **Never** or **10 minutes** while plugged in.

---

## 3. One-Time Supabase Cloud Database Activation

To activate the standalone cloud checkout engine in your Supabase project:

1. Open your [Supabase Dashboard](https://supabase.com/dashboard).
2. Navigate to **SQL Editor** > **New Query**.
3. Copy the entire contents of [`supabase_schema.sql`](../supabase_schema.sql) and paste it into the editor.
4. Click **Run**.
5. *Result*:
   - Creates the hardened catalog and financial tables (`products`, `transactions`, `customer_debts`, `gcash_transactions`).
   - Installs the atomic `process_checkout` and `pay_customer_debt` Postgres RPC stored procedures.
   - Configures secure Row Level Security (RLS) policies.

---

## 4. Running the POS on Xiaomi Pad

### Option 1: Instant PWA Kiosk (Fastest & Zero Build Overhead)
The frontend includes a pre-configured Progressive Web App (PWA) manifest:

1. Ensure the Xiaomi Pad is connected to your **Starlink Wi-Fi**.
2. If running locally with the PC on:
   - Run on your PC: `python run.py --lan`
   - Open Chrome on the Xiaomi Pad and navigate to `http://<YOUR_PC_LAN_IP>:8000`
3. If running purely cloud-hosted (Vercel / Cloudflare Pages / Static host):
   - Navigate to your deployed POS URL in Chrome.
4. In Chrome, tap the **three-dot menu (⋮)** in the top-right corner.
5. Tap **"Install app"** or **"Add to Home screen"**.
6. Tap the **Coldcut POS** icon on your home screen:
   - Opens full-screen in landscape orientation without any browser URL bar or navigation buttons.
   - Connects directly to Supabase cloud over Starlink.

---

### Option 2: Native Android App (.APK via Capacitor)
The codebase includes a fully generated Android native project located in `frontend/android/`:

1. Open **Android Studio** on a computer.
2. Select **Open** and select the folder:
   `coldcut_pos_for_me/frontend/android`
3. Wait for Gradle sync to complete.
4. Go to **Build** > **Build Bundle(s) / APK(s)** > **Build APK(s)**.
5. Transfer the generated `.apk` file (`app-debug.apk`) to your Xiaomi Pad via USB or Google Drive and tap to install!

---

## 5. Daily Operation with the Barcode Scanner

1. **Power Up**: Turn on the Xiaomi Pad and plug in the USB-C Hub. The barcode scanner will emit a beep and its red CMOS LED will illuminate.
2. **Open POS**: Tap the **Coldcut POS** app icon.
3. **Scan Items**:
   - Simply swipe any barcoded item, mother-pack, jar refill QR, or Dahua/Rongta weight-embedded scale label in front of the scanner.
   - The scanner decodes the barcode in < 10ms and the app automatically adds the item to the cart with correct pricing and weight.
4. **Checkout**:
   - Select Cash, GCash, or Utang.
   - Tap **Confirm & Pay**. The sale is atomically recorded in Supabase, and stock is decremented immediately across all store devices!
