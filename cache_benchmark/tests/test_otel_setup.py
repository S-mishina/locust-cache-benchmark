import unittest
from unittest.mock import patch, MagicMock
import cache_benchmark.otel_setup as otel_setup
from cache_benchmark.config import AppConfig, set_config, reset_config


class TestOtelSetup(unittest.TestCase):
    def setUp(self):
        otel_setup._otel_initialized = False
        reset_config()
        set_config(AppConfig())

    def tearDown(self):
        otel_setup._otel_initialized = False
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

        with patch("opentelemetry.trace.set_tracer_provider") as mock_set_provider, \
             patch("opentelemetry.sdk.trace.TracerProvider", return_value=mock_provider), \
             patch("opentelemetry.sdk.trace.export.BatchSpanProcessor", return_value=mock_processor), \
             patch("opentelemetry.exporter.otlp.proto.grpc.trace_exporter.OTLPSpanExporter", return_value=mock_exporter), \
             patch("opentelemetry.sdk.resources.Resource.create") as mock_resource, \
             patch("opentelemetry.instrumentation.redis.RedisInstrumentor", return_value=mock_instrumentor):

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

    @patch("opentelemetry.trace.set_tracer_provider", side_effect=Exception("init error"))
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

        with patch("opentelemetry.trace.get_tracer_provider", return_value=mock_provider):
            result = otel_setup.shutdown_otel_tracing()

            self.assertTrue(result)
            self.assertFalse(otel_setup._otel_initialized)
            mock_provider.force_flush.assert_called_once()
            mock_provider.shutdown.assert_called_once()

    def test_shutdown_exception_returns_false(self):
        otel_setup._otel_initialized = True

        with patch("opentelemetry.trace.get_tracer_provider", side_effect=Exception("shutdown error")):
            result = otel_setup.shutdown_otel_tracing()
            self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
