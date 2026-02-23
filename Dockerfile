# ---------- Stage 1: builder ----------
FROM python:3.11-slim-bookworm AS builder

COPY dist/locust_cache_benchmark-*.whl /tmp/

# hadolint ignore=DL3008
RUN apt-get update \
    && apt-get install --no-install-recommends -y gcc build-essential \
    && pip install --no-cache-dir /tmp/locust_cache_benchmark-*.whl \
    && rm /tmp/locust_cache_benchmark-*.whl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# distroless の Python は /usr/bin/python3 にあるため shebang を修正
RUN sed -i '1s|#!.*python.*|#!/usr/bin/python3|' /usr/local/bin/locust_cache_benchmark /usr/local/bin/locust

# ---------- Stage 2: runtime ----------
FROM gcr.io/distroless/python3-debian12:nonroot

# pip でインストールしたパッケージ
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/lib/python3/dist-packages/

# CLI エントリポイント
COPY --from=builder /usr/local/bin/locust_cache_benchmark /usr/local/bin/
COPY --from=builder /usr/local/bin/locust /usr/local/bin/

ENV PYTHONPATH=/usr/lib/python3/dist-packages
ENV LANG=C.UTF-8
