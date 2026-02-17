from tenacity import Retrying, retry_if_exception_type, stop_after_attempt, wait_fixed, RetryError
from redis.exceptions import ClusterDownError
from opentelemetry import trace
import time
import logging
import os

_tracer = trace.get_tracer("locust-cache-benchmark")

_RETRYABLE_EXCEPTIONS = (TimeoutError, ConnectionError, ClusterDownError)

def _get_request_type():
    cache_type = os.environ.get("CACHE_TYPE", "redis_cluster")
    if cache_type in ("valkey_cluster", "valkey"):
        return "Valkey"
    return "Redis"

def _get_db_system():
    cache_type = os.environ.get("CACHE_TYPE", "redis_cluster")
    if cache_type in ("valkey_cluster", "valkey"):
        return "valkey"
    return "redis"

class LocustCache:
    def locust_redis_get(self, cache_connection, key, name):
        """
        Performs a GET operation on the Redis cluster with retry logic.

        Args:
            self: Locust task instance.
            cache_connection (RedisCluster): Redis cluster connection object.
            key (str): Key to get from Redis.
            name (str): Name for the request event.

        Returns:
            str: Value from Redis.
        """
        result = None
        try:
            retryer = Retrying(
                stop=stop_after_attempt(int(os.environ.get("RETRY_ATTEMPTS", 3))),
                wait=wait_fixed(int(os.environ.get("RETRY_WAIT", 5))),
                retry=retry_if_exception_type(_RETRYABLE_EXCEPTIONS),
            )
            for attempt in retryer:
                with attempt:
                    start_time = time.perf_counter()
                    with _tracer.start_as_current_span("GET", kind=trace.SpanKind.CLIENT) as span:
                        if span.is_recording():
                            span.set_attribute("db.system", _get_db_system())
                            span.set_attribute("db.statement", f"GET {key}")
                        try:
                            result = cache_connection.get(key)
                            total_time = (time.perf_counter() - start_time) * 1000
                            self.user.environment.events.request.fire(
                                request_type=_get_request_type(),
                                name="get_value_{}".format(name),
                                response_time=total_time,
                                response_length=0,
                                context={},
                                exception=None,
                            )
                        except Exception as e:
                            total_time = (time.perf_counter() - start_time) * 1000
                            span.record_exception(e)
                            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                            self.user.environment.events.request.fire(
                                request_type=_get_request_type(),
                                name="get_value_{}".format(name),
                                response_time=total_time,
                                response_length=0,
                                context={},
                                exception=e,
                            )
                            logging.error(f"Error during cache hit: {e}")
                            if isinstance(e, _RETRYABLE_EXCEPTIONS):
                                raise
                            result = None
        except RetryError:
            logging.error(f"All retry attempts exhausted for GET {key}")
            result = None
        return result

    def locust_redis_set(self, cache_connection, key, value, name, ttl):
        """
        Performs a SET operation on the Redis cluster with retry logic.

        Args:
            self: Locust task instance.
            cache_connection (RedisCluster): Redis cluster connection object.
            key (str): Key to set in Redis.
            value (str): Value to set in Redis.
            name (str): Name for the request event.
            ttl (int): Time-to-live for the key in seconds.

        Returns:
            bool: True if the operation was successful, False otherwise.
        """
        result = None
        try:
            retryer = Retrying(
                stop=stop_after_attempt(int(os.environ.get("RETRY_ATTEMPTS", 3))),
                wait=wait_fixed(int(os.environ.get("RETRY_WAIT", 5))),
                retry=retry_if_exception_type(_RETRYABLE_EXCEPTIONS),
            )
            for attempt in retryer:
                with attempt:
                    start_time = time.perf_counter()
                    with _tracer.start_as_current_span("SET", kind=trace.SpanKind.CLIENT) as span:
                        if span.is_recording():
                            span.set_attribute("db.system", _get_db_system())
                            span.set_attribute("db.statement", f"SET {key}")
                        try:
                            result = cache_connection.set(key, value, ex=int(ttl))
                            total_time = (time.perf_counter() - start_time) * 1000
                            self.user.environment.events.request.fire(
                                request_type=_get_request_type(),
                                name="set_value_{}".format(name),
                                response_time=total_time,
                                response_length=0,
                                context={},
                                exception=None,
                            )
                        except Exception as e:
                            total_time = (time.perf_counter() - start_time) * 1000
                            span.record_exception(e)
                            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                            self.user.environment.events.request.fire(
                                request_type=_get_request_type(),
                                name="set_value_{}".format(name),
                                response_time=total_time,
                                response_length=0,
                                context={},
                                exception=e,
                            )
                            logging.error(f"Error during cache set: {e}")
                            if isinstance(e, _RETRYABLE_EXCEPTIONS):
                                raise
                            result = None
        except RetryError:
            logging.error(f"All retry attempts exhausted for SET {key}")
            result = None
        return result
