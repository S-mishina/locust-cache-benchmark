import unittest
from unittest.mock import patch, Mock
from cache_benchmark.cash_connect import CacheConnect
from cache_benchmark.config import AppConfig, set_config, reset_config
from redis.exceptions import TimeoutError, ConnectionError
from redis.cluster import ClusterDownError
from valkey.cluster import ClusterDownError as ValkeyClusterDownError
from valkey.exceptions import ConnectionError as ValkeyConnectionError, TimeoutError as ValkeyTimeoutError

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
