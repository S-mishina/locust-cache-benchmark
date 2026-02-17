import unittest
from unittest.mock import patch, MagicMock
import sys
from cache_benchmark.main import (
    main, redis_load_test, valkey_load_test, init_redis_load_test, init_valkey_load_test, cluster_valkey_load_test,
    redis_standalone_load_test, valkey_standalone_load_test,
    cluster_redis_standalone_load_test, cluster_valkey_standalone_load_test,
    init_redis_standalone_load_test, init_valkey_standalone_load_test,
)
from cache_benchmark.scenario import RedisUser

class TestMain(unittest.TestCase):

    @patch('cache_benchmark.main.set_env_cache_retry')
    @patch('cache_benchmark.main.set_env_vars')
    @patch('cache_benchmark.main.locust_runner_cash_benchmark')
    def test_redis_load_test(self, mock_locust_runner, mock_set_env_vars, mock_set_env_cache_retry):
        args = MagicMock()
        redis_load_test(args)
        mock_set_env_vars.assert_called_once_with(args)
        mock_set_env_cache_retry.assert_called_once_with(args)
        mock_locust_runner.assert_called_once_with(args, RedisUser)

    @patch('cache_benchmark.main.set_env_cache_retry')
    @patch('cache_benchmark.main.set_env_vars')
    @patch('cache_benchmark.main.locust_runner_cash_benchmark')
    def test_valkey_load_test(self, mock_locust_runner, mock_set_env_vars, mock_set_env_cache_retry):
        args = MagicMock()
        valkey_load_test(args)
        mock_set_env_vars.assert_called_once_with(args)
        mock_set_env_cache_retry.assert_called_once_with(args)
        mock_locust_runner.assert_called_once_with(args, RedisUser)

    @patch('cache_benchmark.main.set_env_cache_retry')
    @patch('cache_benchmark.main.set_env_vars')
    @patch('cache_benchmark.main.CacheConnect.valkey_connect')
    @patch('cache_benchmark.main.generate_string')
    @patch('cache_benchmark.main.init_cache_set')
    @patch.dict('os.environ', {'TTL': '60'})
    def test_init_valkey_load_test_success(self, mock_init_cache_set, mock_generate_string, mock_valkey_connect, mock_set_env_vars, mock_set_env_cache_retry):
        args = MagicMock()
        args.set_keys = 500
        mock_valkey_connect.return_value = MagicMock()
        mock_generate_string.return_value = "test_value"
        init_valkey_load_test(args)
        mock_set_env_vars.assert_called_once_with(args)
        mock_set_env_cache_retry.assert_called_once_with(args)
        mock_valkey_connect.assert_called_once()
        mock_generate_string.assert_called_once_with(args.value_size)
        mock_init_cache_set.assert_called_once_with(mock_valkey_connect.return_value, "test_value", 60, 500)

    @patch('cache_benchmark.main.set_env_cache_retry')
    @patch('cache_benchmark.main.set_env_vars')
    @patch('cache_benchmark.main.CacheConnect.redis_connect')
    @patch('cache_benchmark.main.generate_string')
    @patch('cache_benchmark.main.init_cache_set')
    @patch.dict('os.environ', {'TTL': '60'})
    def test_init_redis_load_test_success(self, mock_init_cache_set, mock_generate_string, mock_redis_connect, mock_set_env_vars, mock_set_env_cache_retry):
        args = MagicMock()
        args.set_keys = 1000
        mock_redis_connect.return_value = MagicMock()
        mock_generate_string.return_value = "test_value"
        init_redis_load_test(args)
        mock_set_env_vars.assert_called_once_with(args)
        mock_set_env_cache_retry.assert_called_once_with(args)
        mock_redis_connect.assert_called_once()
        mock_generate_string.assert_called_once_with(args.value_size)
        mock_init_cache_set.assert_called_once_with(mock_redis_connect.return_value, "test_value", 60, 1000)

    @patch('cache_benchmark.main.set_env_cache_retry')
    @patch('cache_benchmark.main.set_env_vars')
    @patch('cache_benchmark.main.locust_master_runner_benchmark')
    def test_cluster_valkey_load_test_master(self, mock_master_runner, mock_set_env_vars, mock_set_env_cache_retry):
        args = MagicMock()
        args.cluster_mode = "master"
        cluster_valkey_load_test(args)
        mock_set_env_vars.assert_called_once_with(args)
        mock_set_env_cache_retry.assert_called_once_with(args)
        mock_master_runner.assert_called_once_with(args, RedisUser)

    @patch('cache_benchmark.main.set_env_cache_retry')
    @patch('cache_benchmark.main.set_env_vars')
    @patch('cache_benchmark.main.locust_worker_runner_benchmark')
    def test_cluster_valkey_load_test_worker(self, mock_worker_runner, mock_set_env_vars, mock_set_env_cache_retry):
        args = MagicMock()
        args.cluster_mode = "worker"
        cluster_valkey_load_test(args)
        mock_set_env_vars.assert_called_once_with(args)
        mock_set_env_cache_retry.assert_called_once_with(args)
        mock_worker_runner.assert_called_once_with(args, RedisUser)

    @patch('cache_benchmark.main.sys.exit')
    def test_cluster_valkey_load_test_no_mode(self, mock_exit):
        args = MagicMock()
        args.cluster_mode = None
        cluster_valkey_load_test(args)
        mock_exit.assert_called_with(1)

    @patch('cache_benchmark.main.set_env_cache_retry')
    @patch('cache_benchmark.main.set_env_vars')
    @patch('cache_benchmark.main.locust_runner_cash_benchmark')
    def test_redis_standalone_load_test(self, mock_locust_runner, mock_set_env_vars, mock_set_env_cache_retry):
        args = MagicMock()
        redis_standalone_load_test(args)
        mock_set_env_vars.assert_called_once_with(args)
        mock_set_env_cache_retry.assert_called_once_with(args)
        mock_locust_runner.assert_called_once_with(args, RedisUser)

    @patch('cache_benchmark.main.set_env_cache_retry')
    @patch('cache_benchmark.main.set_env_vars')
    @patch('cache_benchmark.main.locust_runner_cash_benchmark')
    def test_valkey_standalone_load_test(self, mock_locust_runner, mock_set_env_vars, mock_set_env_cache_retry):
        args = MagicMock()
        valkey_standalone_load_test(args)
        mock_set_env_vars.assert_called_once_with(args)
        mock_set_env_cache_retry.assert_called_once_with(args)
        mock_locust_runner.assert_called_once_with(args, RedisUser)

    @patch('cache_benchmark.main.set_env_cache_retry')
    @patch('cache_benchmark.main.set_env_vars')
    @patch('cache_benchmark.main.locust_master_runner_benchmark')
    def test_cluster_redis_standalone_load_test_master(self, mock_master_runner, mock_set_env_vars, mock_set_env_cache_retry):
        args = MagicMock()
        args.cluster_mode = "master"
        cluster_redis_standalone_load_test(args)
        mock_set_env_vars.assert_called_once_with(args)
        mock_set_env_cache_retry.assert_called_once_with(args)
        mock_master_runner.assert_called_once_with(args, RedisUser)

    @patch('cache_benchmark.main.set_env_cache_retry')
    @patch('cache_benchmark.main.set_env_vars')
    @patch('cache_benchmark.main.locust_worker_runner_benchmark')
    def test_cluster_redis_standalone_load_test_worker(self, mock_worker_runner, mock_set_env_vars, mock_set_env_cache_retry):
        args = MagicMock()
        args.cluster_mode = "worker"
        cluster_redis_standalone_load_test(args)
        mock_set_env_vars.assert_called_once_with(args)
        mock_set_env_cache_retry.assert_called_once_with(args)
        mock_worker_runner.assert_called_once_with(args, RedisUser)

    @patch('cache_benchmark.main.sys.exit')
    def test_cluster_redis_standalone_load_test_no_mode(self, mock_exit):
        args = MagicMock()
        args.cluster_mode = None
        cluster_redis_standalone_load_test(args)
        mock_exit.assert_called_with(1)

    @patch('cache_benchmark.main.set_env_cache_retry')
    @patch('cache_benchmark.main.set_env_vars')
    @patch('cache_benchmark.main.locust_master_runner_benchmark')
    def test_cluster_valkey_standalone_load_test_master(self, mock_master_runner, mock_set_env_vars, mock_set_env_cache_retry):
        args = MagicMock()
        args.cluster_mode = "master"
        cluster_valkey_standalone_load_test(args)
        mock_set_env_vars.assert_called_once_with(args)
        mock_set_env_cache_retry.assert_called_once_with(args)
        mock_master_runner.assert_called_once_with(args, RedisUser)

    @patch('cache_benchmark.main.set_env_cache_retry')
    @patch('cache_benchmark.main.set_env_vars')
    @patch('cache_benchmark.main.locust_worker_runner_benchmark')
    def test_cluster_valkey_standalone_load_test_worker(self, mock_worker_runner, mock_set_env_vars, mock_set_env_cache_retry):
        args = MagicMock()
        args.cluster_mode = "worker"
        cluster_valkey_standalone_load_test(args)
        mock_set_env_vars.assert_called_once_with(args)
        mock_set_env_cache_retry.assert_called_once_with(args)
        mock_worker_runner.assert_called_once_with(args, RedisUser)

    @patch('cache_benchmark.main.sys.exit')
    def test_cluster_valkey_standalone_load_test_no_mode(self, mock_exit):
        args = MagicMock()
        args.cluster_mode = None
        cluster_valkey_standalone_load_test(args)
        mock_exit.assert_called_with(1)

    @patch('cache_benchmark.main.set_env_cache_retry')
    @patch('cache_benchmark.main.set_env_vars')
    @patch('cache_benchmark.main.CacheConnect.redis_standalone_connect')
    @patch('cache_benchmark.main.generate_string')
    @patch('cache_benchmark.main.init_cache_set')
    @patch.dict('os.environ', {'TTL': '60'})
    def test_init_redis_standalone_load_test_success(self, mock_init_cache_set, mock_generate_string, mock_redis_standalone_connect, mock_set_env_vars, mock_set_env_cache_retry):
        args = MagicMock()
        args.set_keys = 1000
        mock_redis_standalone_connect.return_value = MagicMock()
        mock_generate_string.return_value = "test_value"
        init_redis_standalone_load_test(args)
        mock_set_env_vars.assert_called_once_with(args)
        mock_set_env_cache_retry.assert_called_once_with(args)
        mock_redis_standalone_connect.assert_called_once()
        mock_generate_string.assert_called_once_with(args.value_size)
        mock_init_cache_set.assert_called_once_with(mock_redis_standalone_connect.return_value, "test_value", 60, 1000)

    @patch('cache_benchmark.main.set_env_cache_retry')
    @patch('cache_benchmark.main.set_env_vars')
    @patch('cache_benchmark.main.CacheConnect.valkey_standalone_connect')
    @patch('cache_benchmark.main.generate_string')
    @patch('cache_benchmark.main.init_cache_set')
    @patch.dict('os.environ', {'TTL': '60'})
    def test_init_valkey_standalone_load_test_success(self, mock_init_cache_set, mock_generate_string, mock_valkey_standalone_connect, mock_set_env_vars, mock_set_env_cache_retry):
        args = MagicMock()
        args.set_keys = 500
        mock_valkey_standalone_connect.return_value = MagicMock()
        mock_generate_string.return_value = "test_value"
        init_valkey_standalone_load_test(args)
        mock_set_env_vars.assert_called_once_with(args)
        mock_set_env_cache_retry.assert_called_once_with(args)
        mock_valkey_standalone_connect.assert_called_once()
        mock_generate_string.assert_called_once_with(args.value_size)
        mock_init_cache_set.assert_called_once_with(mock_valkey_standalone_connect.return_value, "test_value", 60, 500)

    @patch('argparse.ArgumentParser.parse_args')
    @patch('cache_benchmark.main.sys.exit')
    def test_main_no_args(self, mock_exit, mock_parse_args):
        mock_parse_args.return_value = MagicMock(command=None, subcommand=None)
        main()
        mock_exit.assert_called_once_with(1)

if __name__ == '__main__':
    unittest.main()
