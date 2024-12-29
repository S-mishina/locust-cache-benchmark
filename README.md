
# redis-benchmark

**redis-benchmark** is a tool designed to test the performance of Redis clusters. It uses Locust for load testing and measures metrics such as response time and cache hit rate for Redis clusters.

## Features

- Executes load tests on Redis clusters
- Allows configuration of parameters such as cache hit rate, value size, and TTL
- Displays test results in real-time

## Supported Environments

This tool currently supports Redis (Cluster Mode only).

## Processing Flow

![architecture](./image/architecture.png)

## attention

- About request volume
  - In the creator's environment, the volume of requests is known to be about 700 req/sec more than the overall expected capacity. (Cache hit rate is the same) Therefore, it is required to take this into account before implementation.
    - In the author's environment, I dropped 700 req/sec and set up connection, and it executed as expected.
- About this tool
  - This tool uses the init and loadtest commands to achieve load testing. This tool can be executed using workflow, but a dependency between the init and loadtest commands is necessary because if the init is done on a job running in parallel, a useless set for redis will be executed.

## Installation

### Local Machine

Install the necessary dependencies using the following command:

```sh
pip install -r redis-benchmark/requirements.txt
```

### Container

Build and run the Docker container using the command below:

```sh
docker pull ghcr.io/s-mishina/locust-redis-benchmark:latest
```

## Usage

### Local Machine

To initialize a Redis cluster, run the following command:

```sh
python redis-benchmark/src/redis_benchmark/main.py init redis -f <hostname> -p <port>
```

To execute a load test on a Redis cluster, use the command:

```sh
python redis-benchmark/src/redis_benchmark/main.py loadtest redis -f <hostname> -p <port> -r <hit_rate> -d <duration> -c <connections> -n <requests> -k <value_size> -t <ttl>
```

### Container

To initialize a Redis cluster, use the following command:

```sh
docker run --rm -it ghcr.io/s-mishina/locust-redis-benchmark:latest python redis-benchmark/src/redis_benchmark/main.py init redis -f <hostname> -p <port>
```

To execute a load test on a Redis cluster, run:

```sh
docker run --rm -it ghcr.io/s-mishina/locust-redis-benchmark:latest python redis-benchmark/src/redis_benchmark/main.py loadtest redis -f <hostname> -p <port> -r <hit_rate> -d <duration> -c <connections> -n <requests> -k <value_size> -t <ttl>
```

## Parameters

- `--fqdn, -f`: Hostname of the Redis server (default: `localhost`)
- `--port, -p`: Port of the Redis server (default: `6379`)
- `--hit-rate, -r`: Cache hit rate (default: `0.5`)
- `--duration, -d`: Test duration in seconds (default: `60`)
- `--connections, -c`: Number of concurrent connections (default: `1`)
- `--requests, -n`: Number of requests to send (default: `1000`)
- `--value-size, -k`: Value size in KB (default: `1`)
- `--ttl, -t`: Time-to-live of the key in seconds (default: `60`)

## thips

### It takes time for cloud vendor metrics to appear during the test

If you are using a monitoring tool (e.g., datadog), you can enable redis integration to speed up the data acquisition time by running the redis command to acquire the data.

### I would like to see how you are hitting redis in addition to locust's standard output as a TRACE

This tool will be otel compatible; once otel is supported, you will be able to use otel to check trace.
