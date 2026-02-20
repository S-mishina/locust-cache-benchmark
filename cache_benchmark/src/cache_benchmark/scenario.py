from gevent import monkey
monkey.patch_all()

import hashlib
import logging
import gevent.lock

logger = logging.getLogger(__name__)
from locust import User, TaskSet, task, constant_throughput
from cache_benchmark.locust_cache import LocustCache
from cache_benchmark.utils import generate_string
from cache_benchmark.cash_connect import CacheConnect
from cache_benchmark.config import get_config
import random
import time

class RedisTaskSet(TaskSet):
    total_requests = 0
    cache_hits = 0
    def on_stop(self):
        if self.__class__.total_requests > 0:
            hit_rate = (self.__class__.cache_hits / self.__class__.total_requests) * 100
            logger.info(f"Total Requests: {self.__class__.total_requests}")
            logger.info(f"Cache Hits: {self.__class__.cache_hits}")
            logger.info(f"Cache Hit Rate: {hit_rate:.2f}%")
        else:
            logger.info("Total Requests: 0")
            logger.info("Cache Hit Rate: N/A")

    @task
    def cache_scenario(self):
        cfg = get_config()
        hit_rate = cfg.hit_rate
        self.__class__.total_requests += 1

        if not hasattr(self.user, 'cache_conn') or self.user.cache_conn is None:
            logger.warning(f"User {id(self.user)} cache connection not available")
            return

        if random.random() < hit_rate:
            set_keys = cfg.set_keys
            key = f"key_{random.randint(1, set_keys)}"
            result = LocustCache.locust_redis_get(self, self.user.cache_conn, key, "default")
            if result is not None:
                self.__class__.cache_hits += 1
            if result is None:
                value = generate_string(cfg.value_size)
                ttl = cfg.ttl
                LocustCache.locust_redis_set(self, self.user.cache_conn, key, value, "default", ttl)
        else:
            hash_key = hashlib.sha256(str(time.time_ns()).encode()).hexdigest()
            ttl = cfg.ttl
            result = LocustCache.locust_redis_get(self, self.user.cache_conn, hash_key, "dummy")
            if result is None:
                value = generate_string(cfg.value_size)
                LocustCache.locust_redis_set(self, self.user.cache_conn, hash_key, value, "dummy", ttl)

class RedisUser(User):
    tasks = [RedisTaskSet]
    wait_time = constant_throughput(1.0)
    host = "localhost"
    # Shared connection across all users (RedisCluster is thread/greenlet-safe)
    _shared_cache_conn = None
    _shared_conn_users = 0
    _conn_lock = gevent.lock.Semaphore()

    @classmethod
    def _get_shared_connection(cls):
        """Get or create a shared RedisCluster/ValkeyCluster connection."""
        with cls._conn_lock:
            if cls._shared_cache_conn is None:
                cache = CacheConnect()
                cfg = get_config()
                cache_type = cfg.cache_type
                if cache_type == "redis_cluster":
                    cls._shared_cache_conn = cache.redis_connect()
                elif cache_type == "valkey_cluster":
                    cls._shared_cache_conn = cache.valkey_connect()
                elif cache_type == "redis":
                    cls._shared_cache_conn = cache.redis_standalone_connect()
                elif cache_type == "valkey":
                    cls._shared_cache_conn = cache.valkey_standalone_connect()
            cls._shared_conn_users += 1
            return cls._shared_cache_conn

    @classmethod
    def _release_shared_connection(cls):
        """Release the shared connection when the last user stops."""
        with cls._conn_lock:
            cls._shared_conn_users -= 1
            if cls._shared_conn_users <= 0 and cls._shared_cache_conn is not None:
                try:
                    cls._shared_cache_conn.close()
                    logger.info("Shared cache connection closed")
                except Exception as e:
                    logger.warning(f"Error closing shared cache connection: {e}")
                cls._shared_cache_conn = None
                cls._shared_conn_users = 0

    def on_start(self):
        """Acquire shared connection at user startup"""
        self._connected = False
        self.cache_conn = self.__class__._get_shared_connection()
        if self.cache_conn:
            self._connected = True
            logger.info(f"User {id(self)} connected successfully (shared)")
        else:
            logger.error(f"User {id(self)} connection failed")

    def on_stop(self):
        """Release shared connection reference when user exits"""
        if self._connected:
            self.__class__._release_shared_connection()
            self._connected = False
        logger.info(f"User {id(self)} released connection")
