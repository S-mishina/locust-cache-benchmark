"""E2E tests for Valkey error trace verification.

Verify that exceptions in the actual code path
(LocustCache → cache_connection → _instrument_valkey)
produce proper OTel error traces.

Run:
    poetry run pytest cache_benchmark/tests/test_e2e_error_trace.py -v
"""

import unittest
from unittest.mock import Mock

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
    SpanExporter,
    SpanExportResult,
)

from cache_benchmark.config import AppConfig, set_config, reset_config
from cache_benchmark.locust_cache import LocustCache
import cache_benchmark.otel_setup as otel_setup


class _InMemorySpanExporter(SpanExporter):
    """Minimal in-memory span exporter for testing."""

    def __init__(self):
        self._spans = []

    def export(self, spans):
        self._spans.extend(spans)
        return SpanExportResult.SUCCESS

    def get_finished_spans(self):
        return list(self._spans)

    def clear(self):
        self._spans.clear()

    def shutdown(self):
        self._spans.clear()


def _reset_tracer_provider():
    """Reset OTel global TracerProvider to allow re-setting in tests."""
    trace._TRACER_PROVIDER_SET_ONCE._done = False
    trace._TRACER_PROVIDER = None


def _make_locust_task_mock():
    """Create a mock Locust task with environment.events.request.fire."""
    task = Mock()
    task.user.environment.events.request.fire = Mock()
    return task


class TestValkeyStandaloneErrorTrace(unittest.TestCase):
    """Verify error traces through LocustCache → Valkey standalone path."""

    def setUp(self):
        reset_config()
        set_config(AppConfig(cache_type="valkey"))
        otel_setup._otel_initialized = False
        otel_setup._valkey_instrumented = False

        _reset_tracer_provider()
        self.exporter = _InMemorySpanExporter()
        self.provider = TracerProvider()
        self.provider.add_span_processor(SimpleSpanProcessor(self.exporter))
        trace.set_tracer_provider(self.provider)

        otel_setup._instrument_valkey()

    def tearDown(self):
        self.provider.shutdown()
        otel_setup._otel_initialized = False
        otel_setup._valkey_instrumented = False
        reset_config()

    def _error_spans(self):
        return [
            s for s in self.exporter.get_finished_spans()
            if s.status.status_code == trace.StatusCode.ERROR
        ]

    def test_get_connection_error_produces_error_span(self):
        """LocustCache.locust_redis_get → ConnectionError → error span + Locust failure."""
        from valkey import Valkey

        conn = Valkey.__new__(Valkey)
        conn.auto_close_connection_pool = False
        conn.connection = None
        conn.connection_pool = Mock()
        conn.connection_pool.get_connection.side_effect = ConnectionError(
            "Too many connections"
        )

        task = _make_locust_task_mock()
        result = LocustCache.locust_redis_get(task, conn, "key1", "test")

        self.assertIsNone(result)

        # Locust recorded the failure
        fire = task.user.environment.events.request.fire
        fire.assert_called_once()
        call_kwargs = fire.call_args[1]
        self.assertIsInstance(call_kwargs["exception"], ConnectionError)
        self.assertEqual(call_kwargs["name"], "get_value_test")

        # OTel recorded the error span
        errors = self._error_spans()
        self.assertGreaterEqual(len(errors), 1)
        span = errors[0]
        self.assertEqual(span.attributes.get("db.system"), "valkey")
        exc_events = [e for e in span.events if e.name == "exception"]
        self.assertGreaterEqual(len(exc_events), 1)
        self.assertIn(
            "Too many connections",
            exc_events[0].attributes.get("exception.message", ""),
        )

    def test_set_connection_error_produces_error_span(self):
        """LocustCache.locust_redis_set → ConnectionError → error span + Locust failure."""
        from valkey import Valkey

        conn = Valkey.__new__(Valkey)
        conn.auto_close_connection_pool = False
        conn.connection = None
        conn.connection_pool = Mock()
        conn.connection_pool.get_connection.side_effect = ConnectionError(
            "Too many connections"
        )

        task = _make_locust_task_mock()
        result = LocustCache.locust_redis_set(task, conn, "key1", "val", "test", 60)

        self.assertIsNone(result)

        fire = task.user.environment.events.request.fire
        fire.assert_called_once()
        call_kwargs = fire.call_args[1]
        self.assertIsInstance(call_kwargs["exception"], ConnectionError)
        self.assertEqual(call_kwargs["name"], "set_value_test")

        errors = self._error_spans()
        self.assertGreaterEqual(len(errors), 1)

    def test_get_timeout_error_produces_error_span(self):
        """LocustCache.locust_redis_get → TimeoutError → error span."""
        from valkey import Valkey
        from valkey.exceptions import TimeoutError as ValkeyTimeoutError

        conn = Valkey.__new__(Valkey)
        conn.auto_close_connection_pool = False
        conn.connection = None
        conn.connection_pool = Mock()
        conn.connection_pool.get_connection.side_effect = ValkeyTimeoutError(
            "timed out"
        )

        task = _make_locust_task_mock()
        result = LocustCache.locust_redis_get(task, conn, "key1", "test")

        self.assertIsNone(result)

        errors = self._error_spans()
        self.assertGreaterEqual(len(errors), 1)

    def test_get_success_no_error_span(self):
        """LocustCache.locust_redis_get → success → no error span."""
        from valkey import Valkey

        conn = Valkey.__new__(Valkey)
        conn.auto_close_connection_pool = False
        conn.connection = None
        conn.connection_pool = Mock()

        mock_connection = Mock()
        mock_connection._get_from_local_cache.return_value = "cached"
        mock_connection.can_read.return_value = False
        mock_connection.client_cache = None
        conn.connection_pool.get_connection.return_value = mock_connection

        task = _make_locust_task_mock()
        LocustCache.locust_redis_get(task, conn, "key1", "test")

        fire = task.user.environment.events.request.fire
        fire.assert_called_once()
        call_kwargs = fire.call_args[1]
        self.assertIsNone(call_kwargs["exception"])

        errors = self._error_spans()
        self.assertEqual(len(errors), 0)


class TestValkeyClusterErrorTrace(unittest.TestCase):
    """Verify error traces through LocustCache → ValkeyCluster path."""

    def setUp(self):
        reset_config()
        set_config(AppConfig(cache_type="valkey_cluster"))
        otel_setup._otel_initialized = False
        otel_setup._valkey_instrumented = False

        _reset_tracer_provider()
        self.exporter = _InMemorySpanExporter()
        self.provider = TracerProvider()
        self.provider.add_span_processor(SimpleSpanProcessor(self.exporter))
        trace.set_tracer_provider(self.provider)

        otel_setup._instrument_valkey()

    def tearDown(self):
        self.provider.shutdown()
        otel_setup._otel_initialized = False
        otel_setup._valkey_instrumented = False
        reset_config()

    def _error_spans(self):
        return [
            s for s in self.exporter.get_finished_spans()
            if s.status.status_code == trace.StatusCode.ERROR
        ]

    def _make_cluster_conn(self, execute_side_effect=None, execute_return=None):
        from valkey.cluster import ValkeyCluster

        conn = ValkeyCluster.__new__(ValkeyCluster)
        conn.cluster_error_retry_attempts = 0

        target_node = Mock()
        target_node.name = "node1:7000"
        conn._is_nodes_flag = Mock(return_value=False)
        conn._determine_nodes = Mock(return_value=[target_node])
        conn.get_default_node = Mock(return_value=target_node)
        conn.replace_default_node = Mock()
        conn.nodes_manager = Mock()

        if execute_side_effect is not None:
            conn._execute_command = Mock(side_effect=execute_side_effect)
        else:
            conn._execute_command = Mock(return_value=execute_return)

        return conn

    def test_get_pool_exhaustion_produces_error_span(self):
        """LocustCache.locust_redis_get → ValkeyCluster ConnectionError
        → error span + Locust failure."""
        from valkey.exceptions import ConnectionError as VCE

        conn = self._make_cluster_conn(VCE("Too many connections"))

        task = _make_locust_task_mock()
        result = LocustCache.locust_redis_get(task, conn, "key1", "test")

        self.assertIsNone(result)

        fire = task.user.environment.events.request.fire
        fire.assert_called_once()
        call_kwargs = fire.call_args[1]
        self.assertIsNotNone(call_kwargs["exception"])
        self.assertEqual(call_kwargs["name"], "get_value_test")

        errors = self._error_spans()
        self.assertGreaterEqual(len(errors), 1)
        span = errors[0]
        self.assertEqual(span.attributes.get("db.system"), "valkey")

    def test_set_pool_exhaustion_produces_error_span(self):
        """LocustCache.locust_redis_set → ValkeyCluster ConnectionError
        → error span + Locust failure."""
        from valkey.exceptions import ConnectionError as VCE

        conn = self._make_cluster_conn(VCE("Too many connections"))

        task = _make_locust_task_mock()
        result = LocustCache.locust_redis_set(task, conn, "key1", "val", "test", 60)

        self.assertIsNone(result)

        fire = task.user.environment.events.request.fire
        fire.assert_called_once()
        call_kwargs = fire.call_args[1]
        self.assertIsNotNone(call_kwargs["exception"])

        errors = self._error_spans()
        self.assertGreaterEqual(len(errors), 1)

    def test_retry_success_silent(self):
        """LocustCache.locust_redis_get → ConnectionError → retry → success
        → Locust records success, NO error span."""
        from valkey.exceptions import ConnectionError as VCE

        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise VCE("Too many connections")
            return "ok"

        conn = self._make_cluster_conn(side_effect)
        conn.cluster_error_retry_attempts = 2
        conn._process_result = Mock(return_value="ok")

        task = _make_locust_task_mock()
        result = LocustCache.locust_redis_get(task, conn, "key1", "test")

        # Request succeeded (retry worked)
        self.assertIsNotNone(result)
        fire = task.user.environment.events.request.fire
        fire.assert_called_once()
        call_kwargs = fire.call_args[1]
        self.assertIsNone(call_kwargs["exception"])

        # NO error span - this is the silent retry masking
        errors = self._error_spans()
        self.assertEqual(
            len(errors), 0,
            "Expected NO error span when retry succeeds (silent masking)"
        )

    def test_success_no_error_span(self):
        """LocustCache.locust_redis_get → success → no error span."""
        conn = self._make_cluster_conn(execute_return="value")
        conn._process_result = Mock(return_value="value")

        task = _make_locust_task_mock()
        result = LocustCache.locust_redis_get(task, conn, "key1", "test")

        self.assertIsNotNone(result)

        fire = task.user.environment.events.request.fire
        fire.assert_called_once()
        call_kwargs = fire.call_args[1]
        self.assertIsNone(call_kwargs["exception"])

        errors = self._error_spans()
        self.assertEqual(len(errors), 0)


if __name__ == "__main__":
    unittest.main()
