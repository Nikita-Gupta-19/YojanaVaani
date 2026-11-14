FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend:/app \
    PORT=8000 \
    DATABASE_URL="sqlite:////app/yojanavaani.db"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    tesseract-ocr \
    tesseract-ocr-hin \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY requirements-cloud.txt .
RUN pip install --no-cache-dir --default-timeout=120 -r requirements-cloud.txt

COPY backend /app/backend
COPY data-pipeline /app/data-pipeline

RUN mkdir -p /app/uploads && chmod -R 777 /app

EXPOSE 8000 7860

CMD ["sh", "-c", "uvicorn app.main:app --app-dir /app/backend --host 0.0.0.0 --port ${PORT:-8000}"]
