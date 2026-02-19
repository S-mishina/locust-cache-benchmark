import os
import unittest
from unittest.mock import Mock
from cache_benchmark.locust_cache import LocustCache, _get_request_type, _get_db_system


class TestGetRequestType(unittest.TestCase):
    def setUp(self):
        os.environ.pop("CACHE_TYPE", None)

    def tearDown(self):
        os.environ.pop("CACHE_TYPE", None)

    def test_default_returns_redis(self):
        self.assertEqual(_get_request_type(), "Redis")

    def test_redis_cluster(self):
        os.environ["CACHE_TYPE"] = "redis_cluster"
        self.assertEqual(_get_request_type(), "Redis")

    def test_redis_standalone(self):
        os.environ["CACHE_TYPE"] = "redis"
        self.assertEqual(_get_request_type(), "Redis")

    def test_valkey_cluster(self):
        os.environ["CACHE_TYPE"] = "valkey_cluster"
        self.assertEqual(_get_request_type(), "Valkey")

    def test_valkey_standalone(self):
        os.environ["CACHE_TYPE"] = "valkey"
        self.assertEqual(_get_request_type(), "Valkey")


class TestGetDbSystem(unittest.TestCase):
    def setUp(self):
        os.environ.pop("CACHE_TYPE", None)

    def tearDown(self):
        os.environ.pop("CACHE_TYPE", None)

    def test_default_returns_redis(self):
        self.assertEqual(_get_db_system(), "redis")

    def test_valkey_cluster(self):
        os.environ["CACHE_TYPE"] = "valkey_cluster"
        self.assertEqual(_get_db_system(), "valkey")

    def test_valkey_standalone(self):
        os.environ["CACHE_TYPE"] = "valkey"
        self.assertEqual(_get_db_system(), "valkey")


class TestLocustCacheGet(unittest.TestCase):
    def setUp(self):
        self.locust_cache = LocustCache()
        self.locust_cache.user = Mock()
        self.mock_fire = self.locust_cache.user.environment.events.request.fire
        self.mock_conn = Mock()

    def test_get_success(self):
        self.mock_conn.get.return_value = "test_value"
        result = self.locust_cache.locust_redis_get(self.mock_conn, "key1", "test")
        self.assertEqual(result, "test_value")
        self.mock_conn.get.assert_called_once_with("key1")
        self.mock_fire.assert_called_once()
        call_kwargs = self.mock_fire.call_args[1]
        self.assertEqual(call_kwargs["name"], "get_value_test")
        self.assertIsNone(call_kwargs["exception"])

    def test_get_returns_none_on_miss(self):
        self.mock_conn.get.return_value = None
        result = self.locust_cache.locust_redis_get(self.mock_conn, "missing", "test")
        self.assertIsNone(result)
        self.mock_fire.assert_called_once()
        call_kwargs = self.mock_fire.call_args[1]
        self.assertIsNone(call_kwargs["exception"])

    def test_get_exception_returns_none(self):
        self.mock_conn.get.side_effect = ConnectionError("connection lost")
        result = self.locust_cache.locust_redis_get(self.mock_conn, "key1", "test")
        self.assertIsNone(result)
        self.mock_fire.assert_called_once()
        call_kwargs = self.mock_fire.call_args[1]
        self.assertIsInstance(call_kwargs["exception"], ConnectionError)

    def test_get_fires_request_with_response_time(self):
        self.mock_conn.get.return_value = "val"
        self.locust_cache.locust_redis_get(self.mock_conn, "key1", "test")
        call_kwargs = self.mock_fire.call_args[1]
        self.assertGreaterEqual(call_kwargs["response_time"], 0)


class TestLocustCacheSet(unittest.TestCase):
    def setUp(self):
        self.locust_cache = LocustCache()
        self.locust_cache.user = Mock()
        self.mock_fire = self.locust_cache.user.environment.events.request.fire
        self.mock_conn = Mock()

    def test_set_success(self):
        self.mock_conn.set.return_value = True
        result = self.locust_cache.locust_redis_set(self.mock_conn, "key1", "val1", "test", 60)
        self.assertTrue(result)
        self.mock_conn.set.assert_called_once_with("key1", "val1", ex=60)
        self.mock_fire.assert_called_once()
        call_kwargs = self.mock_fire.call_args[1]
        self.assertEqual(call_kwargs["name"], "set_value_test")
        self.assertIsNone(call_kwargs["exception"])

    def test_set_exception_returns_none(self):
        self.mock_conn.set.side_effect = TimeoutError("timeout")
        result = self.locust_cache.locust_redis_set(self.mock_conn, "key1", "val1", "test", 60)
        self.assertIsNone(result)
        self.mock_fire.assert_called_once()
        call_kwargs = self.mock_fire.call_args[1]
        self.assertIsInstance(call_kwargs["exception"], TimeoutError)

    def test_set_fires_request_with_response_time(self):
        self.mock_conn.set.return_value = True
        self.locust_cache.locust_redis_set(self.mock_conn, "key1", "val1", "test", 30)
        call_kwargs = self.mock_fire.call_args[1]
        self.assertGreaterEqual(call_kwargs["response_time"], 0)

    def test_set_ttl_passed_as_int(self):
        self.mock_conn.set.return_value = True
        self.locust_cache.locust_redis_set(self.mock_conn, "key1", "val1", "test", "120")
        self.mock_conn.set.assert_called_once_with("key1", "val1", ex=120)
