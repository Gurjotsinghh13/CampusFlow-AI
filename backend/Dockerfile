FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN adduser --disabled-password --gecos "" appuser \
    && chown -R appuser:appuser /app

EXPOSE 8000

USER appuser
CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"
