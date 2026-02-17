import argparse
import os
import sys
from cache_benchmark.utils import set_env_vars, set_env_cache_retry, generate_string, init_cache_set, locust_runner_cash_benchmark, locust_master_runner_benchmark, locust_worker_runner_benchmark
from cache_benchmark.args import add_common_arguments
from cache_benchmark.cash_connect import CacheConnect
from cache_benchmark.scenario import RedisUser
from cache_benchmark.otel_setup import setup_otel_tracing, shutdown_otel_tracing
import locust
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

def redis_load_test(args):
    set_env_vars(args)
    set_env_cache_retry(args)
    os.environ["CACHE_TYPE"] = "redis_cluster"
    locust_runner_cash_benchmark(args,RedisUser)

def valkey_load_test(args):
    set_env_vars(args)
    set_env_cache_retry(args)
    os.environ["CACHE_TYPE"] = "valkey_cluster"
    locust_runner_cash_benchmark(args,RedisUser)

def cluster_redis_load_test(args):
    if args.cluster_mode is None:
        logger.error("Cluster mode not provided.")
        logger.error("Please provide the --cluster-mode. master or worker")
        sys.exit(1)
    if args.cluster_mode == "master":
        set_env_vars(args)
        set_env_cache_retry(args)
        os.environ["CACHE_TYPE"] = "redis_cluster"
        locust_master_runner_benchmark(args,RedisUser)
    elif args.cluster_mode == "worker":
        set_env_vars(args)
        set_env_cache_retry(args)
        os.environ["CACHE_TYPE"] = "redis_cluster"
        locust_worker_runner_benchmark(args,RedisUser)
    else:
        logger.error("Invalid cluster mode provided.")
        logger.error("Please provide the --cluster-mode. master or worker")
        sys.exit(1)

def cluster_valkey_load_test(args):
    if args.cluster_mode is None:
        logger.error("Cluster mode not provided.")
        logger.error("Please provide the --cluster-mode. master or worker")
        sys.exit(1)
    if args.cluster_mode == "master":
        set_env_vars(args)
        set_env_cache_retry(args)
        os.environ["CACHE_TYPE"] = "valkey_cluster"
        locust_master_runner_benchmark(args,RedisUser)
    elif args.cluster_mode == "worker":
        set_env_vars(args)
        set_env_cache_retry(args)
        os.environ["CACHE_TYPE"] = "valkey_cluster"
        locust_worker_runner_benchmark(args,RedisUser)
    else:
        logger.error("Invalid cluster mode provided.")
        logger.error("Please provide the --cluster-mode. master or worker")
        sys.exit(1)

def redis_standalone_load_test(args):
    set_env_vars(args)
    set_env_cache_retry(args)
    os.environ["CACHE_TYPE"] = "redis"
    locust_runner_cash_benchmark(args,RedisUser)

def valkey_standalone_load_test(args):
    set_env_vars(args)
    set_env_cache_retry(args)
    os.environ["CACHE_TYPE"] = "valkey"
    locust_runner_cash_benchmark(args,RedisUser)

def cluster_redis_standalone_load_test(args):
    if args.cluster_mode is None:
        logger.error("Cluster mode not provided.")
        logger.error("Please provide the --cluster-mode. master or worker")
        sys.exit(1)
    if args.cluster_mode == "master":
        set_env_vars(args)
        set_env_cache_retry(args)
        os.environ["CACHE_TYPE"] = "redis"
        locust_master_runner_benchmark(args,RedisUser)
    elif args.cluster_mode == "worker":
        set_env_vars(args)
        set_env_cache_retry(args)
        os.environ["CACHE_TYPE"] = "redis"
        locust_worker_runner_benchmark(args,RedisUser)
    else:
        logger.error("Invalid cluster mode provided.")
        logger.error("Please provide the --cluster-mode. master or worker")
        sys.exit(1)

def cluster_valkey_standalone_load_test(args):
    if args.cluster_mode is None:
        logger.error("Cluster mode not provided.")
        logger.error("Please provide the --cluster-mode. master or worker")
        sys.exit(1)
    if args.cluster_mode == "master":
        set_env_vars(args)
        set_env_cache_retry(args)
        os.environ["CACHE_TYPE"] = "valkey"
        locust_master_runner_benchmark(args,RedisUser)
    elif args.cluster_mode == "worker":
        set_env_vars(args)
        set_env_cache_retry(args)
        os.environ["CACHE_TYPE"] = "valkey"
        locust_worker_runner_benchmark(args,RedisUser)
    else:
        logger.error("Invalid cluster mode provided.")
        logger.error("Please provide the --cluster-mode. master or worker")
        sys.exit(1)

def init_redis_standalone_load_test(args):
    set_env_vars(args)
    set_env_cache_retry(args)
    setup_otel_tracing()
    cache = CacheConnect()
    cache_client = cache.redis_standalone_connect()
    if cache_client is None:
        logger.error("Redis standalone client initialization failed.")
        sys.exit(1)
    try:
        value = generate_string(args.value_size)
        init_cache_set(cache_client, value, int(os.environ["TTL"]), args.set_keys)
    finally:
        cache_client.close()
        logger.info("Redis standalone connection closed after init.")
        shutdown_otel_tracing()

def init_valkey_standalone_load_test(args):
    set_env_vars(args)
    set_env_cache_retry(args)
    setup_otel_tracing()
    cache = CacheConnect()
    cache_client = cache.valkey_standalone_connect()
    if cache_client is None:
        logger.error("Valkey standalone client initialization failed.")
        sys.exit(1)
    try:
        value = generate_string(args.value_size)
        init_cache_set(cache_client, value, int(os.environ["TTL"]), args.set_keys)
    finally:
        cache_client.close()
        logger.info("Valkey standalone connection closed after init.")
        shutdown_otel_tracing()

def init_valkey_load_test(args):
    set_env_vars(args)
    set_env_cache_retry(args)
    setup_otel_tracing()
    cache = CacheConnect()
    cache_client = cache.valkey_connect()
    if cache_client is None:
        logger.error("Redis client initialization failed.")
        sys.exit(1)
    try:
        value = generate_string(args.value_size)
        init_cache_set(cache_client, value, int(os.environ["TTL"]), args.set_keys)
    finally:
        cache_client.close()
        logger.info("Valkey connection closed after init.")
        shutdown_otel_tracing()

def init_redis_load_test(args):
    set_env_vars(args)
    set_env_cache_retry(args)
    setup_otel_tracing()
    cache = CacheConnect()
    cache_client = cache.redis_connect()
    if cache_client is None:
        logger.error("Redis client initialization failed.")
        sys.exit(1)
    try:
        value = generate_string(args.value_size)
        init_cache_set(cache_client, value, int(os.environ["TTL"]), args.set_keys)
    finally:
        cache_client.close()
        logger.info("Redis connection closed after init.")
        shutdown_otel_tracing()

def main():
    parser = argparse.ArgumentParser(
        description="A tool to perform load testing of Redis and other systems."
    )
    subparsers = parser.add_subparsers(dest="command")
    # loadtest subcommand
    loadtest_parser = subparsers.add_parser("loadtest", help="Load testing commands")
    loadtest_subparsers = loadtest_parser.add_subparsers(dest="subcommand")
    # loadtest local subcommand
    local_parser = loadtest_subparsers.add_parser("local", help="Run locust Load test locally")
    local_subparsers = local_parser.add_subparsers(dest="subcommand")
    # loadtest local redis subcommand
    local_redis_parser = local_subparsers.add_parser("redis", help="Run load test on Redis locally")
    add_common_arguments(local_redis_parser)
    local_redis_parser.set_defaults(func=redis_load_test)
    # loadtest local valkey subcommand
    local_valkey_parser = local_subparsers.add_parser("valkey", help="Run load test on Valkey locally")
    add_common_arguments(local_valkey_parser)
    local_valkey_parser.set_defaults(func=valkey_load_test)
    # loadtest local redis-standalone subcommand
    local_redis_standalone_parser = local_subparsers.add_parser("redis-standalone", help="Run load test on standalone Redis locally")
    add_common_arguments(local_redis_standalone_parser)
    local_redis_standalone_parser.set_defaults(func=redis_standalone_load_test)
    # loadtest local valkey-standalone subcommand
    local_valkey_standalone_parser = local_subparsers.add_parser("valkey-standalone", help="Run load test on standalone Valkey locally")
    add_common_arguments(local_valkey_standalone_parser)
    local_valkey_standalone_parser.set_defaults(func=valkey_standalone_load_test)
    # loadtest cluster subcommand
    local_parser = loadtest_subparsers.add_parser("cluster", help="Run locust Cluster test locally")
    local_subparsers = local_parser.add_subparsers(dest="subcommand")
    # loadtest cluster redis subcommand
    local_redis_parser = local_subparsers.add_parser("redis", help="Run Cluster test on Redis locally")
    add_common_arguments(local_redis_parser)
    local_redis_parser.set_defaults(func=cluster_redis_load_test)
    # loadtest cluster valkey subcommand
    local_valkey_parser = local_subparsers.add_parser("valkey", help="Run Cluster test on Valkey locally")
    add_common_arguments(local_valkey_parser)
    local_valkey_parser.set_defaults(func=cluster_valkey_load_test)
    # loadtest cluster redis-standalone subcommand
    cluster_redis_standalone_parser = local_subparsers.add_parser("redis-standalone", help="Run Cluster test on standalone Redis")
    add_common_arguments(cluster_redis_standalone_parser)
    cluster_redis_standalone_parser.set_defaults(func=cluster_redis_standalone_load_test)
    # loadtest cluster valkey-standalone subcommand
    cluster_valkey_standalone_parser = local_subparsers.add_parser("valkey-standalone", help="Run Cluster test on standalone Valkey")
    add_common_arguments(cluster_valkey_standalone_parser)
    cluster_valkey_standalone_parser.set_defaults(func=cluster_valkey_standalone_load_test)

    # init subcommand
    init_parser = subparsers.add_parser("init", help="Initialization commands")
    init_subparsers = init_parser.add_subparsers(dest="subcommand")
    # init redis subcommand
    init_redis_parser = init_subparsers.add_parser("redis", help="Initialize Redis")
    add_common_arguments(init_redis_parser)
    init_redis_parser.set_defaults(func=init_redis_load_test)
    # init valkey subcommand
    init_valkey_parser = init_subparsers.add_parser("valkey", help="Initialize Valkey")
    add_common_arguments(init_valkey_parser)
    init_valkey_parser.set_defaults(func=init_valkey_load_test)
    # init redis-standalone subcommand
    init_redis_standalone_parser = init_subparsers.add_parser("redis-standalone", help="Initialize standalone Redis")
    add_common_arguments(init_redis_standalone_parser)
    init_redis_standalone_parser.set_defaults(func=init_redis_standalone_load_test)
    # init valkey-standalone subcommand
    init_valkey_standalone_parser = init_subparsers.add_parser("valkey-standalone", help="Initialize standalone Valkey")
    add_common_arguments(init_valkey_standalone_parser)
    init_valkey_standalone_parser.set_defaults(func=init_valkey_standalone_load_test)

    args = parser.parse_args()
    if args.command and args.subcommand:
        args.func(args)
    else:
        parser.print_help()
        sys.exit(1)
if __name__ == "__main__":
    main()
