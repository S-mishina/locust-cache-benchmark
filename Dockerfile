FROM python:3.13-slim
COPY dist/locust_cache_benchmark-*.whl /
RUN <<EOF
    apt-get update && \
    apt-get install --no-install-recommends -y \
      gcc \
      build-essential && \
    pip install ./locust_cache_benchmark-*.whl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    rm ./locust_cache_benchmark-*.whl
EOF
