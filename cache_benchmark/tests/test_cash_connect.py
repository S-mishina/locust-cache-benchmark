import os
from unittest.mock import patch, Mock
import unittest
from cache_benchmark.cash_connect import CacheConnect
from redis.exceptions import TimeoutError, ConnectionError
from redis.cluster import ClusterDownError
from valkey.cluster import ClusterDownError as ValkeyClusterDownError
from valkey.exceptions import ConnectionError as ValkeyConnectionError, TimeoutError as ValkeyTimeoutError

class TestCashConnect(unittest.TestCase):
    def setUp(self):
        os.environ.clear()
        os.environ["REDIS_HOST"] = "localhost"
        os.environ["REDIS_PORT"] = "6379"
        os.environ["CONNECTIONS_POOL"] = "10"
        os.environ["SSL"] = "false"

    def tearDown(self):
        os.environ.clear()

    def test_redis_connect_missing_env_vars(self):
        self.tearDown()
        conn = CacheConnect.redis_connect(self)
        self.assertIsNone(conn)

    def test_redis_connect_cluster_down_error(self):
        with patch("redis.cluster.RedisCluster", side_effect=ClusterDownError):
            conn = CacheConnect.redis_connect(self)
            self.assertIsNone(conn)

    def test_redis_connect_timeout_error(self):
        with patch("redis.cluster.RedisCluster", side_effect=TimeoutError):
            conn = CacheConnect.redis_connect(self)
            self.assertIsNone(conn)

    def test_redis_connect_connection_error(self):
        with patch("redis.cluster.RedisCluster", side_effect=ConnectionError):
            conn = CacheConnect.redis_connect(self)
            self.assertIsNone(conn)

    def test_redis_connect_unexpected_error(self):
        with patch("redis.cluster.RedisCluster", side_effect=Exception):
            conn = CacheConnect.redis_connect(self)
            self.assertIsNone(conn)

    def test_valkey_connect_missing_env_vars(self):
        self.tearDown()
        conn = CacheConnect.valkey_connect(self)
        self.assertIsNone(conn)

    def test_valkey_connect_cluster_down_error(self):
        with patch("valkey.cluster.ValkeyCluster", side_effect=ValkeyClusterDownError):
            conn = CacheConnect.valkey_connect(self)
            self.assertIsNone(conn)

    def test_valkey_connect_timeout_error(self):
        with patch("valkey.cluster.ValkeyCluster", side_effect=ValkeyTimeoutError):
            conn = CacheConnect.valkey_connect(self)
            self.assertIsNone(conn)

    def test_valkey_connect_connection_error(self):
        with patch("valkey.cluster.ValkeyCluster", side_effect=ValkeyConnectionError):
            conn = CacheConnect.valkey_connect(self)
            self.assertIsNone(conn)

    def test_valkey_connect_unexpected_error(self):
        with patch("valkey.cluster.ValkeyCluster", side_effect=Exception):
            conn = CacheConnect.valkey_connect(self)
            self.assertIsNone(conn)

    def test_redis_standalone_connect_success(self):
        with patch("cache_benchmark.cash_connect.Redis") as mock_redis:
            mock_conn = Mock()
            mock_redis.return_value = mock_conn
            conn = CacheConnect.redis_standalone_connect(self)
            self.assertIsNotNone(conn)
            mock_conn.ping.assert_called_once()

    def test_redis_standalone_connect_missing_env_vars(self):
        self.tearDown()
        conn = CacheConnect.redis_standalone_connect(self)
        self.assertIsNone(conn)

    def test_redis_standalone_connect_timeout_error(self):
        with patch("cache_benchmark.cash_connect.Redis") as mock_redis:
            mock_conn = Mock()
            mock_conn.ping.side_effect = TimeoutError
            mock_redis.return_value = mock_conn
            conn = CacheConnect.redis_standalone_connect(self)
            self.assertIsNone(conn)

    def test_redis_standalone_connect_connection_error(self):
        with patch("cache_benchmark.cash_connect.Redis") as mock_redis:
            mock_conn = Mock()
            mock_conn.ping.side_effect = ConnectionError
            mock_redis.return_value = mock_conn
            conn = CacheConnect.redis_standalone_connect(self)
            self.assertIsNone(conn)

    def test_valkey_standalone_connect_success(self):
        with patch("cache_benchmark.cash_connect.Valkey") as mock_valkey:
            mock_conn = Mock()
            mock_valkey.return_value = mock_conn
            conn = CacheConnect.valkey_standalone_connect(self)
            self.assertIsNotNone(conn)
            mock_conn.ping.assert_called_once()

    def test_valkey_standalone_connect_missing_env_vars(self):
        self.tearDown()
        conn = CacheConnect.valkey_standalone_connect(self)
        self.assertIsNone(conn)

    def test_valkey_standalone_connect_timeout_error(self):
        with patch("cache_benchmark.cash_connect.Valkey") as mock_valkey:
            mock_conn = Mock()
            mock_conn.ping.side_effect = ValkeyTimeoutError
            mock_valkey.return_value = mock_conn
            conn = CacheConnect.valkey_standalone_connect(self)
            self.assertIsNone(conn)

    def test_valkey_standalone_connect_connection_error(self):
        with patch("cache_benchmark.cash_connect.Valkey") as mock_valkey:
            mock_conn = Mock()
            mock_conn.ping.side_effect = ValkeyConnectionError
            mock_valkey.return_value = mock_conn
            conn = CacheConnect.valkey_standalone_connect(self)
            self.assertIsNone(conn)
