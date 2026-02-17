from redis import Redis
from redis.cluster import RedisCluster, ClusterDownError, ClusterNode
from redis.exceptions import TimeoutError, ConnectionError
from valkey import Valkey
from valkey.cluster import ValkeyCluster as ValkeyCluster, ClusterNode as ValleyClusterNode, ClusterDownError as ValkeyClusterDownError
from valkey.exceptions import ConnectionError as ValkeyConnectionError, TimeoutError as ValkeyTimeoutError
import os
import logging


def strtobool(val):
    val = str(val).strip().lower()
    if val in ('y', 'yes', 't', 'true', 'on', '1'):
        return 1
    elif val in ('n', 'no', 'f', 'false', 'off', '0'):
        return 0
    else:
        raise ValueError(f"invalid truth value {val!r}")


class CacheConnect:
    def redis_connect(self):
        """
        Initializes a connection to the Redis cluster.

        Returns:
            RedisCluster: Redis cluster connection object.
        """
        redis_host = os.environ.get("REDIS_HOST")
        redis_port = os.environ.get("REDIS_PORT")
        connections_pool = os.environ.get("CONNECTIONS_POOL", "10")
        ssl = os.environ.get("SSL")
        query_timeout = os.environ.get("QUERY_TIMEOUT", "5")

        pool_size = int(connections_pool)

        logging.info(f"Creating Redis connection with pool size: {pool_size}")
        logging.info(f"Connecting to Redis cluster at {redis_host}:{redis_port} SSL={ssl}")

        if not redis_host or not redis_port:
            logging.error("Environment variables REDIS_HOST and REDIS_PORT must be set.")
            return None

        startup_nodes = [
            ClusterNode(redis_host, int(redis_port))
        ]
        try:
            conn = RedisCluster(
                startup_nodes=startup_nodes,
                decode_responses=True,
                timeout=int(query_timeout),
                ssl=bool(strtobool(ssl)),
                max_connections=pool_size,
                ssl_cert_reqs=None,
                # Facilitates reuse of connections
                connection_pool_kwargs={
                    'retry_on_timeout': True,
                    'socket_keepalive': True,
                    'socket_keepalive_options': {},
                }
            )
            logging.info("Redis connection established successfully")
        except ClusterDownError as e:
            logging.warning(f"Cluster is down. Retrying...: {e}")
            conn = None
        except TimeoutError as e:
            logging.warning(f"Timeout error during Redis initialization: {e}")
            conn = None
        except ConnectionError as e:
            logging.warning(f"Connection error: {e}")
            conn = None
        except Exception as e:
            logging.warning(f"Unexpected error during Redis initialization: {e}")
            conn = None
        return conn

    def redis_standalone_connect(self):
        """
        Initializes a connection to a standalone Redis instance.

        Returns:
            Redis: Redis connection object, or None on failure.
        """
        redis_host = os.environ.get("REDIS_HOST")
        redis_port = os.environ.get("REDIS_PORT")
        connections_pool = os.environ.get("CONNECTIONS_POOL", "10")
        ssl = os.environ.get("SSL")
        query_timeout = os.environ.get("QUERY_TIMEOUT", "5")

        pool_size = int(connections_pool)

        logging.info(f"Creating Redis standalone connection with pool size: {pool_size}")
        logging.info(f"Connecting to Redis standalone at {redis_host}:{redis_port} SSL={ssl}")

        if not redis_host or not redis_port:
            logging.error("Environment variables REDIS_HOST and REDIS_PORT must be set.")
            return None

        try:
            conn = Redis(
                host=redis_host,
                port=int(redis_port),
                decode_responses=True,
                socket_timeout=int(query_timeout),
                ssl=bool(strtobool(ssl)),
                max_connections=pool_size,
                socket_keepalive=True,
            )
            conn.ping()
            logging.info("Redis standalone connection established successfully")
        except TimeoutError as e:
            logging.warning(f"Timeout error during Redis standalone initialization: {e}")
            conn = None
        except ConnectionError as e:
            logging.warning(f"Connection error: {e}")
            conn = None
        except Exception as e:
            logging.warning(f"Unexpected error during Redis standalone initialization: {e}")
            conn = None
        return conn

    def valkey_connect(self):
        """
        Initializes a connection to the Valley cluster.

        Returns:
            ValkeyCluster: Valley cluster connection object.
        """
        redis_host = os.environ.get("REDIS_HOST")
        redis_port = os.environ.get("REDIS_PORT")
        connections_pool = os.environ.get("CONNECTIONS_POOL", "10")
        ssl = os.environ.get("SSL")
        query_timeout = os.environ.get("QUERY_TIMEOUT", "5")

        pool_size = int(connections_pool)

        logging.info(f"Creating Valkey connection with pool size: {pool_size}")
        logging.info(f"Connecting to Valkey cluster at {redis_host}:{redis_port} SSL={ssl}")

        if not redis_host or not redis_port:
            logging.error("Environment variables REDIS_HOST and REDIS_PORT must be set.")
            return None
        startup_nodes = [
            ValleyClusterNode(redis_host, int(redis_port))
        ]
        try:
            conn = ValkeyCluster(
                startup_nodes=startup_nodes,
                decode_responses=True,
                timeout=int(query_timeout),
                ssl=bool(strtobool(ssl)),
                max_connections=pool_size,
                ssl_cert_reqs=None,
                # Facilitates reuse of connections
                connection_pool_kwargs={
                    'retry_on_timeout': True,
                    'socket_keepalive': True,
                    'socket_keepalive_options': {},
                }
            )
            logging.info("Valkey connection established successfully")
        except ValkeyClusterDownError as e:
            logging.warning(f"Cluster is down. Retrying...: {e}")
            conn = None
        except ValkeyTimeoutError as e:
            logging.warning(f"Timeout error during Valkey initialization: {e}")
            conn = None
        except ValkeyConnectionError as e:
            logging.warning(f"Connection error: {e}")
            conn = None
        except Exception as e:
            logging.warning(f"Unexpected error during Valkey initialization: {e}")
            conn = None
        return conn

    def valkey_standalone_connect(self):
        """
        Initializes a connection to a standalone Valkey instance.

        Returns:
            Valkey: Valkey connection object, or None on failure.
        """
        redis_host = os.environ.get("REDIS_HOST")
        redis_port = os.environ.get("REDIS_PORT")
        connections_pool = os.environ.get("CONNECTIONS_POOL", "10")
        ssl = os.environ.get("SSL")
        query_timeout = os.environ.get("QUERY_TIMEOUT", "5")

        pool_size = int(connections_pool)

        logging.info(f"Creating Valkey standalone connection with pool size: {pool_size}")
        logging.info(f"Connecting to Valkey standalone at {redis_host}:{redis_port} SSL={ssl}")

        if not redis_host or not redis_port:
            logging.error("Environment variables REDIS_HOST and REDIS_PORT must be set.")
            return None

        try:
            conn = Valkey(
                host=redis_host,
                port=int(redis_port),
                decode_responses=True,
                socket_timeout=int(query_timeout),
                ssl=bool(strtobool(ssl)),
                max_connections=pool_size,
                socket_keepalive=True,
            )
            conn.ping()
            logging.info("Valkey standalone connection established successfully")
        except ValkeyTimeoutError as e:
            logging.warning(f"Timeout error during Valkey standalone initialization: {e}")
            conn = None
        except ValkeyConnectionError as e:
            logging.warning(f"Connection error: {e}")
            conn = None
        except Exception as e:
            logging.warning(f"Unexpected error during Valkey standalone initialization: {e}")
            conn = None
        return conn
