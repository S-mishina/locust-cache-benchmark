import unittest
from unittest.mock import patch, MagicMock
from cache_benchmark.main import (
    main, redis_load_test, valkey_load_test, init_redis_load_test, init_valkey_load_test, cluster_valkey_load_test,
    redis_standalone_load_test, valkey_standalone_load_test,
    cluster_redis_standalone_load_test, cluster_valkey_standalone_load_test,
    init_redis_standalone_load_test, init_valkey_standalone_load_test,
)
from cache_benchmark.config import AppConfig, reset_config
from cache_benchmark.scenario import RedisUser

class TestMain(unittest.TestCase):

    def tearDown(self):
        reset_config()

    def _make_args(self, **overrides):
        args = MagicMock()
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
        for k, v in overrides.items():
            setattr(args, k, v)
        return args

    @patch('cache_benchmark.main.locust_runner_cash_benchmark')
    def test_redis_load_test(self, mock_locust_runner):
        args = self._make_args()
        redis_load_test(args)
        mock_locust_runner.assert_called_once()
        call_args = mock_locust_runner.call_args
        self.assertIsInstance(call_args[0][0], AppConfig)
        self.assertEqual(call_args[0][0].cache_type, "redis_cluster")
        self.assertIs(call_args[0][1], RedisUser)

    @patch('cache_benchmark.main.locust_runner_cash_benchmark')
    def test_valkey_load_test(self, mock_locust_runner):
        args = self._make_args()
        valkey_load_test(args)
        mock_locust_runner.assert_called_once()
        call_args = mock_locust_runner.call_args
        self.assertIsInstance(call_args[0][0], AppConfig)
        self.assertEqual(call_args[0][0].cache_type, "valkey_cluster")

    @patch('cache_benchmark.main.CacheConnect.valkey_connect')
    @patch('cache_benchmark.main.generate_string')
    @patch('cache_benchmark.main.init_cache_set')
    def test_init_valkey_load_test_success(self, mock_init_cache_set, mock_generate_string, mock_valkey_connect):
        args = self._make_args(set_keys=500)
        mock_valkey_connect.return_value = MagicMock()
        mock_generate_string.return_value = "test_value"
        init_valkey_load_test(args)
        mock_valkey_connect.assert_called_once()
        mock_generate_string.assert_called_once_with(1)
        mock_init_cache_set.assert_called_once_with(mock_valkey_connect.return_value, "test_value", 60, 500)

    @patch('cache_benchmark.main.CacheConnect.redis_connect')
    @patch('cache_benchmark.main.generate_string')
    @patch('cache_benchmark.main.init_cache_set')
    def test_init_redis_load_test_success(self, mock_init_cache_set, mock_generate_string, mock_redis_connect):
        args = self._make_args(set_keys=1000)
        mock_redis_connect.return_value = MagicMock()
        mock_generate_string.return_value = "test_value"
        init_redis_load_test(args)
        mock_redis_connect.assert_called_once()
        mock_generate_string.assert_called_once_with(1)
        mock_init_cache_set.assert_called_once_with(mock_redis_connect.return_value, "test_value", 60, 1000)

    @patch('cache_benchmark.main.locust_master_runner_benchmark')
    def test_cluster_valkey_load_test_master(self, mock_master_runner):
        args = self._make_args(cluster_mode="master")
        cluster_valkey_load_test(args)
        mock_master_runner.assert_called_once()
        call_args = mock_master_runner.call_args
        self.assertIsInstance(call_args[0][0], AppConfig)
        self.assertEqual(call_args[0][0].cache_type, "valkey_cluster")

    @patch('cache_benchmark.main.locust_worker_runner_benchmark')
    def test_cluster_valkey_load_test_worker(self, mock_worker_runner):
        args = self._make_args(cluster_mode="worker")
        cluster_valkey_load_test(args)
        mock_worker_runner.assert_called_once()
        call_args = mock_worker_runner.call_args
        self.assertIsInstance(call_args[0][0], AppConfig)
        self.assertEqual(call_args[0][0].cache_type, "valkey_cluster")

    @patch('cache_benchmark.main.sys.exit')
    def test_cluster_valkey_load_test_no_mode(self, mock_exit):
        args = MagicMock()
        args.cluster_mode = None
        cluster_valkey_load_test(args)
        mock_exit.assert_called_with(1)

    @patch('cache_benchmark.main.locust_runner_cash_benchmark')
    def test_redis_standalone_load_test(self, mock_locust_runner):
        args = self._make_args()
        redis_standalone_load_test(args)
        mock_locust_runner.assert_called_once()
        call_args = mock_locust_runner.call_args
        self.assertIsInstance(call_args[0][0], AppConfig)
        self.assertEqual(call_args[0][0].cache_type, "redis")

    @patch('cache_benchmark.main.locust_runner_cash_benchmark')
    def test_valkey_standalone_load_test(self, mock_locust_runner):
        args = self._make_args()
        valkey_standalone_load_test(args)
        mock_locust_runner.assert_called_once()
        call_args = mock_locust_runner.call_args
        self.assertIsInstance(call_args[0][0], AppConfig)
        self.assertEqual(call_args[0][0].cache_type, "valkey")

    @patch('cache_benchmark.main.locust_master_runner_benchmark')
    def test_cluster_redis_standalone_load_test_master(self, mock_master_runner):
        args = self._make_args(cluster_mode="master")
        cluster_redis_standalone_load_test(args)
        mock_master_runner.assert_called_once()
        call_args = mock_master_runner.call_args
        self.assertIsInstance(call_args[0][0], AppConfig)
        self.assertEqual(call_args[0][0].cache_type, "redis")

    @patch('cache_benchmark.main.locust_worker_runner_benchmark')
    def test_cluster_redis_standalone_load_test_worker(self, mock_worker_runner):
        args = self._make_args(cluster_mode="worker")
        cluster_redis_standalone_load_test(args)
        mock_worker_runner.assert_called_once()
        call_args = mock_worker_runner.call_args
        self.assertIsInstance(call_args[0][0], AppConfig)
        self.assertEqual(call_args[0][0].cache_type, "redis")

    @patch('cache_benchmark.main.sys.exit')
    def test_cluster_redis_standalone_load_test_no_mode(self, mock_exit):
        args = MagicMock()
        args.cluster_mode = None
        cluster_redis_standalone_load_test(args)
        mock_exit.assert_called_with(1)

    @patch('cache_benchmark.main.locust_master_runner_benchmark')
    def test_cluster_valkey_standalone_load_test_master(self, mock_master_runner):
        args = self._make_args(cluster_mode="master")
        cluster_valkey_standalone_load_test(args)
        mock_master_runner.assert_called_once()
        call_args = mock_master_runner.call_args
        self.assertIsInstance(call_args[0][0], AppConfig)
        self.assertEqual(call_args[0][0].cache_type, "valkey")

    @patch('cache_benchmark.main.locust_worker_runner_benchmark')
    def test_cluster_valkey_standalone_load_test_worker(self, mock_worker_runner):
        args = self._make_args(cluster_mode="worker")
        cluster_valkey_standalone_load_test(args)
        mock_worker_runner.assert_called_once()
        call_args = mock_worker_runner.call_args
        self.assertIsInstance(call_args[0][0], AppConfig)
        self.assertEqual(call_args[0][0].cache_type, "valkey")

    @patch('cache_benchmark.main.sys.exit')
    def test_cluster_valkey_standalone_load_test_no_mode(self, mock_exit):
        args = MagicMock()
        args.cluster_mode = None
        cluster_valkey_standalone_load_test(args)
        mock_exit.assert_called_with(1)

    @patch('cache_benchmark.main.CacheConnect.redis_standalone_connect')
    @patch('cache_benchmark.main.generate_string')
    @patch('cache_benchmark.main.init_cache_set')
    def test_init_redis_standalone_load_test_success(self, mock_init_cache_set, mock_generate_string, mock_redis_standalone_connect):
        args = self._make_args(set_keys=1000)
        mock_redis_standalone_connect.return_value = MagicMock()
        mock_generate_string.return_value = "test_value"
        init_redis_standalone_load_test(args)
        mock_redis_standalone_connect.assert_called_once()
        mock_generate_string.assert_called_once_with(1)
        mock_init_cache_set.assert_called_once_with(mock_redis_standalone_connect.return_value, "test_value", 60, 1000)

    @patch('cache_benchmark.main.CacheConnect.valkey_standalone_connect')
    @patch('cache_benchmark.main.generate_string')
    @patch('cache_benchmark.main.init_cache_set')
    def test_init_valkey_standalone_load_test_success(self, mock_init_cache_set, mock_generate_string, mock_valkey_standalone_connect):
        args = self._make_args(set_keys=500)
        mock_valkey_standalone_connect.return_value = MagicMock()
        mock_generate_string.return_value = "test_value"
        init_valkey_standalone_load_test(args)
        mock_valkey_standalone_connect.assert_called_once()
        mock_generate_string.assert_called_once_with(1)
        mock_init_cache_set.assert_called_once_with(mock_valkey_standalone_connect.return_value, "test_value", 60, 500)

    @patch('argparse.ArgumentParser.parse_args')
    @patch('cache_benchmark.main.sys.exit')
    def test_main_no_args(self, mock_exit, mock_parse_args):
        mock_parse_args.return_value = MagicMock(command=None, subcommand=None)
        main()
        mock_exit.assert_called_once_with(1)

if __name__ == '__main__':
    unittest.main()
