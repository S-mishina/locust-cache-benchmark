import os
import logging

logger = logging.getLogger(__name__)

_otel_initialized = False


def setup_otel_tracing():
    """
    Initialize OpenTelemetry tracing with RedisInstrumentor.

    Reads OTEL_TRACING_ENABLED environment variable to determine
    whether to enable tracing. When enabled, configures a
    TracerProvider with BatchSpanProcessor and OTLPSpanExporter,
    then instruments redis-py via RedisInstrumentor.

    Returns:
        bool: True if tracing was successfully initialized, False otherwise.
    """
    global _otel_initialized

    if _otel_initialized:
        logger.debug("OpenTelemetry tracing already initialized, skipping.")
        return True

    enabled = os.environ.get("OTEL_TRACING_ENABLED", "false").lower()
    if enabled != "true":
        logger.debug("OpenTelemetry tracing is disabled.")
        return False

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.instrumentation.redis import RedisInstrumentor

        service_name = os.environ.get("OTEL_SERVICE_NAME", "locust-cache-benchmark")
        endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")

        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)

        RedisInstrumentor().instrument()

        _otel_initialized = True
        logger.info(
            "OpenTelemetry tracing initialized (service=%s, endpoint=%s).",
            service_name,
            endpoint,
        )
        return True
    except Exception:
        logger.exception("Failed to initialize OpenTelemetry tracing.")
        return False


def shutdown_otel_tracing():
    """
    Flush and shut down the OpenTelemetry TracerProvider.

    Returns:
        bool: True if shutdown was successful, False otherwise.
    """
    global _otel_initialized

    if not _otel_initialized:
        return False

    try:
        from opentelemetry import trace

        provider = trace.get_tracer_provider()
        if hasattr(provider, "force_flush"):
            provider.force_flush()
        if hasattr(provider, "shutdown"):
            provider.shutdown()

        _otel_initialized = False
        logger.info("OpenTelemetry tracing shut down successfully.")
        return True
    except Exception:
        logger.exception("Failed to shut down OpenTelemetry tracing.")
        return False
