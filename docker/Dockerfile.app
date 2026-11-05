# Dockerfile for SCADA SUT Core (FastAPI + Modbus TCP + SQLite Historian)
FROM python:3.11-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 8000
EXPOSE 5020

ENV PORT=8000
ENV MODBUS_PORT=5020
ENV DATABASE_URL=sqlite:///./scada_historian.db
ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "app.main"]

