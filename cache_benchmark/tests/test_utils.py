import unittest
from unittest.mock import Mock
from cache_benchmark.utils import generate_string, init_cache_set


class TestUtils(unittest.TestCase):
    def test_generate_string(self):
        result = generate_string(1)
        self.assertIsInstance(result, str)

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
