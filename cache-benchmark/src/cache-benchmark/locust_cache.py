from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed
from cash_connect import *
import time
import locust

@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(2),
    retry=retry_if_exception_type((TimeoutError, ConnectionError, ClusterDownError)),
)
def locust_redis_get(self, cache_connection, key, name):
    """
    Performs a GET operation on the Redis cluster with retry logic.
    
    Args:
        self: Locust task instance.
        redis_connection (RedisCluster): Redis cluster connection object.
        key (str): Key to get from Redis.
        name (str): Name for the request event.
    
    Returns:
        str: Value from Redis.
    """
    start_time = time.perf_counter()
    try:
        result = cache_connection.get(key)
        total_time = (time.perf_counter() - start_time) * 1000
        self.user.environment.events.request.fire(
            request_type="Redis",
            name="get_value_{}".format(name),
            response_time=total_time,
            response_length=0,
            context={},
            exception=None,
        )
    except Exception as e:
        total_time = (time.perf_counter() - start_time) * 1000
        self.user.environment.events.request.fire(
            request_type="Redis",
            name="get_value_{}".format(name),
            response_time=total_time,
            response_length=0,
            context={},
            exception=e,
        )
        logging.error(f"Error during cache hit: {e}")
        result = None
    return result

@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(2),
    retry=retry_if_exception_type((TimeoutError, ConnectionError, ClusterDownError)),
)
def locust_redis_set(self, cache_connection, key, value, name, ttl):
    """
    Performs a SET operation on the Redis cluster with retry logic.
    
    Args:
        self: Locust task instance.
        redis_connection (RedisCluster): Redis cluster connection object.
        key (str): Key to set in Redis.
        value (str): Value to set in Redis.
        name (str): Name for the request event.
        ttl (int): Time-to-live for the key in seconds.
    
    Returns:
        bool: True if the operation was successful, False otherwise.
    """
    start_time = time.perf_counter()
    try:
        result = cache_connection.set(key, value, ex=int(ttl))
        total_time = (time.perf_counter() - start_time) * 1000
        self.user.environment.events.request.fire(
            request_type="Redis",
            name="set_value_{}".format(name),
            response_time=total_time,
            response_length=0,
            context={},
            exception=None,
        )
    except Exception as e:
        total_time = (time.perf_counter() - start_time) * 1000
        self.user.environment.events.request.fire(
            request_type="Redis",
            name="set_value_{}".format(name),
            response_time=total_time,
            response_length=0,
            context={},
            exception=e,
        )
        logging.error(f"Error during cache set: {e}")
        result = None
    return result
