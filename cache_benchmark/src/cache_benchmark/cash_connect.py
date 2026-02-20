from redis import Redis
from redis.cluster import RedisCluster, ClusterDownError, ClusterNode
from redis.exceptions import TimeoutError, ConnectionError
from valkey import Valkey
from valkey.cluster import ValkeyCluster as ValkeyCluster, ClusterNode as ValleyClusterNode, ClusterDownError as ValkeyClusterDownError
from valkey.exceptions import ConnectionError as ValkeyConnectionError, TimeoutError as ValkeyTimeoutError
from cache_benchmark.config import get_config
import logging


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

        logging.info(f"Creating Redis connection with pool size: {pool_size}")
        logging.info(f"Connecting to Redis cluster at {cache_host}:{cache_port} SSL={ssl}")

        if not cache_host or not cache_port:
            logging.error("cache_host and cache_port must be set in AppConfig.")
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
                # Facilitates reuse of connections
                connection_pool_kwargs={
                    'retry_on_timeout': True,
                    'socket_keepalive': True,
                    'socket_keepalive_options': {},
                },
                **extra_kwargs,
            )
            logging.info("Redis connection established successfully")
        except ClusterDownError as e:
            logging.error(f"Cluster is down. Retrying...: {e}")
            conn = None
        except TimeoutError as e:
            logging.error(f"Timeout error during Redis initialization: {e}")
            conn = None
        except ConnectionError as e:
            logging.error(f"Connection error: {e}")
            conn = None
        except Exception as e:
            logging.error(f"Unexpected error during Redis initialization: {e}")
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

        logging.info(f"Creating Redis standalone connection with pool size: {pool_size}")
        logging.info(f"Connecting to Redis standalone at {cache_host}:{cache_port} SSL={ssl}")

        if not cache_host or not cache_port:
            logging.error("cache_host and cache_port must be set in AppConfig.")
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
                **extra_kwargs,
            )
            conn.ping()
            logging.info("Redis standalone connection established successfully")
        except TimeoutError as e:
            logging.error(f"Timeout error during Redis standalone initialization: {e}")
            conn = None
        except ConnectionError as e:
            logging.error(f"Connection error: {e}")
            conn = None
        except Exception as e:
            logging.error(f"Unexpected error during Redis standalone initialization: {e}")
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

        logging.info(f"Creating Valkey connection with pool size: {pool_size}")
        logging.info(f"Connecting to Valkey cluster at {cache_host}:{cache_port} SSL={ssl}")

        if not cache_host or not cache_port:
            logging.error("cache_host and cache_port must be set in AppConfig.")
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
                # Facilitates reuse of connections
                connection_pool_kwargs={
                    'retry_on_timeout': True,
                    'socket_keepalive': True,
                    'socket_keepalive_options': {},
                },
                **extra_kwargs,
            )
            logging.info("Valkey connection established successfully")
        except ValkeyClusterDownError as e:
            logging.error(f"Cluster is down. Retrying...: {e}")
            conn = None
        except ValkeyTimeoutError as e:
            logging.error(f"Timeout error during Valkey initialization: {e}")
            conn = None
        except ValkeyConnectionError as e:
            logging.error(f"Connection error: {e}")
            conn = None
        except Exception as e:
            logging.error(f"Unexpected error during Valkey initialization: {e}")
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

        logging.info(f"Creating Valkey standalone connection with pool size: {pool_size}")
        logging.info(f"Connecting to Valkey standalone at {cache_host}:{cache_port} SSL={ssl}")

        if not cache_host or not cache_port:
            logging.error("cache_host and cache_port must be set in AppConfig.")
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
                **extra_kwargs,
            )
            conn.ping()
            logging.info("Valkey standalone connection established successfully")
        except ValkeyTimeoutError as e:
            logging.error(f"Timeout error during Valkey standalone initialization: {e}")
            conn = None
        except ValkeyConnectionError as e:
            logging.error(f"Connection error: {e}")
            conn = None
        except Exception as e:
            logging.error(f"Unexpected error during Valkey standalone initialization: {e}")
            conn = None
        return conn
