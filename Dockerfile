# Multi-stage: build React UI, then run FastAPI (one service on Render)
FROM node:22-bookworm-slim AS frontend
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

FROM python:3.12-slim-bookworm
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=10000

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=frontend /web/dist ./web/dist

# Optional: uncomment for server-side PDF export on Render
# RUN apt-get update && apt-get install -y --no-install-recommends libreoffice-writer \
#     && rm -rf /var/lib/apt/lists/*

EXPOSE 10000
CMD ["sh", "-c", "uvicorn sads.api:app --host 0.0.0.0 --port ${PORT}"]
