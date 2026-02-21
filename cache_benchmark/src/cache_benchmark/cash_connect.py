from redis import Redis
from redis.cluster import RedisCluster, ClusterDownError, ClusterNode
from redis.exceptions import TimeoutError, ConnectionError
from redis.retry import Retry
from redis.backoff import ExponentialBackoff
from valkey import Valkey
from valkey.cluster import ValkeyCluster as ValkeyCluster, ClusterNode as ValleyClusterNode, ClusterDownError as ValkeyClusterDownError
from valkey.exceptions import ConnectionError as ValkeyConnectionError, TimeoutError as ValkeyTimeoutError
from valkey.retry import Retry as ValkeyRetry
from valkey.backoff import EqualJitterBackoff
from cache_benchmark.config import get_config
import logging

logger = logging.getLogger(__name__)


class CacheConnect:
    @staticmethod
    def _build_auth_ssl_kwargs():
        """Build extra kwargs for authentication and SSL certificate settings."""
        cfg = get_config()
        kwargs = {}
        if cfg.cache_password is not None:
            kwargs["password"] = cfg.cache_password
        if cfg.cache_username is not None:
            kwargs["username"] = cfg.cache_username
        if cfg.ssl_cert_reqs is not None:
            kwargs["ssl_cert_reqs"] = cfg.ssl_cert_reqs
        if cfg.ssl_ca_certs is not None:
            kwargs["ssl_ca_certs"] = cfg.ssl_ca_certs
        return kwargs

    def redis_connect(self):
        """
        Initializes a connection to the Redis cluster.

        Returns:
            RedisCluster: Redis cluster connection object.
        """
        cfg = get_config()
        cache_host = cfg.cache_host
        cache_port = cfg.cache_port
        pool_size = cfg.connections_pool
        ssl = cfg.ssl
        query_timeout = cfg.query_timeout
        retry_attempts = cfg.retry_attempts
        retry_wait = cfg.retry_wait

        logger.info(f"Creating Redis connection with pool size: {pool_size}")
        logger.info(f"Connecting to Redis cluster at {cache_host}:{cache_port} SSL={ssl}")

        if not cache_host or not cache_port:
            logger.error("cache_host and cache_port must be set in AppConfig.")
            return None

        extra_kwargs = CacheConnect._build_auth_ssl_kwargs()
        startup_nodes = [
            ClusterNode(cache_host, int(cache_port))
        ]
        try:
            conn = RedisCluster(
                startup_nodes=startup_nodes,
                decode_responses=True,
                timeout=int(query_timeout),
                ssl=ssl,
                max_connections=pool_size,
                retry=Retry(ExponentialBackoff(cap=retry_wait, base=0.5), retries=retry_attempts),
                # Facilitates reuse of connections
                connection_pool_kwargs={
                    'socket_keepalive': True,
                    'socket_keepalive_options': {},
                },
                **extra_kwargs,
            )
            logger.info("Redis connection established successfully")
        except ClusterDownError as e:
            logger.error(f"Cluster is down. Retrying...: {e}")
            conn = None
        except TimeoutError as e:
            logger.error(f"Timeout error during Redis initialization: {e}")
            conn = None
        except ConnectionError as e:
            logger.error(f"Connection error: {e}")
            conn = None
        except Exception as e:
            logger.error(f"Unexpected error during Redis initialization: {e}")
            conn = None
        return conn

    def redis_standalone_connect(self):
        """
        Initializes a connection to a standalone Redis instance.

        Returns:
            Redis: Redis connection object, or None on failure.
        """
        cfg = get_config()
        cache_host = cfg.cache_host
        cache_port = cfg.cache_port
        pool_size = cfg.connections_pool
        ssl = cfg.ssl
        query_timeout = cfg.query_timeout
        retry_attempts = cfg.retry_attempts
        retry_wait = cfg.retry_wait

        logger.info(f"Creating Redis standalone connection with pool size: {pool_size}")
        logger.info(f"Connecting to Redis standalone at {cache_host}:{cache_port} SSL={ssl}")

        if not cache_host or not cache_port:
            logger.error("cache_host and cache_port must be set in AppConfig.")
            return None

        extra_kwargs = CacheConnect._build_auth_ssl_kwargs()
        try:
            conn = Redis(
                host=cache_host,
                port=int(cache_port),
                decode_responses=True,
                socket_timeout=int(query_timeout),
                ssl=ssl,
                max_connections=pool_size,
                socket_keepalive=True,
                retry=Retry(ExponentialBackoff(cap=retry_wait, base=0.5), retries=retry_attempts),
                retry_on_error=[ConnectionError, TimeoutError],
                **extra_kwargs,
            )
            conn.ping()
            logger.info("Redis standalone connection established successfully")
        except TimeoutError as e:
            logger.error(f"Timeout error during Redis standalone initialization: {e}")
            conn = None
        except ConnectionError as e:
            logger.error(f"Connection error: {e}")
            conn = None
        except Exception as e:
            logger.error(f"Unexpected error during Redis standalone initialization: {e}")
            conn = None
        return conn

    def valkey_connect(self):
        """
        Initializes a connection to the Valley cluster.

        Returns:
            ValkeyCluster: Valley cluster connection object.
        """
        cfg = get_config()
        cache_host = cfg.cache_host
        cache_port = cfg.cache_port
        pool_size = cfg.connections_pool
        ssl = cfg.ssl
        query_timeout = cfg.query_timeout
        retry_attempts = cfg.retry_attempts
        retry_wait = cfg.retry_wait

        logger.info(f"Creating Valkey connection with pool size: {pool_size}")
        logger.info(f"Connecting to Valkey cluster at {cache_host}:{cache_port} SSL={ssl}")

        if not cache_host or not cache_port:
            logger.error("cache_host and cache_port must be set in AppConfig.")
            return None
        extra_kwargs = CacheConnect._build_auth_ssl_kwargs()
        startup_nodes = [
            ValleyClusterNode(cache_host, int(cache_port))
        ]
        try:
            conn = ValkeyCluster(
                startup_nodes=startup_nodes,
                decode_responses=True,
                timeout=int(query_timeout),
                ssl=ssl,
                max_connections=pool_size,
                cluster_error_retry_attempts=retry_attempts,
                retry=ValkeyRetry(EqualJitterBackoff(cap=retry_wait, base=0.5), retries=retry_attempts),
                # Facilitates reuse of connections
                connection_pool_kwargs={
                    'socket_keepalive': True,
                    'socket_keepalive_options': {},
                },
                **extra_kwargs,
            )
            logger.info("Valkey connection established successfully")
        except ValkeyClusterDownError as e:
            logger.error(f"Cluster is down. Retrying...: {e}")
            conn = None
        except ValkeyTimeoutError as e:
            logger.error(f"Timeout error during Valkey initialization: {e}")
            conn = None
        except ValkeyConnectionError as e:
            logger.error(f"Connection error: {e}")
            conn = None
        except Exception as e:
            logger.error(f"Unexpected error during Valkey initialization: {e}")
            conn = None
        return conn

    def valkey_standalone_connect(self):
        """
        Initializes a connection to a standalone Valkey instance.

        Returns:
            Valkey: Valkey connection object, or None on failure.
        """
        cfg = get_config()
        cache_host = cfg.cache_host
        cache_port = cfg.cache_port
        pool_size = cfg.connections_pool
        ssl = cfg.ssl
        query_timeout = cfg.query_timeout
        retry_attempts = cfg.retry_attempts
        retry_wait = cfg.retry_wait

        logger.info(f"Creating Valkey standalone connection with pool size: {pool_size}")
        logger.info(f"Connecting to Valkey standalone at {cache_host}:{cache_port} SSL={ssl}")

        if not cache_host or not cache_port:
            logger.error("cache_host and cache_port must be set in AppConfig.")
            return None

        extra_kwargs = CacheConnect._build_auth_ssl_kwargs()
        try:
            conn = Valkey(
                host=cache_host,
                port=int(cache_port),
                decode_responses=True,
                socket_timeout=int(query_timeout),
                ssl=ssl,
                max_connections=pool_size,
                socket_keepalive=True,
                retry=ValkeyRetry(EqualJitterBackoff(cap=retry_wait, base=0.5), retries=retry_attempts),
                retry_on_error=[ValkeyConnectionError, ValkeyTimeoutError],
                **extra_kwargs,
            )
            conn.ping()
            logger.info("Valkey standalone connection established successfully")
        except ValkeyTimeoutError as e:
            logger.error(f"Timeout error during Valkey standalone initialization: {e}")
            conn = None
        except ValkeyConnectionError as e:
            logger.error(f"Connection error: {e}")
            conn = None
        except Exception as e:
            logger.error(f"Unexpected error during Valkey standalone initialization: {e}")
            conn = None
        return conn
