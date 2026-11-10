FROM rust:1.95-slim AS verifier
RUN apt-get update && apt-get install -y --no-install-recommends git pkg-config libssl-dev libudev-dev ca-certificates build-essential && rm -rf /var/lib/apt/lists/*
RUN cargo install --git https://github.com/out-layer/outlayer-verify outlayer-verify --locked
RUN cargo install near-cli-rs --version 0.31.1 --locked

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=verifier /usr/local/cargo/bin/outlayer-verify /usr/local/bin/outlayer-verify
COPY --from=verifier /usr/local/cargo/bin/near /usr/local/bin/near
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt
COPY agent /app/agent
COPY backend /app/backend
WORKDIR /app/backend
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
