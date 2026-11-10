# Multi-stage Containerfile using Red Hat Universal Base Image (UBI)
# Stage 1: Builder - install dependencies and download VADER lexicon
FROM registry.access.redhat.com/ubi9/python-311:9.8-1779945715 AS builder

ARG APP_VERSION=1.0.0
ENV APP_VERSION=${APP_VERSION}

USER 0

RUN python3.11 -m venv /opt/app-venv

ENV PATH="/opt/app-venv/bin:$PATH"

COPY requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

RUN python -c "from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer; SentimentIntensityAnalyzer()" && \
    echo "VADER lexicon downloaded and cached"

# Stage 1.5: Test stage with test dependencies
FROM builder AS test

COPY requirements-test.txt .
RUN pip install --no-cache-dir -r requirements-test.txt

COPY app/ ./app/
COPY tests/ ./tests/

# Clear ENTRYPOINT so pytest can be run directly
ENTRYPOINT []

# Stage 2: Runtime - minimal image with application
FROM registry.access.redhat.com/ubi9/ubi-minimal:9.8-1794186349 AS runtime

ARG APP_VERSION=1.0.0
ARG BUILD_DATE
ARG PORT=8080

ENV APP_VERSION=${APP_VERSION:-1.0.0} \
    BUILD_DATE=${BUILD_DATE} \
    PORT=${PORT:-8080} \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/app-venv/bin:$PATH"

LABEL name="sentiment-analyzer" \
      version="${APP_VERSION}" \
      description="Sentiment Analyzer for Reviews using VADER" \
      maintainer="DO188 Student" \
      build-date="${BUILD_DATE}" \
      io.openshift.expose-services="${PORT}:http" \
      io.k8s.description="Flask application for sentiment analysis of product/movie reviews" \
      io.k8s.display-name="Sentiment Analyzer" \
      io.openshift.tags="python,flask,sentiment,vader"

RUN microdnf install -y python3.11 shadow-utils iproute && \
    microdnf clean all && \
    rm -rf /var/cache/yum

COPY --from=builder /opt/app-venv /opt/app-venv

RUN useradd -u 1001 -r -g 0 -d /app -s /sbin/nologin \
      -c "Application user" appuser && \
    mkdir -p /app && \
    chown -R 1001:0 /app && \
    chmod -R g=u /app

WORKDIR /app

COPY --chown=1001:0 app/ ./app/

USER 1001

EXPOSE ${PORT}

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python3.11 -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/health').read()" || exit 1

ENTRYPOINT ["gunicorn"]
CMD ["--workers", "2", "--timeout", "60", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
