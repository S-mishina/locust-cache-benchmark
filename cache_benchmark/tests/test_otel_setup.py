import unittest
from unittest.mock import patch, MagicMock
import cache_benchmark.otel_setup as otel_setup
from cache_benchmark.config import AppConfig, set_config, reset_config


class TestOtelSetup(unittest.TestCase):
    def setUp(self):
        otel_setup._otel_initialized = False
        otel_setup._metrics_initialized = False
        reset_config()
        set_config(AppConfig())

    def tearDown(self):
        otel_setup._otel_initialized = False
        otel_setup._metrics_initialized = False
        reset_config()

    def test_setup_disabled_by_default(self):
        result = otel_setup.setup_otel_tracing()
        self.assertFalse(result)
        self.assertFalse(otel_setup._otel_initialized)

    def test_setup_disabled_explicitly(self):
        reset_config()
        set_config(AppConfig(otel_tracing_enabled=False))
        result = otel_setup.setup_otel_tracing()
        self.assertFalse(result)
        self.assertFalse(otel_setup._otel_initialized)

    def test_setup_enabled(self):
        reset_config()
        set_config(AppConfig(
            otel_tracing_enabled=True,
            otel_service_name="test-service",
            otel_exporter_endpoint="http://localhost:4317",
        ))

        mock_provider = MagicMock()
        mock_exporter = MagicMock()
        mock_processor = MagicMock()
        mock_instrumentor = MagicMock()

        with patch("cache_benchmark.otel_setup.trace.set_tracer_provider") as mock_set_provider, \
             patch("cache_benchmark.otel_setup.TracerProvider", return_value=mock_provider), \
             patch("cache_benchmark.otel_setup.BatchSpanProcessor", return_value=mock_processor), \
             patch("cache_benchmark.otel_setup.OTLPSpanExporter", return_value=mock_exporter), \
             patch("cache_benchmark.otel_setup.Resource.create"), \
             patch("cache_benchmark.otel_setup.RedisInstrumentor", return_value=mock_instrumentor):

            result = otel_setup.setup_otel_tracing()

            self.assertTrue(result)
            self.assertTrue(otel_setup._otel_initialized)
            mock_set_provider.assert_called_once_with(mock_provider)
            mock_provider.add_span_processor.assert_called_once_with(mock_processor)
            mock_instrumentor.instrument.assert_called_once()

    def test_setup_idempotent(self):
        otel_setup._otel_initialized = True
        result = otel_setup.setup_otel_tracing()
        self.assertTrue(result)

    @patch("cache_benchmark.otel_setup.trace.set_tracer_provider", side_effect=OSError("init error"))
    def test_setup_exception_returns_false(self, _mock):
        reset_config()
        set_config(AppConfig(otel_tracing_enabled=True))
        result = otel_setup.setup_otel_tracing()
        self.assertFalse(result)
        self.assertFalse(otel_setup._otel_initialized)

    def test_shutdown_when_not_initialized(self):
        result = otel_setup.shutdown_otel_tracing()
        self.assertFalse(result)

    def test_shutdown_success(self):
        otel_setup._otel_initialized = True
        mock_provider = MagicMock()
        mock_provider.force_flush = MagicMock()
        mock_provider.shutdown = MagicMock()

        with patch("cache_benchmark.otel_setup.trace.get_tracer_provider", return_value=mock_provider):
            result = otel_setup.shutdown_otel_tracing()

            self.assertTrue(result)
            self.assertFalse(otel_setup._otel_initialized)
            mock_provider.force_flush.assert_called_once()
            mock_provider.shutdown.assert_called_once()

    def test_shutdown_exception_returns_false(self):
        otel_setup._otel_initialized = True

        with patch("cache_benchmark.otel_setup.trace.get_tracer_provider", side_effect=OSError("shutdown error")):
            result = otel_setup.shutdown_otel_tracing()
            self.assertFalse(result)


class TestOtelMetrics(unittest.TestCase):
    def setUp(self):
        otel_setup._otel_initialized = False
        otel_setup._metrics_initialized = False
        reset_config()
        set_config(AppConfig())

    def tearDown(self):
        otel_setup._otel_initialized = False
        otel_setup._metrics_initialized = False
        reset_config()

    def test_metrics_disabled_by_default(self):
        result = otel_setup.setup_otel_metrics()
        self.assertFalse(result)
        self.assertFalse(otel_setup._metrics_initialized)

    def test_metrics_enabled_redis(self):
        reset_config()
        set_config(AppConfig(
            otel_metrics_enabled=True,
            cache_type="redis",
            otel_service_name="test-service",
            otel_exporter_endpoint="http://otel-collector:4317",
        ))

        mock_otel_instance = MagicMock()

        with patch("cache_benchmark.otel_setup.Resource.create"), \
             patch("cache_benchmark.otel_setup.OTLPMetricExporter"), \
             patch("cache_benchmark.otel_setup.PeriodicExportingMetricReader"), \
             patch("cache_benchmark.otel_setup.MeterProvider"), \
             patch("cache_benchmark.otel_setup.metrics.set_meter_provider"), \
             patch("cache_benchmark.otel_setup.get_observability_instance", return_value=mock_otel_instance):

            result = otel_setup.setup_otel_metrics()

            self.assertTrue(result)
            self.assertTrue(otel_setup._metrics_initialized)
            mock_otel_instance.init.assert_called_once()

    def test_metrics_enabled_redis_cluster(self):
        reset_config()
        set_config(AppConfig(
            otel_metrics_enabled=True,
            cache_type="redis_cluster",
            otel_service_name="test-service",
            otel_exporter_endpoint="http://otel-collector:4317",
        ))

        mock_otel_instance = MagicMock()

        with patch("cache_benchmark.otel_setup.Resource.create"), \
             patch("cache_benchmark.otel_setup.OTLPMetricExporter"), \
             patch("cache_benchmark.otel_setup.PeriodicExportingMetricReader"), \
             patch("cache_benchmark.otel_setup.MeterProvider"), \
             patch("cache_benchmark.otel_setup.metrics.set_meter_provider"), \
             patch("cache_benchmark.otel_setup.get_observability_instance", return_value=mock_otel_instance):

            result = otel_setup.setup_otel_metrics()

            self.assertTrue(result)
            self.assertTrue(otel_setup._metrics_initialized)

    def test_metrics_skipped_for_valkey(self):
        reset_config()
        set_config(AppConfig(
            otel_metrics_enabled=True,
            cache_type="valkey",
        ))

        with self.assertLogs("cache_benchmark.otel_setup", level="WARNING") as cm:
            result = otel_setup.setup_otel_metrics()

        self.assertFalse(result)
        self.assertFalse(otel_setup._metrics_initialized)
        self.assertTrue(any("only supported for Redis" in msg for msg in cm.output))

    def test_metrics_skipped_for_valkey_cluster(self):
        reset_config()
        set_config(AppConfig(
            otel_metrics_enabled=True,
            cache_type="valkey_cluster",
        ))

        with self.assertLogs("cache_benchmark.otel_setup", level="WARNING") as cm:
            result = otel_setup.setup_otel_metrics()

        self.assertFalse(result)
        self.assertFalse(otel_setup._metrics_initialized)
        self.assertTrue(any("only supported for Redis" in msg for msg in cm.output))

    def test_metrics_idempotent(self):
        otel_setup._metrics_initialized = True
        result = otel_setup.setup_otel_metrics()
        self.assertTrue(result)

    def test_metrics_shutdown(self):
        otel_setup._metrics_initialized = True

        mock_otel_instance = MagicMock()
        mock_provider = MagicMock()

        with patch("cache_benchmark.otel_setup.get_observability_instance", return_value=mock_otel_instance), \
             patch("cache_benchmark.otel_setup.metrics.get_meter_provider", return_value=mock_provider):
            result = otel_setup.shutdown_otel_metrics()

        self.assertTrue(result)
        self.assertFalse(otel_setup._metrics_initialized)
        mock_otel_instance.shutdown.assert_called_once()
        mock_provider.shutdown.assert_called_once()

    def test_metrics_shutdown_when_not_initialized(self):
        result = otel_setup.shutdown_otel_metrics()
        self.assertFalse(result)
        self.assertFalse(otel_setup._metrics_initialized)

    def test_metrics_exception_returns_false(self):
        reset_config()
        set_config(AppConfig(
            otel_metrics_enabled=True,
            cache_type="redis",
        ))

        with patch("cache_benchmark.otel_setup.Resource.create", side_effect=Exception("fail")):
            result = otel_setup.setup_otel_metrics()

        self.assertFalse(result)
        self.assertFalse(otel_setup._metrics_initialized)

    def test_metrics_warns_on_default_endpoint(self):
        reset_config()
        set_config(AppConfig(
            otel_metrics_enabled=True,
            cache_type="redis",
            otel_exporter_endpoint="http://localhost:4317",
        ))

        with self.assertLogs("cache_benchmark.otel_setup", level="WARNING") as cm:
            with patch("cache_benchmark.otel_setup.Resource.create", side_effect=Exception("fail")):
                otel_setup.setup_otel_metrics()

        self.assertTrue(any("default" in msg for msg in cm.output))

    def test_metrics_no_warning_on_custom_endpoint(self):
        reset_config()
        set_config(AppConfig(
            otel_metrics_enabled=True,
            cache_type="redis",
            otel_exporter_endpoint="http://otel-collector:4317",
        ))

        mock_otel_instance = MagicMock()

        with patch("cache_benchmark.otel_setup.Resource.create"), \
             patch("cache_benchmark.otel_setup.OTLPMetricExporter"), \
             patch("cache_benchmark.otel_setup.PeriodicExportingMetricReader"), \
             patch("cache_benchmark.otel_setup.MeterProvider"), \
             patch("cache_benchmark.otel_setup.metrics.set_meter_provider"), \
             patch("cache_benchmark.otel_setup.get_observability_instance", return_value=mock_otel_instance):
            with self.assertLogs("cache_benchmark.otel_setup", level="INFO") as cm:
                otel_setup.setup_otel_metrics()

            warning_msgs = [m for m in cm.output if "WARNING" in m and "default" in m]
            self.assertEqual(len(warning_msgs), 0)


class TestOtelTracingEndpointWarning(unittest.TestCase):
    def setUp(self):
        otel_setup._otel_initialized = False
        otel_setup._metrics_initialized = False
        reset_config()

    def tearDown(self):
        otel_setup._otel_initialized = False
        otel_setup._metrics_initialized = False
        reset_config()

    def test_tracing_warns_on_default_endpoint(self):
        reset_config()
        set_config(AppConfig(
            otel_tracing_enabled=True,
            otel_exporter_endpoint="http://localhost:4317",
        ))

        with self.assertLogs("cache_benchmark.otel_setup", level="WARNING") as cm:
            with patch("cache_benchmark.otel_setup.trace.set_tracer_provider"), \
                 patch("cache_benchmark.otel_setup.TracerProvider"), \
                 patch("cache_benchmark.otel_setup.BatchSpanProcessor"), \
                 patch("cache_benchmark.otel_setup.OTLPSpanExporter"), \
                 patch("cache_benchmark.otel_setup.Resource.create"), \
                 patch("cache_benchmark.otel_setup.RedisInstrumentor"):
                otel_setup.setup_otel_tracing()

        self.assertTrue(any("default" in msg for msg in cm.output))

    def test_tracing_no_warning_on_custom_endpoint(self):
        reset_config()
        set_config(AppConfig(
            otel_tracing_enabled=True,
            otel_exporter_endpoint="http://otel-collector:4317",
        ))

        with patch("cache_benchmark.otel_setup.trace.set_tracer_provider"), \
             patch("cache_benchmark.otel_setup.TracerProvider"), \
             patch("cache_benchmark.otel_setup.BatchSpanProcessor"), \
             patch("cache_benchmark.otel_setup.OTLPSpanExporter"), \
             patch("cache_benchmark.otel_setup.Resource.create"), \
             patch("cache_benchmark.otel_setup.RedisInstrumentor"):
            with self.assertLogs("cache_benchmark.otel_setup", level="INFO") as cm:
                otel_setup.setup_otel_tracing()

            warning_msgs = [m for m in cm.output if "WARNING" in m and "default" in m]
            self.assertEqual(len(warning_msgs), 0)


if __name__ == "__main__":
    unittest.main()
