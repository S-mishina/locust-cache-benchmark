import os
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock
from cache_benchmark.utils import (
    generate_string,
    init_cache_set,
    save_results_to_csv,
    locust_runner_cash_benchmark,
    locust_master_runner_benchmark,
    locust_worker_runner_benchmark,
)
from cache_benchmark.config import AppConfig, set_config, reset_config


class TestGenerateString(unittest.TestCase):
    def test_generate_string(self):
        result = generate_string(1)
        self.assertIsInstance(result, str)

    def test_generate_string_length(self):
        result = generate_string(2)
        self.assertEqual(len(result), 2 * 1024)

    def test_generate_string_content(self):
        result = generate_string(1)
        self.assertEqual(result, "A" * 1024)

    def test_generate_string_accepts_string_input(self):
        result = generate_string("3")
        self.assertEqual(len(result), 3 * 1024)


class TestInitCacheSet(unittest.TestCase):
    def test_init_cache_set(self):
        cache_client = Mock()
        cache_client.get.return_value = None
        cache_client.set.return_value = True
        init_cache_set(cache_client, "test_value", 60, 1000)
        self.assertEqual(cache_client.set.call_count, 1000)
        self.assertEqual(cache_client.get.call_count, 1000)

    def test_init_cache_set_custom_keys(self):
        cache_client = Mock()
        cache_client.get.return_value = None
        cache_client.set.return_value = True
        init_cache_set(cache_client, "test_value", 60, 50)
        self.assertEqual(cache_client.set.call_count, 50)
        self.assertEqual(cache_client.get.call_count, 50)

    def test_init_cache_set_default_keys(self):
        cache_client = Mock()
        cache_client.get.return_value = None
        cache_client.set.return_value = True
        init_cache_set(cache_client, "test_value", 60)
        self.assertEqual(cache_client.set.call_count, 1000)
        self.assertEqual(cache_client.get.call_count, 1000)

    def test_init_cache_set_skips_existing_keys(self):
        cache_client = Mock()
        cache_client.get.return_value = "already_exists"
        init_cache_set(cache_client, "test_value", 60, 10)
        self.assertEqual(cache_client.get.call_count, 10)
        cache_client.set.assert_not_called()

    def test_init_cache_set_none_client_exits(self):
        with self.assertRaises(SystemExit) as ctx:
            init_cache_set(None, "test_value", 60, 10)
        self.assertEqual(ctx.exception.code, 1)


class TestSaveResultsToCsv(unittest.TestCase):
    def test_save_results_to_csv(self):
        mock_entry = Mock()
        mock_entry.num_requests = 100
        mock_entry.num_failures = 2
        mock_entry.avg_response_time = 15.5
        mock_entry.min_response_time = 1.0
        mock_entry.max_response_time = 50.0
        mock_entry.current_rps = 10.0

        mock_stats = Mock()
        mock_stats.entries = {("GET /test", "GET"): mock_entry}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            tmpfile = f.name

        try:
            save_results_to_csv(mock_stats, filename=tmpfile)
            with open(tmpfile, "r") as f:
                content = f.read()
            self.assertIn("Request Name", content)
            self.assertIn("100", content)
            self.assertIn("15.5", content)
        finally:
            os.unlink(tmpfile)

    def test_save_results_to_csv_empty_stats(self):
        mock_stats = Mock()
        mock_stats.entries = {}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            tmpfile = f.name

        try:
            save_results_to_csv(mock_stats, filename=tmpfile)
            with open(tmpfile, "r") as f:
                lines = f.readlines()
            self.assertEqual(len(lines), 1)  # header only
        finally:
            os.unlink(tmpfile)


@patch("cache_benchmark.utils.shutdown_otel_tracing")
@patch("cache_benchmark.utils.save_results_to_csv")
@patch("cache_benchmark.utils.gevent")
@patch("cache_benchmark.utils.stats_printer")
@patch("cache_benchmark.utils.LocalRunner")
@patch("cache_benchmark.utils.Environment")
@patch("cache_benchmark.utils.setup_otel_tracing")
class TestLocustRunnerCashBenchmark(unittest.TestCase):
    def setUp(self):
        self.config = AppConfig(
            cache_host="localhost",
            cache_port=6379,
            connections=5,
            spawn_rate=2,
            request_rate=1.0,
            duration=10,
        )

    def test_locust_runner_cash_benchmark(
        self, mock_setup_otel, mock_env_cls, mock_runner_cls,
        mock_stats_printer, mock_gevent, mock_save_csv, mock_shutdown_otel,
    ):
        mock_env = MagicMock()
        mock_env_cls.return_value = mock_env
        mock_runner = MagicMock()
        mock_runner_cls.return_value = mock_runner
        mock_user_cls = MagicMock()

        locust_runner_cash_benchmark(self.config, mock_user_cls)

        mock_setup_otel.assert_called_once()
        mock_env_cls.assert_called_once_with(user_classes=[mock_user_cls])
        mock_runner_cls.assert_called_once_with(mock_env)
        mock_runner.start.assert_called_once_with(user_count=5, spawn_rate=2)
        mock_gevent.sleep.assert_called_once_with(10)
        mock_runner.quit.assert_called_once()
        mock_save_csv.assert_called_once()
        mock_shutdown_otel.assert_called_once()


@patch("cache_benchmark.utils.shutdown_otel_tracing")
@patch("cache_benchmark.utils.save_results_to_csv")
@patch("cache_benchmark.utils.gevent")
@patch("cache_benchmark.utils.time")
@patch("cache_benchmark.utils.stats_printer")
@patch("cache_benchmark.utils.MasterRunner")
@patch("cache_benchmark.utils.Environment")
@patch("cache_benchmark.utils.setup_otel_tracing")
class TestLocustMasterRunnerBenchmark(unittest.TestCase):
    def setUp(self):
        self.config = AppConfig(
            cache_host="localhost",
            cache_port=6379,
            connections=5,
            spawn_rate=2,
            request_rate=1.0,
            duration=10,
            master_bind_host="127.0.0.1",
            master_bind_port=5557,
            num_workers=1,
        )

    def test_locust_master_runner_benchmark(
        self, mock_setup_otel, mock_env_cls, mock_runner_cls,
        mock_stats_printer, mock_time, mock_gevent, mock_save_csv, mock_shutdown_otel,
    ):
        mock_env = MagicMock()
        mock_env_cls.return_value = mock_env
        mock_runner = MagicMock()
        # Simulate: first call has 0 clients, second call has 1 (enough workers)
        mock_runner.clients = {"worker1": Mock()}
        mock_runner_cls.return_value = mock_runner
        mock_user_cls = MagicMock()

        locust_master_runner_benchmark(self.config, mock_user_cls)

        mock_setup_otel.assert_called_once()
        mock_env_cls.assert_called_once_with(user_classes=[mock_user_cls])
        mock_runner_cls.assert_called_once_with(
            mock_env,
            master_bind_host="127.0.0.1",
            master_bind_port=5557,
        )
        mock_runner.start.assert_called_once_with(user_count=5, spawn_rate=2)
        mock_gevent.sleep.assert_called_once_with(10)
        mock_runner.quit.assert_called_once()
        mock_save_csv.assert_called_once()
        mock_shutdown_otel.assert_called_once()

    def test_master_waits_for_workers(
        self, mock_setup_otel, mock_env_cls, mock_runner_cls,
        mock_stats_printer, mock_time, mock_gevent, mock_save_csv, mock_shutdown_otel,
    ):
        mock_env = MagicMock()
        mock_env_cls.return_value = mock_env
        mock_runner = MagicMock()

        call_count = 0
        def clients_property():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                return {}
            return {"worker1": Mock()}

        type(mock_runner).clients = unittest.mock.PropertyMock(side_effect=clients_property)
        mock_runner_cls.return_value = mock_runner
        mock_user_cls = MagicMock()

        locust_master_runner_benchmark(self.config, mock_user_cls)

        self.assertTrue(mock_time.sleep.call_count >= 1)


@patch("cache_benchmark.utils.shutdown_otel_tracing")
@patch("cache_benchmark.utils.WorkerRunner")
@patch("cache_benchmark.utils.Environment")
@patch("cache_benchmark.utils.setup_otel_tracing")
class TestLocustWorkerRunnerBenchmark(unittest.TestCase):
    def setUp(self):
        self.config = AppConfig(
            cache_host="localhost",
            cache_port=6379,
            request_rate=1.0,
            master_bind_host="127.0.0.1",
            master_bind_port=5557,
        )

    def test_locust_worker_runner_benchmark(
        self, mock_setup_otel, mock_env_cls, mock_runner_cls, mock_shutdown_otel,
    ):
        mock_env = MagicMock()
        mock_env_cls.return_value = mock_env
        mock_runner = MagicMock()
        mock_runner_cls.return_value = mock_runner
        mock_user_cls = MagicMock()

        locust_worker_runner_benchmark(self.config, mock_user_cls)

        mock_setup_otel.assert_called_once()
        mock_env_cls.assert_called_once_with(user_classes=[mock_user_cls])
        mock_runner_cls.assert_called_once_with(
            mock_env,
            master_host="127.0.0.1",
            master_port=5557,
        )
        mock_runner.greenlet.join.assert_called_once()
        mock_shutdown_otel.assert_called_once()


if __name__ == "__main__":
    unittest.main()
