# ==========================================
# Stage 1: Frontend Build (Vite + React 19)
# ==========================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# ==========================================
# Stage 2: Production Python Backend & SPA
# ==========================================
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install backend Python dependencies
COPY backend/requirements.txt /app/backend/
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy backend application code
COPY backend/ /app/backend/

# Copy compiled frontend assets from Stage 1 so FastAPI serves SPA
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Set working directory to backend
WORKDIR /app/backend

# Configure runtime environment
ENV PYTHONPATH=/app/backend \
    DATABASE_URL=sqlite:////app/backend/shipguard.db \
    JWT_SECRET=shipguard-prod-jwt-secret-key \
    PORT=8000

EXPOSE 8000

# Start FastAPI application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
