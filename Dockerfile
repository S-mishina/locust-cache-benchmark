FROM python:3.13-slim
COPY dist/locust_cache_benchmark-*.whl /
RUN apt -y update && apt --no-install-recommends install gcc && pip install ./locust_cache_benchmark-*.whl && apt clean
