# syntax=docker/dockerfile:1

# python:3.12-slim (Debian/glibc) — NOT alpine.
# uvicorn[standard] bundles uvloop, a C extension that requires glibc.
# alpine uses musl libc and will fail to compile uvloop.
# slim is ~50 MB vs the full image at ~900 MB.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependency layer before source — cached independently of source code changes.
# If requirements.txt is unchanged, pip install is skipped on rebuild.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application source
COPY . .

# Non-root user for security.
# mkdir /app/data before switching user so Docker copies its ownership into the
# named volume on first mount (empty volume inherits the image directory's owner).
RUN adduser --system --no-create-home --group appuser \
    && chown -R appuser:appuser /app \
    && mkdir -p /app/data \
    && chown appuser:appuser /app/data

USER appuser

EXPOSE 8000 8501
# No CMD — docker-compose overrides this per service (api vs ui).
