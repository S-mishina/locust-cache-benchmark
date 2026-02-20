from opentelemetry import trace
from cache_benchmark.config import get_config
import time
import logging

logger = logging.getLogger(__name__)

_tracer = trace.get_tracer("locust-cache-benchmark")

def _get_request_type():
    cfg = get_config()
    if cfg.cache_type in ("valkey_cluster", "valkey"):
        return "Valkey"
    return "Redis"

def _get_db_system():
    cfg = get_config()
    if cfg.cache_type in ("valkey_cluster", "valkey"):
        return "valkey"
    return "redis"

class LocustCache:
    @staticmethod
    def locust_redis_get(task, cache_connection, key, name):
        """
        Performs a GET operation on the Redis cluster.

        Args:
            task: Locust task instance.
            cache_connection (RedisCluster): Redis cluster connection object.
            key (str): Key to get from Redis.
            name (str): Name for the request event.

        Returns:
            str: Value from Redis.
        """
        start_time = time.perf_counter()
        with _tracer.start_as_current_span("GET", kind=trace.SpanKind.CLIENT) as span:
            if span.is_recording():
                span.set_attribute("db.system", _get_db_system())
                span.set_attribute("db.statement", f"GET {key}")
            try:
                result = cache_connection.get(key)
                total_time = (time.perf_counter() - start_time) * 1000
                task.user.environment.events.request.fire(
                    request_type=_get_request_type(),
                    name="get_value_{}".format(name),
                    response_time=total_time,
                    response_length=0,
                    context={},
                    exception=None,
                )
                return result
            except Exception as e:
                total_time = (time.perf_counter() - start_time) * 1000
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                task.user.environment.events.request.fire(
                    request_type=_get_request_type(),
                    name="get_value_{}".format(name),
                    response_time=total_time,
                    response_length=0,
                    context={},
                    exception=e,
                )
                logger.error(f"Error during cache hit: {e}")
                return None

    @staticmethod
    def locust_redis_set(task, cache_connection, key, value, name, ttl):
        """
        Performs a SET operation on the Redis cluster.

        Args:
            task: Locust task instance.
            cache_connection (RedisCluster): Redis cluster connection object.
            key (str): Key to set in Redis.
            value (str): Value to set in Redis.
            name (str): Name for the request event.
            ttl (int): Time-to-live for the key in seconds.

        Returns:
            bool: True if the operation was successful, False otherwise.
        """
        start_time = time.perf_counter()
        with _tracer.start_as_current_span("SET", kind=trace.SpanKind.CLIENT) as span:
            if span.is_recording():
                span.set_attribute("db.system", _get_db_system())
                span.set_attribute("db.statement", f"SET {key}")
            try:
                result = cache_connection.set(key, value, ex=int(ttl))
                total_time = (time.perf_counter() - start_time) * 1000
                task.user.environment.events.request.fire(
                    request_type=_get_request_type(),
                    name="set_value_{}".format(name),
                    response_time=total_time,
                    response_length=0,
                    context={},
                    exception=None,
                )
                return result
            except Exception as e:
                total_time = (time.perf_counter() - start_time) * 1000
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                task.user.environment.events.request.fire(
                    request_type=_get_request_type(),
                    name="set_value_{}".format(name),
                    response_time=total_time,
                    response_length=0,
                    context={},
                    exception=e,
                )
                logger.error(f"Error during cache set: {e}")
                return None
