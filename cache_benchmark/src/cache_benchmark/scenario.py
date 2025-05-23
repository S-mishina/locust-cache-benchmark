from gevent import monkey
monkey.patch_all()

import hashlib
import os
import logging
from locust import User, TaskSet, task, between
from cache_benchmark.locust_cache import LocustCache
from cache_benchmark.utils import generate_string
import random
import time

class RedisTaskSet(TaskSet):
    total_requests = 0
    cache_hits = 0
    def on_stop(self):
        if self.__class__.total_requests > 0:
            hit_rate = (self.__class__.cache_hits / self.__class__.total_requests) * 100
            logging.info(f"Total Requests: {self.__class__.total_requests}")
            logging.info(f"Cache Hits: {self.__class__.cache_hits}")
            logging.info(f"Cache Hit Rate: {hit_rate:.2f}%")
        else:
            logging.info("Total Requests: 0")
            logging.info("Cache Hit Rate: N/A")

    @task
    def cache_scenario(self):
        hit_rate = float(os.environ.get("HIT_RATE"))
        self.__class__.total_requests += 1
        if self.user.environment.cache_conn is None:
            logging.warning("Redis client is not initialized.")
            return
        if random.random() < float(hit_rate):
            key = f"key_{random.randint(1, 1000)}"
            result = LocustCache.locust_redis_get(self, self.user.environment.cache_conn, key, "default")
            if result is None:
                value = generate_string(os.environ.get("VALUE_SIZE"))
                ttl = int(os.environ.get("TTL"))
                LocustCache.locust_redis_set(self, self.user.environment.cache_conn, key , value , "default", ttl)
        else:
            hash_key = hashlib.sha256(str(time.time_ns()).encode()).hexdigest()
            ttl = int(os.environ.get("TTL"))
            result = LocustCache.locust_redis_get(self, self.user.environment.cache_conn, hash_key, "dummy")
            if result is None:
                value = generate_string(os.environ.get("VALUE_SIZE"))
                LocustCache.locust_redis_set(self, self.user.environment.cache_conn, hash_key , value , "dummy", ttl)

class RedisUser(User):
    tasks = [RedisTaskSet]
    wait_time = between(1, 1)
    host = os.environ.get("REDIS_HOST")
