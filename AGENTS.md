# Sari-Sari / Coldcut POS — Agent Guidelines & Instructions

Welcome! When working on this codebase, adhere strictly to the following standards, security mandates, and architectural patterns.

---

## 1. Required Agent Skills

Always load and follow the specialized skills located in `.agents/skills/` (also accessible via `.agent/skills/`):

1. **`supabase`** (`.agents/skills/supabase/SKILL.md`)
   - Read and apply whenever touching Supabase configuration, schema definitions, storage buckets, RLS policies, or cloud synchronization.
   - **Crucial Rule**: Never expose secret/service role keys, and never write permissive `USING (true) WITH CHECK (true)` policies for untrusted roles.

2. **`supabase-postgres-best-practices`** (`.agents/skills/supabase-postgres-best-practices/SKILL.md`)
   - Consult when modifying database schemas, table definitions, foreign keys, indexes, and migrations.

3. **`svelte-5-runes`** (`.agents/skills/svelte-5-runes/SKILL.md`)
   - Read and follow for all frontend work in `frontend/src/`.
   - **Crucial Rule**: Always use modern Svelte 5 Runes (`$state`, `$derived`, `$derived.by`, `$props`, `$bindable`, `$effect`).
   - Do NOT use legacy Svelte 4 reactivity syntax (`let` for reactive variables, `$:` reactive statements, or `export let` for props).

---

## 2. Security Mandates

When authoring or modifying backend routes and schemas:

1. **Protect Admin & Sensitive Endpoints**:
   - Every route modifying inventory (`POST/PUT/DELETE /api/products`), reading/changing store settings (`/api/admin/settings`), or exporting/downloading database backups (`/api/sync/download-db`, `/api/sync/export-json`, `/api/sync/supabase/*`) **must** enforce server-side authentication using the `admin_sessions` token via FastAPI `Depends()`.
   - Never rely solely on client-side frontend redirects (e.g. `sessionStorage.getItem('admin_auth')`).

2. **No Hardcoded Credentials or Project Keys**:
   - Never hardcode Supabase project URLs, API keys, or database credentials into source code, default database values, or frontend scripts.
   - Always load sensitive configuration from `.env.local` or environment variables with empty/safe defaults.

3. **Strict Row Level Security (RLS)**:
   - Supabase tables must never have wide-open write policies for anonymous (`anon`) clients.
   - Storage buckets storing SQLite database backups (`store-backups`) must be private (`public = false`) and only accessible by authenticated admin roles or through authorized server-side sync proxies.

4. **Server-Side Financial & Input Validation**:
   - Validate that item quantities and unit prices in carts are positive (`> 0`).
   - Always verify and recalculate fees on the backend for GCash transactions (`app/services/gcash_engine.py`) rather than trusting amounts provided by the client.

5. **Network Binding**:
   - Development servers must bind to `127.0.0.1` by default unless explicitly configured for LAN deployment with authentication enabled.

---

## 3. Architecture & Tech Stack

- **Backend**: FastAPI (`app/main.py`) + SQLite in WAL mode (`data/store.db`) via `aiosqlite`.
- **Frontend**: Svelte 5 + Vite + Tailwind CSS (`frontend/`), compiled to `static/dist/`.
- **Desktop Kiosk**: PySide6 / pywebview wrapper (`desktop_app.py`, `build_desktop.py`).
- **Cloud Disaster Recovery**: Supabase Storage snapshots & mirrored sales ledger (`app/services/supabase_sync.py`).

---

## 4. Build & Verification Commands

- Run Backend: `python run.py` (Cashier: `http://localhost:8000`, Admin: `http://localhost:8000/admin`)
- Build Frontend: `cd frontend && npm run build` (outputs to `static/dist/`)
- Run Integration Tests: `python test_system_integrity.py` and `python test_svelte_pos_integration.py`
