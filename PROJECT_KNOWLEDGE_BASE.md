# PROJECT_KNOWLEDGE_BASE.md
> **SENTINEL AI — 30-Minute Onboarding for New Engineers**
> Source of truth reconciled against the **actual codebase**, not just prior AI-generated docs.
> Generated: 2026-06-24 · Validates `PROJECT_MASTER_DOCUMENTATION.md` + `CLAUDE_PROJECT_HISTORY.md`

> ⚠️ **READ THIS FIRST.** The two pre-existing docs systematically over-report completeness. Where this file disagrees with them, **this file is correct** — it was checked against running code. Each ⚠️ marks a place a prior doc claims "done" but the code is stubbed/faked.

---

## 1. Project Summary
SENTINEL AI extends **KavachG** (a working YOLO/CCTV safety-incident platform) into an **Industrial Safety Intelligence OS** for the ET AI Hackathon. The pitch: detect **compound risks** — e.g. methane near threshold + active hot-work permit + shift change — that no single sensor flags alone. Built **additively** (KavachG files untouched; only `database.py` + `main.py` modified). Target users: safety officers, plant managers, regulatory auditors, hackathon judges.

**Honest status:** the **plumbing, UI, and DB are real and impressive**; the **four flagship "intelligence" capabilities are scaffolds.** See §5.

## 2. Architecture Summary
- **Backend:** FastAPI, 7 new routers + KavachG routers, 2 background threads (`sensor_service`, `risk_engine`), wired in `main.py`.
- **Frontend:** Next.js 14 (App Router, TS, Tailwind, Recharts, Three.js) in `sentinel-frontend/`. 10 real pages + 1 mock (digital-twin). Legacy `Frontend/` (vanilla JS) is deprecated, kept.
- **Data flow:** `sensor_service` (writes every 5s) → `risk_engine` (evaluates every 30s) → `orchestrator` → `ws_manager.broadcast` → frontend. **Serial pipeline, no queue/retry — a SPOF.**
- **Storage:** single SQLite file `Database/factory.db` (WAL mode, 9 indexes). `app.db` is dead legacy.

## 3. Tech Stack Summary
FastAPI · Uvicorn · SQLite(WAL) · python-jose(JWT) · **passlib + bcrypt==3.2.2 (PIN IS CORRECT — do NOT bump; bcrypt 4/5 breaks passlib)** · Ultralytics YOLO · OpenCV · **Ollama (local LLM)** · TF-IDF (custom, not vector RAG) · Next.js 14 · Three.js · Recharts.
⚠️ `requirements.txt` lists **`anthropic`** (cloud) but **not** `ollama`/`chromadb`. Provider story is unresolved (§9 Decision-Needed).

## 4. Major Features (real vs. claimed)
| Module | Doc claim | **Reality (code-verified)** |
|---|---|---|
| M1 Sensors | 100% | ✅ **Real** — sim + DB + `/ws/sensors` |
| M2 Compound Risk | 100% | ⚠️ **Stub** — flat-ANDed single-signal rules; **no temporal/spatial fusion**, no real prediction (ETA hardcoded), trajectory wiped every 30s |
| M3 Digital Twin | 100% | ⚠️ **Mock** — hardcoded `ZONES_3D` grid; only colors live |
| M4 RAG Copilot | 95% | ⚠️ **TF-IDF over 7 hardcoded summaries**; no embeddings, no real OISD/DGMS PDFs |
| M5 Permits | 100% | ✅ **Real** CRUD + overlap rules (but no live-sensor validation) |
| M6 Emergency | 100% | ⚠️ **`print()` + WebSocket only** — no evacuation action, no evidence capture, no report gen |
| M7 Compliance | 100% | ⚠️ **Partial** — `_check_permit_coverage` always returns PASS; `shift_records` never populated |
| FA Multi-Agent | 100% | ⚠️ **No LLM** — agents are deterministic SQL wrappers |
| FB Knowledge Graph | 0% | ❌ Not started |
| CV / Auth / Realtime | 100% | ✅ Real (inherited from KavachG) |

## 5. Current Status (corrected)
- Backend plumbing **~85%**, intelligence **~30%**. Frontend **~85%** (9/10 pages real). DB **~95%**. Testing **0%**. DevOps **~5%**. Security **~35%**.
- **Overall realistic: ~55% for the hackathon thesis** (not the 75% the docs claim), because the judged differentiators are stubbed.

## 6. Active Risks (top 6 — full list in the audit)
1. ✅ **FIXED (2026-06-24)** — AI Copilot now uses a real LLM. `.env` was `OLLAMA_MODEL=llama3.2:3b` (not installed → silent template fallback); changed to **`OLLAMA_MODEL=llama3.1:8b`** (installed, verified returning real answers). Do not revert without pulling the target model first.
2. 🔴 Compound fusion is fake — cannot demonstrate "a risk no single sensor caught."
3. 🔴 Default `SECRET_KEY`/`ADMIN_PASSWORD` unchanged.
4. 🔴 Anthropic cloud fallback can exfiltrate plant data / breaks offline.
5. 🟠 No JWT expiry, no rate limit, no RBAC enforcement; HTTP only.
6. 🟠 0% tests on a shared-file, multi-thread system; no backup/migration/rollback.

## 7. Pending Work (prioritized — see Ownership §)
P0: fix `OLLAMA_MODEL`; change secrets; decide Ollama-vs-Anthropic + fix requirements; browser E2E smoke.
P1: real fusion (temporal+spatial correlation, trajectory, computed ETA); wire agents to Ollama tool-calling; real emergency actions; JWT expiry + RBAC.
P2: ChromaDB + ingest real OISD/DGMS/Factory Act docs; fix `_check_permit_coverage`; populate `shift_records`; digital-twin geometry endpoint; SQLite backup.
P3: Knowledge Graph (FB) or descope; Docker/SSL/CI; cross-OS docs.

## 8. Team Responsibilities
PM: status-honesty + provider decision + demo script. Backend: emergency actions, auth hardening, geometry endpoint. **AI/Automation: the big three — real fusion, agent LLM wiring, vector RAG.** Database: backup/migrations, corpus storage. DevOps: `.env`/model reconciliation, Docker/SSL, cross-OS setup. Frontend: digital-twin dynamic zones, loading/error states. QA: OpenAPI endpoint inventory + blocking E2E.

## 9. Critical Decisions (settled + OPEN)
Settled: additive-only on KavachG; new Next.js frontend; SQLite; rules over ML for explainability; ThreadPoolExecutor for agents.
**OPEN / must decide:** (a) **Ollama-only vs Anthropic-allowed** — affects privacy, offline, requirements. (b) Real vector RAG vs keep TF-IDF for demo. (c) Is fake fusion acceptable for the demo, or is real correlation a hard requirement? (d) FB Knowledge Graph in scope?

## 10. Deployment Overview
Local only. macOS now (docs say Windows `C:\Users\MOHIT\…` — **ignore those paths**). Backend: `cd Backend && python main.py` (:8000). Frontend: `cd sentinel-frontend && npm run dev` (:3000). Ollama on :11434. **No Docker/CI/SSL/monitoring/backup.** First run needs `create_admin_user.py` + a pulled model matching `.env`.

## 11. Database Overview
`factory.db`, 15 tables. New: `zones`(6), `sensors`(36), `sensor_readings`(~432 rows/min, 6h retention), `permits`, `risk_assessments`, `emergency_events`, `knowledge_base`(7 docs), `shift_records`(**empty at runtime**). Forward-only `ensure_column()` migrations; **no backup, no rollback**. `app.db` = delete.

## 12. API Overview
~40 endpoints across `/sensors /risk /permits /emergency /intelligence /compliance /agents` + KavachG `/auth /incidents /detection /video /cameras /people /settings /reports`. Auth = JWT Bearer (query-param `?token=` for WS/media).
⚠️ **Doc errors:** `/auth/me` does **not** exist. Real auth routes: `/auth/login`, `/auth/register`, `/auth/admin/create`. **Always regenerate the endpoint list from `/openapi.json`, not prose.**

---
*Reconciled against live code on macOS. Where prior docs differ, trust this file. Owner of doc-honesty: PM.*
