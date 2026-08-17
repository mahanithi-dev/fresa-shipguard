# ShipGuard Codebase Audit & Production Readiness Changelog

This document provides a comprehensive record of the code audit, dead code cleanup, correctness fixes, security hardening, and verification steps performed on **ShipGuard**. Use this document during your technical interview walkthrough at Fresa Technologies to explain every architectural decision and fix.

---

## Table of Contents
1. [Phase 1: Architecture & Data Flow Map](#phase-1-architecture--data-flow-map)
2. [Phase 2: Dead Code & Junk Removal](#phase-2-dead-code--junk-removal)
3. [Phase 3: Correctness & Bug Fixes](#phase-3-correctness--bug-fixes)
4. [Phase 4: Security & Configuration Hygiene](#phase-4-security--configuration-hygiene)
5. [Phase 5: Consistency & Readability](#phase-5-consistency--readability)
6. [Phase 6: Verification Matrix & Interview Defense Guide](#phase-6-verification-matrix--interview-defense-guide)

---

## Phase 1: Architecture & Data Flow Map

### 1.1 Core Components & Technology Stack
- **Frontend**: React 19 Single Page Application with Lucide icons, styled using responsive Vanilla CSS tokens.
- **Backend API Gateway**: FastAPI with Pydantic v2 validation models and JWT bearer token authentication.
- **Data Persistence**: SQLAlchemy 2.0 ORM with support for Oracle database schema in production (`database/schema.sql`) and SQLite for local development (`backend/shipguard.db`).
- **Machine Learning & Scoring**: Hybrid intelligence combining an offline scikit-learn Logistic Regression classifier (`model.joblib`) with a real-time domain-calibrated multi-factor risk engine (`scoring_service.py`).
- **External Real-Time Intelligence**: Live integration with Open-Meteo (maritime weather), Frankfurter (foreign exchange rates), Nager.Date (international port closures), and Global Port Congestion indices.
- **AI & RAG Co-Pilot**: In-memory TF-IDF vectorizer + cosine similarity search over active freight lanes, backed by Google Gemini 1.5/Flash and OpenAI/NVIDIA LLM integrations with deterministic local rule fallbacks.

### 1.2 End-to-End Data Flow
1. **User Authentication**: Client submits credentials to `POST /api/v1/auth/login` → verified against bcrypt hash → returns signed HS256 JWT access token.
2. **Worklist Ingestion**: Client requests `GET /api/v1/shipments` with pagination and filters → FastAPI queries DB with eager `joinedload` on Carrier, Route, and RiskScore → returns `PaginatedShipments`.
3. **Shipment Creation & Scoring**: User fills Intake Modal → `POST /api/v1/shipments` validates `eta >= etd` → inserts DB record → triggers `score_shipment()` → extracts historical on-time % and route delay as-of shipment ETD → calculates sigmoid risk score + external risk deltas → commits `RiskScore`.
4. **AI Risk Explanation (RAG)**: User clicks "AI Risk Explanation" → `GET /api/v1/ai/explain/{id}` → extracts shipment telemetry → queries in-memory TF-IDF index for top-3 relevant lane contexts → prompts LLM with operational parameters → returns plain-language analysis and mitigation steps.
5. **AI Operational Co-Pilot**: User chats in Floating Widget → `POST /api/v1/ai/chat` → checked against sliding-window rate limiter (15 req/min) → injects live network summary → streams/returns assistant response (with fallback if API key quota exceeded).

---

## Phase 2: Dead Code & Junk Removal

### 2.1 Unused Imports Cleaned
- `backend/app/seed.py`: Removed unused `random`, `datetime`, `Carrier`, `Route`, `ShipmentHistory`, `User`, and `hash_password`.
- `backend/app/ml/features.py`: Removed unused `Carrier`, `ShipmentHistory`, and `date`.
- `backend/app/models/schemas.py`: Removed unused typing import `Any`.
- `backend/app/routers/ai.py`: Removed unused typing import `Optional`.
- `backend/app/routers/reports.py`: Removed unused `func` and `User` entities.
- `backend/app/routers/shipments.py`: Removed unused `func` and consolidated duplicate `RiskScore` imports.
- `backend/app/services/ai_generator.py`: Removed unused `Any`.
- `backend/app/services/external_data.py`: Removed unused `urllib.error`, `timedelta`, and `List`.
- `backend/app/services/llm_nvidia.py`: Removed unused `urllib.error`.
- `backend/app/config.py`: Lifted `Path` to module top; removed inline `BaseSettings` import in `customise_sources`.
- `frontend/src/main.jsx`: Removed unused Lucide icons (`Settings`, `ExternalLink`, `ArrowUpRight`, `TrendingUp`).

### 2.2 Deduplicated Logic
- **Carrier & Route Historical Aggregation**: Refactored `scoring_service.py` to import `carrier_on_time_pct_as_of` and `route_avg_delay_days_as_of` directly from `app.ml.features`. Eliminated redundant private helper functions (`_carrier_reliability_as_of`, `_route_delay_as_of`) and eliminated train/serve metric skew.
- **Environment Configuration**: Removed duplicate `DATABASE_URL` and `JWT_SECRET` key definitions from `backend/.env.example`.

### 2.3 Unused Package & Dependency Removal
- `frontend/package.json`: Removed unused `axios` dependency (application utilizes native browser `fetch()`).
- Moved `vite` and `@vitejs/plugin-react` from runtime `dependencies` to `devDependencies`.

### 2.4 Stray Artifacts & Logs Deleted
- Removed stray duplicate SQLite databases: `frontend/shipguard.db` and root `shipguard.db`.
- Added `*.db` pattern to `.gitignore` under Database & Local Data.
- Removed local server logs (`backend/api.log`, `backend/api.err.log`, `frontend/vite.log`, `frontend/vite.err.log`, `frontend/preview.log`, `frontend/preview.err.log`).
- Removed obsolete single-file debug test scripts (`login_post.py`, `login_test.py`, `options_check.py`, `check_health.py`, `check_routers.py`, `inspect_app.py`).

---

## Phase 3: Correctness & Bug Fixes

### 3.1 Input Validation & Date Ordering
- **Issue**: `ShipmentUpdate` schema allowed patching `eta` to a date prior to `etd` without validation before reaching database checks.
- **Fix**: Added `@model_validator(mode="after")` to `ShipmentUpdate` in `backend/app/models/schemas.py` to enforce `eta >= etd` on partial updates.
- **Verification**: Evaluated invalid date update; verified schema raises HTTP 422 Unprocessable Entity.

### 3.2 Robust CSV Import Processing
- **Issue**: `import_shipments` in `routers/shipments.py` added all parsed rows in a single batch. A database constraint failure on a single row (e.g. duplicate reference) caused an unhandled 500 error on `db.commit()`.
- **Fix**: Updated import loop with per-row `db.flush()` and transactional `db.rollback()` on exception. Valid rows are committed and scored; invalid rows are caught and returned in the structured `errors` array.
- **Verification**: Simulated mixed CSV with valid and invalid rows; valid shipments were committed and returned while errors were logged per line number.

### 3.3 Dynamic ML Metrics Endpoint
- **Issue**: `/api/v1/risk/metrics` returned static hardcoded dictionary constants in `seed.py`.
- **Fix**: Updated `model_metrics()` in `routers/risk.py` to dynamically load evaluation metrics (`precision`, `recall`, `f1_score`, `roc_auc`) from `backend/app/ml/model.joblib` when trained, retaining default guardrail metadata as fallback.
- **Verification**: Executed `train_and_save()`; queried `GET /api/v1/risk/metrics` and verified dynamically computed metrics are returned.

### 3.4 Error Logging & Exception Visibility
- **Issue**: Startup RAG indexing used bare `except Exception: pass` which silently swallowed vectorizer failures.
- **Fix**: Replaced with `logger.warning("Retrieval index build notice: %s", exc)`.
- **Issue**: Startup external sync used bare `print()`.
- **Fix**: Replaced with `logger.warning("External data sync notice: %s", exc)`.

### 3.5 Frontend CSV Export Error Feedback
- **Issue**: `downloadCSV()` in `frontend/src/main.jsx` failed silently without user notification if the network or auth token failed.
- **Fix**: Added `showToast(err.message || "Failed to export CSV report", "error")` inside the catch block.

---

## Phase 4: Security & Configuration Hygiene

### 4.1 Secrets & Environment Variable Management
- Verified no API keys, private keys, or database credentials are committed to version control.
- `backend/.env` is ignored by `.gitignore`.
- Configured Pydantic `BaseSettings` with automatic fallback to `.env.example` in development mode.

### 4.2 CORS Configuration Hardening
- Replaced wildcard regex `allow_origin_regex=r"https?://.*"` in `backend/app/main.py` with explicit allowed origin parsing from `settings.cors_origins` (`http://localhost:5173`, `http://127.0.0.1:5173`, `http://localhost:5176`, `http://127.0.0.1:5176`).

### 4.3 AI Rate Limiting & Provider Quota Protection
- `AIRateLimiter` in `services/rate_limiter.py` enforces sliding-window rate limits (15 requests/minute, 200/hour, 1000/day) and provider daily quotas (500/day for Gemini, 500/day for NVIDIA).
- Returns HTTP 429 `Too Many Requests` with standard `Retry-After` headers and remaining quota headers (`X-RateLimit-Remaining-Minute`, `X-RateLimit-Remaining-Day`).

---

## Phase 5: Consistency & Readability

### 5.1 Standardized Error Handling Pattern
- Standardized all FastAPI endpoints on `raise HTTPException(status_code=status.HTTP_..., detail="...")`.
- Unified return shapes across routers for consistent consumption by `api.request` in React.

### 5.2 Naming Conventions & Anti-Leakage Documentation
- Preserved snake_case for database entities and API schema fields (`shipment_ref`, `carrier_name`, `risk_score`, `risk_tier`, `avg_transit_days`).
- Added explanatory docstrings to feature calculation functions detailing temporal guardrails (`actual_arrival < shipment.etd`) to defend against target data leakage in ML evaluation.

---

## Phase 6: Verification Matrix & Interview Defense Guide

### 6.1 Automated Verification Commands

| Component | Command | Expected Output | Status |
| :--- | :--- | :--- | :--- |
| **Backend Imports & App Initialization** | `python -c "import sys; sys.path.insert(0, 'backend'); import app.main; print('OK')"` | `OK` | ✅ Passed |
| **ML Pipeline Training** | `python backend/app/ml/train_model.py` | `Saved model to .../model.joblib; Metrics: {...}` | ✅ Passed |
| **Dynamic Metrics Query** | `python -c "import sys; sys.path.insert(0, 'backend'); from app.routers.risk import model_metrics; print(model_metrics().model_dump())"` | Metrics dictionary loaded from `model.joblib` | ✅ Passed |
| **External Intelligence Sync** | `python scripts/test_external_sync.py` | `Synced: 15 weather ports, 5 FX pairs, 46 holidays, 15 port statuses` | ✅ Passed |
| **Frontend Production Build** | `npm.cmd --prefix frontend run build` | `✓ 1664 modules transformed. dist/ built with 0 errors` | ✅ Passed |

---

### 6.2 Key Interview Walkthrough Talking Points

1. **Why use SQLite in dev and Oracle in production?**
   > *"The application is architected with SQLAlchemy 2.0 ORM decoupling. In local demo and testing environments, SQLite provides zero-configuration startup. In production, `database/schema.sql` establishes a strict Oracle schema with identity columns, check constraints, foreign keys, and indexes (`idx_shipments_eta`, `idx_risk_scores_scored_at`). Switchover requires only updating `DATABASE_URL` in the environment."*

2. **How does the ML feature pipeline avoid target data leakage?**
   > *"When computing historical carrier reliability or average route delay, we strictly enforce a temporal filter: `Shipment.actual_arrival < shipment.etd`. We only aggregate outcomes that were physically known prior to the departure of the shipment being scored. This prevents future arrival data from leaking into feature vectors."*

3. **Why combine offline ML training with a dynamic scoring engine?**
   > *"Offline Logistic Regression evaluates baseline feature importances (carrier SLA history, route baseline transit, seasonal month). In real-time freight forwarding operations, sudden external shocks occur (typhoons, port berth congestion, currency volatility). The dynamic scoring engine applies calibrated delta adjustments from live telemetry on top of statistical baselines, giving operators instant situational awareness without requiring full model retraining every hour."*

4. **How are AI API rate limits and failures defended?**
   > *"We implemented an in-memory sliding-window `AIRateLimiter` dependency that tracks request timestamps per user and per provider. If a user exceeds 15 calls/min or daily provider quotas are reached, it raises HTTP 429 with `Retry-After`. Furthermore, if external LLMs experience network timeouts, `gemini_service.py` and `llm_nvidia.py` seamlessly drop down to domain rule-based intelligence generators without exposing raw tracebacks to the user."*
