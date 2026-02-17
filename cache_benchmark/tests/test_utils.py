import os
import unittest
from unittest.mock import Mock
from cache_benchmark.utils import generate_string, init_cache_set, set_env_vars, set_env_cache_retry


class TestUtils(unittest.TestCase):
    def test_generate_string(self):
        result = generate_string(1)
        self.assertIsInstance(result, str)

    def test_set_env_vars(self):
        args = Mock()
        args.fqdn = "localhost"
        args.port = 6379
        args.hit_rate = 0.9
        args.value_size = 1024
        args.ttl = 60
        args.connections_pool = 10
        args.ssl = "False"
        args.request_rate = 1.0
        args.otel_tracing_enabled = "false"
        args.otel_exporter_endpoint = "http://localhost:4317"
        args.otel_service_name = "locust-cache-benchmark"
        args.query_timeout = 2
        args.set_keys = 500

        set_env_vars(args)

        self.assertEqual(os.environ["REDIS_HOST"], "localhost")
        self.assertEqual(os.environ["REDIS_PORT"], "6379")
        self.assertEqual(os.environ["HIT_RATE"], "0.9")
        self.assertEqual(os.environ["VALUE_SIZE"], "1024")
        self.assertEqual(os.environ["TTL"], "60")
        self.assertEqual(os.environ["CONNECTIONS_POOL"], "10")
        self.assertEqual(os.environ["SSL"] , "False")
        self.assertEqual(os.environ["REQUEST_RATE"], "1.0")
        self.assertEqual(os.environ["OTEL_TRACING_ENABLED"], "false")
        self.assertEqual(os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"], "http://localhost:4317")
        self.assertEqual(os.environ["OTEL_SERVICE_NAME"], "locust-cache-benchmark")
        self.assertEqual(os.environ["QUERY_TIMEOUT"], "2")
        self.assertEqual(os.environ["SET_KEYS"], "500")

    def test_set_env_cache_retry(self):
        args = Mock()
        args.retry_count = 5
        args.retry_wait = 3

        set_env_cache_retry(args)

        self.assertEqual(os.environ["RETRY_ATTEMPTS"], "5")
        self.assertEqual(os.environ["RETRY_WAIT"], "3")

    def test_init_cache_set(self):
        cache_client = Mock()
        value = "test_value"
        ttl = 60
        cache_client.get.return_value = None
        cache_client.set.return_value = True
        init_cache_set(cache_client, value, ttl, 1000)
        self.assertEqual(cache_client.set.call_count, 1000)
        self.assertEqual(cache_client.get.call_count, 1000)

    def test_init_cache_set_custom_keys(self):
        cache_client = Mock()
        value = "test_value"
        ttl = 60
        cache_client.get.return_value = None
        cache_client.set.return_value = True
        init_cache_set(cache_client, value, ttl, 50)
        self.assertEqual(cache_client.set.call_count, 50)
        self.assertEqual(cache_client.get.call_count, 50)

    def test_init_cache_set_default_keys(self):
        cache_client = Mock()
        value = "test_value"
        ttl = 60
        cache_client.get.return_value = None
        cache_client.set.return_value = True
        init_cache_set(cache_client, value, ttl)
        self.assertEqual(cache_client.set.call_count, 1000)
        self.assertEqual(cache_client.get.call_count, 1000)


if __name__ == "__main__":
    unittest.main()
