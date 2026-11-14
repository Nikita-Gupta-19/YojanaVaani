FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend:/app \
    PORT=7860 \
    HF_HUB_OFFLINE=0 \
    DATABASE_URL="sqlite:////app/yojanavaani.db"

WORKDIR /app

# Install system dependencies including Tesseract OCR (Hindi + English), ffmpeg, curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    tesseract-ocr \
    tesseract-ocr-hin \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch CPU first to keep image lightweight and fast
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Copy requirements and install
COPY requirements-cloud.txt .
RUN pip install --no-cache-dir --default-timeout=120 -r requirements-cloud.txt

# Copy backend and data-pipeline code
COPY backend /app/backend
COPY data-pipeline /app/data-pipeline

# Pre-create directory for uploaded docs and SQLite db permissions
RUN mkdir -p /app/uploads && chmod -R 777 /app

EXPOSE 10000 8000 7860

CMD ["sh", "-c", "uvicorn app.main:app --app-dir /app/backend --host 0.0.0.0 --port ${PORT:-10000}"]

