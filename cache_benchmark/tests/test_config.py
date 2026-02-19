import json
import os
import unittest
from unittest.mock import Mock, patch
from pydantic import ValidationError
from cache_benchmark.config import (
    AppConfig,
    get_config, set_config, reset_config, _strtobool,
)


class TestStrtobool(unittest.TestCase):
    def test_true_values(self):
        for val in ('y', 'yes', 't', 'true', 'on', '1', 'True', 'YES', ' True '):
            self.assertTrue(_strtobool(val))

    def test_false_values(self):
        for val in ('n', 'no', 'f', 'false', 'off', '0', 'False', 'NO', ' False '):
            self.assertFalse(_strtobool(val))

    def test_invalid_value(self):
        with self.assertRaises(ValueError):
            _strtobool("invalid")


class TestAppConfig(unittest.TestCase):
    def test_defaults(self):
        config = AppConfig()
        self.assertEqual(config.cache_host, "localhost")
        self.assertEqual(config.cache_port, 6379)
        self.assertFalse(config.ssl)
        self.assertEqual(config.query_timeout, 1)
        self.assertEqual(config.connections_pool, 10)
        self.assertEqual(config.cache_type, "redis_cluster")
        self.assertEqual(config.hit_rate, 0.5)
        self.assertEqual(config.value_size, 1)
        self.assertEqual(config.ttl, 60)
        self.assertEqual(config.request_rate, 1.0)
        self.assertEqual(config.set_keys, 1000)
        self.assertEqual(config.retry_attempts, 3)
        self.assertEqual(config.retry_wait, 2)
        self.assertFalse(config.otel_tracing_enabled)
        self.assertEqual(config.otel_exporter_endpoint, "http://localhost:4317")
        self.assertEqual(config.otel_service_name, "locust-cache-benchmark")
        self.assertEqual(config.duration, 60)
        self.assertEqual(config.connections, 1)
        self.assertEqual(config.spawn_rate, 1)
        self.assertIsNone(config.cluster_mode)
        self.assertEqual(config.master_bind_host, "127.0.0.1")
        self.assertEqual(config.master_bind_port, 5557)
        self.assertEqual(config.num_workers, 1)
        self.assertIsNone(config.ssl_cert_reqs)
        self.assertIsNone(config.ssl_ca_certs)
        self.assertIsNone(config.cache_username)
        self.assertIsNone(config.cache_password)

    def test_frozen(self):
        config = AppConfig()
        with self.assertRaises(ValidationError):
            config.cache_host = "other"

    @patch.dict(os.environ, {}, clear=True)
    def test_from_args(self):
        args = Mock()
        args.fqdn = "redis.example.com"
        args.port = 6380
        args.ssl = "true"
        args.query_timeout = 5
        args.connections_pool = 20
        args.hit_rate = 0.8
        args.value_size = 2
        args.ttl = 120
        args.request_rate = 2.5
        args.set_keys = 500
        args.retry_count = 5
        args.retry_wait = 3
        args.otel_tracing_enabled = "true"
        args.otel_exporter_endpoint = "http://otel:4317"
        args.otel_service_name = "my-service"
        args.duration = 120
        args.connections = 4
        args.spawn_rate = 2
        args.cluster_mode = "master"
        args.master_bind_host = "0.0.0.0"
        args.master_bind_port = 5558
        args.num_workers = 3
        args.cache_username = "myuser"
        args.cache_password = "mypass"
        args.ssl_cert_reqs = "required"
        args.ssl_ca_certs = "/path/to/ca.pem"

        config = AppConfig.from_args(args, cache_type="valkey_cluster")

        self.assertEqual(config.cache_host, "redis.example.com")
        self.assertEqual(config.cache_port, 6380)
        self.assertTrue(config.ssl)
        self.assertEqual(config.query_timeout, 5)
        self.assertEqual(config.connections_pool, 20)
        self.assertEqual(config.cache_type, "valkey_cluster")
        self.assertEqual(config.hit_rate, 0.8)
        self.assertEqual(config.value_size, 2)
        self.assertEqual(config.ttl, 120)
        self.assertEqual(config.request_rate, 2.5)
        self.assertEqual(config.set_keys, 500)
        self.assertEqual(config.retry_attempts, 5)
        self.assertEqual(config.retry_wait, 3)
        self.assertTrue(config.otel_tracing_enabled)
        self.assertEqual(config.otel_exporter_endpoint, "http://otel:4317")
        self.assertEqual(config.otel_service_name, "my-service")
        self.assertEqual(config.duration, 120)
        self.assertEqual(config.connections, 4)
        self.assertEqual(config.spawn_rate, 2)
        self.assertEqual(config.cluster_mode, "master")
        self.assertEqual(config.master_bind_host, "0.0.0.0")
        self.assertEqual(config.master_bind_port, 5558)
        self.assertEqual(config.num_workers, 3)
        self.assertEqual(config.cache_username, "myuser")
        self.assertEqual(config.cache_password, "mypass")
        self.assertEqual(config.ssl_cert_reqs, "required")
        self.assertEqual(config.ssl_ca_certs, "/path/to/ca.pem")


class TestFromArgsEnvOverride(unittest.TestCase):
    """Verify that environment variables take priority when set."""

    def _make_default_args(self):
        args = Mock()
        args.fqdn = "localhost"
        args.port = 6379
        args.ssl = "false"
        args.query_timeout = 1
        args.connections_pool = 10
        args.hit_rate = 0.5
        args.value_size = 1
        args.ttl = 60
        args.request_rate = 1.0
        args.set_keys = 1000
        args.retry_count = 3
        args.retry_wait = 2
        args.otel_tracing_enabled = "false"
        args.otel_exporter_endpoint = "http://localhost:4317"
        args.otel_service_name = "locust-cache-benchmark"
        args.duration = 60
        args.connections = 1
        args.spawn_rate = 1
        args.cluster_mode = None
        args.master_bind_host = "127.0.0.1"
        args.master_bind_port = 5557
        args.num_workers = 1
        args.cache_username = None
        args.cache_password = None
        args.ssl_cert_reqs = None
        args.ssl_ca_certs = None
        return args

    @patch.dict(os.environ, {"CACHE_HOST": "env-redis.example.com", "CACHE_PORT": "7000"}, clear=True)
    def test_env_overrides_args_host_port(self):
        args = self._make_default_args()
        config = AppConfig.from_args(args)
        self.assertEqual(config.cache_host, "env-redis.example.com")
        self.assertEqual(config.cache_port, 7000)

    @patch.dict(os.environ, {"SSL": "true", "TTL": "300", "HIT_RATE": "0.9"}, clear=True)
    def test_env_overrides_ssl_ttl_hitrate(self):
        args = self._make_default_args()
        config = AppConfig.from_args(args)
        self.assertTrue(config.ssl)
        self.assertEqual(config.ttl, 300)
        self.assertEqual(config.hit_rate, 0.9)

    @patch.dict(os.environ, {"CACHE_TYPE": "valkey"}, clear=True)
    def test_env_overrides_cache_type(self):
        args = self._make_default_args()
        config = AppConfig.from_args(args, cache_type="redis_cluster")
        self.assertEqual(config.cache_type, "valkey")

    @patch.dict(os.environ, {"RETRY_ATTEMPTS": "10", "RETRY_WAIT": "5"}, clear=True)
    def test_env_overrides_retry(self):
        args = self._make_default_args()
        config = AppConfig.from_args(args)
        self.assertEqual(config.retry_attempts, 10)
        self.assertEqual(config.retry_wait, 5)

    @patch.dict(os.environ, {"OTEL_TRACING_ENABLED": "true", "OTEL_SERVICE_NAME": "env-svc"}, clear=True)
    def test_env_overrides_otel(self):
        args = self._make_default_args()
        config = AppConfig.from_args(args)
        self.assertTrue(config.otel_tracing_enabled)
        self.assertEqual(config.otel_service_name, "env-svc")

    @patch.dict(os.environ, {}, clear=True)
    def test_no_env_uses_args(self):
        args = self._make_default_args()
        args.fqdn = "cli-host"
        args.port = 9999
        config = AppConfig.from_args(args)
        self.assertEqual(config.cache_host, "cli-host")
        self.assertEqual(config.cache_port, 9999)


# --- JSON ---

class TestJsonSerialization(unittest.TestCase):
    def test_to_dict(self):
        config = AppConfig()
        d = config.to_dict()
        self.assertIsInstance(d, dict)
        self.assertEqual(d["cache_host"], "localhost")
        self.assertEqual(d["cache_port"], 6379)
        self.assertIsNone(d["cluster_mode"])

    def test_to_json(self):
        config = AppConfig()
        j = config.to_json()
        parsed = json.loads(j)
        self.assertEqual(parsed["cache_host"], "localhost")
        self.assertEqual(parsed["cache_port"], 6379)

    def test_from_dict(self):
        data = {"cache_host": "myhost", "cache_port": 7000, "hit_rate": 0.8}
        config = AppConfig.from_dict(data)
        self.assertEqual(config.cache_host, "myhost")
        self.assertEqual(config.cache_port, 7000)
        self.assertEqual(config.hit_rate, 0.8)
        self.assertEqual(config.ttl, 60)  # default preserved

    def test_from_dict_ignores_unknown_keys(self):
        data = {"cache_host": "myhost", "unknown_key": "should_be_ignored"}
        config = AppConfig.from_dict(data)
        self.assertEqual(config.cache_host, "myhost")

    def test_from_dict_bool_string(self):
        data = {"ssl": "true", "otel_tracing_enabled": "false"}
        config = AppConfig.from_dict(data)
        self.assertTrue(config.ssl)
        self.assertFalse(config.otel_tracing_enabled)

    def test_from_json(self):
        j = '{"cache_host": "jsonhost", "cache_port": 8000, "ttl": 120}'
        config = AppConfig.from_json(j)
        self.assertEqual(config.cache_host, "jsonhost")
        self.assertEqual(config.cache_port, 8000)
        self.assertEqual(config.ttl, 120)

    def test_roundtrip(self):
        original = AppConfig(cache_host="roundtrip", cache_port=9999, hit_rate=0.3)
        j = original.to_json()
        restored = AppConfig.from_json(j)
        self.assertEqual(original, restored)

    def test_json_schema(self):
        schema = AppConfig.json_schema()
        self.assertIsInstance(schema, dict)
        self.assertIn("properties", schema)
        self.assertIn("cache_host", schema["properties"])
        self.assertIn("cache_port", schema["properties"])

    def test_json_schema_string(self):
        s = AppConfig.json_schema_string()
        parsed = json.loads(s)
        self.assertIn("properties", parsed)


# --- Validation ---

class TestValidation(unittest.TestCase):
    def test_valid_default(self):
        config = AppConfig()
        self.assertIsNotNone(config)

    def test_invalid_port_too_low(self):
        with self.assertRaises(ValidationError) as ctx:
            AppConfig(cache_port=0)
        self.assertIn("cache_port", str(ctx.exception))

    def test_invalid_port_too_high(self):
        with self.assertRaises(ValidationError):
            AppConfig(cache_port=70000)

    def test_invalid_hit_rate_negative(self):
        with self.assertRaises(ValidationError):
            AppConfig(hit_rate=-0.1)

    def test_invalid_hit_rate_over_one(self):
        with self.assertRaises(ValidationError):
            AppConfig(hit_rate=1.5)

    def test_invalid_cache_type(self):
        with self.assertRaises(ValidationError):
            AppConfig(cache_type="memcached")

    def test_invalid_cluster_mode(self):
        with self.assertRaises(ValidationError):
            AppConfig(cluster_mode="standalone")

    def test_valid_cluster_mode_master(self):
        config = AppConfig(cluster_mode="master")
        self.assertEqual(config.cluster_mode, "master")

    def test_valid_cluster_mode_worker(self):
        config = AppConfig(cluster_mode="worker")
        self.assertEqual(config.cluster_mode, "worker")

    def test_valid_cluster_mode_none(self):
        config = AppConfig(cluster_mode=None)
        self.assertIsNone(config.cluster_mode)

    def test_invalid_ttl_zero(self):
        with self.assertRaises(ValidationError):
            AppConfig(ttl=0)

    def test_invalid_value_size_zero(self):
        with self.assertRaises(ValidationError):
            AppConfig(value_size=0)

    def test_invalid_request_rate_zero(self):
        with self.assertRaises(ValidationError):
            AppConfig(request_rate=0)

    def test_invalid_master_bind_port(self):
        with self.assertRaises(ValidationError):
            AppConfig(master_bind_port=0)

    def test_multiple_errors(self):
        with self.assertRaises(ValidationError) as ctx:
            AppConfig(cache_port=0, hit_rate=2.0, ttl=-1, cache_type="bad")
        self.assertGreater(ctx.exception.error_count(), 1)

    def test_master_mode_requires_bind_host(self):
        with self.assertRaises(ValidationError):
            AppConfig(cluster_mode="master", master_bind_host="")

    def test_worker_mode_requires_bind_host(self):
        with self.assertRaises(ValidationError):
            AppConfig(cluster_mode="worker", master_bind_host="")

    def test_from_json_invalid_values(self):
        j = '{"cache_port": 0, "hit_rate": 2.0}'
        with self.assertRaises(ValidationError):
            AppConfig.from_json(j)

    def test_invalid_ssl_cert_reqs(self):
        with self.assertRaises(ValidationError):
            AppConfig(ssl_cert_reqs="invalid")

    def test_valid_ssl_cert_reqs_none(self):
        config = AppConfig(ssl_cert_reqs="none")
        self.assertEqual(config.ssl_cert_reqs, "none")

    def test_valid_ssl_cert_reqs_optional(self):
        config = AppConfig(ssl_cert_reqs="optional")
        self.assertEqual(config.ssl_cert_reqs, "optional")

    def test_valid_ssl_cert_reqs_required(self):
        config = AppConfig(ssl_cert_reqs="required")
        self.assertEqual(config.ssl_cert_reqs, "required")


class TestAuthSslEnvOverride(unittest.TestCase):
    """Verify that environment variables override auth/SSL settings."""

    def _make_default_args(self):
        args = Mock()
        args.fqdn = "localhost"
        args.port = 6379
        args.ssl = "false"
        args.query_timeout = 1
        args.connections_pool = 10
        args.hit_rate = 0.5
        args.value_size = 1
        args.ttl = 60
        args.request_rate = 1.0
        args.set_keys = 1000
        args.retry_count = 3
        args.retry_wait = 2
        args.otel_tracing_enabled = "false"
        args.otel_exporter_endpoint = "http://localhost:4317"
        args.otel_service_name = "locust-cache-benchmark"
        args.duration = 60
        args.connections = 1
        args.spawn_rate = 1
        args.cluster_mode = None
        args.master_bind_host = "127.0.0.1"
        args.master_bind_port = 5557
        args.num_workers = 1
        args.cache_username = None
        args.cache_password = None
        args.ssl_cert_reqs = None
        args.ssl_ca_certs = None
        return args

    @patch.dict(os.environ, {
        "CACHE_USERNAME": "env-user",
        "CACHE_PASSWORD": "env-pass",
        "SSL_CERT_REQS": "required",
        "SSL_CA_CERTS": "/env/ca.pem",
    }, clear=True)
    def test_env_overrides_auth_ssl(self):
        args = self._make_default_args()
        config = AppConfig.from_args(args)
        self.assertEqual(config.cache_username, "env-user")
        self.assertEqual(config.cache_password, "env-pass")
        self.assertEqual(config.ssl_cert_reqs, "required")
        self.assertEqual(config.ssl_ca_certs, "/env/ca.pem")


# --- Singleton ---

class TestSingleton(unittest.TestCase):
    def setUp(self):
        reset_config()

    def tearDown(self):
        reset_config()

    def test_get_config_before_set_raises(self):
        with self.assertRaises(RuntimeError):
            get_config()

    def test_set_and_get(self):
        config = AppConfig(cache_host="myhost")
        set_config(config)
        self.assertIs(get_config(), config)
        self.assertEqual(get_config().cache_host, "myhost")

    def test_reset(self):
        set_config(AppConfig())
        reset_config()
        with self.assertRaises(RuntimeError):
            get_config()


if __name__ == "__main__":
    unittest.main()
