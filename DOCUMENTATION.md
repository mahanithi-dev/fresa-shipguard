# 🚢 ShipGuard — Complete Technical & Operational Documentation

---

## 1. 📌 Executive Overview & Problem Statement

**ShipGuard** is an enterprise-grade **Shipment Delay Risk & Exception Prediction System** built for global freight forwarding and logistics operations (designed specifically for Fresa Technologies' ecosystem).

### 🎯 Business Problem
In international supply chain operations, shipments face dynamic disruptions such as severe port congestion, maritime weather anomalies, carrier reliability fluctuations, holiday port closures, and customs dwell times. Traditional freight management systems only record delays *after* they happen.

### 💡 ShipGuard Solution
ShipGuard moves logistics operations from **reactive firefighting** to **proactive risk mitigation**:
- Pre-computes delay probabilities for every active booking before departure.
- Integrates live external telemetry (weather, port congestion, currency fluctuations, port holiday closures).
- Combines an offline-trained **Machine Learning Logistic Classifier** with a **real-time domain-calibrated risk scoring engine**.
- Features an **AI Operations Co-Pilot** (powered by Google Gemini 2.0 Flash & RAG) to provide automated plain-language risk explanations and draft customer exception notices.

---

## 2. 🏛️ System Architecture & Tech Stack

```
+---------------------------------------------------------------------------------------+
|                                    USER INTERFACE                                     |
|                       React 19 SPA (Vite) + Lucide Icons + CSS Tokens                 |
+------------------------------------------+--------------------------------------------+
                                           | HTTPS / WebSocket / REST
                                           v
+---------------------------------------------------------------------------------------+
|                                NGINX REVERSE PROXY                                    |
|                       SSL Termination (Certbot) + Port 443 -> 8000                    |
+------------------------------------------+--------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
|                               FASTAPI APPLICATION GATEWAY                             |
|                                                                                       |
|  +--------------------+  +----------------------+  +-------------------------------+  |
|  | JWT Authentication |  | Rate Limiting Engine |  | Pydantic v2 Request Validation|  |
|  +--------------------+  +----------------------+  +-------------------------------+  |
|                                                                                       |
|  +--------------------+  +----------------------+  +-------------------------------+  |
|  | ML Scoring Service |  | TF-IDF RAG Engine    |  | Google Gemini 2.0 / LLM Serv. |  |
|  +--------------------+  +----------------------+  +-------------------------------+  |
|                                                                                       |
|  +---------------------------------------------------------------------------------+  |
|  | External Sync Service (Open-Meteo Weather, Port Congestion, Frankfurter, Nager) |  |
|  +---------------------------------------------------------------------------------+  |
+------------------------------------------+--------------------------------------------+
                                           | SQLAlchemy 2.0 ORM
                                           v
+---------------------------------------------------------------------------------------+
|                                 DATABASE STORAGE                                      |
|            Oracle Autonomous DB (Production DDL) / SQLite (Persistent Volume)        |
+---------------------------------------------------------------------------------------+
```

### 💻 Technology Stack

| Layer | Technologies Used |
| :--- | :--- |
| **Frontend** | React 19, Vite, Lucide React, Responsive Vanilla CSS Design Tokens |
| **Backend API** | Python 3.11, FastAPI, Pydantic v2, Uvicorn (ASGI) |
| **Database & ORM** | SQLAlchemy 2.0, Oracle Autonomous DB (Production DDL) / SQLite (Persistent volume) |
| **Machine Learning** | Scikit-Learn (Logistic Regression), Joblib, Pandas, NumPy |
| **AI & LLM** | Google Gemini 2.0 Flash (`google-genai` SDK), OpenAI/NVIDIA LLM, In-Memory TF-IDF Vectorizer |
| **External APIs** | Open-Meteo, Frankfurter FX, Nager.Date Public Holidays, Port Congestion Indices |
| **Security & Auth** | JWT (HS256 with `python-jose`), Passlib/Bcrypt, Sliding-window Rate Limiting, CSP Headers |
| **Container & CI/CD** | Docker Multi-stage Build, Docker Compose, GitHub Actions, Hostinger VPS, Nginx, Certbot SSL |

---

## 3. ⚙️ Core Modules & Capabilities

### 3.1 Active Worklist & Freight Dashboard
- Real-time KPI counters: **Total Active Shipments**, **High Risk Exceptions**, **Delayed Shipments**, and **In-Transit Volume**.
- Interactive worklist table with multi-criteria filtering (Mode: Air/Sea/Land, Risk Tier: High/Medium/Low, Status: Booked/In-Transit/Delayed/Delivered).
- Deep inspection **Shipment Drawer** displaying interactive milestone checkpoints, route timeline, risk factor breakdown, and carrier details.
- Full CSV export and transactional batch CSV import with per-line validation and error reporting.

### 3.2 Dynamic Risk Scoring & Machine Learning
- Hybrid design combining a trained Scikit-Learn statistical model with real-time heuristic adjustments.
- Strict **as-of temporal filtering** ensuring zero data leakage (only historical records with timestamps strictly prior to shipment departure are computed).
- Outputs normalized probability scores ($0.0000$ to $1.0000$) mapped into risk tiers:
  - 🟢 **LOW RISK**: Score < 0.35
  - 🟡 **MEDIUM RISK**: 0.35 <= Score <= 0.65
  - 🔴 **HIGH RISK**: Score > 0.65

### 3.3 Real-Time External Telemetry Synchronization
- **Open-Meteo**: Queries wind speed, precipitation, and sea conditions for maritime hubs (Rotterdam, Shanghai, Singapore, Los Angeles, Chennai, Tuticorin, Jebel Ali, Hamburg, etc.).
- **Global Port Congestion**: Tracks berth waiting times and terminal queue congestion levels.
- **Nager.Date**: Identifies national port closure dates and statutory holidays across trade corridors.
- **Frankfurter FX**: Monitors exchange rate volatility between international trade currency pairs.

### 3.4 AI Co-Pilot & RAG Engine
- **Floating Interactive Widget**: Multimodal conversation assistant available across all views.
- **Dynamic Context Injection**: Co-pilot automatically receives a snapshot of active operations, delayed shipments, carrier rankings, and route bottlenecks.
- **General & Domain Intelligence**: Handles arbitrary conversational queries, math, number selection, jokes, deep freight intelligence, and automated exception email drafting.
- **Clickable Shipment Chips**: AI messages render references like `SHP-2026-A0001` as clickable interactive buttons that open the inspection drawer directly.

---

## 4. 🧠 Risk Scoring Engine & Mathematical Formulation

### 4.1 Hybrid Scoring Formula
The risk score calculation combines **historical performance vectors** with **real-time environmental deltas**:

$$z = w_0 + w_1 \cdot (1 - \text{CarrierOnTimePct}) + w_2 \cdot \text{RouteDelayDays} + w_3 \cdot \text{TransitRatio} + \Delta_{\text{ext}}$$

Where:
1. $\text{CarrierOnTimePct} \in [0, 1]$: Historical on-time delivery rate of the carrier calculated **strictly as-of the shipment's ETD**.
2. $\text{RouteDelayDays}$: Average historical delay observed on the specific trade lane prior to the ETD.
3. $\text{TransitRatio}$: Scheduled Transit Days / Route Benchmark Days.
4. $\Delta_{\text{ext}}$: Composite delta calculated from live external signals:
   - Severe port weather / gale force winds: $+0.15$
   - Critical terminal berth waiting time (> 24h): $+0.20$
   - Active port holiday closure during schedule: $+0.10$

The final probability is mapped through the sigmoid function:

$$\text{RiskScore} = \sigma(z) = \frac{1}{1 + e^{-z}}$$

---

## 5. 🗄️ Database Architecture & Schema (Oracle & SQLite)

### Key Database Entities:
1. **`carriers`**: Stores carrier codes, names, and historical on-time delivery percentages.
2. **`routes`**: Origin port, destination port, transport mode (`AIR`, `SEA`, `LAND`), and baseline transit days.
3. **`shipments`**: Primary shipment master containing references, ETD, ETA, actual arrivals, container numbers, status, and consignee.
4. **`shipment_history`**: Event audit trail and historical delay timestamps used for ML features.
5. **`risk_scores`**: Calculated risk score, tier (`LOW`, `MEDIUM`, `HIGH`), JSON top contributing factors, and operational recommendations.
6. **`external_weather`**: Port temperature, wind speed, precipitation, and severity alerts.
7. **`external_port_status`**: Port terminal congestion indices and average vessel berth wait hours.
8. **`external_holidays`**: National holiday calendars and statutory port closure events.
9. **`external_currencies`**: Foreign currency exchange rates and volatility indexes.
10. **`users`**: Operator authentication records, roles, and bcrypt password hashes.

---

## 6. 🌐 REST API Endpoints Reference

Base Path: `/api/v1`

### 🔑 Authentication (`/auth`)
- `POST /auth/login`: Authenticate user using email & password; returns signed JWT bearer token.
- `POST /auth/register`: Create a new operator account (enforces password length & complexity).
- `GET /auth/me`: Retrieve current logged-in user profile and permissions.

### 📦 Shipments (`/shipments`)
- `GET /shipments`: Paginated search, sorting, and filtering of active worklist shipments.
- `POST /shipments`: Create and automatically score a new freight booking.
- `GET /shipments/{id}`: Detailed shipment profile with milestone timeline and risk factors.
- `PATCH /shipments/{id}`: Partial update (validates `eta >= etd` and triggers automated re-scoring).
- `DELETE /shipments/{id}`: Remove shipment record.
- `POST /shipments/import-csv`: Transactional bulk ingestion from CSV with error logging.
- `GET /shipments/export-csv`: Export filtered active shipments to downloadable CSV report.

### 📊 Risk Intelligence & ML (`/risk`)
- `POST /risk/score/{id}`: Force re-evaluation of shipment risk score.
- `GET /risk/metrics`: Model evaluation metrics (Accuracy, F1-Score, ROC-AUC, Precision, Recall).
- `GET /risk/distribution`: Global risk tier breakdown (High, Medium, Low counts & percentages).

### 🤖 AI Co-Pilot & RAG (`/ai`)
- `POST /ai/chat`: Interactive conversational Co-Pilot with live system context injection.
- `GET /ai/explain/{id}`: RAG-backed plain-language risk breakdown for a specific shipment.
- `GET /ai/status`: Health and configuration status of Gemini and rate limit quotas.

### 🌍 External Intelligence (`/external-intelligence`)
- `POST /external-intelligence/sync`: Trigger live sync with Open-Meteo, Frankfurter, and Nager.Date.
- `GET /external-intelligence/weather`: Current weather and severe alerts for maritime gateways.
- `GET /external-intelligence/ports`: Congestion levels and vessel berth wait metrics.

---

## 7. 🛡️ Security & Rate Limiting Architecture

1. **Sliding-Window Rate Limiting**:
   - In-memory thread-safe rate limiter tracking per-minute, per-hour, and per-day usage.
   - Enforces provider daily quotas (e.g., Gemini 1,000 requests/day).
   - Injects standard RFC rate limit headers (`X-RateLimit-Limit-Minute`, `X-RateLimit-Remaining-Minute`, `Retry-After`).
2. **HTTP Security Headers**:
   - `Content-Security-Policy`: Protects against cross-site scripting (XSS).
   - `X-Frame-Options: SAMEORIGIN`: Protects against clickjacking.
   - `X-Content-Type-Options: nosniff`: Prevents MIME-type sniffing.
   - `Referrer-Policy: strict-origin-when-cross-origin`.
3. **Password Security**:
   - Industry-standard `bcrypt` hashing with salt rounds.

---

## 8. 🚢 DevOps, Docker & CI/CD Pipeline

### Multi-Stage Dockerfile Architecture
```dockerfile
# Stage 1: Build React 19 Frontend with Vite
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Serve Python Backend and SPA
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt /app/backend/
RUN pip install --no-cache-dir -r /app/backend/requirements.txt
COPY backend/ /app/backend/
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist
RUN mkdir -p /app/data
ENV PYTHONPATH=/app/backend DATABASE_URL=sqlite:////app/data/shipguard.db PORT=8000
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### GitHub Actions CI/CD Pipeline (`.github/workflows/deploy.yml`)
- **Stage 1 (Test & Build Check)**:
  1. Checks out repository.
  2. Sets up Python 3.11 & runs backend unit tests (`pytest`).
  3. Sets up Node.js 20 & compiles frontend bundle (`npm run build`).
- **Stage 2 (Automated VPS Deployment)**:
  1. Triggers on `push` to `main` branch.
  2. Connects via SSH to Hostinger VPS (`appleboy/ssh-action`).
  3. Pulls latest changes, executes `docker compose build --pull`, and restarts containers.
  4. Runs healthcheck verification at `http://127.0.0.1:8000/health`.

---

## 9. 🚀 Local Development Quickstart

### Backend Setup (PowerShell / Bash)
```bash
cd backend
python -m venv .venv

# On Windows:
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt
python -m app.ml.train_model
uvicorn app.main:app --reload --port 8000
```
- API Documentation (Swagger UI): `http://localhost:8000/docs`
- Demo Credentials:
  - **Email**: `ops@shipguard.local`
  - **Password**: `shipguard123`

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
- Web Application: `http://localhost:5173`
