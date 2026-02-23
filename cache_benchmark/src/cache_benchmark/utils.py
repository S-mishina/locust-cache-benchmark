import csv
import logging
import sys
import gevent
from opentelemetry import trace
from locust.env import Environment
from locust.runners import LocalRunner, MasterRunner, WorkerRunner
from locust import constant_throughput
import time
from cache_benchmark.otel_setup import setup_otel_tracing, shutdown_otel_tracing

_tracer = trace.get_tracer("locust-cache-benchmark")

logger = logging.getLogger(__name__)

def generate_string(size_in_kb):
    """
    Generates a string of a given size in kilobytes.

    Args:
        size_in_kb (int): Size of the string in kilobytes.

    Returns:
        str: Generated string.
    """
    return "A" * (int(size_in_kb) * 1024)

def init_cache_set(cache_client, value, ttl, set_keys=1000):
    """
    Initializes the Redis cache with a set of keys.

    Args:
        cache_client (RedisCluster): Redis cluster connection object.
        value (str): Value to set in Redis.
        ttl (int): Time-to-live for the keys in seconds.
        set_keys (int): Number of keys to set in the cache (default: 1000).
    """
    if cache_client is not None:
        logger.info("Redis client initialized successfully.")
        logger.info(f"Populating cache with {set_keys} keys...")
        with _tracer.start_as_current_span("init_cache_set", kind=trace.SpanKind.CLIENT) as span:
            span.set_attribute("cache.set_keys", set_keys)
            try:
                for i in range(1, set_keys + 1):
                    key = f"key_{i}"
                    if cache_client.get(key) is None:
                        cache_client.set(key, value, ex=int(ttl))
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                logger.error(f"Error during cache initialization: {e}")
                sys.exit(1)
        logger.info("Success")
    else:
        logger.error("Cache client initialization failed.")
        sys.exit(1)

def save_results_to_csv(stats, filename="test_results.csv"):
    """
    Saves the test results to a CSV file.

    Args:
        stats (Stats): Locust stats object.
        filename (str): Name of the CSV file to save the results to.
    """
    with open(filename, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Request Name", "Total Requests", "Failures", "Average Response Time",
                         "Min Response Time", "Max Response Time", "RPS"])
        for name, entry in stats.entries.items():
            writer.writerow([
                name,
                entry.num_requests,
                entry.num_failures,
                entry.avg_response_time,
                entry.min_response_time,
                entry.max_response_time,
                entry.current_rps
            ])

def _log_stats(stats):
    for (request_type, name), entry in stats.entries.items():
        logger.info(
            "stats",
            extra={
                "request_name": name,
                "request_type": request_type,
                "num_requests": entry.num_requests,
                "num_failures": entry.num_failures,
                "avg_response_time": round(entry.avg_response_time, 2),
                "min_response_time": round(entry.min_response_time or 0, 2),
                "max_response_time": round(entry.max_response_time or 0, 2),
                "current_rps": round(entry.current_rps, 2),
            },
        )

def locust_runner_cash_benchmark(config, redisuser):
    setup_otel_tracing()
    redisuser.wait_time = constant_throughput(config.request_rate)
    env = Environment(user_classes=[redisuser])
    runner = LocalRunner(env)
    redisuser.host = f"http://{config.cache_host}:{config.cache_port}"
    runner.start(user_count=config.connections, spawn_rate=config.spawn_rate)
    logger.info("Starting Locust load test...")
    gevent.sleep(config.duration)
    runner.quit()
    _log_stats(env.stats)
    logger.info("Load test completed.")
    save_results_to_csv(env.stats, filename="redis_test_results.csv")
    shutdown_otel_tracing()

def locust_master_runner_benchmark(config, redisuser):
    """
    Run Locust in Master mode.
    """
    setup_otel_tracing()
    redisuser.wait_time = constant_throughput(config.request_rate)
    env = Environment(user_classes=[redisuser])
    runner = MasterRunner(env, master_bind_host=config.master_bind_host, master_bind_port=config.master_bind_port)
    logger.info("Master is waiting for workers to connect...")
    while len(runner.clients) < config.num_workers:
        logger.info(f"Waiting for workers... ({len(runner.clients)}/{config.num_workers} connected)")
        time.sleep(1)
    logger.info(f"All {config.num_workers} workers are connected. Starting the load test...")
    runner.start(user_count=config.connections, spawn_rate=config.spawn_rate)
    logger.info("Starting Locust load test in Master mode...")
    gevent.sleep(config.duration)
    runner.quit()
    _log_stats(env.stats)
    logger.info("Load test completed.")
    save_results_to_csv(env.stats, filename="redis_test_results_master.csv")
    shutdown_otel_tracing()

def locust_worker_runner_benchmark(config, redisuser):
    """
    Run Locust in Worker mode.
    """
    setup_otel_tracing()
    redisuser.wait_time = constant_throughput(config.request_rate)
    env = Environment(user_classes=[redisuser])

    runner = WorkerRunner(env, master_host=config.master_bind_host, master_port=config.master_bind_port)

    logger.info(f"Worker connecting to Master at {config.master_bind_host}:{config.master_bind_port}...")
    runner.greenlet.join()

    logger.info("Worker load test completed.")
    shutdown_otel_tracing()
