import os
import unittest
from unittest.mock import patch, Mock
from cache_benchmark.cash_connect import CacheConnect
from cache_benchmark.config import AppConfig, set_config, reset_config
from redis.exceptions import TimeoutError, ConnectionError
from redis.cluster import ClusterDownError
from redis.retry import Retry
from redis.backoff import ExponentialBackoff
from valkey.cluster import ClusterDownError as ValkeyClusterDownError
from valkey.exceptions import ConnectionError as ValkeyConnectionError, TimeoutError as ValkeyTimeoutError
from valkey.retry import Retry as ValkeyRetry
from valkey.backoff import EqualJitterBackoff

class TestCashConnect(unittest.TestCase):
    def setUp(self):
        set_config(AppConfig(
            cache_host="localhost",
            cache_port=6379,
            connections_pool=10,
            ssl=False,
        ))

    def tearDown(self):
        reset_config()

    def test_redis_connect_success(self):
        with patch("cache_benchmark.cash_connect.RedisCluster") as mock_cls:
            mock_conn = Mock()
            mock_cls.return_value = mock_conn
            conn = CacheConnect.redis_connect(self)
            self.assertIsNotNone(conn)
            _, kwargs = mock_cls.call_args
            self.assertIn("retry", kwargs)
            self.assertIsInstance(kwargs["retry"], Retry)

    def test_redis_connect_retry_uses_config(self):
        reset_config()
        set_config(AppConfig(
            cache_host="localhost",
            cache_port=6379,
            connections_pool=10,
            ssl=False,
            retry_attempts=5,
            retry_wait=10,
        ))
        with patch("cache_benchmark.cash_connect.RedisCluster") as mock_cls:
            mock_cls.return_value = Mock()
            CacheConnect.redis_connect(self)
            _, kwargs = mock_cls.call_args
            self.assertEqual(kwargs["retry"]._retries, 5)

    def test_redis_connect_missing_env_vars(self):
        reset_config()
        set_config(AppConfig(cache_host=""))
        conn = CacheConnect().redis_connect()
        self.assertIsNone(conn)

    def test_redis_connect_cluster_down_error(self):
        with patch("redis.cluster.RedisCluster", side_effect=ClusterDownError):
            conn = CacheConnect().redis_connect()
            self.assertIsNone(conn)

    def test_redis_connect_timeout_error(self):
        with patch("redis.cluster.RedisCluster", side_effect=TimeoutError):
            conn = CacheConnect().redis_connect()
            self.assertIsNone(conn)

    def test_redis_connect_connection_error(self):
        with patch("redis.cluster.RedisCluster", side_effect=ConnectionError):
            conn = CacheConnect().redis_connect()
            self.assertIsNone(conn)

    def test_redis_connect_unexpected_error(self):
        with patch("redis.cluster.RedisCluster", side_effect=Exception):
            conn = CacheConnect().redis_connect()
            self.assertIsNone(conn)

    def test_valkey_connect_success(self):
        with patch("cache_benchmark.cash_connect.ValkeyCluster") as mock_cls:
            mock_conn = Mock()
            mock_cls.return_value = mock_conn
            conn = CacheConnect.valkey_connect(self)
            self.assertIsNotNone(conn)
            _, kwargs = mock_cls.call_args
            self.assertIn("retry", kwargs)
            self.assertIsInstance(kwargs["retry"], ValkeyRetry)
            self.assertIn("cluster_error_retry_attempts", kwargs)

    def test_valkey_connect_retry_uses_config(self):
        reset_config()
        set_config(AppConfig(
            cache_host="localhost",
            cache_port=6379,
            connections_pool=10,
            ssl=False,
            retry_attempts=7,
            retry_wait=4,
        ))
        with patch("cache_benchmark.cash_connect.ValkeyCluster") as mock_cls:
            mock_cls.return_value = Mock()
            CacheConnect.valkey_connect(self)
            _, kwargs = mock_cls.call_args
            self.assertEqual(kwargs["retry"]._retries, 7)
            self.assertEqual(kwargs["cluster_error_retry_attempts"], 7)

    def test_valkey_connect_missing_env_vars(self):
        reset_config()
        set_config(AppConfig(cache_host=""))
        conn = CacheConnect().valkey_connect()
        self.assertIsNone(conn)

    def test_valkey_connect_cluster_down_error(self):
        with patch("valkey.cluster.ValkeyCluster", side_effect=ValkeyClusterDownError):
            conn = CacheConnect().valkey_connect()
            self.assertIsNone(conn)

    def test_valkey_connect_timeout_error(self):
        with patch("valkey.cluster.ValkeyCluster", side_effect=ValkeyTimeoutError):
            conn = CacheConnect().valkey_connect()
            self.assertIsNone(conn)

    def test_valkey_connect_connection_error(self):
        with patch("valkey.cluster.ValkeyCluster", side_effect=ValkeyConnectionError):
            conn = CacheConnect().valkey_connect()
            self.assertIsNone(conn)

    def test_valkey_connect_unexpected_error(self):
        with patch("valkey.cluster.ValkeyCluster", side_effect=Exception):
            conn = CacheConnect().valkey_connect()
            self.assertIsNone(conn)

    def test_redis_standalone_connect_success(self):
        with patch("cache_benchmark.cash_connect.Redis") as mock_redis:
            mock_conn = Mock()
            mock_redis.return_value = mock_conn
            conn = CacheConnect().redis_standalone_connect()
            self.assertIsNotNone(conn)
            mock_conn.ping.assert_called_once()

    def test_redis_standalone_connect_passes_retry(self):
        with patch("cache_benchmark.cash_connect.Redis") as mock_redis:
            mock_redis.return_value = Mock()
            CacheConnect.redis_standalone_connect(self)
            _, kwargs = mock_redis.call_args
            self.assertIn("retry", kwargs)
            self.assertIsInstance(kwargs["retry"], Retry)
            self.assertIn("retry_on_error", kwargs)
            self.assertIn(ConnectionError, kwargs["retry_on_error"])
            self.assertIn(TimeoutError, kwargs["retry_on_error"])

    def test_redis_standalone_connect_missing_env_vars(self):
        reset_config()
        set_config(AppConfig(cache_host=""))
        conn = CacheConnect().redis_standalone_connect()
        self.assertIsNone(conn)

    def test_redis_standalone_connect_timeout_error(self):
        with patch("cache_benchmark.cash_connect.Redis") as mock_redis:
            mock_conn = Mock()
            mock_conn.ping.side_effect = TimeoutError
            mock_redis.return_value = mock_conn
            conn = CacheConnect().redis_standalone_connect()
            self.assertIsNone(conn)

    def test_redis_standalone_connect_connection_error(self):
        with patch("cache_benchmark.cash_connect.Redis") as mock_redis:
            mock_conn = Mock()
            mock_conn.ping.side_effect = ConnectionError
            mock_redis.return_value = mock_conn
            conn = CacheConnect().redis_standalone_connect()
            self.assertIsNone(conn)

    def test_valkey_standalone_connect_success(self):
        with patch("cache_benchmark.cash_connect.Valkey") as mock_valkey:
            mock_conn = Mock()
            mock_valkey.return_value = mock_conn
            conn = CacheConnect().valkey_standalone_connect()
            self.assertIsNotNone(conn)
            mock_conn.ping.assert_called_once()

    def test_valkey_standalone_connect_passes_retry(self):
        with patch("cache_benchmark.cash_connect.Valkey") as mock_valkey:
            mock_valkey.return_value = Mock()
            CacheConnect.valkey_standalone_connect(self)
            _, kwargs = mock_valkey.call_args
            self.assertIn("retry", kwargs)
            self.assertIsInstance(kwargs["retry"], ValkeyRetry)
            self.assertIn("retry_on_error", kwargs)
            self.assertIn(ValkeyConnectionError, kwargs["retry_on_error"])
            self.assertIn(ValkeyTimeoutError, kwargs["retry_on_error"])

    def test_valkey_standalone_connect_missing_env_vars(self):
        reset_config()
        set_config(AppConfig(cache_host=""))
        conn = CacheConnect().valkey_standalone_connect()
        self.assertIsNone(conn)

    def test_valkey_standalone_connect_timeout_error(self):
        with patch("cache_benchmark.cash_connect.Valkey") as mock_valkey:
            mock_conn = Mock()
            mock_conn.ping.side_effect = ValkeyTimeoutError
            mock_valkey.return_value = mock_conn
            conn = CacheConnect().valkey_standalone_connect()
            self.assertIsNone(conn)

    def test_valkey_standalone_connect_connection_error(self):
        with patch("cache_benchmark.cash_connect.Valkey") as mock_valkey:
            mock_conn = Mock()
            mock_conn.ping.side_effect = ValkeyConnectionError
            mock_valkey.return_value = mock_conn
            conn = CacheConnect().valkey_standalone_connect()
            self.assertIsNone(conn)


class TestAuthSslParams(unittest.TestCase):
    """Test that auth/SSL parameters are correctly passed to connection constructors."""

    def tearDown(self):
        reset_config()

    def _config_with_auth(self, **overrides):
        defaults = dict(
            cache_host="localhost",
            cache_port=6379,
            connections_pool=10,
            ssl=True,
            cache_username="testuser",
            cache_password="testpass",
            ssl_cert_reqs="required",
            ssl_ca_certs="/path/to/ca.pem",
        )
        defaults.update(overrides)
        return AppConfig(**defaults)

    def _config_without_auth(self):
        return AppConfig(
            cache_host="localhost",
            cache_port=6379,
            connections_pool=10,
            ssl=False,
        )

    # -- Redis cluster: auth set --
    def test_redis_connect_with_auth(self):
        set_config(self._config_with_auth())
        with patch("cache_benchmark.cash_connect.RedisCluster") as mock_cls:
            mock_cls.return_value = Mock()
            CacheConnect().redis_connect()
            kwargs = mock_cls.call_args
            self.assertEqual(kwargs.kwargs["password"], "testpass")
            self.assertEqual(kwargs.kwargs["username"], "testuser")
            self.assertEqual(kwargs.kwargs["ssl_cert_reqs"], "required")
            self.assertEqual(kwargs.kwargs["ssl_ca_certs"], "/path/to/ca.pem")

    # -- Redis cluster: auth not set --
    def test_redis_connect_without_auth(self):
        set_config(self._config_without_auth())
        with patch("cache_benchmark.cash_connect.RedisCluster") as mock_cls:
            mock_cls.return_value = Mock()
            CacheConnect().redis_connect()
            kwargs = mock_cls.call_args
            self.assertNotIn("password", kwargs.kwargs)
            self.assertNotIn("username", kwargs.kwargs)
            self.assertNotIn("ssl_cert_reqs", kwargs.kwargs)
            self.assertNotIn("ssl_ca_certs", kwargs.kwargs)

    # -- Redis standalone: auth set --
    def test_redis_standalone_connect_with_auth(self):
        set_config(self._config_with_auth())
        with patch("cache_benchmark.cash_connect.Redis") as mock_cls:
            mock_conn = Mock()
            mock_cls.return_value = mock_conn
            CacheConnect().redis_standalone_connect()
            kwargs = mock_cls.call_args
            self.assertEqual(kwargs.kwargs["password"], "testpass")
            self.assertEqual(kwargs.kwargs["username"], "testuser")
            self.assertEqual(kwargs.kwargs["ssl_cert_reqs"], "required")
            self.assertEqual(kwargs.kwargs["ssl_ca_certs"], "/path/to/ca.pem")

    # -- Redis standalone: auth not set --
    def test_redis_standalone_connect_without_auth(self):
        set_config(self._config_without_auth())
        with patch("cache_benchmark.cash_connect.Redis") as mock_cls:
            mock_conn = Mock()
            mock_cls.return_value = mock_conn
            CacheConnect().redis_standalone_connect()
            kwargs = mock_cls.call_args
            self.assertNotIn("password", kwargs.kwargs)
            self.assertNotIn("username", kwargs.kwargs)
            self.assertNotIn("ssl_cert_reqs", kwargs.kwargs)
            self.assertNotIn("ssl_ca_certs", kwargs.kwargs)

    # -- Valkey cluster: auth set --
    def test_valkey_connect_with_auth(self):
        set_config(self._config_with_auth())
        with patch("cache_benchmark.cash_connect.ValkeyCluster") as mock_cls:
            mock_cls.return_value = Mock()
            CacheConnect().valkey_connect()
            kwargs = mock_cls.call_args
            self.assertEqual(kwargs.kwargs["password"], "testpass")
            self.assertEqual(kwargs.kwargs["username"], "testuser")
            self.assertEqual(kwargs.kwargs["ssl_cert_reqs"], "required")
            self.assertEqual(kwargs.kwargs["ssl_ca_certs"], "/path/to/ca.pem")

    # -- Valkey cluster: auth not set --
    def test_valkey_connect_without_auth(self):
        set_config(self._config_without_auth())
        with patch("cache_benchmark.cash_connect.ValkeyCluster") as mock_cls:
            mock_cls.return_value = Mock()
            CacheConnect().valkey_connect()
            kwargs = mock_cls.call_args
            self.assertNotIn("password", kwargs.kwargs)
            self.assertNotIn("username", kwargs.kwargs)
            self.assertNotIn("ssl_cert_reqs", kwargs.kwargs)
            self.assertNotIn("ssl_ca_certs", kwargs.kwargs)

    # -- Valkey standalone: auth set --
    def test_valkey_standalone_connect_with_auth(self):
        set_config(self._config_with_auth())
        with patch("cache_benchmark.cash_connect.Valkey") as mock_cls:
            mock_conn = Mock()
            mock_cls.return_value = mock_conn
            CacheConnect().valkey_standalone_connect()
            kwargs = mock_cls.call_args
            self.assertEqual(kwargs.kwargs["password"], "testpass")
            self.assertEqual(kwargs.kwargs["username"], "testuser")
            self.assertEqual(kwargs.kwargs["ssl_cert_reqs"], "required")
            self.assertEqual(kwargs.kwargs["ssl_ca_certs"], "/path/to/ca.pem")

    # -- Valkey standalone: auth not set --
    def test_valkey_standalone_connect_without_auth(self):
        set_config(self._config_without_auth())
        with patch("cache_benchmark.cash_connect.Valkey") as mock_cls:
            mock_conn = Mock()
            mock_cls.return_value = mock_conn
            CacheConnect().valkey_standalone_connect()
            kwargs = mock_cls.call_args
            self.assertNotIn("password", kwargs.kwargs)
            self.assertNotIn("username", kwargs.kwargs)
            self.assertNotIn("ssl_cert_reqs", kwargs.kwargs)
            self.assertNotIn("ssl_ca_certs", kwargs.kwargs)
