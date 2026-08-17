# ShipGuard

Shipment Delay Risk & Exception Predictor for freight forwarding operations.

## Stack

- Frontend: React + Vite
- Backend: FastAPI
- Database: Oracle for production schema, SQLite for local demo/dev
- ML: scikit-learn-compatible scoring design with a deterministic fallback model for easy demos

## Quick Start

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.ml.train_model
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

Demo login:

- Email: `ops@shipguard.local`
- Password: `shipguard123`

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:5173

## Notes

- `database/schema.sql` is the Oracle DDL aligned to the corrected PRD/TRD.
- The backend uses SQLite by default so the app can run immediately without Oracle setup.
- Set `DATABASE_URL=oracle://...` and the Oracle environment variables from `backend/.env.example` when wiring to Oracle Autonomous DB.
- `scikit-learn` is optional in this scaffold because Python 3.14 may not have prebuilt wheels yet. Use Python 3.11/3.12 if you want to add a trained classifier artifact.

## Secrets & local env

- Do NOT commit real API keys or secrets into the repository. Use the provided `.env.example` files as placeholders.
- For local development create a `.env` in `backend/` (gitignored) with your NVIDIA key:

```
NVIDIA_API_KEY=sk-<your-real-key>
```

- Alternatively set the env var in PowerShell before starting the backend:

```powershell
$env:NVIDIA_API_KEY = "sk-..."
$env:PYTHONPATH = "C:\Users\mahan\shipguard (fresa technologies)\backend"
python -m uvicorn app.main:app --reload
```

The backend reads `.env` via Pydantic `BaseSettings`; keys should remain local and out of source control.
