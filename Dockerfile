# ---------- Frontend build ----------
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---------- Runtime ----------
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=7860 \
    PIP_NO_CACHE_DIR=1

# System deps for Chromium/Chromedriver & fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl wget gnupg ca-certificates xdg-utils unzip \
    libnss3 libasound2 libatk-bridge2.0-0 libatk1.0-0 \
    libdrm2 libxkbcommon0 libx11-xcb1 libxcomposite1 libxcursor1 libxi6 \
    libxrandr2 libxdamage1 libgbm1 libgtk-3-0 fonts-liberation \
    libxshmfence1 libxfixes3 \
    chromium chromium-driver \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# NOTE: If your requirements.txt lives here (Railway_Fair_finder/requirements.txt), this is correct
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

# App source
COPY . /app
# Copy built frontend
COPY --from=frontend-builder /app/frontend/dist /app/static

# Runtime env
ENV CHROME_BIN=/usr/bin/chromium \
    CHROMEDRIVER=/usr/bin/chromedriver \
    STATIC_DIR=/app/static

EXPOSE 7860

CMD ["sh", "-c", "uvicorn app_entry:app --host 0.0.0.0 --port ${PORT:-7860}"]