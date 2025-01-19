import argparse
import os
import sys
from cache_benchmark.utils import set_env_vars, set_env_cache_retry, generate_string, init_cache_set, locust_runner_cash_benchmark, locust_master_runner_benchmark, locust_worker_runner_benchmark
from cache_benchmark.args import add_common_arguments
from cache_benchmark.cash_connect import CacheConnect
from cache_benchmark.scenario import RedisUser
import locust
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

@locust.events.init.add_listener
def on_locust_init(environment, **kwargs):
    cache = CacheConnect()
    if kwargs.get('cache_type'):
        if kwargs.get('cache_type') == "redis_cluster":
            logger.info("Locust environment redis_conn initialized.")
            environment.cache_conn = cache.redis_connect()
        elif kwargs.get('cache_type') == "valkey_cluster":
            logger.info("Locust environment valkey_conn initialized.")
            environment.cache_conn = cache.valkey_connect()


def redis_load_test(args):
    set_env_vars(args)
    set_env_cache_retry(args)
    locust_runner_cash_benchmark(args,RedisUser)

def valkey_load_test(args):
    set_env_vars(args)
    set_env_cache_retry(args)
    locust_runner_cash_benchmark(args,RedisUser)

def cluster_redis_load_test(args):
    if args.cluster_mode is None:
        logger.error("Cluster mode not provided.")
        logger.error("Please provide the --cluster-mode. master or worker")
        sys.exit(1)
    if args.cluster_mode == "master":
        set_env_vars(args)
        set_env_cache_retry(args)
        locust_master_runner_benchmark(args,RedisUser)
    elif args.cluster_mode == "worker":
        set_env_vars(args)
        set_env_cache_retry(args)
        locust_worker_runner_benchmark(args,RedisUser)
    else:
        logger.error("Invalid cluster mode provided.")
        logger.error("Please provide the --cluster-mode. master or worker")
        sys.exit(1)

def init_valkey_load_test(args):
    set_env_vars(args)
    set_env_cache_retry(args)
    cache = CacheConnect()
    cache_client = cache.valkey_connect()
    if cache_client is None:
        logger.error("Redis client initialization failed.")
        sys.exit(1)
    value = generate_string(args.value_size)
    init_cache_set(cache_client, value, int(os.environ["TTL"]))

def init_redis_load_test(args):
    set_env_vars(args)
    set_env_cache_retry(args)
    cache = CacheConnect()
    cache_client = cache.redis_connect()
    if cache_client is None:
        logger.error("Redis client initialization failed.")
        sys.exit(1)
    value = generate_string(args.value_size)
    init_cache_set(cache_client, value, int(os.environ["TTL"]))

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

    args = parser.parse_args()
    if args.command and args.subcommand:
        args.func(args)
    else:
        parser.print_help()
        sys.exit(1)
if __name__ == "__main__":
    main()
