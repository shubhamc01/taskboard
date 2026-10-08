FROM python:3.14-slim AS build

WORKDIR /build
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir --prefix=/install -r requirements.txt gunicorn

FROM python:3.14-slim AS runtime

RUN groupadd --gid 10001 app \
    && useradd --uid 10001 --gid app --create-home --shell /usr/sbin/nologin app

COPY --from=build /install /usr/local
WORKDIR /app
COPY --chown=app:app . .

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER app
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/healthz', timeout=3).close()"]

# Assumes the Flask application is exposed as app in app.py.
# Persist state in external stores/volumes: the container filesystem is ephemeral.
# A single EC2 host has no HA; scaling requires a larger host or re-architecture.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
